"""AI provider abstraction layer using LiteLLM"""

import asyncio
import os
import warnings
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

import litellm
from pydantic import BaseModel, Field

# Suppress Pydantic warnings from LiteLLM usage
warnings.filterwarnings("ignore", category=UserWarning, message=".*Pydantic serializer warnings.*")
warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

# Configure LiteLLM for quiet operation
litellm.set_verbose = False
litellm.drop_params = True


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

        # Add extra parameters
        params.update(self.config.extra_params)
        params.update(kwargs)

        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = litellm.completion(**params)

                # Calculate cost using LiteLLM's built-in function
                cost = None
                try:
                    from litellm import completion_cost

                    cost = completion_cost(completion_response=response)
                    cost = float(cost) if cost else None
                except Exception:
                    # If cost calculation fails, continue without cost info
                    pass

                return AIResponse(
                    content=response.choices[0].message.content,
                    provider=self.config.provider,
                    model=response.model,
                    usage=response.usage.model_dump() if response.usage else None,
                    finish_reason=response.choices[0].finish_reason,
                    cost_usd=cost,
                )

            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    # Exponential backoff
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break

        # All retries failed
        raise AIProviderError(
            f"Failed after {self.config.max_retries + 1} attempts: {last_error}",
            self.config.provider,
            last_error,
        ) from last_error

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


class MCPSamplingProvider(BaseAIProvider):
    """AI provider using MCP Sampling API"""

    def __init__(self, mcp_context: Any, config: AIProviderConfig):
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
                content=response.text,
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
