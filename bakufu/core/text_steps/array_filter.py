"""Array filtering text processing step"""

from typing import Any, Literal

from pydantic import Field

from .base import TextProcessStep


class ArrayFilterStep(TextProcessStep):
    """Array filtering text processing step"""

    method: Literal["array_filter"] = "array_filter"
    condition: str = Field(..., description="Filter condition")

    async def process(self, input_data: Any, step_id: str) -> list[Any]:
        """Filter array elements based on condition"""
        from ..exceptions import ErrorContext, StepExecutionError

        if not isinstance(input_data, list):
            raise StepExecutionError(
                message="Input must be an array for array_filter",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ArrayFilterStep.process"),
                suggestions=["Provide an array as input"],
            )

        if not self.condition:
            return input_data

        filtered = []
        for item in input_data:
            try:
                if await self._evaluate_condition(item, self.condition):
                    filtered.append(item)
            except Exception as e:
                raise StepExecutionError(
                    message=f"Error evaluating condition: {e}",
                    step_id=step_id,
                    context=ErrorContext(step_id=step_id, function_name="ArrayFilterStep.process"),
                    original_error=e,
                    suggestions=["Check condition syntax"],
                ) from e

        return filtered

    async def _evaluate_condition(self, item: Any, condition: str) -> bool:
        """Evaluate filter condition for an item"""
        # Try direct evaluation first
        try:
            return bool(eval(condition, {"item": item}))
        except Exception:
            pass

        # Handle dict items with dot notation
        if isinstance(item, dict):
            return self._evaluate_dict_condition(item, condition)

        # Fallback to string matching
        return condition.lower() in str(item).lower()

    def _evaluate_dict_condition(self, item: dict, condition: str) -> bool:
        """Evaluate condition for dictionary items"""
        import re

        # Replace item.key with item["key"] in condition
        condition_eval = condition
        for key in item:
            pattern = rf"item\.{key}\b"
            replacement = f'item["{key}"]'
            condition_eval = re.sub(pattern, replacement, condition_eval)

        try:
            return bool(eval(condition_eval, {"item": item}))
        except Exception:
            # Fallback to string matching
            return str(item).find(condition) != -1
