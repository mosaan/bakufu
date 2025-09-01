"""Extract text between markers processing step"""

from typing import Literal

from pydantic import Field

from ..step_registry import step_type
from .base import TextProcessStep


@step_type("text_process", "extract_between_marker")
class ExtractBetweenMarkerStep(TextProcessStep):
    """Extract text between markers processing step"""

    method: Literal["extract_between_marker"] = "extract_between_marker"
    begin: str = Field(..., description="Beginning marker")
    end: str = Field(..., description="Ending marker")
    extract_all: bool = Field(False, description="Extract all matches, not just the first")

    async def process(self, input_data: str, step_id: str) -> str | list[str]:
        """Extract text between begin and end markers"""
        from ..exceptions import ErrorContext, StepExecutionError

        try:
            if self.extract_all:
                results = []
                text = input_data
                while True:
                    begin_idx = text.find(self.begin)
                    if begin_idx == -1:
                        break

                    start_pos = begin_idx + len(self.begin)
                    end_idx = text.find(self.end, start_pos)
                    if end_idx == -1:
                        break

                    results.append(text[start_pos:end_idx])
                    text = text[end_idx + len(self.end) :]

                return results
            else:
                begin_idx = input_data.find(self.begin)
                if begin_idx == -1:
                    return ""

                start_pos = begin_idx + len(self.begin)
                end_idx = input_data.find(self.end, start_pos)
                if end_idx == -1:
                    return ""

                return input_data[start_pos:end_idx]

        except Exception as e:
            raise StepExecutionError(
                message=f"Failed to extract text between markers: {e}",
                step_id=step_id,
                context=ErrorContext(
                    step_id=step_id, function_name="ExtractBetweenMarkerStep.process"
                ),
                original_error=e,
                suggestions=[
                    "Check if begin and end markers exist in the input",
                    f"Begin marker: '{self.begin}'",
                    f"End marker: '{self.end}'",
                    f"Input preview: {input_data[:100]}...",
                ],
            ) from e
