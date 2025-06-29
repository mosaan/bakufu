"""Array aggregation text processing step"""

from typing import Any, Literal

from pydantic import Field

from .base import TextProcessStep


class ArrayAggregateStep(TextProcessStep):
    """Array aggregation text processing step"""

    method: Literal["array_aggregate"] = "array_aggregate"
    aggregate_operation: Literal["sum", "avg", "min", "max", "count", "join"] = Field(
        ..., description="Aggregation operation"
    )
    separator: str | None = Field(None, description="Separator for join operation")

    async def process(self, input_data: Any, step_id: str) -> Any:
        """Aggregate array elements"""
        from ..exceptions import ErrorContext, StepExecutionError

        if not isinstance(input_data, list):
            raise StepExecutionError(
                message="Input must be an array for array_aggregate",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ArrayAggregateStep.process"),
                suggestions=["Provide an array as input"],
            )

        try:
            if self.aggregate_operation == "count":
                return len(input_data)
            elif self.aggregate_operation == "sum":
                numbers = [x for x in input_data if isinstance(x, int | float)]
                return sum(numbers) if numbers else 0
            elif self.aggregate_operation == "avg":
                numbers = [x for x in input_data if isinstance(x, int | float)]
                return sum(numbers) / len(numbers) if numbers else 0
            elif self.aggregate_operation == "min":
                numbers = [x for x in input_data if isinstance(x, int | float)]
                return min(numbers) if numbers else None
            elif self.aggregate_operation == "max":
                numbers = [x for x in input_data if isinstance(x, int | float)]
                return max(numbers) if numbers else None
            elif self.aggregate_operation == "join":
                separator = self.separator or ", "
                return separator.join(str(item) for item in input_data)
            else:
                raise StepExecutionError(
                    message=f"Unknown aggregate operation: {self.aggregate_operation}",
                    step_id=step_id,
                    context=ErrorContext(
                        step_id=step_id, function_name="ArrayAggregateStep.process"
                    ),
                    suggestions=["Use one of: sum, avg, min, max, count, join"],
                )
        except Exception as e:
            raise StepExecutionError(
                message=f"Error in aggregation: {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ArrayAggregateStep.process"),
                original_error=e,
                suggestions=["Check input data types match the operation"],
            ) from e
