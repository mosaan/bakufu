"""Enhanced error handling and exception classes for bakufu"""

import traceback
from typing import Any

from pydantic import BaseModel


class ErrorContext(BaseModel):
    """Context information for errors"""

    file_path: str | None = None
    line_number: int | None = None
    function_name: str | None = None
    step_id: str | None = None
    workflow_name: str | None = None
    input_data: dict[str, Any] = {}


class BakufuError(Exception):
    """Base exception class for all bakufu errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        context: ErrorContext | None = None,
        original_error: Exception | None = None,
        suggestions: list[str] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or ErrorContext()
        self.original_error = original_error
        self.suggestions = suggestions or []
        self.traceback_str = traceback.format_exc() if original_error else None

    def __str__(self) -> str:
        """String representation including error code"""
        return f"{self.message} ({self.error_code})"

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON serialization"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context.model_dump(),
            "suggestions": self.suggestions,
            "original_error": str(self.original_error) if self.original_error else None,
        }

    def get_detailed_message(self) -> str:
        """Get detailed error message with context and suggestions"""
        parts = [f"Error {self.error_code}: {self.message}"]

        # Add context information
        if self.context.workflow_name:
            parts.append(f"Workflow: {self.context.workflow_name}")
        if self.context.step_id:
            parts.append(f"Step: {self.context.step_id}")
        if self.context.file_path:
            location = self.context.file_path
            if self.context.line_number:
                location += f":{self.context.line_number}"
            parts.append(f"Location: {location}")

        # Add original error if available
        if self.original_error:
            parts.append(f"Underlying error: {self.original_error}")

        # Add suggestions
        if self.suggestions:
            parts.append("Suggestions:")
            for suggestion in self.suggestions:
                parts.append(f"  - {suggestion}")

        return "\n".join(parts)


class WorkflowError(BakufuError):
    """Errors related to workflow definition and validation"""

    pass


class WorkflowValidationError(WorkflowError):
    """Workflow validation failed"""

    def __init__(
        self, message: str, field_errors: list[dict[str, Any]] | None = None, **kwargs: Any
    ):
        super().__init__(message=message, error_code="WORKFLOW_VALIDATION_ERROR", **kwargs)
        self.field_errors = field_errors or []

        # Add field-specific suggestions
        if self.field_errors:
            suggestions = []
            for error in self.field_errors:
                field = error.get("field", "unknown")
                error_type = error.get("type", "validation")
                suggestions.append(
                    f"Fix {error_type} error in field '{field}': {error.get('message', '')}"
                )
            self.suggestions.extend(suggestions)


class WorkflowFileError(WorkflowError):
    """Workflow file loading/parsing errors"""

    def __init__(self, message: str, file_path: str, **kwargs: Any):
        if "context" not in kwargs:
            kwargs["context"] = ErrorContext(file_path=file_path)
        if "suggestions" not in kwargs:
            kwargs["suggestions"] = [
                "Check if the file exists and is readable",
                "Verify the YAML/JSON syntax is correct",
                "Ensure the file follows the bakufu workflow schema",
            ]
        super().__init__(
            message=message,
            error_code="WORKFLOW_FILE_ERROR",
            **kwargs,
        )


class StepExecutionError(BakufuError):
    """Errors during step execution"""

    def __init__(self, message: str, step_id: str, workflow_name: str | None = None, **kwargs: Any):
        # Only create context if not provided in kwargs
        if "context" not in kwargs:
            kwargs["context"] = ErrorContext(step_id=step_id, workflow_name=workflow_name)
        super().__init__(message=message, error_code="STEP_EXECUTION_ERROR", **kwargs)
        # Store step_id as attribute for backward compatibility
        self.step_id = step_id


class TemplateError(BakufuError):
    """Template rendering errors"""

    def __init__(
        self,
        message: str,
        template_content: str | None = None,
        line_number: int | None = None,
        **kwargs: Any,
    ):
        # Only create context if not provided in kwargs
        if "context" not in kwargs:
            kwargs["context"] = ErrorContext(line_number=line_number)

        suggestions = [
            "Check template syntax for typos",
            "Verify all variables are available in context",
            "Use template validation before rendering",
        ]
        if template_content:
            suggestions.append(f"Template content: {template_content[:100]}...")

        # Add suggestions if not provided
        if "suggestions" not in kwargs:
            kwargs["suggestions"] = suggestions

        super().__init__(
            message=message,
            error_code="TEMPLATE_ERROR",
            **kwargs,
        )


class AIProviderError(BakufuError):
    """AI provider related errors"""

    def __init__(self, message: str, provider: str, model: str | None = None, **kwargs: Any):
        if "context" not in kwargs:
            kwargs["context"] = ErrorContext()
        if "suggestions" not in kwargs:
            kwargs["suggestions"] = [
                f"Check {provider} API key configuration",
                "Verify network connectivity",
                "Check if the model is available",
                "Try using a fallback provider",
            ]

        super().__init__(
            message=f"AI Provider '{provider}': {message}",
            error_code="AI_PROVIDER_ERROR",
            **kwargs,
        )
        self.provider = provider
        self.model = model


class ConfigurationError(BakufuError):
    """Configuration related errors"""

    def __init__(self, message: str, config_key: str | None = None, **kwargs: Any):
        if "suggestions" not in kwargs:
            suggestions = [
                "Check configuration file syntax",
                "Verify all required fields are present",
                "Use 'bakufu config validate' to check configuration",
            ]
            if config_key:
                suggestions.append(f"Check the '{config_key}' configuration value")
            kwargs["suggestions"] = suggestions

        super().__init__(message=message, error_code="CONFIGURATION_ERROR", **kwargs)


class ResourceError(BakufuError):
    """Resource related errors (files, network, etc.)"""

    def __init__(
        self,
        message: str,
        resource_type: str = "resource",
        resource_path: str | None = None,
        **kwargs: Any,
    ):
        if "context" not in kwargs:
            kwargs["context"] = ErrorContext(file_path=resource_path)
        if "suggestions" not in kwargs:
            kwargs["suggestions"] = [
                f"Check if the {resource_type} exists and is accessible",
                "Verify file permissions",
                "Check network connectivity if applicable",
            ]

        super().__init__(
            message=message,
            error_code="RESOURCE_ERROR",
            **kwargs,
        )


def create_error_from_exception(
    exc: Exception, context: ErrorContext | None = None, suggestions: list[str] | None = None
) -> BakufuError:
    """Create appropriate BakufuError from a generic exception"""

    error_type = type(exc).__name__
    message = str(exc)

    # Map common exceptions to specific error types
    if isinstance(exc, FileNotFoundError):
        filename = getattr(exc, "filename", None)
        # If no context provided, create one with file path
        if context is None:
            context = ErrorContext(file_path=filename)
        return ResourceError(
            message=f"File not found: {message}",
            resource_type="file",
            resource_path=filename,
            context=context,
            original_error=exc,
            suggestions=suggestions,
        )
    elif isinstance(exc, PermissionError):
        return ResourceError(
            message=f"Permission denied: {message}",
            resource_type="file",
            context=context,
            original_error=exc,
            suggestions=suggestions or ["Check file/directory permissions"],
        )
    elif isinstance(exc, ValueError):
        return ConfigurationError(
            message=f"Invalid value: {message}",
            context=context,
            original_error=exc,
            suggestions=suggestions or ["Check input data format and values"],
        )
    elif isinstance(exc, TypeError):
        return ConfigurationError(
            message=f"Type error: {message}",
            context=context,
            original_error=exc,
            suggestions=suggestions or ["Check data types match expected schema"],
        )
    else:
        # Generic error
        return BakufuError(
            message=f"{error_type}: {message}",
            error_code="UNKNOWN_ERROR",
            context=context,
            original_error=exc,
            suggestions=suggestions or ["Check logs for more details"],
        )


class ErrorReporter:
    """Utility class for error reporting and logging"""

    @staticmethod
    def format_error_for_cli(error: BakufuError, verbose: bool = False) -> str:
        """Format error for CLI display"""
        if verbose:
            return error.get_detailed_message()
        else:
            # Simplified error message for normal output
            message_parts = [f"❌ {error.message}"]

            if error.context.step_id:
                message_parts.append(f"   Step: {error.context.step_id}")

            if error.suggestions:
                message_parts.append(f"   Suggestion: {error.suggestions[0]}")

            return "\n".join(message_parts)

    @staticmethod
    def format_error_for_json(error: BakufuError) -> dict[str, Any]:
        """Format error for JSON output"""
        return error.to_dict()

    @staticmethod
    def extract_line_number_from_traceback(tb_str: str) -> int | None:
        """Extract line number from traceback string"""
        try:
            lines = tb_str.split("\n")
            for line in lines:
                if "line " in line and ", in " in line:
                    # Look for pattern like "line 42, in function_name"
                    parts = line.split("line ")
                    if len(parts) > 1:
                        line_part = parts[1].split(",")[0].strip()
                        return int(line_part)
        except (ValueError, IndexError):
            pass
        return None
