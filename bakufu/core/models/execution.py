"""Execution context and usage tracking models for Bakufu workflows"""

from dataclasses import dataclass, field
from typing import Any

from fastmcp import Context
from pydantic import BaseModel, Field, PrivateAttr

from ..template_engine import WorkflowTemplateEngine
from .workflow import WorkflowConfig


@dataclass
class UsageSummary:
    """AI API usage summary"""

    total_api_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    step_usage: dict[str, dict] = field(default_factory=dict)

    def add_step_usage(
        self, step_id: str, usage: dict[str, Any] | None, cost_usd: float | None
    ) -> None:
        """Add usage data for a step"""
        # Always count API calls, even if usage data is empty/None
        self.total_api_calls += 1
        self.total_cost_usd += cost_usd or 0.0

        if not usage:
            # Store step with zero usage
            self.step_usage[step_id] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost_usd": cost_usd or 0.0,
            }
            return

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Update totals
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total_tokens

        # Store step-specific data
        self.step_usage[step_id] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd or 0.0,
        }


class ExecutionContext(BaseModel):
    """Runtime execution context"""

    workflow_name: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    step_outputs: dict[str, Any] = Field(default_factory=dict)
    config: WorkflowConfig

    # MCP sampling mode
    sampling_mode: bool = Field(
        default=False, description="Use MCP sampling instead of LLM providers"
    )
    mcp_context: Context | None = Field(
        default=None, description="FastMCP Context for sampling API"
    )

    # Template engine (not serialized)
    _template_engine: WorkflowTemplateEngine = PrivateAttr(default_factory=WorkflowTemplateEngine)

    # Usage tracking (not serialized)
    _usage_summary: UsageSummary = PrivateAttr(default_factory=UsageSummary)

    def get_step_output(self, step_id: str) -> Any:
        """Get output from a specific step"""
        return self.step_outputs.get(step_id)

    def set_step_output(self, step_id: str, output: Any) -> None:
        """Set output for a specific step"""
        self.step_outputs[step_id] = output

    def get_template_context(self) -> dict[str, Any]:
        """Get context for Jinja2 template rendering"""
        context = {
            "input": self.input_data,
            "steps": self.step_outputs,
            "config": self.config.model_dump(),
            "workflow": {"name": self.workflow_name},
        }

        # Add input data as top-level context for convenience (allows {{ key }} access)
        context.update(self.input_data)

        return context

    def render_template(self, template: str) -> str:
        """Render template with current execution context"""
        return self._template_engine.render(template, self.get_template_context())

    def render_template_object(self, template: str) -> Any:
        """Render template and return the actual object (not string representation)"""
        return self._template_engine.render_object(template, self.get_template_context())

    def validate_template(self, template: str) -> tuple[bool, str]:
        """Validate template syntax"""
        return self._template_engine.validate_template(template)

    def add_step_usage(
        self, step_id: str, usage: dict[str, Any] | None, cost_usd: float | None
    ) -> None:
        """Add usage data for a step"""
        self._usage_summary.add_step_usage(step_id, usage, cost_usd)

    def get_usage_summary(self) -> UsageSummary:
        """Get current usage summary"""
        return self._usage_summary
