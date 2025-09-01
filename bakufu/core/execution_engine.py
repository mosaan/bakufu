"""Workflow execution engine for running steps sequentially

This module implements the main WorkflowExecutionEngine using the Command Pattern
with polymorphic dispatch for truly decoupled step execution.
"""

from collections.abc import Callable
from typing import Any

from .base_types import WorkflowStep
from .exceptions import (
    ErrorContext,
    StepExecutionError,
)
from .models import (
    ConditionalStep,
    ExecutionContext,
    Workflow,
)

# Type aliases for better type safety
type StepResult = Any  # Step results can be of various types based on step type
type WorkflowResults = dict[str, StepResult]  # Workflow results are step_id -> result mappings


class WorkflowExecutionEngine:
    """Engine for executing workflow steps using Command Pattern

    This class serves as the main orchestrator, using polymorphic dispatch
    to delegate execution to each step's own execute method.
    """

    def __init__(self, progress_callback: Callable | None = None) -> None:
        """Initialize execution engine"""
        self.progress_callback = progress_callback

    async def execute_workflow(
        self, workflow: Workflow, context: ExecutionContext
    ) -> WorkflowResults:
        """Execute complete workflow with all steps"""
        results = {}

        # Notify workflow start
        if self.progress_callback:
            self.progress_callback(
                "workflow_start", workflow_name=workflow.name, total_steps=len(workflow.steps)
            )

        for i, step in enumerate(workflow.steps, 1):
            # Notify step start
            if self.progress_callback:
                self.progress_callback(
                    "workflow_step", current_step=i, step_name=step.id, step_type=step.type
                )

            try:
                result = await self.execute_step(step, context)
                context.set_step_output(step.id, result)
                results[step.id] = result

            except Exception as e:
                error_context = ErrorContext(
                    step_id=step.id, workflow_name=workflow.name, function_name="execute_workflow"
                )

                if isinstance(e, StepExecutionError):
                    error = e
                else:
                    error = StepExecutionError(
                        message=str(e),
                        step_id=step.id,
                        workflow_name=workflow.name,
                        context=error_context,
                        original_error=e,
                    )

                if step.on_error == "stop":
                    raise error from e
                elif step.on_error == "continue":
                    context.set_step_output(step.id, None)
                    results[step.id] = None
                    continue
                elif step.on_error == "skip_remaining":
                    context.set_step_output(step.id, None)
                    results[step.id] = None
                    break

        # Notify workflow completion
        if self.progress_callback:
            self.progress_callback("workflow_complete")

        return results

    async def execute_step(self, step: WorkflowStep, context: ExecutionContext) -> StepResult:
        """Execute a single workflow step using polymorphic dispatch (Command Pattern)"""
        # For ConditionalStep, we need to provide step_executor for nested execution
        if isinstance(step, ConditionalStep):
            return await step.execute(context, step_executor=self.execute_step)

        # For all other steps, use polymorphic execute method
        return await step.execute(context)

    # Compatibility methods for tests - delegate to strategies
    async def _execute_ai_call_step(
        self, step: WorkflowStep, context: ExecutionContext
    ) -> StepResult:
        """Delegate to step's execute method for backward compatibility with tests"""
        return await step.execute(context)

    async def _execute_collection_step(
        self, step: WorkflowStep, context: ExecutionContext
    ) -> StepResult:
        """Delegate to step's execute method for backward compatibility with tests"""
        return await step.execute(context)

    async def _execute_text_process_step(
        self, step: WorkflowStep, context: ExecutionContext
    ) -> StepResult:
        """Delegate to step's execute method for backward compatibility with tests"""
        return await step.execute(context)

    async def _execute_conditional_step(
        self, step: WorkflowStep, context: ExecutionContext
    ) -> StepResult:
        """Delegate to step's execute method for backward compatibility with tests"""
        return await step.execute(context)
