"""Jinja2 template engine for workflow variable substitution"""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, StrictUndefined, TemplateError, meta


class TemplateRenderError(Exception):
    """Template rendering error"""

    def __init__(
        self, message: str, template_content: str | None = None, line_number: int | None = None
    ):
        self.message = message
        self.template_content = template_content
        self.line_number = line_number
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.line_number:
            return f"{self.message} at line {self.line_number}"
        return self.message


class WorkflowTemplateEngine:
    """Jinja2 template engine for workflow templates"""

    def __init__(self) -> None:
        """Initialize template engine with custom configuration"""
        from datetime import datetime

        self.env = Environment(
            # Use custom delimiters to avoid conflicts with common text
            variable_start_string="{{",
            variable_end_string="}}",
            block_start_string="{%",
            block_end_string="%}",
            comment_start_string="{#",
            comment_end_string="#}",
            # Security settings
            autoescape=False,  # We're processing prompts, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
            # Enable extensions
            extensions=["jinja2.ext.do"],
            # Strict undefined behavior - raise exceptions for undefined variables
            undefined=StrictUndefined,
        )

        # Add custom filters for workflow context
        self.env.filters.update(
            {
                "strip_whitespace": self._filter_strip_whitespace,
                "truncate_words": self._filter_truncate_words,
                "escape_quotes": self._filter_escape_quotes,
                "extract_json": self._filter_extract_json,
                "tojson": self._filter_tojson,  # Override default tojson with Unicode support
                "parse_json_array": self._filter_parse_json_array,  # Parse JSON strings in arrays
            }
        )

        # Add global functions for date/time operations
        self.env.globals.update(
            {
                "now": datetime.now,
            }
        )

    def render(self, template_content: str, context: dict[str, Any]) -> str:
        """Render template with given context"""
        try:
            template = self.env.from_string(template_content)
            return str(template.render(context))
        except TemplateError as e:
            # Extract line number if available
            line_number = getattr(e, "lineno", None)
            raise TemplateRenderError(
                f"Template rendering failed: {e}",
                template_content=template_content,
                line_number=line_number,
            ) from e
        except Exception as e:
            raise TemplateRenderError(
                f"Unexpected template error: {e}",
                template_content=template_content,
            ) from e

    def render_object(self, template_content: str, context: dict[str, Any]) -> Any:
        """Render template and return the actual object (not string representation)"""
        try:
            template = self.env.from_string(template_content)
            result = template.render(context)

            # If template is a simple variable reference, return the actual object
            if template_content.strip().startswith("{{") and template_content.strip().endswith(
                "}}"
            ):
                # Extract variable path from template
                var_path = template_content.strip()[2:-2].strip()

                # Navigate through the context to get the actual object
                try:
                    obj = context
                    for part in var_path.split("."):
                        obj = obj[part]
                    return obj
                except (KeyError, TypeError):
                    # If we can't resolve the path, fall back to string result
                    pass

            return result
        except TemplateError as e:
            # Extract line number if available
            line_number = getattr(e, "lineno", None)
            raise TemplateRenderError(
                f"Template rendering failed: {e}",
                template_content=template_content,
                line_number=line_number,
            ) from e
        except Exception as e:
            raise TemplateRenderError(
                f"Unexpected template error: {e}",
                template_content=template_content,
            ) from e

    def validate_template(self, template_content: str) -> tuple[bool, str]:
        """Validate template syntax without rendering"""
        try:
            self.env.parse(template_content)
            return True, "Template syntax is valid"
        except TemplateError as e:
            return False, f"Template syntax error: {e}"
        except Exception as e:
            return False, f"Unexpected validation error: {e}"

    def get_template_variables(self, template_content: str) -> set[str]:
        """Get all variables referenced in template"""
        try:
            ast = self.env.parse(template_content)
            return meta.find_undeclared_variables(ast)
        except TemplateError:
            return set()

    def render_with_fallback(
        self, template_content: str, context: dict[str, Any], fallback_value: str = ""
    ) -> str:
        """Render template with fallback for missing variables"""
        try:
            return self.render(template_content, context)
        except TemplateRenderError:
            # Get all variables in template
            variables = self.get_template_variables(template_content)

            # Create fallback context with missing variables
            fallback_context = context.copy()
            for var in variables:
                if var not in fallback_context:
                    fallback_context[var] = fallback_value

            try:
                return self.render(template_content, fallback_context)
            except TemplateRenderError:
                # If still failing, return the template as-is
                return template_content

    @staticmethod
    def _filter_strip_whitespace(value: str) -> str:
        """Remove extra whitespace from text"""
        return re.sub(r"\s+", " ", str(value)).strip()

    @staticmethod
    def _filter_truncate_words(value: str, length: int = 10, suffix: str = "...") -> str:
        """Truncate text to specified number of words"""
        words = str(value).split()
        if len(words) <= length:
            return str(value)
        return " ".join(words[:length]) + suffix

    @staticmethod
    def _filter_escape_quotes(value: str) -> str:
        """Escape quotes in text"""
        return str(value).replace('"', '\\"').replace("'", "\\'")

    @staticmethod
    def _filter_extract_json(value: str) -> str:
        """Extract JSON from text using regex"""
        import json
        import re

        # Find JSON-like patterns in text
        json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```|(\{.*?\})"
        matches = re.findall(json_pattern, str(value), re.DOTALL)

        for match in matches:
            json_text = match[0] or match[1]
            try:
                # Validate that it's actually JSON
                json.loads(json_text)
                return str(json_text)
            except json.JSONDecodeError:
                continue

        return ""

    def _filter_tojson(self, value: Any) -> str:
        """Convert value to JSON string with Unicode support"""
        import json

        return json.dumps(value, ensure_ascii=False)

    def _filter_parse_json_array(self, value: list[str]) -> list[dict]:
        """Parse JSON strings in an array and return the parsed objects"""
        import json

        if not isinstance(value, list):
            return value

        parsed_items = []
        for item in value:
            if isinstance(item, str):
                try:
                    parsed_items.append(json.loads(item))
                except json.JSONDecodeError:
                    # If parsing fails, keep the original string
                    parsed_items.append(item)
            else:
                parsed_items.append(item)

        return parsed_items


class WorkflowTemplateLoader(BaseLoader):
    """Custom template loader for workflow templates from files"""

    def __init__(self, template_dir: str | Path):
        self.template_dir = Path(template_dir)

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str | None, Callable[[], bool] | None]:
        """Load template source from file"""
        template_path = self.template_dir / template

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        try:
            source = template_path.read_text(encoding="utf-8")

            def uptodate() -> bool:
                return template_path.exists()

            return source, str(template_path), uptodate
        except Exception as e:
            raise TemplateError(f"Failed to load template {template}: {e}") from e
