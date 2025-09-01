"""AI call step models for Bakufu workflows"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

from ...base_types import WorkflowStep
from ...step_registry import step_type

if TYPE_CHECKING:
    from ...ai_provider import AIProviderConfig, BaseAIProvider
    from ...models import ExecutionContext
    from ...validation import OutputValidator


@step_type("ai_call")
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
        description=(
            "AI provider parameters passed directly to LiteLLM. "
            "All OpenAI-compatible parameters are supported transparently. "
            "Common examples: response_format, top_p, presence_penalty, frequency_penalty, "
            "logit_bias, stop, functions, tools, tool_choice, seed, etc. "
            "Provider-specific parameters (e.g., Anthropic's top_k) are also supported. "
            "See docs/08-reference/ai-parameters.md for complete usage guide."
        ),
    )

    # Validation configuration
    validation: dict[str, Any] | None = Field(None, description="Output validation configuration")

    async def execute(self, context: Any) -> Any:
        """Execute AI call step directly using Command Pattern"""
        from typing import cast

        from ...ai_provider import (
            AIProvider,
            AIProviderError,
            MCPSamplingProvider,
        )
        from ...exceptions import (
            ErrorContext,
            StepExecutionError,
            TemplateError,
        )
        from ...models import ExecutionContext

        context = cast(ExecutionContext, context)

        # Render prompt template
        try:
            rendered_prompt = context.render_template(self.prompt)
        except Exception as e:
            raise TemplateError(
                message=f"AI step prompt template rendering failed: {e}",
                template_content=self.prompt,
                line_number=getattr(e, "lineno", None),
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    "Check prompt template syntax",
                    "Verify all variables are available in context",
                    f"Template: {self.prompt[:50]}...",
                ],
            ) from e

        # Create AI provider configuration
        provider_config = self._build_ai_provider_config(context)

        try:
            # Choose provider based on sampling mode
            ai_provider: BaseAIProvider
            if context.sampling_mode and context.mcp_context:
                ai_provider = MCPSamplingProvider(context.mcp_context, provider_config)
            else:
                ai_provider = AIProvider(provider_config)

            # Handle validation if specified
            if self.validation:
                return await self._execute_ai_call_with_validation(
                    ai_provider, rendered_prompt, context
                )
            else:
                response = await ai_provider.complete(rendered_prompt)
                # Add usage information to context
                context.add_step_usage(self.id, response.usage, response.cost_usd)
                return response.content
        except AIProviderError as e:
            # AI provider errors are already well-structured
            raise StepExecutionError(
                message=f"AI provider error: {e!s}",
                step_id=self.id,
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    "Check AI provider configuration",
                    "Verify API keys",
                    "Check network connectivity",
                ],
            ) from e
        except Exception as e:
            raise StepExecutionError(
                message=f"Unexpected AI call error: {e}",
                step_id=self.id,
                context=ErrorContext(step_id=self.id, function_name="execute"),
                original_error=e,
                suggestions=[
                    "Check AI provider configuration",
                    "Verify network connectivity",
                    "Check input prompt format",
                ],
            ) from e

    def _build_ai_provider_config(self, context: ExecutionContext) -> AIProviderConfig:
        """Build AI provider configuration from step and context."""
        from ...ai_provider import AIProviderConfig

        provider_config = AIProviderConfig(
            provider=self.provider or context.config.default_provider,
            temperature=self.temperature if self.temperature is not None else 0.7,
            max_tokens=self.max_tokens,
            timeout=context.config.timeout_per_step,
            max_retries=3,
        )

        # Apply provider-specific settings if available
        provider_name = (
            provider_config.provider.split("/")[0]
            if "/" in provider_config.provider
            else provider_config.provider
        )
        if provider_name in context.config.provider_settings:
            provider_config.extra_params.update(context.config.provider_settings[provider_name])  # type: ignore[typeddict-item]

        # Apply step-level ai_params (takes precedence over provider settings)
        if hasattr(self, "ai_params") and getattr(self, "ai_params", None):
            provider_config.extra_params.update(getattr(self, "ai_params", {}))  # type: ignore[typeddict-item]

        return provider_config

    def _prepare_retry_prompt(
        self, original_prompt: str, validator: OutputValidator, validation_result: Any
    ) -> str:
        """Prepare the prompt for a validation retry."""
        retry_prompt_suffix = validator.get_retry_prompt(validation_result)
        return f"{original_prompt}\n\n{retry_prompt_suffix}"

    async def _execute_ai_call_with_validation(
        self, ai_provider: BaseAIProvider, prompt: str, context: ExecutionContext
    ) -> str:
        """Execute AI call with output validation and retry logic"""
        from ...ai_provider import AIProviderError
        from ...exceptions import ErrorContext, StepExecutionError
        from ...validation import OutputValidator, ValidationConfig, ValidationError

        if self.validation is None:
            raise ValueError("Validation configuration is required")
        validation_config = ValidationConfig(**self.validation)
        validator = OutputValidator(validation_config)

        original_prompt = prompt
        current_prompt = prompt

        # Add JSON wrapper instruction if needed
        if validator.should_force_json_wrapper():
            current_prompt = f"{current_prompt}\n\n{validator.get_json_wrapper_instruction()}"

        for attempt in range(validation_config.max_retries + 1):
            try:
                response = await ai_provider.complete(current_prompt)

                # Add usage information to context
                context.add_step_usage(self.id, response.usage, response.cost_usd)

                # Validate the response
                validation_result = validator.validate(response.content, attempt + 1)

                if validation_result.is_valid:
                    # Return the validated output (could be parsed JSON or original text)
                    return validation_result.validated_output or response.content

                # Validation failed, prepare for retry
                if attempt < validation_config.max_retries:
                    current_prompt = self._prepare_retry_prompt(
                        original_prompt, validator, validation_result
                    )
                    continue
                else:
                    # All retries exhausted
                    raise ValidationError(
                        f"Validation failed after {validation_config.max_retries + 1} attempts",
                        response.content,
                        validation_result.errors,
                    )

            except ValidationError:
                raise
            except AIProviderError as e:
                # Re-raise AI provider errors as-is
                raise StepExecutionError(
                    message=f"AI provider error during validation attempt {attempt + 1}: {e!s}",
                    step_id=self.id,
                    context=ErrorContext(
                        step_id=self.id, function_name="_execute_ai_call_with_validation"
                    ),
                    original_error=e,
                    suggestions=[
                        "Check AI provider configuration",
                        "Verify API keys",
                        "Check network connectivity",
                    ],
                ) from e
            except Exception as e:
                if attempt < validation_config.max_retries:
                    continue
                else:
                    raise StepExecutionError(
                        message=f"Unexpected error during validated AI call: {e}",
                        step_id=self.id,
                        context=ErrorContext(
                            step_id=self.id, function_name="_execute_ai_call_with_validation"
                        ),
                        original_error=e,
                        suggestions=[
                            "Check validation configuration",
                            "Verify JSON schema format",
                            "Check custom validation function",
                        ],
                    ) from e

        # This should never be reached
        raise RuntimeError("Validation loop completed without returning a result")
