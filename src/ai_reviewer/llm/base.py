"""Abstract base classes for LLM provider integrations.

This module defines the generic LLM interface that all providers must implement.
The abstraction enables pluggable LLM backends (Gemini, Claude, OpenAI, etc.)
while maintaining a consistent API for the reviewer and discovery engine.

Typical usage:
    provider = GeminiProvider(api_key="...", model_name="gemini-2.5-flash")
    response = provider.generate(prompt, response_schema=ReviewResult)
    result: ReviewResult = response.content
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import overload

from pydantic import BaseModel, ConfigDict, Field


class LLMResponse[T](BaseModel):
    """Unified response from any LLM provider.

    Generic parameter T is the type of parsed content (e.g. ReviewResult,
    ProjectProfile). When no response_schema is provided, T is ``str``.

    Attributes:
        content: Parsed model instance or raw text.
        prompt_tokens: Number of input tokens consumed.
        completion_tokens: Number of output tokens generated.
        total_tokens: Total tokens (prompt + completion).
        model_name: The model identifier used for the request.
        latency_ms: Wall-clock API call latency in milliseconds.
        estimated_cost_usd: Estimated cost in USD based on provider pricing.
    """

    model_config = ConfigDict(frozen=True)

    content: T | str
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    model_name: str = ""
    latency_ms: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)


class LLMProvider(ABC):
    """Abstract LLM provider interface.

    Single method ``generate()`` — prompt in, structured response out.
    Implementations: GeminiProvider, (future) ClaudeProvider, OpenAIProvider.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier (e.g. ``gemini-2.5-flash``)."""
        ...

    @overload
    @abstractmethod
    def generate[T: BaseModel](
        self,
        prompt: str,
        *,
        system_prompt: str | None = ...,
        response_schema: type[T],
        temperature: float = ...,
    ) -> LLMResponse[T]: ...

    @overload
    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = ...,
        response_schema: None = ...,
        temperature: float = ...,
    ) -> LLMResponse[str]: ...

    @abstractmethod
    def generate[T: BaseModel](
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: type[T] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse[T] | LLMResponse[str]:
        """Send a prompt to the LLM and receive a structured response.

        Args:
            prompt: User prompt text.
            system_prompt: Optional system instruction prepended to the request.
            response_schema: Pydantic model class for structured JSON output.
                When ``None``, raw text is returned in ``content``.
            temperature: Sampling temperature (0.0 = deterministic).

        Returns:
            ``LLMResponse[T]`` when ``response_schema`` is given,
            ``LLMResponse[str]`` otherwise.

        Raises:
            AuthenticationError: Invalid API key.
            RateLimitError: Rate limit exceeded (retryable).
            ServerError: Provider server error (retryable).
        """
        ...


__all__ = [
    "LLMProvider",
    "LLMResponse",
]
