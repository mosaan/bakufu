"""Collection operation step models for Bakufu workflows"""

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, field_validator

from ...base_types import WorkflowStep
from ...step_registry import step_type

# Import for type hints only to avoid circular imports
if TYPE_CHECKING:
    from ...text_steps import AnyTextProcessStep
    from .ai import AICallStep


class CollectionErrorHandling(BaseModel):
    """Error handling configuration for collection operations"""

    on_item_failure: Literal["skip", "stop", "retry"] = Field(
        default="skip", description="Action on individual item failure"
    )
    on_condition_error: Literal["skip_item", "stop", "default_false"] = Field(
        default="skip_item", description="Action when condition evaluation fails"
    )
    max_retries_per_item: int = Field(default=2, ge=0, description="Maximum retries per item")
    preserve_errors: bool = Field(default=True, description="Keep error information in results")


class CollectionStep(WorkflowStep):
    """Collection operation step for functional programming operations"""

    type: Literal["collection"] = "collection"
    operation: Literal[
        "map", "filter", "reduce", "zip", "group_by", "sort", "flatten", "distinct", "pipeline"
    ] = Field(..., description="Collection operation to perform")
    input: str = Field(..., description="Input data reference with Jinja2 syntax")

    # Error handling
    error_handling: CollectionErrorHandling = Field(default_factory=CollectionErrorHandling)

    # Concurrency for operations that support it (like map)
    concurrency: dict[str, Any] | None = Field(
        None, description="Concurrency settings for parallel operations"
    )

    async def execute(self, context: Any) -> Any:
        """Execute collection step directly using Command Pattern"""
        from collections.abc import Callable
        from typing import cast

        from ...collection_processors import CollectionProcessor
        from ...exceptions import (
            ErrorContext,
            StepExecutionError,
            TemplateError,
        )
        from ...models import ExecutionContext

        context = cast(ExecutionContext, context)

        # Render input template to get the collection
        input_attr = getattr(self, "input", None)
        if not input_attr:
            raise StepExecutionError(
                message="Collection step missing required 'input' attribute",
                step_id=self.id,
                workflow_name=context.workflow_name,
            )

        try:
            input_data = context.render_template_object(input_attr)
        except Exception as e:
            raise TemplateError(
                message=f"Collection step input template rendering failed: {e}",
                template_content=str(input_attr),
                line_number=getattr(e, "lineno", None),
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    "Check input template syntax",
                    "Verify all variables are available in context",
                    f"Template: {str(input_attr)[:50]}...",
                ],
            ) from e

        # Create and execute collection processor
        try:
            # Note: progress_callback is not available at step level,
            # could be added in future if needed
            progress_callback: Callable | None = None
            processor = CollectionProcessor(self, progress_callback)
            result = await processor.process(input_data, context)

            # Return the output, but store the full CollectionResult for debugging
            # For now, we return just the output to maintain compatibility
            return result.output

        except StepExecutionError:
            # Re-raise StepExecutionError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise StepExecutionError(
                message=f"Collection operation failed: {e}",
                step_id=self.id,
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    f"Check {getattr(self, 'operation', 'unknown')} operation configuration",
                    "Verify input data is a list/array",
                    "Check operation-specific parameters",
                ],
            ) from e


@step_type("collection", "map")
class MapOperation(CollectionStep):
    """Map operation - transform each element"""

    operation: Literal["map"] = "map"
    steps: list["AICallStep | AnyTextProcessStep"] = Field(
        ..., description="Steps to apply to each item"
    )


@step_type("collection", "filter")
class FilterOperation(CollectionStep):
    """Filter operation - select elements matching a condition"""

    operation: Literal["filter"] = "filter"
    condition: str = Field(
        ..., description="Filter condition with Jinja2 syntax, using 'item' variable"
    )

    @field_validator("condition")
    @classmethod
    def validate_condition_has_item_reference(cls, v: str) -> str:
        if "item" not in v:
            raise ValueError("Condition must reference 'item' variable")
        return v


@step_type("collection", "reduce")
class ReduceOperation(CollectionStep):
    """Reduce operation - aggregate elements into a single value"""

    operation: Literal["reduce"] = "reduce"
    initial_value: Any = Field(default=None, description="Initial accumulator value")
    accumulator_var: str = Field(default="acc", description="Variable name for accumulator")
    item_var: str = Field(default="item", description="Variable name for current item")
    steps: list["AICallStep | AnyTextProcessStep"] = Field(
        ..., description="Steps to apply for reduction"
    )


@step_type("collection", "pipeline")
class PipelineOperation(CollectionStep):
    """Pipeline operation - chain multiple collection operations"""

    operation: Literal["pipeline"] = "pipeline"
    pipeline: list[dict[str, Any]] = Field(..., description="List of operations to chain")
