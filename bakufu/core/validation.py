"""AI output validation functionality"""

import importlib
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import jsonschema
from pydantic import BaseModel, Field


class ValidationError(Exception):
    """Error raised during validation"""

    def __init__(self, message: str, original_output: str, validation_errors: list[str]):
        super().__init__(message)
        self.original_output = original_output
        self.validation_errors = validation_errors


class ValidationResult(BaseModel):
    """Result of validation attempt"""

    is_valid: bool
    validated_output: Any = None
    errors: list[str] = Field(default_factory=list)
    attempt_count: int = 1
    original_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template usage"""
        return {
            "is_valid": self.is_valid,
            "validated_output": self.validated_output,
            "errors": self.errors,
            "attempt_count": self.attempt_count,
            "original_output": self.original_output,
        }


class BaseValidator(ABC):
    """Base class for output validators"""

    @abstractmethod
    def validate(self, output: str) -> ValidationResult:
        """Validate the output and return result"""
        pass

    @abstractmethod
    def get_retry_prompt_suffix(self, validation_result: ValidationResult) -> str:
        """Get additional prompt text for retry attempts"""
        pass


class JSONSchemaValidator(BaseValidator):
    """Validator using JSON Schema"""

    def __init__(self, schema: dict[str, Any]):
        self.schema = schema

    def validate(self, output: str) -> ValidationResult:
        """Validate output against JSON schema"""

        try:
            # Try to parse as JSON
            try:
                parsed_output = json.loads(output)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Invalid JSON format: {e!s}"],
                    original_output=output,
                )

            # Validate against schema
            try:
                jsonschema.validate(parsed_output, self.schema)
                return ValidationResult(
                    is_valid=True, validated_output=parsed_output, original_output=output
                )
            except jsonschema.ValidationError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Schema validation failed: {e.message}"],
                    original_output=output,
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False, errors=[f"Validation error: {e!s}"], original_output=output
            )

    def get_retry_prompt_suffix(self, validation_result: ValidationResult) -> str:
        """Get retry prompt for JSON schema validation"""
        error_msg = "; ".join(validation_result.errors)
        return f"""
Previous response failed validation: {error_msg}

Please respond with valid JSON that matches this schema:
{json.dumps(self.schema, indent=2)}

Ensure your response is valid JSON and includes all required fields.
"""


class PydanticValidator(BaseValidator):
    """Validator using Pydantic models"""

    def __init__(self, model_class: type[BaseModel]):
        self.model_class = model_class

    def validate(self, output: str) -> ValidationResult:
        """Validate output against Pydantic model"""
        try:
            # Try to parse as JSON first
            try:
                parsed_output = json.loads(output)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Invalid JSON format: {e!s}"],
                    original_output=output,
                )

            # Validate with Pydantic model
            try:
                validated_model = self.model_class(**parsed_output)
                return ValidationResult(
                    is_valid=True,
                    validated_output=validated_model.model_dump(),
                    original_output=output,
                )
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Pydantic validation failed: {e!s}"],
                    original_output=output,
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False, errors=[f"Validation error: {e!s}"], original_output=output
            )

    def get_retry_prompt_suffix(self, validation_result: ValidationResult) -> str:
        """Get retry prompt for Pydantic validation"""
        error_msg = "; ".join(validation_result.errors)
        schema = self.model_class.model_json_schema()
        return f"""
Previous response failed validation: {error_msg}

Please respond with valid JSON that matches this structure:
{json.dumps(schema, indent=2)}

Ensure your response is valid JSON and follows the exact field requirements.
"""


class CustomValidator(BaseValidator):
    """Validator using custom validation function"""

    def __init__(
        self,
        validator_func: Callable[[str], ValidationResult],
        criteria: dict[str, Any] | None = None,
    ):
        self.validator_func = validator_func
        self.criteria = criteria or {}

    def validate(self, output: str) -> ValidationResult:
        """Validate using custom function"""
        try:
            return self.validator_func(output)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Custom validation error: {e!s}"],
                original_output=output,
            )

    def get_retry_prompt_suffix(self, validation_result: ValidationResult) -> str:
        """Get retry prompt for custom validation"""
        error_msg = "; ".join(validation_result.errors)
        criteria_str = ""
        if self.criteria:
            criteria_str = f"\nValidation criteria: {json.dumps(self.criteria, indent=2)}"

        return f"""
Previous response failed validation: {error_msg}{criteria_str}

Please ensure your response meets all the specified requirements.
"""


class ValidationConfig(BaseModel):
    """Configuration for AI output validation"""

    # Validation type and configuration
    json_schema: dict[str, Any] | None = Field(None, alias="schema")
    pydantic_model: str | None = None  # Model class name as string
    custom_validator: str | None = None  # Function name as string
    criteria: dict[str, Any] = Field(default_factory=dict)

    # Retry configuration
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_prompt: str | None = None

    # Output recovery
    allow_partial_success: bool = Field(default=False)
    extract_json_pattern: str | None = None

    # Response formatting
    force_json_output: bool = Field(default=False)
    json_wrapper_instruction: str = Field(default="Please format your response as valid JSON.")


class OutputValidator:
    """Main validator that orchestrates different validation strategies"""

    def __init__(self, config: ValidationConfig):
        self.config = config
        self.validator = self._create_validator()

    def _create_validator(self) -> BaseValidator:
        """Create appropriate validator based on config"""
        if self.config.json_schema:
            return JSONSchemaValidator(self.config.json_schema)
        elif self.config.pydantic_model:
            model_class = self._resolve_pydantic_model(self.config.pydantic_model)
            return PydanticValidator(model_class)
        elif self.config.custom_validator:
            validator_func = self._resolve_custom_validator(self.config.custom_validator)
            return CustomValidator(validator_func, self.config.criteria)
        else:
            raise ValueError("No validation method specified in config")

    def _resolve_pydantic_model(self, model_name: str) -> type[BaseModel]:
        """Resolve Pydantic model class from string name"""
        try:
            if "." in model_name:
                # Module.ClassName format
                module_name, class_name = model_name.rsplit(".", 1)
                module = importlib.import_module(module_name)
                model_class = getattr(module, class_name)
            else:
                # Try to find in common locations
                # First try in the current module's globals
                import sys

                calling_frame = sys._getframe(1)
                if model_name in calling_frame.f_globals:
                    model_class = calling_frame.f_globals[model_name]
                else:
                    raise ValueError(f"Could not resolve Pydantic model: {model_name}")

            if not issubclass(model_class, BaseModel):
                raise ValueError(f"{model_name} is not a Pydantic BaseModel")

            return model_class  # type: ignore[no-any-return]
        except Exception as e:
            raise ValueError(f"Failed to resolve Pydantic model '{model_name}': {e}") from e

    def _resolve_custom_validator(self, func_name: str) -> Callable[[str], ValidationResult]:
        """Resolve custom validation function from string name"""
        try:
            if "." in func_name:
                # Module.function_name format
                module_name, function_name = func_name.rsplit(".", 1)
                module = importlib.import_module(module_name)
                validator_func = getattr(module, function_name)
            else:
                # Try to find in common locations
                import sys

                calling_frame = sys._getframe(1)
                if func_name in calling_frame.f_globals:
                    validator_func = calling_frame.f_globals[func_name]
                else:
                    raise ValueError(f"Could not resolve custom validator: {func_name}")

            if not callable(validator_func):
                raise ValueError(f"{func_name} is not callable")

            return validator_func  # type: ignore[no-any-return]
        except Exception as e:
            raise ValueError(f"Failed to resolve custom validator '{func_name}': {e}") from e

    def validate(self, output: str, attempt: int = 1) -> ValidationResult:
        """Validate output and return result"""
        result = self.validator.validate(output)
        result.attempt_count = attempt

        # Try output recovery if validation failed
        if not result.is_valid and self.config.allow_partial_success:
            recovery_result = self._attempt_output_recovery(output)
            if recovery_result.is_valid:
                return recovery_result

        return result

    def _attempt_output_recovery(self, output: str) -> ValidationResult:
        """Attempt to recover valid output from invalid response"""
        if not self.config.extract_json_pattern:
            return ValidationResult(is_valid=False, original_output=output)

        try:
            # Try to extract JSON using regex pattern
            pattern = re.compile(self.config.extract_json_pattern, re.DOTALL)
            match = pattern.search(output)

            if match:
                extracted_json = match.group(1) if match.groups() else match.group(0)
                # Try to validate the extracted content
                return self.validator.validate(extracted_json)

        except Exception:
            pass

        return ValidationResult(is_valid=False, original_output=output)

    def get_retry_prompt(self, validation_result: ValidationResult) -> str:
        """Get prompt for retry attempt"""
        base_prompt = self.config.retry_prompt or ""
        validator_prompt = self.validator.get_retry_prompt_suffix(validation_result)

        return f"{base_prompt}\n{validator_prompt}".strip()

    def should_force_json_wrapper(self) -> bool:
        """Check if JSON wrapper should be forced"""
        return self.config.force_json_output

    def get_json_wrapper_instruction(self) -> str:
        """Get JSON wrapper instruction"""
        return self.config.json_wrapper_instruction
