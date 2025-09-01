"""Jinja2 template formatting processing step"""

from typing import Any, Literal

from pydantic import Field, field_validator

from ..exceptions import ErrorContext, StepExecutionError
from ..step_registry import step_type
from .base import TextProcessStep

# Constants for template truncation in error messages
TEMPLATE_PREVIEW_LENGTH = 100
TEMPLATE_SHORT_PREVIEW_LENGTH = 50


@step_type("text_process", "format")
class FormatStep(TextProcessStep):
    """Jinja2 template formatting processing step"""

    method: Literal["format"] = "format"
    template: str = Field(..., description="Jinja2 template string for formatting")

    @field_validator("template")
    @classmethod
    def validate_template_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Template cannot be empty")
        return v

    async def process(self, input_data: Any, step_id: str) -> str:
        """Process input using Jinja2 template formatting

        Note: This method receives input_data, but the actual template context
        is provided by the ExecutionEngine through the ExecutionContext.
        The input_data is available as 'input' in the template context.
        """
        # Import here to avoid circular imports during module loading
        from ..template_engine import TemplateRenderError, WorkflowTemplateEngine

        try:
            # Create a template engine instance
            # Note: In the actual execution, this will use the context's template engine
            # which already has access to steps, input variables, etc.
            # This is a fallback implementation for direct testing
            engine = WorkflowTemplateEngine()

            # For direct testing, create a minimal context
            # In real execution, the context will be richer with steps, input, etc.
            template_context = {
                "input": input_data,
            }

            result = engine.render(self.template, template_context)
            return result

        except TemplateRenderError as e:
            raise StepExecutionError(
                message=f"Template rendering failed: {e.message}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="FormatStep.process"),
                original_error=e,
                suggestions=[
                    "Check template syntax",
                    "Verify all variables are available in context",
                    "Check for typos in variable names",
                    f"Template: {self.template[:TEMPLATE_PREVIEW_LENGTH]}{'...' if len(self.template) > TEMPLATE_PREVIEW_LENGTH else ''}",
                ],
            ) from e
        except Exception as e:
            raise StepExecutionError(
                message=f"Unexpected template processing error: {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="FormatStep.process"),
                original_error=e,
                suggestions=[
                    "Check template content for unusual patterns",
                    "Verify input data format",
                    f"Template: {self.template[:TEMPLATE_SHORT_PREVIEW_LENGTH]}{'...' if len(self.template) > TEMPLATE_SHORT_PREVIEW_LENGTH else ''}",
                ],
            ) from e

    async def process_with_context(self, template_context: dict[str, Any], step_id: str) -> str:
        """Process using provided template context (used by ExecutionEngine)

        This method is called by the ExecutionEngine with the full template context
        that includes steps, input variables, etc.
        """
        from ..template_engine import TemplateRenderError, WorkflowTemplateEngine

        try:
            engine = WorkflowTemplateEngine()
            result = engine.render(self.template, template_context)
            return result

        except TemplateRenderError as e:
            raise StepExecutionError(
                message=f"Template rendering failed: {e.message}",
                step_id=step_id,
                context=ErrorContext(
                    step_id=step_id, function_name="FormatStep.process_with_context"
                ),
                original_error=e,
                suggestions=[
                    "Check template syntax",
                    "Verify all variables are available in context",
                    "Check for typos in variable names",
                    f"Available variables: {', '.join(template_context.keys())}",
                    f"Template: {self.template[:TEMPLATE_PREVIEW_LENGTH]}{'...' if len(self.template) > TEMPLATE_PREVIEW_LENGTH else ''}",
                ],
            ) from e
        except Exception as e:
            raise StepExecutionError(
                message=f"Unexpected template processing error: {e}",
                step_id=step_id,
                context=ErrorContext(
                    step_id=step_id, function_name="FormatStep.process_with_context"
                ),
                original_error=e,
                suggestions=[
                    "Check template content for unusual patterns",
                    "Verify template context data",
                    f"Template: {self.template[:TEMPLATE_SHORT_PREVIEW_LENGTH]}{'...' if len(self.template) > TEMPLATE_SHORT_PREVIEW_LENGTH else ''}",
                ],
            ) from e
