"""Base model definitions and common types for Bakufu workflows"""

from typing import TYPE_CHECKING, Any, Literal, Union

from pydantic import BaseModel, Field


class InputParameter(BaseModel):
    """Input parameter definition"""

    name: str
    type: Literal["string", "integer", "float", "boolean", "array", "object"]
    required: bool = True
    description: str | None = None
    default: Any | None = None


class OutputFormat(BaseModel):
    """Workflow output format definition"""

    format: Literal["text", "json", "yaml"] = "text"
    template: str | None = None

    # Large output control settings
    large_output_control: bool = Field(
        default=False,
        description="Enable large output control - requires output_file_path parameter when enabled",
    )


class StructuredInputValue(BaseModel):
    """
    Structured input value specification for MCP integration.

    Supports two types of input data:
    - value: Direct value data
    - file: File-based data with format and encoding specifications
    """

    type: Literal["value", "file"]
    data: Any = Field(description="Direct value for 'value' type, or file path for 'file' type")
    format: Literal["text", "json", "yaml", "csv", "lines"] | None = Field(
        default=None, description="File format for 'file' type (ignored for 'value' type)"
    )
    encoding: str | None = Field(
        default=None, description="File encoding for 'file' type (ignored for 'value' type)"
    )

    class Config:
        extra = "forbid"


if TYPE_CHECKING:
    from ..text_steps import AnyTextProcessStep
    from .steps.ai import AICallStep
    from .steps.collection import FilterOperation, MapOperation, PipelineOperation, ReduceOperation
    from .steps.conditional import ConditionalStep

# Type alias for all workflow steps
AnyWorkflowStep = Union[
    "AICallStep",
    "AnyTextProcessStep",
    "MapOperation",
    "FilterOperation",
    "ReduceOperation",
    "PipelineOperation",
    "ConditionalStep",
]
