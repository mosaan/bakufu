"""Regex extraction text processing step"""

from typing import Literal

from pydantic import Field, field_validator

from .base import TextProcessStep


class RegexExtractStep(TextProcessStep):
    """Regex extraction text processing step"""

    method: Literal["regex_extract"] = "regex_extract"
    pattern: str = Field(..., description="Regex pattern for extraction")
    flags: list[str] | None = Field(None, description="Regex flags")
    output_format: Literal["string", "array"] = Field("string", description="Output format")

    @field_validator("pattern")
    @classmethod
    def pattern_required_for_regex(cls, v: str) -> str:
        if not v:
            raise ValueError("pattern is required for regex_extract method")
        return v

    async def process(self, input_data: str, step_id: str) -> str | list[str]:
        """Extract text using regex pattern"""
        import re

        from ..exceptions import ErrorContext, StepExecutionError
        from ..text_processing import TextExtractor

        if not self.pattern:
            raise StepExecutionError(
                message="Pattern is required for regex_extract",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="RegexExtractStep.process"),
                suggestions=["Provide a valid regex pattern"],
            )

        # Convert flag strings to re flags
        flag_value = 0
        flag_map = {
            "IGNORECASE": re.IGNORECASE,
            "MULTILINE": re.MULTILINE,
            "DOTALL": re.DOTALL,
            "VERBOSE": re.VERBOSE,
        }
        for flag in self.flags or []:
            if flag in flag_map:
                flag_value |= flag_map[flag]

        try:
            matches = TextExtractor.extract_by_regex(input_data, self.pattern, flags=flag_value)

            if self.output_format == "array":
                return matches
            else:
                return matches[0] if matches else ""

        except re.error as e:
            raise StepExecutionError(
                message=f"Invalid regex pattern '{self.pattern}': {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="RegexExtractStep.process"),
                original_error=e,
                suggestions=[
                    "Check regex syntax and escape special characters properly",
                    f"Pattern: {self.pattern}",
                ],
            ) from e
