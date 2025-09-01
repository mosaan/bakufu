"""Workflow file loading and parsing"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

# Import step classes to trigger their @step_type decorators
from .models import Workflow
from .models.steps import ai, collection, conditional  # noqa: F401
from .models.steps.ai import AICallStep
from .models.steps.collection import CollectionStep
from .models.steps.conditional import ConditionalStep
from .step_registry import get_global_registry
from .text_steps import (
    AnyTextProcessStep,
)


class WorkflowParseError(Exception):
    """Workflow parsing error"""

    def __init__(self, message: str, file_path: str | None = None, line_number: int | None = None):
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.file_path:
            location = f" in {self.file_path}"
            if self.line_number:
                location += f" at line {self.line_number}"
            return f"{self.message}{location}"
        return self.message


class WorkflowLoader:
    """Load and parse workflow files"""

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> Workflow:
        """Load workflow from YAML or JSON file"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise WorkflowParseError(f"Workflow file not found: {file_path}")

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise WorkflowParseError(f"Failed to read file: {e}", str(file_path)) from e

        return cls.load_from_string(content, str(file_path))

    @classmethod
    def load_from_string(cls, content: str, file_path: str | None = None) -> Workflow:
        """Load workflow from string content"""
        try:
            # Try YAML first (supports JSON as well)
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            line_number = getattr(e, "problem_mark", None)
            line_num = line_number.line + 1 if line_number else None
            raise WorkflowParseError(f"Invalid YAML/JSON syntax: {e}", file_path, line_num) from e

        if data is None:
            raise WorkflowParseError("Empty workflow file", file_path)

        return cls._parse_workflow_data(data, file_path)

    @classmethod
    def _parse_workflow_data(cls, data: dict[str, Any], file_path: str | None = None) -> Workflow:
        """Parse workflow data into Pydantic model"""
        try:
            # Transform steps data to include proper types
            if "steps" in data:
                data["steps"] = cls._transform_steps(data["steps"])

            return Workflow(**data)

        except ValidationError as e:
            error_details = cls._format_validation_errors(e)
            raise WorkflowParseError(
                f"Workflow validation failed:\n{error_details}", file_path
            ) from e
        except Exception as e:
            raise WorkflowParseError(f"Unexpected error parsing workflow: {e}", file_path) from e

    @classmethod
    def _transform_steps(
        cls, steps_data: list
    ) -> list[AICallStep | AnyTextProcessStep | CollectionStep | ConditionalStep]:
        """Transform steps data to proper step objects using StepRegistry"""
        transformed_steps: list[
            AICallStep | AnyTextProcessStep | CollectionStep | ConditionalStep
        ] = []

        registry = get_global_registry()

        for i, step_data in enumerate(steps_data):
            if not isinstance(step_data, dict):
                raise ValueError(f"Step {i} must be an object")

            step_type = step_data.get("type")
            if not step_type:
                raise ValueError(f"Step {i} missing required 'type' field")

            try:
                # Special handling for conditional steps with nested steps
                if step_type == "conditional":
                    step = cls._create_conditional_step(step_data, i)
                else:
                    # Use registry for all other step types
                    step = registry.create_step(step_data)  # type: ignore

                transformed_steps.append(step)

            except Exception as e:
                available_types = registry.get_registered_types()
                raise ValueError(
                    f"Failed to create step {i} of type '{step_type}': {e}. "
                    f"Available types: {', '.join(available_types)}"
                ) from e

        return transformed_steps

    @classmethod
    def _format_validation_errors(cls, error: ValidationError) -> str:
        """Format Pydantic validation errors for user-friendly display"""
        error_lines = []

        for err in error.errors():
            location = " -> ".join(str(loc) for loc in err["loc"])
            message = err["msg"]
            error_lines.append(f"  - {location}: {message}")

        return "\n".join(error_lines)

    @classmethod
    def _create_conditional_step(
        cls, step_data: dict[str, Any], step_index: int
    ) -> ConditionalStep:
        """Create a conditional step with nested step transformation"""
        step_data = step_data.copy()

        # Transform nested steps in if_true and if_false
        if step_data.get("if_true"):
            step_data["if_true"] = cls._transform_steps(step_data["if_true"])

        if step_data.get("if_false"):
            step_data["if_false"] = cls._transform_steps(step_data["if_false"])

        # Transform nested steps in conditions array
        if step_data.get("conditions"):
            for condition_data in step_data["conditions"]:
                if condition_data.get("steps"):
                    condition_data["steps"] = cls._transform_steps(condition_data["steps"])

        return ConditionalStep(**step_data)


def validate_workflow_file(file_path: str | Path) -> tuple[bool, str]:
    """Validate a workflow file and return success status and message"""
    try:
        WorkflowLoader.load_from_file(file_path)
        return True, "Workflow is valid"
    except WorkflowParseError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"
