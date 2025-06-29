"""Base types for workflow steps to avoid circular imports"""

from typing import Literal

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """Base workflow step definition"""

    id: str = Field(..., description="Unique step identifier")
    type: Literal["ai_call", "text_process", "collection", "conditional"]
    description: str | None = None
    on_error: Literal["stop", "continue", "skip_remaining"] = "stop"
