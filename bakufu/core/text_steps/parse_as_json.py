"""JSON parsing with validation and metadata processing step"""

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from .base import TextProcessStep


class ParseAsJsonStep(TextProcessStep):
    """JSON parsing with validation and metadata processing step"""

    method: Literal["parse_as_json"] = "parse_as_json"
    schema_file: str | None = Field(None, description="Path to JSON schema file")
    strict_validation: bool = Field(False, description="Fail on schema validation errors")
    format_output: bool = Field(False, description="Format JSON output with indentation")

    def _parse_json_data(self, input_data: str, step_id: str) -> Any:
        """Parse JSON data with error handling"""
        from ..text_processing import JsonProcessor

        # Use unified JsonProcessor for consistent JSON parsing
        return JsonProcessor.parse_json_string(input_data, step_id=step_id)

    def _validate_with_schema(
        self, parsed_data: Any, validation_result: dict[str, Any], step_id: str
    ) -> None:
        """Perform schema validation if schema_file is provided"""
        from ..exceptions import ErrorContext, StepExecutionError

        if not self.schema_file:
            return

        try:
            import jsonschema  # noqa: F401
        except ImportError:
            error_msg = "jsonschema library not available for validation"
            validation_result["schema_valid"] = False
            validation_result["errors"].append(error_msg)

            if self.strict_validation:
                raise StepExecutionError(
                    message=error_msg,
                    step_id=step_id,
                    context=ErrorContext(step_id=step_id, function_name="ParseAsJsonStep.process"),
                    suggestions=[
                        "Install jsonschema library: pip install jsonschema",
                        "Or disable schema validation by not providing schema_file",
                    ],
                ) from None
            return

        schema_path = Path(self.schema_file)
        if not schema_path.is_absolute():
            schema_path = Path.cwd() / schema_path

        if not schema_path.exists():
            self._handle_schema_file_not_found(schema_path, validation_result, step_id)
            return

        self._validate_against_schema_file(parsed_data, schema_path, validation_result, step_id)

    def _handle_schema_file_not_found(
        self, schema_path: Path, validation_result: dict[str, Any], step_id: str
    ) -> None:
        """Handle missing schema file"""
        from ..exceptions import ErrorContext, StepExecutionError

        error_msg = f"Schema file not found: {schema_path}"
        validation_result["schema_valid"] = False
        validation_result["errors"].append(error_msg)

        if self.strict_validation:
            raise StepExecutionError(
                message=error_msg,
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ParseAsJsonStep.process"),
                suggestions=[
                    "Check if schema file path is correct",
                    f"Expected path: {schema_path}",
                    "Use absolute path or ensure file is in working directory",
                ],
            )

    def _validate_against_schema_file(
        self, parsed_data: Any, schema_path: Path, validation_result: dict[str, Any], step_id: str
    ) -> None:
        """Validate data against schema file"""
        from ..exceptions import ErrorContext, StepExecutionError

        try:
            import jsonschema

            with open(schema_path, encoding="utf-8") as f:
                schema = json.load(f)

            jsonschema.validate(parsed_data, schema)
        except jsonschema.ValidationError as ve:
            validation_result["schema_valid"] = False
            validation_result["errors"].append(str(ve))

            if self.strict_validation:
                raise StepExecutionError(
                    message=f"JSON schema validation failed: {ve}",
                    step_id=step_id,
                    context=ErrorContext(step_id=step_id, function_name="ParseAsJsonStep.process"),
                    original_error=ve,
                    suggestions=[
                        "Check if JSON data matches the schema",
                        f"Schema file: {schema_path}",
                        f"Validation error: {ve.message}",
                        f"Failed at path: {'.'.join(str(p) for p in ve.absolute_path)}",
                    ],
                ) from ve
        except jsonschema.SchemaError as se:
            error_msg = f"Invalid schema file: {se}"
            validation_result["schema_valid"] = False
            validation_result["errors"].append(error_msg)

            if self.strict_validation:
                raise StepExecutionError(
                    message=error_msg,
                    step_id=step_id,
                    context=ErrorContext(step_id=step_id, function_name="ParseAsJsonStep.process"),
                    original_error=se,
                    suggestions=[
                        "Check schema file syntax",
                        f"Schema file: {schema_path}",
                        "Ensure schema follows JSON Schema specification",
                    ],
                ) from se

    async def process(self, input_data: str, step_id: str) -> dict[str, Any]:
        """Parse JSON with optional schema validation and return data with metadata"""
        from ..exceptions import ErrorContext, StepExecutionError

        try:
            # Parse JSON
            parsed_data = self._parse_json_data(input_data, step_id)

            # Initialize validation result
            validation_result: dict[str, Any] = {"valid": True, "errors": [], "schema_valid": True}

            # Schema validation if schema_file is provided
            self._validate_with_schema(parsed_data, validation_result, step_id)

            # Update overall validation status
            validation_result["valid"] = (
                validation_result["schema_valid"] and len(validation_result["errors"]) == 0
            )

            # Format output if requested
            output_data = parsed_data
            if self.format_output:
                output_data = json.dumps(parsed_data, indent=2, ensure_ascii=False)

            # Return data with validation metadata
            return {
                "data": output_data,
                "validation_result": validation_result,
                "metadata": {
                    "schema_file": self.schema_file,
                    "strict_validation": self.strict_validation,
                    "format_output": self.format_output,
                    "data_type": type(parsed_data).__name__,
                    "data_size": len(str(parsed_data)),
                },
            }

        except StepExecutionError:
            # Re-raise StepExecutionError as-is
            raise
        except Exception as e:
            raise StepExecutionError(
                message=f"Failed to parse JSON: {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ParseAsJsonStep.process"),
                original_error=e,
                suggestions=[
                    "Check JSON format and schema file",
                    "Verify all file paths are accessible",
                    f"Input preview: {input_data[:100]}...",
                ],
            ) from e
