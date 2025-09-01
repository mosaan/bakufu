"""Select items from array processing step"""

from typing import Any, Literal

from pydantic import Field, field_validator

from ..step_registry import step_type
from .base import TextProcessStep


@step_type("text_process", "select_item")
class SelectItemStep(TextProcessStep):
    """Select items from array processing step"""

    method: Literal["select_item"] = "select_item"
    index: int | None = Field(None, description="Index to select")
    slice: str | None = Field(None, description="Slice notation (e.g., '1:3', ':2', '1:')")
    condition: str | None = Field(None, description="Python condition to filter items")

    @field_validator("slice")
    @classmethod
    def validate_slice(cls, v: str | None) -> str | None:
        if v is None:
            return v

        # Basic validation of slice format
        if ":" not in v:
            raise ValueError("Slice must contain ':' character")

        MAX_SLICE_PARTS = 3
        parts = v.split(":")
        if len(parts) > MAX_SLICE_PARTS:
            raise ValueError("Slice cannot have more than 3 parts")

        # Validate each part is empty or a valid integer
        for part in parts:
            if part and not (part.isdigit() or (part.startswith("-") and part[1:].isdigit())):
                raise ValueError(f"Invalid slice part: '{part}'")

        return v

    def _parse_input_data(self, input_data: str | list) -> list:
        """Convert input data to list format"""
        if isinstance(input_data, str):
            try:
                import json

                data = json.loads(input_data)
                if not isinstance(data, list):
                    raise ValueError("Input must be a JSON array")
                return data
            except (json.JSONDecodeError, ValueError):
                # Treat as comma-separated values
                return [item.strip() for item in input_data.split(",")]

        if not isinstance(input_data, list):
            raise ValueError("Input must be a list or array")
        return input_data

    def _validate_selection_parameters(self) -> None:
        """Validate that exactly one selection parameter is provided"""
        selection_methods = [
            self.index is not None,
            self.slice is not None,
            self.condition is not None,
        ]
        if sum(selection_methods) != 1:
            raise ValueError("Exactly one of 'index', 'slice', or 'condition' must be specified")

    def _select_by_index(self, data: list) -> Any:
        """Select item by index"""
        if self.index is None:
            raise ValueError("Index must be specified")
        if abs(self.index) >= len(data):
            raise IndexError(f"Index {self.index} out of range for array of length {len(data)}")
        return data[self.index]

    def _select_by_slice(self, data: list) -> list:
        """Select items by slice notation"""
        if self.slice is None:
            raise ValueError("Slice must be specified")
        STEP_PART_INDEX = 2
        parts = self.slice.split(":")
        start = int(parts[0]) if parts[0] else None
        end = int(parts[1]) if len(parts) > 1 and parts[1] else None
        step = (
            int(parts[STEP_PART_INDEX])
            if len(parts) > STEP_PART_INDEX and parts[STEP_PART_INDEX]
            else None
        )
        return data[start:end:step]

    def _select_by_condition(self, data: list) -> list:
        """Select items by condition evaluation"""
        if self.condition is None:
            raise ValueError("Condition must be specified")
        safe_globals = {"len": len, "str": str, "int": int, "float": float}
        filtered_items = []

        for item in data:
            try:
                local_scope = {"item": item}
                if eval(self.condition, safe_globals, local_scope):
                    filtered_items.append(item)
            except Exception as e:
                raise ValueError(
                    f"Error evaluating condition '{self.condition}' on item '{item}': {e}"
                ) from e

        return filtered_items

    async def process(self, input_data: str | list, step_id: str) -> Any:
        """Select items from array based on index, slice, or condition"""
        from ..exceptions import ErrorContext, StepExecutionError

        try:
            # Convert input to list format
            data = self._parse_input_data(input_data)

            # Validate selection parameters
            self._validate_selection_parameters()

            # Apply selection based on parameter type
            if self.index is not None:
                return self._select_by_index(data)
            elif self.slice is not None:
                return self._select_by_slice(data)
            elif self.condition is not None:
                return self._select_by_condition(data)

        except Exception as e:
            raise StepExecutionError(
                message=f"Failed to select items: {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="SelectItemStep.process"),
                original_error=e,
                suggestions=[
                    "Check that input is a valid array or JSON array",
                    "Verify index is within array bounds",
                    "Check slice notation syntax (e.g., '1:3', ':2', '1:')",
                    "Ensure condition uses safe Python syntax",
                    f"Input type: {type(input_data)}, value preview: {str(input_data)[:100]}...",
                ],
            ) from e
