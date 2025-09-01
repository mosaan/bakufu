"""AI provider abstraction layer using LiteLLM"""

import asyncio
import logging
import os
import warnings
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

import litellm
from fastmcp import Context
from mcp.types import TextContent
from pydantic import BaseModel, Field
from rich.console import Console

# Suppress Pydantic warnings from LiteLLM usage
warnings.filterwarnings("ignore", category=UserWarning, message=".*Pydantic serializer warnings.*")
warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

# Configure LiteLLM for quiet operation (temporarily enable for debugging)
litellm.set_verbose = True  # Enable for debugging max_tokens issue
litellm.drop_params = False  # Disable dropping for debugging

# Set up logger and console
logger = logging.getLogger(__name__)
console = Console()


class AIProviderConfig(BaseModel):
    """Configuration for AI providers"""

    provider: str = "gemini/gemini-2.0-flash"
    api_key: str | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, gt=0)
    timeout: int = Field(30, gt=0)
    max_retries: int = Field(3, ge=0)

    # Provider-specific settings
    extra_params: dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    """Response from AI provider"""

    content: str
    provider: str
    model: str
    usage: dict[str, Any] | None = None
    finish_reason: str | None = None
    cost_usd: float | None = None


class AIProviderError(Exception):
    """Error from AI provider"""

    def __init__(self, message: str, provider: str, original_error: Exception | None = None):
        super().__init__(f"AI Provider '{provider}': {message}")
        self.provider = provider
        self.original_error = original_error


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config: AIProviderConfig):
        self.config = config

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Generate completion from AI provider"""
        pass

    # stream_complete is implemented by subclasses with async generator pattern

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to AI provider"""
        pass

    def _get_temperature(self, kwargs: dict[str, Any]) -> float:
        """Get temperature parameter with fallback to config"""
        temp = kwargs.get("temperature", self.config.temperature)
        return float(temp)

    def _get_max_tokens(self, kwargs: dict[str, Any]) -> int | None:
        """Get max_tokens parameter with fallback to config"""
        return kwargs.get("max_tokens", self.config.max_tokens)


class AIProvider(BaseAIProvider):
    """AI provider using LiteLLM for multiple AI services"""

    def __init__(self, config: AIProviderConfig):
        """Initialize AI provider with configuration"""
        super().__init__(config)

        # Set up API keys from environment or config
        self._setup_api_keys()

        # Configure litellm settings
        litellm.set_verbose = False
        litellm.drop_params = True  # Drop unsupported params instead of failing

    def _setup_api_keys(self) -> None:
        """Set up API keys from environment variables or config"""
        # Google Gemini
        if "gemini" in self.config.provider.lower():
            api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key

        # OpenAI
        elif "gpt" in self.config.provider.lower() or "openai" in self.config.provider.lower():
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key

        # Anthropic
        elif (
            "claude" in self.config.provider.lower() or "anthropic" in self.config.provider.lower()
        ):
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key

    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Generate completion from AI provider"""
        # Get max_auto_retry_attempts from kwargs or use default of 0 (disabled by default)
        max_auto_retry_attempts = kwargs.pop("max_auto_retry_attempts", 0)

        # Merge config with call-specific parameters
        params = {
            "model": self.config.provider,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "timeout": kwargs.get("timeout", self.config.timeout),
        }

        # Add max_tokens if specified
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            params["max_tokens"] = max_tokens
            console.print(f"🎯 max_tokens set to: {max_tokens}", style="yellow")

        # Add extra parameters
        params.update(self.config.extra_params)
        params.update(kwargs)

        # Main completion with auto-continuation logic
        return await self._complete_with_auto_retry(params, max_auto_retry_attempts)

    async def _complete_with_auto_retry(
        self, params: dict[str, Any], max_auto_retry_attempts: int
    ) -> AIResponse:
        """Complete with auto-continuation when responses are truncated"""
        if max_auto_retry_attempts > 0:
            console.print(
                f"🔄 Auto-Continuation enabled: max_retry_attempts={max_auto_retry_attempts}",
                style="cyan",
            )
        else:
            console.print("⏹️ Auto-Continuation disabled (max_retry_attempts=0)", style="dim")

        context = _CompletionContext(
            params=params,
            max_auto_retry_attempts=max_auto_retry_attempts,
            max_retries=self.config.max_retries,
            provider=self.config.provider,
        )

        processor = _CompletionProcessor()
        return await processor.process_completion(context)

    async def stream_complete(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """Generate streaming completion from AI provider"""
        # Merge config with call-specific parameters
        params = {
            "model": self.config.provider,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "timeout": kwargs.get("timeout", self.config.timeout),
            "stream": True,
        }

        # Add max_tokens if specified
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        if max_tokens:
            params["max_tokens"] = max_tokens

        # Add extra parameters
        params.update(self.config.extra_params)
        params.update(kwargs)

        try:
            response = litellm.completion(**params)

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise AIProviderError(f"Streaming failed: {e}", self.config.provider, e) from e

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to AI provider"""
        try:
            # Simple test prompt
            response = litellm.completion(
                model=self.config.provider,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                timeout=10,
            )

            if response.choices[0].message.content:
                return True, f"Connection successful to {self.config.provider}"
            else:
                return False, "No response content received"

        except Exception as e:
            return False, f"Connection failed: {e}"


class _CompletionContext:
    """Context object for completion processing"""

    def __init__(
        self, params: dict[str, Any], max_auto_retry_attempts: int, max_retries: int, provider: str
    ):
        self.params = params
        self.max_auto_retry_attempts = max_auto_retry_attempts
        self.max_retries = max_retries
        self.provider = provider
        self.accumulated_content = ""
        self.accumulated_usage: dict[str, int | float] = {}
        self.accumulated_cost = 0.0
        self.total_api_calls = 0


class _CompletionProcessor:
    """Processes AI completions with auto-retry logic"""

    async def process_completion(self, context: _CompletionContext) -> AIResponse:
        """Process completion with auto-continuation"""
        for continuation_attempt in range(context.max_auto_retry_attempts + 1):
            if continuation_attempt == 0:
                console.print("📤 Making initial AI request...", style="blue")
            else:
                console.print(
                    f"🔄 Auto-continuation attempt {continuation_attempt}/{context.max_auto_retry_attempts}",
                    style="yellow",
                )
                console.print(
                    f"📝 Current accumulated content length: {len(context.accumulated_content)} characters",
                    style="dim",
                )

            self._prepare_continuation_messages(context, continuation_attempt)

            try:
                response = await self._execute_completion_with_retries(
                    context, continuation_attempt
                )
                if response:
                    return response
            except AIProviderError:
                raise

        return self._create_fallback_response(context)

    def _prepare_continuation_messages(
        self, context: _CompletionContext, continuation_attempt: int
    ) -> None:
        """Prepare messages for continuation attempts"""
        if continuation_attempt > 0 and context.accumulated_content:
            console.print("💬 Preparing continuation conversation context...", style="magenta")
            original_message = context.params["messages"][0]["content"]
            context.params["messages"] = [
                {"role": "user", "content": original_message},
                {"role": "assistant", "content": context.accumulated_content},
                {
                    "role": "user",
                    "content": "Please continue writing from where you left off. Keep your continuation brief and conclude naturally when you have completed your thought. Do not repeat previous content.",
                },
            ]
            console.print(
                f"   📋 Conversation now has {len(context.params['messages'])} messages",
                style="dim",
            )

    async def _execute_completion_with_retries(
        self, context: _CompletionContext, continuation_attempt: int
    ) -> AIResponse | None:
        """Execute completion with error retry logic"""
        last_error = None

        for attempt in range(context.max_retries + 1):
            try:
                response = litellm.completion(**context.params)
                context.total_api_calls += 1

                # # HACK: For Ollama, check "done_reason" to handle truncation
                if "ollama" in context.provider.lower():
                    done_reason = response.done_reason
                    response.choices[0].finish_reason = done_reason
                # if (
                #     "ollama" in context.provider.lower()
                #     and response.choices[0].finish_reason == "stop"
                #     and "max_tokens" in context.params
                #     and len(response.choices[0].message.content or "") > 0
                # ):
                #     # If content looks truncated, manually set finish_reason to length
                #     content_length = len(response.choices[0].message.content or "")
                #     console.print(f"🔍 Ollama hack: content_length={content_length}, checking for truncation...", style="dim")

                #     # Simple heuristic: if content doesn't end with sentence punctuation, assume truncated
                #     content = response.choices[0].message.content or ""
                #     if content and not content.rstrip().endswith(('.', '!', '?', ':', ';')):
                #         console.print("🔧 Ollama hack: Overriding finish_reason to 'length'", style="yellow")
                #         response.choices[0].finish_reason = "length"

                self._accumulate_response_data(context, response)
                return self._handle_completion_result(context, response, continuation_attempt)

            except Exception as e:
                last_error = e
                if attempt < context.max_retries:
                    await asyncio.sleep(2**attempt)
                    continue
                else:
                    raise AIProviderError(
                        f"Failed after {context.max_retries + 1} attempts on continuation {continuation_attempt + 1}: {last_error}",
                        context.provider,
                        last_error,
                    ) from last_error

        return None

    def _accumulate_response_data(self, context: _CompletionContext, response: Any) -> None:
        """Accumulate content, usage, and cost from response"""
        current_content = response.choices[0].message.content or ""
        context.accumulated_content += current_content

        if response.usage:
            usage_dict = response.usage.model_dump()
            for key, value in usage_dict.items():
                if isinstance(value, int | float):
                    context.accumulated_usage[key] = context.accumulated_usage.get(key, 0) + value

        cost = self._calculate_cost(response)
        if cost:
            context.accumulated_cost += cost

    def _calculate_cost(self, response: Any) -> float | None:
        """Calculate cost using LiteLLM's built-in function"""
        try:
            from litellm.cost_calculator import completion_cost

            cost = completion_cost(completion_response=response)
            return float(cost) if cost else None
        except Exception:
            return None

    def _handle_completion_result(
        self, context: _CompletionContext, response: Any, continuation_attempt: int
    ) -> AIResponse | None:
        """Handle the completion result based on finish reason"""
        finish_reason = response.choices[0].finish_reason
        current_content_length = len(response.choices[0].message.content or "")

        console.print(
            f"📨 Response received: finish_reason='{finish_reason}', content_length={current_content_length}",
            style="blue",
        )

        if finish_reason == "stop":
            console.print("✅ Response completed naturally (finish_reason='stop')", style="green")
            return self._create_final_response(context, response, finish_reason)
        elif finish_reason in ["length", "max_tokens"]:
            if continuation_attempt >= context.max_auto_retry_attempts:
                console.print(
                    f"⚠️ Max auto-retry attempts ({context.max_auto_retry_attempts}) reached, stopping continuation",
                    style="yellow",
                )
                return self._create_final_response(context, response, finish_reason)
            else:
                console.print(
                    f"🔄 Response truncated due to token limit (finish_reason='{finish_reason}'), will continue...",
                    style="yellow",
                )
                return None  # Continue to next auto-retry attempt
        else:
            console.print(
                f"🔚 Response completed with finish_reason='{finish_reason}', stopping",
                style="cyan",
            )
            return self._create_final_response(context, response, finish_reason)

    def _create_final_response(
        self, context: _CompletionContext, response: Any, finish_reason: str
    ) -> AIResponse:
        """Create final AIResponse object"""
        final_response = AIResponse(
            content=context.accumulated_content,
            provider=context.provider,
            model=response.model,
            usage=context.accumulated_usage if context.accumulated_usage else None,
            finish_reason=finish_reason,
            cost_usd=context.accumulated_cost if context.accumulated_cost > 0 else None,
        )

        # Print completion summary
        console.print("🎯 Auto-Continuation completed:", style="bold green")
        console.print(f"   📊 Total API calls: {context.total_api_calls}", style="green")
        console.print(
            f"   📝 Final content length: {len(context.accumulated_content)} characters",
            style="green",
        )
        console.print(f"   🏁 Final finish_reason: '{finish_reason}'", style="green")
        if context.accumulated_usage:
            total_tokens = context.accumulated_usage.get("total_tokens", 0)
            console.print(f"   🪙 Total tokens used: {total_tokens}", style="green")

        return final_response

    def _create_fallback_response(self, context: _CompletionContext) -> AIResponse:
        """Create fallback response when max retries reached"""
        console.print(
            f"⚠️ Auto-Continuation fallback: max attempts ({context.max_auto_retry_attempts}) reached",
            style="bold yellow",
        )
        console.print(
            f"   📝 Accumulated content length: {len(context.accumulated_content)} characters",
            style="yellow",
        )
        console.print(f"   📊 Total API calls made: {context.total_api_calls}", style="yellow")

        return AIResponse(
            content=context.accumulated_content,
            provider=context.provider,
            model=context.params["model"],
            usage=context.accumulated_usage if context.accumulated_usage else None,
            finish_reason="max_auto_retries_reached",
            cost_usd=context.accumulated_cost if context.accumulated_cost > 0 else None,
        )


class MCPSamplingProvider(BaseAIProvider):
    """AI provider using MCP Sampling API"""

    def __init__(self, mcp_context: Context, config: AIProviderConfig):
        """Initialize MCP Sampling provider with context and configuration"""
        super().__init__(config)
        self.mcp_context = mcp_context

    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Generate completion using MCP sampling API"""
        try:
            # Prepare sampling parameters using inherited methods
            temperature = self._get_temperature(kwargs)
            max_tokens = self._get_max_tokens(kwargs)

            # Use MCP sampling API
            response = await self.mcp_context.sample(
                messages=prompt, temperature=temperature, max_tokens=max_tokens
            )

            return AIResponse(
                content=response.text
                if isinstance(response, TextContent)
                else "[WARNING] response is not text content. Check your MCP context configuration.",
                provider="mcp_sampling",
                model="client_llm",
                usage=None,  # MCP sampling doesn't provide usage stats
                finish_reason="stop",
                cost_usd=None,  # No cost for MCP sampling
            )

        except Exception as e:
            raise AIProviderError(
                f"MCP sampling failed: {e}",
                "mcp_sampling",
                e,
            ) from e

    async def stream_complete(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """MCP sampling doesn't support streaming, fallback to complete"""
        response = await self.complete(prompt, **kwargs)
        yield response.content

    def test_connection(self) -> tuple[bool, str]:
        """Test MCP context availability"""
        try:
            if self.mcp_context is None:
                return False, "MCP context is not available"
            return True, "MCP sampling provider is available"
        except Exception as e:
            return False, f"MCP context test failed: {e}"


class AIProviderManager:
    """Manager for multiple AI providers with fallback support"""

    def __init__(
        self,
        primary_config: AIProviderConfig,
        fallback_configs: list[AIProviderConfig] | None = None,
    ):
        """Initialize with primary and fallback providers"""
        self.primary = AIProvider(primary_config)
        self.fallbacks = [AIProvider(config) for config in (fallback_configs or [])]

    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Try completion with primary, then fallback providers"""
        providers = [self.primary, *self.fallbacks]

        last_error = None
        for provider in providers:
            try:
                return await provider.complete(prompt, **kwargs)
            except AIProviderError as e:
                last_error = e
                continue

        # All providers failed
        raise AIProviderError(
            f"All providers failed. Last error: {last_error}", "all_providers", last_error
        ) from last_error

    async def stream_complete(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """Try streaming with primary, then fallback providers"""
        providers = [self.primary, *self.fallbacks]

        last_error = None
        for provider in providers:
            try:
                async for chunk in provider.stream_complete(prompt, **kwargs):
                    yield chunk
                return  # Success, don't try fallbacks
            except AIProviderError as e:
                last_error = e
                continue

        # All providers failed
        raise AIProviderError(
            f"All streaming providers failed. Last error: {last_error}", "all_providers", last_error
        ) from last_error

    def test_all_connections(self) -> dict[str, tuple[bool, str]]:
        """Test connections to all providers"""
        results = {}

        # Test primary
        success, message = self.primary.test_connection()
        results[self.primary.config.provider] = (success, message)

        # Test fallbacks
        for provider in self.fallbacks:
            success, message = provider.test_connection()
            results[provider.config.provider] = (success, message)

        return results
