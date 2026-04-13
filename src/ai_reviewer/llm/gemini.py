"""Google Gemini LLM provider for AI Code Reviewer.

This module implements ``LLMProvider`` using the Google GenAI SDK.
It supports both structured (Pydantic schema) and raw-text responses,
token tracking, cost estimation, and automatic retry on transient errors.

Typical usage:
    provider = GeminiProvider(api_key="...", model_name="gemini-2.5-flash")
    response = provider.generate(prompt, response_schema=ReviewResult)
"""

from __future__ import annotations

import logging
import re
import time
from typing import overload

import httpx
from google import genai
from google.api_core import exceptions as google_exceptions
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from ai_reviewer.llm.base import LLMProvider, LLMResponse
from ai_reviewer.utils.retry import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
    with_retry,
)

# Timeout for Gemini API requests (milliseconds).
# google-genai HttpOptions.timeout is in milliseconds.
_API_TIMEOUT_MS = 300_000  # 5 minutes

logger = logging.getLogger(__name__)

# Gemini pricing per 1M tokens (as of February 2026)
# https://ai.google.dev/pricing
GEMINI_PRICING: dict[str, dict[str, float]] = {
    # Gemini 3.x (preview)
    "gemini-3-flash-preview": {"input": 0.075, "output": 0.30},
    "gemini-3.1-flash-lite-preview": {"input": 0.01875, "output": 0.075},
    "gemini-3.1-pro-preview": {"input": 1.25, "output": 5.00},
    # Gemini 2.5
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-flash-lite": {"input": 0.01875, "output": 0.075},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    # Gemini 2.0 Flash
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
    # Legacy models
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-pro-latest": {"input": 1.25, "output": 5.00},
    "gemini-pro": {"input": 0.50, "output": 1.50},
}

# Default pricing for unknown models (conservative estimate)
DEFAULT_PRICING: dict[str, float] = {"input": 1.00, "output": 3.00}

# Default model to use when not specified
DEFAULT_MODEL = "gemini-2.5-flash"


def calculate_cost(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculate estimated cost for Gemini API usage.

    Args:
        model_name: The model name used for the request.
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.

    Returns:
        Estimated cost in USD.
    """
    pricing = GEMINI_PRICING.get(model_name, DEFAULT_PRICING)
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


_PARSING_ERROR_MSG = "Gemini response could not be parsed"

# Regex to extract file paths from "File: path (type)" headers in the prompt.
_FILE_HEADER_RE = re.compile(r"^File:\s*(\S+)\s*\(", re.MULTILINE)


def _log_prompt_debug_info(prompt: str, system_prompt: str | None) -> None:
    """Log diagnostic information about the prompt for debugging API errors.

    Logs prompt length (chars), system prompt length, and the list of
    files included in the prompt (extracted from ``### File:`` headers).

    Args:
        prompt: The user prompt sent to the API.
        system_prompt: The system prompt, if any.
    """
    files = _FILE_HEADER_RE.findall(prompt)
    system_len = len(system_prompt) if system_prompt else 0
    logger.warning(
        "Prompt debug: %d chars (system: %d chars), %d files: %s",
        len(prompt),
        system_len,
        len(files),
        files,
    )


# Keywords in quotaId that indicate a daily or free-tier quota (not retryable).
_DAILY_QUOTA_KEYWORDS = ("perday", "freetier", "daily")


def _is_daily_quota_error(error_msg: str) -> str | None:
    """Check if a 429 error is caused by daily/free-tier quota exhaustion.

    Parses the error message for ``quotaId`` values containing keywords
    like ``PerDay`` or ``FreeTier``.

    Args:
        error_msg: The stringified error message from Gemini API.

    Returns:
        The matched quotaId string if daily quota detected, None otherwise.
    """
    match = re.search(r"'quotaId':\s*'([^']+)'", error_msg)
    if match:
        quota_id = match.group(1)
        if any(kw in quota_id.lower() for kw in _DAILY_QUOTA_KEYWORDS):
            return quota_id
    return None


def _match_by_error_message(e: Exception) -> Exception:
    """Match exception by error message keywords (fallback heuristic).

    Args:
        e: Exception whose message is inspected.

    Returns:
        Converted exception or the original if no keyword matched.
    """
    error_msg_str = str(e)
    error_msg = error_msg_str.lower()
    if "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
        quota_id = _is_daily_quota_error(error_msg_str)
        if quota_id:
            return QuotaExhaustedError(f"Gemini: {e}", quota_id=quota_id)
        return RateLimitError(f"Gemini: {e}")
    if any(kw in error_msg for kw in ("500", "502", "503", "504", "server error", "deadline")):
        return ServerError(f"Gemini: {e}")
    if "404" in error_msg or "not_found" in error_msg or "not found" in error_msg:
        return NotFoundError(f"Gemini: {e}")
    return e


def _convert_google_exception(e: Exception) -> Exception:  # noqa: PLR0911
    """Convert Google API exception to the internal exception hierarchy.

    Checks concrete ``google.api_core.exceptions`` types first, then
    falls back to keyword matching on the error message.

    Args:
        e: Google API exception.

    Returns:
        Converted exception (RetryableError subclass or APIClientError subclass),
        or the original exception if no match is found.
    """
    if isinstance(e, google_exceptions.ResourceExhausted):
        quota_id = _is_daily_quota_error(str(e))
        if quota_id:
            return QuotaExhaustedError(f"Gemini: {e}", quota_id=quota_id)
        return RateLimitError(f"Gemini: {e}")

    if isinstance(e, google_exceptions.Unauthenticated):
        return AuthenticationError(f"Gemini: Invalid API key - {e}")

    if isinstance(e, google_exceptions.PermissionDenied):
        return ForbiddenError(f"Gemini: {e}")

    if isinstance(e, google_exceptions.NotFound):
        return NotFoundError(f"Gemini: {e}")

    if isinstance(
        e,
        (
            google_exceptions.InternalServerError,
            google_exceptions.ServiceUnavailable,
            google_exceptions.DeadlineExceeded,
        ),
    ):
        return ServerError(f"Gemini: {e}")

    return _match_by_error_message(e)


class GeminiProvider(LLMProvider):
    """LLM provider backed by Google Gemini.

    Attributes:
        model_name: The Gemini model identifier in use.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
    ) -> None:
        """Initialize Gemini provider.

        Args:
            api_key: Google API key (plain string; caller is responsible
                for extracting from ``SecretStr`` if needed).
            model_name: Gemini model to use.
        """
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=_API_TIMEOUT_MS),
        )
        self._model_name = model_name
        logger.debug("GeminiProvider initialized with model %s", model_name)

    @property
    def model_name(self) -> str:
        """Return the Gemini model identifier."""
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
        """Send a prompt to Gemini and return a structured response.

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
            ServerError: If Gemini server error (will retry).
            ValueError: If structured response cannot be parsed.
        """
        try:
            start_time = time.perf_counter()

            config = types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json" if response_schema else None,
                response_schema=response_schema,
            )
            if system_prompt:
                config.system_instruction = system_prompt

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=config,
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Parse content
            content = self._parse_response(response, response_schema)

            # Extract token usage
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count or 0
                completion_tokens = response.usage_metadata.candidates_token_count or 0
                total_tokens = response.usage_metadata.total_token_count or 0

            estimated_cost = calculate_cost(self.model_name, prompt_tokens, completion_tokens)

            logger.debug(
                "Gemini API call: %d tokens (%d in, %d out), %dms, $%.4f",
                total_tokens,
                prompt_tokens,
                completion_tokens,
                elapsed_ms,
                estimated_cost,
            )

            return LLMResponse(
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model_name=self.model_name,
                latency_ms=elapsed_ms,
                estimated_cost_usd=estimated_cost,
            )

        except ValidationError:
            logger.exception("Failed to validate Gemini response structure")
            raise
        except genai_errors.ServerError as e:
            logger.warning("Gemini SDK server error (retryable): %s", e)
            _log_prompt_debug_info(prompt, system_prompt)
            msg = f"Gemini: {e}"
            raise ServerError(msg) from e
        except genai_errors.ClientError as e:
            logger.warning("Gemini SDK client error: %s", e)
            _log_prompt_debug_info(prompt, system_prompt)
            raise _convert_google_exception(e) from e
        except (
            google_exceptions.GoogleAPIError,
            google_exceptions.RetryError,
        ) as e:
            logger.warning("Gemini API error: %s", e)
            _log_prompt_debug_info(prompt, system_prompt)
            raise _convert_google_exception(e) from e
        except (
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.ConnectError,
            ConnectionError,
            OSError,
        ) as e:
            logger.warning(
                "Gemini connection/timeout error (%s): %s",
                type(e).__name__,
                e,
            )
            _log_prompt_debug_info(prompt, system_prompt)
            msg = f"Gemini: connection error - {e}"
            raise ServerError(msg) from e
        except Exception as e:
            converted = _convert_google_exception(e)
            if converted is not e:
                logger.warning("Gemini API error: %s", e)
                _log_prompt_debug_info(prompt, system_prompt)
                raise converted from e
            _log_prompt_debug_info(prompt, system_prompt)
            logger.exception("Gemini API call failed")
            raise

    @staticmethod
    def _parse_response[T: BaseModel](
        response: types.GenerateContentResponse,
        schema: type[T] | None,
    ) -> T | str:
        """Parse Gemini response into structured model or raw text.

        Args:
            response: Raw Gemini API response.
            schema: Pydantic model class for validation, or None for raw text.

        Returns:
            Parsed model instance or raw text string.

        Raises:
            ValueError: If response was blocked by safety filters,
                text is empty, or cannot be parsed.
        """
        try:
            text = response.text
        except ValueError as e:
            if "safety" in str(e).lower():
                msg = f"Gemini response blocked by safety filters: {e}"
                raise ValueError(msg) from e
            raise

        if not text:
            raise ValueError(_PARSING_ERROR_MSG)

        if schema is None:
            return text

        return schema.model_validate_json(text)


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PRICING",
    "GEMINI_PRICING",
    "GeminiProvider",
    "calculate_cost",
]
