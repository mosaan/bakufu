"""Step registry for centralized step type management"""

from collections.abc import Callable
from typing import Any, TypeVar

from .base_types import WorkflowStep

# Type aliases for better readability
type StepClass = type[WorkflowStep]
type StepFactory = Callable[[dict[str, Any]], WorkflowStep]
type StepTypeKey = str  # e.g., "text_process.regex_extract", "collection.map"

T = TypeVar("T", bound=WorkflowStep)


class StepRegistryError(Exception):
    """Registry-related errors"""

    pass


class StepRegistry:
    """Centralized registry for workflow step types with factory pattern support"""

    def __init__(self) -> None:
        self._step_factories: dict[StepTypeKey, StepFactory] = {}
        self._step_classes: dict[StepTypeKey, StepClass] = {}

    def register_step(
        self,
        step_type: str,
        step_subtype: str | None = None,
        *,
        step_class: StepClass,
    ) -> None:
        """Register a step class with optional subtype

        Args:
            step_type: Main step type (e.g., "text_process", "collection")
            step_subtype: Optional subtype (e.g., "regex_extract", "map")
            step_class: Step class to register

        Examples:
            registry.register_step("text_process", "regex_extract", step_class=RegexExtractStep)
            registry.register_step("ai_call", step_class=AICallStep)
        """
        key = self._build_key(step_type, step_subtype)

        if key in self._step_classes:
            raise StepRegistryError(f"Step type '{key}' is already registered")

        self._step_classes[key] = step_class
        self._step_factories[key] = lambda data: step_class(**data)

    def create_step(self, step_data: dict[str, Any]) -> WorkflowStep:
        """Create a step instance from data

        Args:
            step_data: Step configuration data with 'type' field required

        Returns:
            Instantiated step object

        Raises:
            StepRegistryError: If step type is not registered or required fields missing
        """
        if not isinstance(step_data, dict):
            raise StepRegistryError("Step data must be a dictionary")

        step_type = step_data.get("type")
        if not step_type:
            raise StepRegistryError("Step data missing required 'type' field")

        # Extract subtype based on step_type
        subtype = self._extract_subtype(step_data, step_type)
        key = self._build_key(step_type, subtype)

        if key not in self._step_factories:
            available_types = ", ".join(self._step_factories.keys())
            raise StepRegistryError(
                f"Unknown step type '{key}'. Available types: {available_types}"
            )

        try:
            return self._step_factories[key](step_data)
        except Exception as e:
            raise StepRegistryError(f"Failed to create step '{key}': {e}") from e

    def is_registered(self, step_type: str, step_subtype: str | None = None) -> bool:
        """Check if a step type is registered"""
        key = self._build_key(step_type, step_subtype)
        return key in self._step_classes

    def get_registered_types(self) -> list[StepTypeKey]:
        """Get all registered step type keys"""
        return list(self._step_classes.keys())

    def get_step_class(self, step_type: str, step_subtype: str | None = None) -> StepClass:
        """Get the registered step class

        Raises:
            StepRegistryError: If step type is not registered
        """
        key = self._build_key(step_type, step_subtype)
        if key not in self._step_classes:
            raise StepRegistryError(f"Step type '{key}' is not registered")
        return self._step_classes[key]

    def _build_key(self, step_type: str, step_subtype: str | None) -> StepTypeKey:
        """Build a unique key for step type and subtype"""
        if step_subtype:
            return f"{step_type}.{step_subtype}"
        return step_type

    def _extract_subtype(self, step_data: dict[str, Any], step_type: str) -> str | None:
        """Extract subtype from step data based on step type"""
        if step_type == "text_process":
            return step_data.get("method")
        elif step_type == "collection":
            return step_data.get("operation")
        # For ai_call, conditional, etc. - no subtype
        return None


# Global registry instance
_global_registry = StepRegistry()


def get_global_registry() -> StepRegistry:
    """Get the global step registry instance"""
    return _global_registry


def register_step(
    step_type: str,
    step_subtype: str | None = None,
    *,
    step_class: StepClass,
) -> None:
    """Register a step class in the global registry

    This is a convenience function for the most common use case.
    """
    _global_registry.register_step(step_type, step_subtype, step_class=step_class)


def step_type(
    type_name: str,
    subtype_name: str | None = None,
) -> Callable[[type[T]], type[T]]:
    """Decorator for registering step classes

    Args:
        type_name: Main step type
        subtype_name: Optional subtype

    Examples:
        @step_type("text_process", "regex_extract")
        class RegexExtractStep(TextProcessStep):
            ...

        @step_type("ai_call")
        class AICallStep(WorkflowStep):
            ...
    """

    def decorator(cls: type[T]) -> type[T]:
        register_step(type_name, subtype_name, step_class=cls)
        return cls

    return decorator
