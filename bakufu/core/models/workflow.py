"""Workflow definition and configuration models for Bakufu"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from .base import AnyWorkflowStep, InputParameter, OutputFormat


class Workflow(BaseModel):
    """Complete workflow definition"""

    name: str
    description: str | None = None
    version: str = "1.0"

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate workflow name to prevent MCP tool name conflicts"""
        import string

        if not v:
            raise ValueError("Workflow name cannot be empty")

        # Check for leading or trailing spaces
        if v != v.strip():
            raise ValueError("Workflow name cannot have leading or trailing spaces")

        # Check if name contains only ASCII letters, numbers, hyphens, underscores, and spaces
        # This prevents Japanese characters while allowing existing naming patterns
        allowed_chars = string.ascii_letters + string.digits + "-_ "
        if not all(c in allowed_chars for c in v):
            raise ValueError(
                "Workflow name must contain only ASCII letters, numbers, hyphens, underscores, and spaces"
            )

        # Must start with a letter to be a valid identifier
        if not v[0].isalpha():
            raise ValueError("Workflow name must start with a letter")

        return v

    input_parameters: list[InputParameter] | None = Field(default_factory=list)
    steps: list[AnyWorkflowStep] = Field(..., min_length=1)
    output: OutputFormat | None = None

    @field_validator("steps")
    @classmethod
    def validate_step_ids_unique(cls, v: list[AnyWorkflowStep]) -> list[AnyWorkflowStep]:
        step_ids = [step.id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Step IDs must be unique")
        return v


class WorkflowConfig(BaseModel):
    """Workflow execution configuration"""

    default_provider: str = "gemini/gemini-2.0-flash"
    max_parallel_ai_calls: int = Field(default=3, gt=0)
    max_parallel_text_processing: int = Field(default=5, gt=0)
    timeout_per_step: int = Field(default=60, gt=0)

    provider_settings: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # MCP Large Output Control Settings
    mcp_max_output_chars: int = Field(
        default=8000,
        gt=0,
        description="Maximum characters in MCP output before switching to file output",
    )
    mcp_auto_file_output_dir: str = Field(
        default="./mcp_outputs", description="Directory for automatic file outputs from MCP server"
    )

    @classmethod
    def from_bakufu_config(cls, bakufu_config: Any) -> "WorkflowConfig":
        """Create WorkflowConfig from BakufuConfig"""
        from ..config_loader import BakufuConfig

        if not isinstance(bakufu_config, BakufuConfig):
            raise TypeError("Expected BakufuConfig instance")

        provider_settings = {}
        for provider_name, provider_config in bakufu_config.provider_settings.items():
            provider_settings[provider_name] = provider_config.model_dump(exclude_none=True)

        return cls(
            default_provider=bakufu_config.default_provider,
            max_parallel_ai_calls=bakufu_config.max_parallel_ai_calls,
            max_parallel_text_processing=bakufu_config.max_parallel_text_processing,
            timeout_per_step=bakufu_config.timeout_per_step,
            provider_settings=provider_settings,
            mcp_max_output_chars=bakufu_config.mcp_max_output_chars,
            mcp_auto_file_output_dir=bakufu_config.mcp_auto_file_output_dir,
        )
