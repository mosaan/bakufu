"""Conditional execution step models for Bakufu workflows"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, field_validator

from ...base_types import WorkflowStep
from ...step_registry import step_type

# Import for type hints only to avoid circular imports
if TYPE_CHECKING:
    from ...models import ConditionalResult, ExecutionContext
    from ..base import AnyWorkflowStep

    # Type alias for step executor function
    StepExecutor = Callable[[WorkflowStep, ExecutionContext], Awaitable[Any]]


class ConditionalBranch(BaseModel):
    """A single conditional branch definition"""

    condition: str = Field(..., description="Condition expression with Jinja2 syntax")
    name: str = Field(..., description="Branch name for identification")
    steps: list[AnyWorkflowStep] = Field(..., description="Steps to execute in this branch")
    default: bool = Field(default=False, description="Whether this is the default branch")

    def model_post_init(self, __context: Any) -> None:
        """Validate condition requirements after all fields are set"""
        if not self.default and not self.condition.strip():
            raise ValueError("Condition cannot be empty for non-default branches")

    @field_validator("condition")
    @classmethod
    def validate_condition_or_default(cls, v: str, info: Any) -> str:
        # Allow empty condition for default branches
        # We need to check this after all fields are processed, not here
        return v


@step_type("conditional")
class ConditionalStep(WorkflowStep):
    """Conditional execution step with if-else or multi-branch support"""

    type: Literal["conditional"] = "conditional"

    # Basic if-else structure (optional)
    condition: str | None = Field(None, description="Simple condition for if-else structure")
    if_true: list[AnyWorkflowStep] | None = Field(
        None, description="Steps to execute when condition is true"
    )
    if_false: list[AnyWorkflowStep] | None = Field(
        None, description="Steps to execute when condition is false"
    )

    # Multi-branch structure (optional)
    conditions: list[ConditionalBranch] | None = Field(
        None, description="Multiple conditional branches"
    )

    # Error handling
    on_condition_error: Literal["stop", "continue", "skip_remaining"] = Field(
        default="stop", description="Action when condition evaluation fails"
    )

    @field_validator("conditions")
    @classmethod
    def validate_conditions_structure(
        cls, v: list[ConditionalBranch] | None, info: Any
    ) -> list[ConditionalBranch] | None:
        if v is None:
            return v

        # Check for duplicate names
        names = [branch.name for branch in v]
        if len(names) != len(set(names)):
            raise ValueError("Branch names must be unique")

        # Check for multiple default branches
        default_count = sum(1 for branch in v if branch.default)
        if default_count > 1:
            raise ValueError("Only one default branch is allowed")

        return v

    @field_validator("condition")
    @classmethod
    def validate_simple_condition(cls, v: str | None, info: Any) -> str | None:
        # Ensure either basic if-else or multi-branch is used, not both
        if v is not None and info.data.get("conditions") is not None:
            raise ValueError("Cannot use both 'condition' and 'conditions' fields")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that either basic or multi-branch structure is provided"""
        has_basic = self.condition is not None
        has_multi = self.conditions is not None

        if not has_basic and not has_multi:
            raise ValueError("Either 'condition' or 'conditions' must be provided")

        if has_basic and has_multi:
            raise ValueError("Cannot use both basic and multi-branch structures")

        # For basic structure, at least if_true should be provided
        if has_basic and self.if_true is None:
            raise ValueError("'if_true' steps must be provided for basic conditional structure")

    async def execute(self, context: Any, step_executor: StepExecutor | None = None) -> Any:
        """Execute conditional step directly using Command Pattern

        Args:
            context: Execution context
            step_executor: Function to execute nested steps (to avoid circular import)
        """
        from typing import cast

        from ...exceptions import (
            ErrorContext,
            StepExecutionError,
            TemplateError,
        )
        from ...models import ExecutionContext

        context = cast(ExecutionContext, context)

        if step_executor is None:
            raise RuntimeError(
                "step_executor not provided - ConditionalStep needs a step executor for nested steps"
            )

        try:
            if self.condition is not None:
                # Basic if-else structure
                return await self._execute_basic_conditional(context, step_executor)
            elif self.conditions is not None:
                # Multi-branch structure
                return await self._execute_multi_branch_conditional(context, step_executor)
            else:
                raise StepExecutionError(
                    message="Conditional step has neither 'condition' nor 'conditions' field",
                    step_id=self.id,
                    context=ErrorContext(step_id=self.id, function_name="execute"),
                    suggestions=["Check conditional step configuration"],
                )
        except (StepExecutionError, TemplateError):
            # Re-raise StepExecutionError and TemplateError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise StepExecutionError(
                message=f"Conditional step execution failed: {e}",
                step_id=self.id,
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    "Check conditional step configuration",
                    "Verify condition template syntax",
                ],
            ) from e

    async def _execute_basic_conditional(
        self, context: ExecutionContext, step_executor: StepExecutor
    ) -> ConditionalResult:
        """Execute basic if-else conditional structure"""
        from ...models import ConditionalResult

        condition_result = None
        evaluation_error = None
        executed_branch = None
        output = None

        # Evaluate condition
        try:
            condition_result_raw = context.render_template_object(self.condition or "")
            # Handle different types that Jinja2 might return
            if isinstance(condition_result_raw, str):
                # If it's a string representation, evaluate it as Python expression
                condition_result = condition_result_raw.lower() in ("true", "1", "yes")
            else:
                condition_result = bool(condition_result_raw)
        except Exception as e:
            evaluation_error = str(e)
            # Handle condition evaluation error based on configuration
            if self.on_condition_error == "stop":
                from ...exceptions import ErrorContext, TemplateError

                raise TemplateError(
                    message=f"Condition evaluation failed: {e}",
                    template_content=self.condition or "",
                    line_number=getattr(e, "lineno", None),
                    context=ErrorContext(
                        step_id=self.id, function_name="_execute_basic_conditional"
                    ),
                    original_error=e,
                    suggestions=[
                        "Check condition template syntax",
                        "Verify all variables are available in context",
                        f"Condition: {self.condition}",
                    ],
                ) from e
            elif self.on_condition_error == "continue":
                # Treat as false and continue
                condition_result = False
            elif self.on_condition_error == "skip_remaining":
                # Return empty result
                return ConditionalResult(
                    output=None,
                    condition_result=None,
                    executed_branch=None,
                    evaluation_error=evaluation_error,
                )

        # Execute appropriate branch
        try:
            if condition_result and self.if_true:
                executed_branch = "if_true"
                output = await self._execute_step_list(self.if_true, context, step_executor)
            elif not condition_result and self.if_false:
                executed_branch = "if_false"
                output = await self._execute_step_list(self.if_false, context, step_executor)
            # If no matching branch, output remains None
        except Exception:
            # Handle execution errors in branches based on parent step's on_error setting
            if self.on_error == "stop":
                raise
            elif self.on_error in {"continue", "skip_remaining"}:
                output = None

        return ConditionalResult(
            output=output,
            condition_result=condition_result,
            executed_branch=executed_branch,
            evaluation_error=evaluation_error,
        )

    async def _execute_multi_branch_conditional(
        self, context: ExecutionContext, step_executor: StepExecutor
    ) -> ConditionalResult:
        """Execute multi-branch conditional structure"""
        from ...exceptions import ErrorContext, TemplateError
        from ...models import ConditionalResult

        condition_result = None
        evaluation_error = None
        executed_branch = None
        output = None

        # Evaluate conditions in order until one matches
        for branch in self.conditions or []:
            if branch.default:
                # Default branch - execute if no other branch matched
                if executed_branch is None:
                    executed_branch = branch.name
                    output = await self._execute_step_list(branch.steps, context, step_executor)
                    condition_result = True  # Default branch is considered "true"
                break
            else:
                # Regular condition branch
                try:
                    condition_result_raw = context.render_template_object(branch.condition)
                    # Handle different types that Jinja2 might return
                    if isinstance(condition_result_raw, str):
                        # If it's a string representation, evaluate it as Python expression
                        condition_result = condition_result_raw.lower() in ("true", "1", "yes")
                    else:
                        condition_result = bool(condition_result_raw)

                    if condition_result:
                        executed_branch = branch.name
                        output = await self._execute_step_list(branch.steps, context, step_executor)
                        break
                except Exception as e:
                    evaluation_error = str(e)
                    # Handle condition evaluation error
                    if self.on_condition_error == "stop":
                        raise TemplateError(
                            message=f"Branch '{branch.name}' condition evaluation failed: {e}",
                            template_content=branch.condition,
                            line_number=getattr(e, "lineno", None),
                            context=ErrorContext(
                                step_id=self.id, function_name="_execute_multi_branch_conditional"
                            ),
                            original_error=e,
                            suggestions=[
                                "Check branch condition template syntax",
                                "Verify all variables are available in context",
                                f"Branch: {branch.name}, Condition: {branch.condition}",
                            ],
                        ) from e
                    elif self.on_condition_error == "continue":
                        # Skip this branch and continue to next
                        continue
                    elif self.on_condition_error == "skip_remaining":
                        # Return empty result
                        return ConditionalResult(
                            output=None,
                            condition_result=None,
                            executed_branch=None,
                            evaluation_error=evaluation_error,
                        )

        # If no branch was executed, set condition_result to None for multi-branch
        if executed_branch is None and not evaluation_error:
            condition_result = None

        return ConditionalResult(
            output=output,
            condition_result=condition_result,
            executed_branch=executed_branch,
            evaluation_error=evaluation_error,
        )

    async def _execute_step_list(
        self,
        steps: Sequence[WorkflowStep],
        context: ExecutionContext,
        step_executor: StepExecutor | None,
    ) -> Any:
        """Execute a list of steps and return the output of the last step"""
        if step_executor is None:
            raise RuntimeError(
                "step_executor not provided - ConditionalStep needs a step executor for nested steps"
            )

        last_output = None

        for step in steps:
            result = await step_executor(step, context)
            context.set_step_output(step.id, result)
            last_output = result

        return last_output
