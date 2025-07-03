"""Workflow definition models using Pydantic"""

from dataclasses import dataclass, field
from typing import Any, Literal, Union

from fastmcp import Context
from pydantic import BaseModel, Field, PrivateAttr, field_validator

from .base_types import WorkflowStep
from .template_engine import WorkflowTemplateEngine

# Import text processing steps from the dedicated module
from .text_steps import (
    AnyTextProcessStep,
)


class InputParameter(BaseModel):
    """Input parameter definition"""

    name: str
    type: Literal["string", "integer", "float", "boolean", "array", "object"]
    required: bool = True
    description: str | None = None
    default: Any | None = None


class AICallStep(WorkflowStep):
    """AI API call step"""

    type: Literal["ai_call"] = "ai_call"
    prompt: str = Field(..., description="Prompt template with Jinja2 syntax")
    provider: str | None = Field(default=None, description="Override default AI provider")
    model: str | None = Field(default=None, description="Override default model")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    ai_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional AI provider parameters (e.g., response_format, top_p, presence_penalty)",
    )

    # Validation configuration
    validation: dict[str, Any] | None = Field(None, description="Output validation configuration")


class CollectionErrorHandling(BaseModel):
    """Error handling configuration for collection operations"""

    on_item_failure: Literal["skip", "stop", "retry"] = Field(
        default="skip", description="Action on individual item failure"
    )
    on_condition_error: Literal["skip_item", "stop", "default_false"] = Field(
        default="skip_item", description="Action when condition evaluation fails"
    )
    max_retries_per_item: int = Field(default=2, ge=0, description="Maximum retries per item")
    preserve_errors: bool = Field(default=True, description="Keep error information in results")


class CollectionStep(WorkflowStep):
    """Collection operation step for functional programming operations"""

    type: Literal["collection"] = "collection"
    operation: Literal[
        "map", "filter", "reduce", "zip", "group_by", "sort", "flatten", "distinct", "pipeline"
    ] = Field(..., description="Collection operation to perform")
    input: str = Field(..., description="Input data reference with Jinja2 syntax")

    # Error handling
    error_handling: CollectionErrorHandling = Field(default_factory=CollectionErrorHandling)

    # Concurrency for operations that support it (like map)
    concurrency: dict[str, Any] | None = Field(
        None, description="Concurrency settings for parallel operations"
    )


class MapOperation(CollectionStep):
    """Map operation - transform each element"""

    operation: Literal["map"] = "map"
    steps: list["AICallStep | AnyTextProcessStep"] = Field(
        ..., description="Steps to apply to each item"
    )


class FilterOperation(CollectionStep):
    """Filter operation - select elements matching a condition"""

    operation: Literal["filter"] = "filter"
    condition: str = Field(
        ..., description="Filter condition with Jinja2 syntax, using 'item' variable"
    )

    @field_validator("condition")
    @classmethod
    def validate_condition_has_item_reference(cls, v: str) -> str:
        if "item" not in v:
            raise ValueError("Condition must reference 'item' variable")
        return v


class ReduceOperation(CollectionStep):
    """Reduce operation - aggregate elements into a single value"""

    operation: Literal["reduce"] = "reduce"
    initial_value: Any = Field(default=None, description="Initial accumulator value")
    accumulator_var: str = Field(default="acc", description="Variable name for accumulator")
    item_var: str = Field(default="item", description="Variable name for current item")
    steps: list["AICallStep | AnyTextProcessStep"] = Field(
        ..., description="Steps to apply for reduction"
    )


class PipelineOperation(CollectionStep):
    """Pipeline operation - chain multiple collection operations"""

    operation: Literal["pipeline"] = "pipeline"
    pipeline: list[dict[str, Any]] = Field(..., description="List of operations to chain")


class ConditionalBranch(BaseModel):
    """A single conditional branch definition"""

    condition: str = Field(..., description="Condition expression with Jinja2 syntax")
    name: str = Field(..., description="Branch name for identification")
    steps: list["AnyWorkflowStep"] = Field(..., description="Steps to execute in this branch")
    default: bool = Field(default=False, description="Whether this is the default branch")

    def model_post_init(self, __context: Any) -> None:
        """Validate condition requirements after all fields are set"""
        if not self.default and not self.condition.strip():
            raise ValueError("Condition cannot be empty for non-default branches")

    @field_validator("condition")
    @classmethod
    def validate_condition_or_default(cls, v: str, info: Any) -> str:
        # Allow empty condition for default branches
        # We need to check this after all fields are processed, not here
        return v


class ConditionalStep(WorkflowStep):
    """Conditional execution step with if-else or multi-branch support"""

    type: Literal["conditional"] = "conditional"

    # Basic if-else structure (optional)
    condition: str | None = Field(None, description="Simple condition for if-else structure")
    if_true: list["AnyWorkflowStep"] | None = Field(
        None, description="Steps to execute when condition is true"
    )
    if_false: list["AnyWorkflowStep"] | None = Field(
        None, description="Steps to execute when condition is false"
    )

    # Multi-branch structure (optional)
    conditions: list[ConditionalBranch] | None = Field(
        None, description="Multiple conditional branches"
    )

    # Error handling
    on_condition_error: Literal["stop", "continue", "skip_remaining"] = Field(
        default="stop", description="Action when condition evaluation fails"
    )

    @field_validator("conditions")
    @classmethod
    def validate_conditions_structure(
        cls, v: list[ConditionalBranch] | None, info: Any
    ) -> list[ConditionalBranch] | None:
        if v is None:
            return v

        # Check for duplicate names
        names = [branch.name for branch in v]
        if len(names) != len(set(names)):
            raise ValueError("Branch names must be unique")

        # Check for multiple default branches
        default_count = sum(1 for branch in v if branch.default)
        if default_count > 1:
            raise ValueError("Only one default branch is allowed")

        return v

    @field_validator("condition")
    @classmethod
    def validate_simple_condition(cls, v: str | None, info: Any) -> str | None:
        # Ensure either basic if-else or multi-branch is used, not both
        if v is not None and info.data.get("conditions") is not None:
            raise ValueError("Cannot use both 'condition' and 'conditions' fields")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that either basic or multi-branch structure is provided"""
        has_basic = self.condition is not None
        has_multi = self.conditions is not None

        if not has_basic and not has_multi:
            raise ValueError("Either 'condition' or 'conditions' must be provided")

        if has_basic and has_multi:
            raise ValueError("Cannot use both basic and multi-branch structures")

        # For basic structure, at least if_true should be provided
        if has_basic and self.if_true is None:
            raise ValueError("'if_true' steps must be provided for basic conditional structure")


@dataclass
class CollectionResult:
    """Result of a collection operation"""

    output: Any = None
    operation: str | None = None
    input_count: int = 0
    output_count: int = 0
    processing_stats: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "operation": self.operation,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "processing_stats": self.processing_stats,
            "errors": self.errors,
        }


@dataclass
class ConditionalResult:
    """Result of a conditional step execution"""

    output: Any = None
    condition_result: bool | None = None
    executed_branch: str | None = None
    evaluation_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return as dictionary for Jinja2 template reference"""
        return {
            "output": self.output,
            "condition_result": self.condition_result,
            "executed_branch": self.executed_branch,
            "evaluation_error": self.evaluation_error,
        }


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


class OutputFormat(BaseModel):
    """Workflow output format definition"""

    format: Literal["text", "json", "yaml"] = "text"
    template: str | None = None


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

    @classmethod
    def from_bakufu_config(cls, bakufu_config: Any) -> "WorkflowConfig":
        """Create WorkflowConfig from BakufuConfig"""
        from .config_loader import BakufuConfig

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
        )


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
