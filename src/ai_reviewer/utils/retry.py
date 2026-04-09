"""Retry utilities for API calls.

This module provides retry decorators and custom exceptions for handling
transient API errors with exponential backoff.

Usage:
    from ai_reviewer.utils.retry import with_retry, RateLimitError

    @with_retry
    def call_api():
        ...
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Retry configuration
MAX_ATTEMPTS = 3
MIN_WAIT_SECONDS = 4
MAX_WAIT_SECONDS = 60

# =============================================================================
# Custom Exceptions
# =============================================================================


class RetryableError(Exception):
    """Base class for errors that should trigger retry."""


class RateLimitError(RetryableError):
    """API rate limit exceeded (HTTP 429).

    This error triggers retry with exponential backoff.
    """

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        """Initialize RateLimitError.

        Args:
            message: Error message.
            retry_after: Suggested retry delay in seconds (from Retry-After header).
        """
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(RetryableError):
    """Server-side error (HTTP 5xx).

    This error triggers retry with exponential backoff.
    """

    def __init__(
        self,
        message: str = "Server error",
        status_code: int | None = None,
    ) -> None:
        """Initialize ServerError.

        Args:
            message: Error message.
            status_code: HTTP status code (500, 502, 503, etc.).
        """
        super().__init__(message)
        self.status_code = status_code


class QuotaExhaustedError(Exception):
    """Daily or free-tier quota exhausted (HTTP 429 with PerDay/FreeTier quotaId).

    Unlike ``RateLimitError``, this is NOT retryable because the quota
    will not reset within a reasonable retry window.  The caller should
    fall back to another model or abort immediately.
    """

    def __init__(
        self,
        message: str = "API daily quota exhausted",
        quota_id: str | None = None,
    ) -> None:
        """Initialize QuotaExhaustedError.

        Args:
            message: Error message.
            quota_id: The Gemini quotaId that was exceeded.
        """
        super().__init__(message)
        self.quota_id = quota_id


class AllModelsFailedError(Exception):
    """All configured Gemini models failed (primary + fallback chain).

    Wraps the list of per-model failures so the caller can determine
    the dominant error category (quota vs server vs rate-limit).

    Args:
        message: Human-readable summary.
        is_quota: True when **all** failures are QuotaExhaustedError.
    """

    def __init__(self, message: str, *, is_quota: bool = False) -> None:
        """Initialize AllModelsFailedError."""
        super().__init__(message)
        self.is_quota = is_quota


class APIClientError(Exception):
    """Base class for client errors that should NOT trigger retry (Fail Fast)."""


class AuthenticationError(APIClientError):
    """Authentication failed (HTTP 401).

    Invalid or missing API token.
    """

    def __init__(self, message: str = "Authentication failed: invalid or missing token") -> None:
        """Initialize AuthenticationError."""
        super().__init__(message)


class ForbiddenError(APIClientError):
    """Access forbidden (HTTP 403).

    Token valid but lacks required permissions.
    """

    def __init__(self, message: str = "Access forbidden: insufficient permissions") -> None:
        """Initialize ForbiddenError."""
        super().__init__(message)


class NotFoundError(APIClientError):
    """Resource not found (HTTP 404).

    Repository, PR, or other resource doesn't exist.
    """

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize NotFoundError."""
        super().__init__(message)


class ValidationError(APIClientError):
    """Validation error (HTTP 422).

    Request was well-formed but could not be processed.
    For example, inline comment on a line not in the diff.
    """

    def __init__(self, message: str = "Validation failed: unprocessable entity") -> None:
        """Initialize ValidationError."""
        super().__init__(message)


class APIError(Exception):
    """Generic API error with details.

    Used when retry is exhausted or for non-categorized errors.
    """

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        operation: str | None = None,
        original_error: BaseException | None = None,
    ) -> None:
        """Initialize APIError.

        Args:
            message: Error description.
            provider: API provider (github, gitlab, gemini).
            operation: Operation that failed (get_pr, post_comment, etc.).
            original_error: The underlying exception.
        """
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.original_error = original_error

    def format_for_comment(self) -> str:
        """Format error for posting as PR comment.

        Returns:
            Markdown-formatted error message.
        """
        from ai_reviewer.core.config import BOT_NAME  # noqa: PLC0415

        parts = [f"## :x: {BOT_NAME}: Review Failed", ""]
        parts.append(f"**Error:** {self}")

        if self.provider:
            parts.append(f"**Provider:** {self.provider}")
        if self.operation:
            parts.append(f"**Operation:** {self.operation}")

        parts.append("")
        parts.append("Please check the CI logs for more details.")

        return "\n".join(parts)


# =============================================================================
# Retry Callbacks
# =============================================================================


def _log_retry_attempt(retry_state: RetryCallState) -> None:  # type: ignore[name-defined]  # noqa: F821
    """Log retry attempt with details.

    Args:
        retry_state: Tenacity retry state object.
    """
    attempt = retry_state.attempt_number
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    error_type = type(exception).__name__ if exception else "Unknown"

    # Calculate wait time for next attempt
    wait_time_ms = 0
    if retry_state.next_action:
        wait_time_ms = int(retry_state.next_action.sleep * 1000)

    logger.warning(
        "API call failed, retrying... | attempt=%d/%d | error_type=%s | retry_in_ms=%d | error=%s",
        attempt,
        MAX_ATTEMPTS,
        error_type,
        wait_time_ms,
        str(exception)[:100] if exception else "N/A",
    )


# =============================================================================
# Retry Decorators
# =============================================================================

# Base retry configuration for API calls
_retry_config = retry(
    retry=retry_if_exception_type(RetryableError),
    wait=wait_exponential(multiplier=1, min=MIN_WAIT_SECONDS, max=MAX_WAIT_SECONDS),
    stop=stop_after_attempt(MAX_ATTEMPTS),
    before_sleep=_log_retry_attempt,
    reraise=True,
)


def with_retry[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that adds retry logic to a function.

    Retries on RetryableError (RateLimitError, ServerError) with
    exponential backoff. Does NOT retry on client errors (4xx).

    Configuration:
        - Max attempts: 3
        - Wait: exponential backoff (4s to 60s)
        - Retryable: RateLimitError, ServerError

    Example:
        @with_retry
        def call_api():
            response = requests.get(url)
            if response.status_code == 429:
                raise RateLimitError()
            return response.json()

    Args:
        func: Function to wrap with retry logic.

    Returns:
        Wrapped function with retry behavior.
    """
    return _retry_config(func)


def with_retry_and_context[**P, R](
    provider: str,
    operation: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator factory that adds retry logic with error context.

    Similar to @with_retry but wraps RetryError in APIError with context
    for better error reporting.

    Args:
        provider: API provider name (github, gitlab, gemini).
        operation: Operation name for error reporting.

    Returns:
        Decorator function.

    Example:
        @with_retry_and_context("github", "get_pull_request")
        def get_pr(pr_id: int):
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return _retry_config(func)(*args, **kwargs)
            except RetryError as e:
                # Extract the last exception from retry attempts
                last_exception = e.last_attempt.exception() if e.last_attempt else None
                raise APIError(
                    message=f"API call failed after {MAX_ATTEMPTS} attempts",
                    provider=provider,
                    operation=operation,
                    original_error=last_exception,
                ) from e

        return wrapper

    return decorator


# =============================================================================
# HTTP Status Code Helpers
# =============================================================================

HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500


def raise_for_status(status_code: int, message: str = "") -> None:
    """Raise appropriate exception based on HTTP status code.

    Args:
        status_code: HTTP response status code.
        message: Optional error message.

    Raises:
        AuthenticationError: For 401 status.
        ForbiddenError: For 403 status (non-rate-limit).
        NotFoundError: For 404 status.
        ValidationError: For 422 status.
        RateLimitError: For 429 status.
        ServerError: For 5xx status codes.
    """
    if status_code == HTTP_UNAUTHORIZED:
        raise AuthenticationError(message or "Authentication failed: invalid or missing token")

    if status_code == HTTP_FORBIDDEN:
        # Note: Some APIs return 403 for rate limit, caller should check
        raise ForbiddenError(message or "Access forbidden: insufficient permissions")

    if status_code == HTTP_NOT_FOUND:
        raise NotFoundError(message or "Resource not found")

    if status_code == HTTP_UNPROCESSABLE_ENTITY:
        raise ValidationError(message or "Validation failed: unprocessable entity")

    if status_code == HTTP_TOO_MANY_REQUESTS:
        raise RateLimitError(message or "API rate limit exceeded")

    if status_code >= HTTP_INTERNAL_SERVER_ERROR:
        raise ServerError(message or f"Server error: {status_code}", status_code=status_code)


def is_retryable_status(status_code: int) -> bool:
    """Check if HTTP status code should trigger retry.

    Args:
        status_code: HTTP response status code.

    Returns:
        True if the error is transient and should be retried.
    """
    return status_code == HTTP_TOO_MANY_REQUESTS or status_code >= HTTP_INTERNAL_SERVER_ERROR
