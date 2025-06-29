"""Array sorting text processing step"""

from typing import Any, Literal

from pydantic import Field

from .base import TextProcessStep


class ArraySortStep(TextProcessStep):
    """Array sorting text processing step"""

    method: Literal["array_sort"] = "array_sort"
    sort_key: str | None = Field(None, description="Sort key")
    sort_reverse: bool = Field(False, description="Sort in reverse order")

    async def process(self, input_data: Any, step_id: str) -> list[Any]:
        """Sort array elements"""
        from ..exceptions import ErrorContext, StepExecutionError

        if not isinstance(input_data, list):
            raise StepExecutionError(
                message="Input must be an array for array_sort",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ArraySortStep.process"),
                suggestions=["Provide an array as input"],
            )

        try:
            if self.sort_key:
                # Sort by key
                def get_sort_value(item: Any) -> Any:
                    if isinstance(item, dict) and self.sort_key in item:
                        return item[self.sort_key]
                    elif self.sort_key and hasattr(item, self.sort_key):
                        return getattr(item, self.sort_key)
                    else:
                        return str(item)

                return sorted(input_data, key=get_sort_value, reverse=self.sort_reverse)
            else:
                # Natural sort
                return sorted(input_data, reverse=self.sort_reverse)
        except Exception as e:
            raise StepExecutionError(
                message=f"Error in sorting: {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ArraySortStep.process"),
                original_error=e,
                suggestions=["Check sort key exists in all items"],
            ) from e
