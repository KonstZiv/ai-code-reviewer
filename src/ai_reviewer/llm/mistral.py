"""Mistral LLM provider for AI Code Reviewer.

This module implements ``LLMProvider`` using the Mistral AI SDK.
It supports both structured (Pydantic schema) and raw-text responses,
token tracking, cost estimation, and automatic retry on transient errors.

Typical usage::

    provider = MistralProvider(api_key="...", model_name="mistral-large-latest")
    response = provider.generate(prompt, response_schema=ReviewResult)
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, overload

import httpx
from mistralai.client import Mistral
from mistralai.client.errors.sdkerror import SDKError
from mistralai.client.models import ResponseFormat
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from mistralai.client.models import ChatCompletionResponse

from ai_reviewer.llm.base import LLMProvider, LLMResponse
from ai_reviewer.utils.retry import (
    AuthenticationError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
    with_retry,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "mistral-large-latest"

# Timeout for Mistral API requests (seconds).
_API_TIMEOUT_S = 300  # 5 minutes


def _convert_mistral_exception(e: SDKError) -> Exception:
    """Convert Mistral SDK error to the internal exception hierarchy.

    Inspects the HTTP status code on the ``SDKError.raw_response`` and
    the error message to determine the correct internal type.

    Args:
        e: Mistral SDK error.

    Returns:
        Converted exception or the original if no match.
    """
    status = e.raw_response.status_code if hasattr(e, "raw_response") else 0
    msg = f"Mistral: {e}"

    if status == 401:  # noqa: PLR2004
        return AuthenticationError(msg)
    if status == 429:  # noqa: PLR2004
        error_str = str(e).lower()
        if "quota" in error_str or "limit" in error_str:
            return QuotaExhaustedError(msg)
        return RateLimitError(msg)
    if status >= 500:  # noqa: PLR2004
        return ServerError(msg, status_code=status)

    return _match_by_error_message(e)


def _match_by_error_message(e: Exception) -> Exception:
    """Match exception by error message keywords (fallback heuristic).

    Args:
        e: Exception whose message is inspected.

    Returns:
        Converted exception or the original if no keyword matched.
    """
    error_msg = str(e).lower()
    if "rate limit" in error_msg or "429" in error_msg:
        return RateLimitError(f"Mistral: {e}")
    if "quota" in error_msg:
        return QuotaExhaustedError(f"Mistral: {e}")
    if any(kw in error_msg for kw in ("500", "502", "503", "504", "server error")):
        return ServerError(f"Mistral: {e}")
    if "unauthorized" in error_msg or "authentication" in error_msg:
        return AuthenticationError(f"Mistral: {e}")
    return e


_PARSING_ERROR_MSG = "Mistral response could not be parsed"


class MistralProvider(LLMProvider):
    """LLM provider backed by Mistral AI.

    Attributes:
        model_name: The Mistral model identifier in use.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        server_url: str | None = None,
    ) -> None:
        """Initialize Mistral provider.

        Args:
            api_key: Mistral API key.
            model_name: Mistral model to use.
            server_url: Custom API base URL (e.g. ``https://codestral.mistral.ai``).
        """
        client_kwargs: dict[str, object] = {
            "api_key": api_key,
            "timeout_ms": _API_TIMEOUT_S * 1000,
        }
        if server_url:
            client_kwargs["server_url"] = server_url

        self._client = Mistral(**client_kwargs)  # type: ignore[arg-type]
        self._model_name = model_name
        logger.debug("MistralProvider initialized with model %s (url=%s)", model_name, server_url)

    @property
    def model_name(self) -> str:
        """Return the Mistral model identifier."""
        return self._model_name

    @overload
    def generate[T: BaseModel](
        self,
        prompt: str,
        *,
        system_prompt: str | None = ...,
        response_schema: type[T],
        temperature: float = ...,
    ) -> LLMResponse[T]: ...

    @overload
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = ...,
        response_schema: None = ...,
        temperature: float = ...,
    ) -> LLMResponse[str]: ...

    @with_retry
    def generate[T: BaseModel](
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: type[T] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse[T] | LLMResponse[str]:
        """Send a prompt to Mistral and return a structured response.

        Args:
            prompt: User prompt text.
            system_prompt: Optional system instruction.
            response_schema: Pydantic model for structured JSON output.
            temperature: Sampling temperature (0.0 = deterministic).

        Returns:
            LLMResponse with parsed content or raw text.

        Raises:
            AuthenticationError: If API key is invalid.
            RateLimitError: If rate limit exceeded (will retry).
            ServerError: If Mistral server error (will retry).
            ValueError: If structured response cannot be parsed.
        """
        try:
            start_time = time.perf_counter()

            messages: list[dict[str, str]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            kwargs: dict[str, object] = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
            }
            if response_schema is not None:
                kwargs["response_format"] = ResponseFormat(type="json_object")

            response: ChatCompletionResponse = self._client.chat.complete(**kwargs)  # type: ignore[arg-type]

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            content = self._parse_response(response, response_schema)

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            if response.usage:
                prompt_tokens = response.usage.prompt_tokens or 0
                completion_tokens = response.usage.completion_tokens or 0
                total_tokens = response.usage.total_tokens or 0

            logger.debug(
                "Mistral API call: %d tokens (%d in, %d out), %dms",
                total_tokens,
                prompt_tokens,
                completion_tokens,
                elapsed_ms,
            )

            return LLMResponse(
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model_name=self.model_name,
                latency_ms=elapsed_ms,
                estimated_cost_usd=0.0,
            )

        except ValidationError:
            logger.exception("Failed to validate Mistral response structure")
            raise
        except SDKError as e:
            logger.warning("Mistral SDK error: %s", e)
            raise _convert_mistral_exception(e) from e
        except (
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.ConnectError,
            ConnectionError,
            OSError,
        ) as e:
            logger.warning(
                "Mistral connection/timeout error (%s): %s",
                type(e).__name__,
                e,
            )
            msg = f"Mistral: connection error - {e}"
            raise ServerError(msg) from e
        except Exception as e:
            converted = _match_by_error_message(e)
            if converted is not e:
                logger.warning("Mistral API error: %s", e)
                raise converted from e
            logger.exception("Mistral API call failed")
            raise

    @staticmethod
    def _parse_response[T: BaseModel](
        response: ChatCompletionResponse,
        schema: type[T] | None,
    ) -> T | str:
        """Parse Mistral response into structured model or raw text.

        Args:
            response: Raw Mistral API response.
            schema: Pydantic model class for validation, or None for raw text.

        Returns:
            Parsed model instance or raw text string.

        Raises:
            ValueError: If response is empty or cannot be parsed.
        """
        if not response.choices or not response.choices[0].message:
            raise ValueError(_PARSING_ERROR_MSG)

        text = response.choices[0].message.content
        if not text:
            raise ValueError(_PARSING_ERROR_MSG)

        # Mistral returns content as str or list; normalize to str
        if isinstance(text, list):
            text = "".join(str(chunk) for chunk in text)

        if schema is None:
            return text

        return schema.model_validate_json(text)


__all__ = [
    "DEFAULT_MODEL",
    "MistralProvider",
]
