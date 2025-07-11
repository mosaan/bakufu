"""JSON parsing text processing step"""

from typing import Any, Literal

from .base import TextProcessStep


class JsonParseStep(TextProcessStep):
    """JSON parsing text processing step"""

    method: Literal["json_parse"] = "json_parse"

    async def process(self, input_data: str, step_id: str) -> Any:
        """Parse JSON from text"""
        import json

        from ..exceptions import ErrorContext, StepExecutionError

        try:
            return json.loads(input_data.strip())
        except json.JSONDecodeError as e:
            raise StepExecutionError(
                message=f"Invalid JSON format: {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="JsonParseStep.process"),
                original_error=e,
                suggestions=[
                    "Check JSON syntax and quotes",
                    "Verify JSON structure is valid",
                    "Ensure all strings are properly quoted",
                    f"Text preview: {input_data.strip()[:100]}...",
                ],
            ) from e
