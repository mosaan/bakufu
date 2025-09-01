"""Base types for workflow steps to avoid circular imports"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .models.execution import ExecutionContext


class WorkflowStep(BaseModel, ABC):
    """Base workflow step definition with polymorphic execution"""

    id: str = Field(..., description="Unique step identifier")
    type: Literal["ai_call", "text_process", "collection", "conditional"]
    description: str | None = None
    on_error: Literal["stop", "continue", "skip_remaining"] = "stop"

    @abstractmethod
    async def execute(self, context: "ExecutionContext") -> Any:
        """Execute this workflow step

        Args:
            context: The execution context containing template data and configuration

        Returns:
            The result of executing this step

        Raises:
            StepExecutionError: If step execution fails
        """
        pass


# Forward declaration removed as it conflicts with the actual implementation
