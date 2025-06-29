"""Text replacement processing step"""

from typing import Literal

from pydantic import Field, field_validator

from .base import TextProcessStep


class ReplaceStep(TextProcessStep):
    """Text replacement processing step"""

    method: Literal["replace"] = "replace"
    replacements: list[dict[str, str]] = Field(..., description="Replacement rules")

    @field_validator("replacements")
    @classmethod
    def replacements_required_for_replace(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        # Allow empty list, but not None (which is handled by Field(...))
        return v

    async def process(self, input_data: str, step_id: str) -> str:
        """Replace text using replacement rules"""
        import re

        from ..exceptions import ErrorContext, StepExecutionError

        if not self.replacements:
            return input_data

        result = input_data
        for replacement in self.replacements:
            try:
                if "from" in replacement and "to" in replacement:
                    result = result.replace(replacement["from"], replacement["to"])
                elif "pattern" in replacement and "to" in replacement:
                    # Regex replacement
                    result = re.sub(replacement["pattern"], replacement["to"], result)
            except re.error as e:
                raise StepExecutionError(
                    message=f"Invalid replacement pattern: {e}",
                    step_id=step_id,
                    context=ErrorContext(step_id=step_id, function_name="ReplaceStep.process"),
                    original_error=e,
                    suggestions=[
                        "Check replacement pattern syntax",
                        f"Replacement: {replacement}",
                    ],
                ) from e

        return result
