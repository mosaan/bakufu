"""Base class for text processing steps"""

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import Field

from ..base_types import WorkflowStep


class TextProcessStep(WorkflowStep, ABC):
    """Text processing step with polymorphic behavior"""

    type: Literal["text_process"] = "text_process"
    method: Literal[
        "regex_extract",
        "replace",
        "json_parse",
        "markdown_split",
        "fixed_split",
        "split",
        "extract_between_marker",
        "select_item",
        "parse_as_json",
        "format",
        "csv_parse",
        "tsv_parse",
        "yaml_parse",
    ]
    input: str = Field(..., description="Input text with template syntax")

    @abstractmethod
    async def process(self, input_data: Any, step_id: str) -> Any:
        """Process the input data and return the result"""
        pass

    async def execute(self, context: Any) -> Any:
        """Execute text processing step directly using Command Pattern"""
        from typing import cast

        from ..exceptions import (
            ErrorContext,
            StepExecutionError,
            TemplateError,
        )
        from ..models import ExecutionContext

        context = cast(ExecutionContext, context)

        # Render input template
        try:
            input_text = context.render_template(self.input)
        except Exception as e:
            raise TemplateError(
                message=f"Text processing step input template rendering failed: {e}",
                template_content=self.input,
                line_number=getattr(e, "lineno", None),
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    "Check input template syntax",
                    "Verify all variables are available in context",
                    f"Template: {self.input[:50]}...",
                ],
            ) from e

        # Use direct process method on step
        try:
            # Special handling for FormatStep to provide rich template context
            if self.method == "format" and hasattr(self, "process_with_context"):
                # FormatStep needs the full template context, not just the input text
                template_context = context.get_template_context()
                # Add the rendered input as 'input' in the context for compatibility
                template_context["input"] = input_text
                return await self.process_with_context(template_context, self.id)  # type: ignore
            else:
                return await self.process(input_text, self.id)
        except StepExecutionError:
            # Re-raise StepExecutionError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise StepExecutionError(
                message=f"Text processing failed: {e}",
                step_id=self.id,
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    f"Check {self.method} method configuration",
                    "Verify input text format",
                ],
            ) from e
