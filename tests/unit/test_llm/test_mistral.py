"""Unit tests for MistralProvider."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import httpx
import pytest
from pydantic import BaseModel

if TYPE_CHECKING:
    from unittest.mock import MagicMock

from ai_reviewer.llm.base import LLMResponse
from ai_reviewer.llm.mistral import (
    DEFAULT_MODEL,
    MistralProvider,
    _convert_mistral_exception,
    _match_by_error_message,
)
from ai_reviewer.utils.retry import (
    AuthenticationError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
)


class _TestSchema(BaseModel):
    """Minimal Pydantic model for testing structured output."""

    answer: str
    score: int = 0


def _make_sdk_error(status_code: int, message: str = "error") -> Mock:
    """Create a mock SDKError with given status code.

    Args:
        status_code: HTTP status code for raw_response.
        message: Error message string.

    Returns:
        Mock SDKError with raw_response.status_code set.
    """
    from mistralai.client.errors.sdkerror import SDKError

    err = Mock(spec=SDKError)
    err.raw_response = Mock()
    err.raw_response.status_code = status_code
    err.__str__ = Mock(return_value=message)
    err.__class__ = SDKError
    return err


def _make_chat_response(  # noqa: PLR0913
    text: str | list[str] | None = "ok",
    prompt_tokens: int | None = 100,
    completion_tokens: int | None = 50,
    total_tokens: int | None = 150,
    *,
    empty_choices: bool = False,
    no_message: bool = False,
) -> Mock:
    """Build a mock ChatCompletionResponse.

    Args:
        text: Content text (str, list, or None).
        prompt_tokens: Prompt token count (None to omit usage).
        completion_tokens: Completion token count.
        total_tokens: Total token count.
        empty_choices: If True, set choices to empty list.
        no_message: If True, set message to None.

    Returns:
        Mock ChatCompletionResponse.
    """
    response = Mock()
    if empty_choices:
        response.choices = []
        return response

    choice = Mock()
    if no_message:
        choice.message = None
    else:
        choice.message = Mock()
        choice.message.content = text

    response.choices = [choice]

    if prompt_tokens is not None:
        response.usage = Mock()
        response.usage.prompt_tokens = prompt_tokens
        response.usage.completion_tokens = completion_tokens
        response.usage.total_tokens = total_tokens
    else:
        response.usage = None

    return response


# ---------------------------------------------------------------------------
# MistralProvider init
# ---------------------------------------------------------------------------


class TestMistralProviderInit:
    """Tests for MistralProvider initialization."""

    @patch("ai_reviewer.llm.mistral.Mistral")
    def test_default_model(self, mock_client_cls: MagicMock) -> None:
        """Test provider initializes with default model."""
        provider = MistralProvider(api_key="key")
        assert provider.model_name == DEFAULT_MODEL
        mock_client_cls.assert_called_once_with(
            api_key="key",
            timeout_ms=300_000,
        )

    @patch("ai_reviewer.llm.mistral.Mistral")
    def test_custom_model(self, mock_client_cls: MagicMock) -> None:
        """Test provider initializes with custom model."""
        provider = MistralProvider(api_key="key", model_name="mistral-small-latest")
        assert provider.model_name == "mistral-small-latest"

    @patch("ai_reviewer.llm.mistral.Mistral")
    def test_custom_server_url(self, mock_client_cls: MagicMock) -> None:
        """Test provider passes server_url to Mistral client."""
        MistralProvider(
            api_key="key",
            model_name="codestral-latest",
            server_url="https://codestral.mistral.ai",
        )
        mock_client_cls.assert_called_once_with(
            api_key="key",
            timeout_ms=300_000,
            server_url="https://codestral.mistral.ai",
        )

    @patch("ai_reviewer.llm.mistral.Mistral")
    def test_none_server_url_not_passed(self, mock_client_cls: MagicMock) -> None:
        """Test that server_url=None is not forwarded to client."""
        MistralProvider(api_key="key", server_url=None)
        mock_client_cls.assert_called_once_with(
            api_key="key",
            timeout_ms=300_000,
        )


# ---------------------------------------------------------------------------
# generate() — structured response
# ---------------------------------------------------------------------------


class TestMistralProviderGenerateStructured:
    """Tests for generate() with response_schema."""

    @pytest.fixture
    def provider(self) -> MistralProvider:
        """Create MistralProvider with mocked Mistral client."""
        with patch("ai_reviewer.llm.mistral.Mistral"):
            return MistralProvider(api_key="test-key")

    def test_returns_parsed_model(self, provider: MistralProvider) -> None:
        """Test that generate() returns parsed Pydantic model in content."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "yes", "score": 42}',
        )

        result = provider.generate("test", response_schema=_TestSchema)

        assert isinstance(result, LLMResponse)
        assert isinstance(result.content, _TestSchema)
        assert result.content.answer == "yes"
        assert result.content.score == 42

    def test_token_counting(self, provider: MistralProvider) -> None:
        """Test that token counts are extracted from usage."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
            prompt_tokens=200,
            completion_tokens=80,
            total_tokens=280,
        )

        result = provider.generate("test", response_schema=_TestSchema)

        assert result.prompt_tokens == 200
        assert result.completion_tokens == 80
        assert result.total_tokens == 280
        assert result.model_name == DEFAULT_MODEL

    def test_missing_usage(self, provider: MistralProvider) -> None:
        """Test graceful handling when usage is None."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
            prompt_tokens=None,
        )

        result = provider.generate("test", response_schema=_TestSchema)

        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0

    def test_cost_always_zero(self, provider: MistralProvider) -> None:
        """Test that estimated cost is always 0.0 (no pricing table yet)."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
            prompt_tokens=1_000_000,
            completion_tokens=500_000,
            total_tokens=1_500_000,
        )

        result = provider.generate("test", response_schema=_TestSchema)

        assert result.estimated_cost_usd == 0.0

    def test_empty_choices_raises(self, provider: MistralProvider) -> None:
        """Test that empty choices list raises ValueError."""
        provider._client.chat.complete.return_value = _make_chat_response(empty_choices=True)

        with pytest.raises(ValueError, match="could not be parsed"):
            provider.generate("test", response_schema=_TestSchema)

    def test_none_message_raises(self, provider: MistralProvider) -> None:
        """Test that None message raises ValueError."""
        provider._client.chat.complete.return_value = _make_chat_response(no_message=True)

        with pytest.raises(ValueError, match="could not be parsed"):
            provider.generate("test", response_schema=_TestSchema)

    def test_empty_content_raises(self, provider: MistralProvider) -> None:
        """Test that empty content string raises ValueError."""
        provider._client.chat.complete.return_value = _make_chat_response(text="")

        with pytest.raises(ValueError, match="could not be parsed"):
            provider.generate("test", response_schema=_TestSchema)

    def test_none_content_raises(self, provider: MistralProvider) -> None:
        """Test that None content raises ValueError."""
        provider._client.chat.complete.return_value = _make_chat_response(text=None)

        with pytest.raises(ValueError, match="could not be parsed"):
            provider.generate("test", response_schema=_TestSchema)

    def test_list_content_joined(self, provider: MistralProvider) -> None:
        """Test that list content is joined into a single string."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text=['{"answer":', ' "yes"}'],
        )

        result = provider.generate("test", response_schema=_TestSchema)

        assert isinstance(result.content, _TestSchema)
        assert result.content.answer == "yes"

    def test_json_object_response_format(self, provider: MistralProvider) -> None:
        """Test that response_format is set to json_object for structured output."""
        from mistralai.client.models import ResponseFormat

        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
        )

        provider.generate("test", response_schema=_TestSchema)

        call_kwargs = provider._client.chat.complete.call_args.kwargs
        assert isinstance(call_kwargs["response_format"], ResponseFormat)
        assert call_kwargs["response_format"].type == "json_object"

    def test_system_prompt_prepended(self, provider: MistralProvider) -> None:
        """Test that system_prompt is added as first message."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
        )

        provider.generate(
            "test",
            system_prompt="You are a reviewer",
            response_schema=_TestSchema,
        )

        call_kwargs = provider._client.chat.complete.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "You are a reviewer"}
        assert messages[1] == {"role": "user", "content": "test"}

    def test_no_system_prompt(self, provider: MistralProvider) -> None:
        """Test that messages contain only user when no system_prompt."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
        )

        provider.generate("test", response_schema=_TestSchema)

        call_kwargs = provider._client.chat.complete.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "test"}

    def test_temperature_passed(self, provider: MistralProvider) -> None:
        """Test that temperature is forwarded to the API call."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
        )

        provider.generate("test", response_schema=_TestSchema, temperature=0.7)

        call_kwargs = provider._client.chat.complete.call_args.kwargs
        assert call_kwargs["temperature"] == 0.7

    def test_model_name_passed(self, provider: MistralProvider) -> None:
        """Test that model name is forwarded to the API call."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
        )

        provider.generate("test", response_schema=_TestSchema)

        call_kwargs = provider._client.chat.complete.call_args.kwargs
        assert call_kwargs["model"] == DEFAULT_MODEL

    def test_latency_measured(self, provider: MistralProvider) -> None:
        """Test that latency is captured in milliseconds."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"answer": "ok"}',
        )

        result = provider.generate("test", response_schema=_TestSchema)

        assert result.latency_ms >= 0


# ---------------------------------------------------------------------------
# generate() — raw text response
# ---------------------------------------------------------------------------


class TestMistralProviderGenerateRawText:
    """Tests for generate() without response_schema (raw text)."""

    @pytest.fixture
    def provider(self) -> MistralProvider:
        """Create MistralProvider with mocked Mistral client."""
        with patch("ai_reviewer.llm.mistral.Mistral"):
            return MistralProvider(api_key="test-key")

    def test_returns_raw_text(self, provider: MistralProvider) -> None:
        """Test that generate() returns raw text when no schema is given."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text="Plain text answer",
        )

        result = provider.generate("test")

        assert isinstance(result, LLMResponse)
        assert result.content == "Plain text answer"

    def test_no_response_format_for_raw_text(self, provider: MistralProvider) -> None:
        """Test that response_format is not set for raw text output."""
        provider._client.chat.complete.return_value = _make_chat_response(text="text")

        provider.generate("test")

        call_kwargs = provider._client.chat.complete.call_args.kwargs
        assert "response_format" not in call_kwargs


# ---------------------------------------------------------------------------
# _convert_mistral_exception
# ---------------------------------------------------------------------------


class TestConvertMistralException:
    """Tests for _convert_mistral_exception."""

    def test_401_becomes_auth_error(self) -> None:
        """Test 401 status → AuthenticationError."""
        err = _make_sdk_error(401, "Unauthorized")
        result = _convert_mistral_exception(err)
        assert isinstance(result, AuthenticationError)

    def test_429_with_quota_becomes_quota_exhausted(self) -> None:
        """Test 429 with 'quota' keyword → QuotaExhaustedError."""
        err = _make_sdk_error(429, "Quota limit reached")
        result = _convert_mistral_exception(err)
        assert isinstance(result, QuotaExhaustedError)

    def test_429_with_limit_becomes_quota_exhausted(self) -> None:
        """Test 429 with 'limit' keyword → QuotaExhaustedError."""
        err = _make_sdk_error(429, "Rate limit exceeded")
        result = _convert_mistral_exception(err)
        assert isinstance(result, QuotaExhaustedError)

    def test_429_plain_becomes_rate_limit(self) -> None:
        """Test 429 without quota/limit keywords → RateLimitError."""
        err = _make_sdk_error(429, "Too many requests")
        result = _convert_mistral_exception(err)
        assert isinstance(result, RateLimitError)

    def test_500_becomes_server_error(self) -> None:
        """Test 500 status → ServerError."""
        err = _make_sdk_error(500, "Internal server error")
        result = _convert_mistral_exception(err)
        assert isinstance(result, ServerError)
        assert result.status_code == 500

    def test_502_becomes_server_error(self) -> None:
        """Test 502 status → ServerError."""
        err = _make_sdk_error(502, "Bad gateway")
        result = _convert_mistral_exception(err)
        assert isinstance(result, ServerError)
        assert result.status_code == 502

    def test_503_becomes_server_error(self) -> None:
        """Test 503 status → ServerError."""
        err = _make_sdk_error(503, "Service unavailable")
        result = _convert_mistral_exception(err)
        assert isinstance(result, ServerError)
        assert result.status_code == 503

    def test_no_raw_response_falls_through_to_message_match(self) -> None:
        """Test SDKError without raw_response falls to message matching."""
        from mistralai.client.errors.sdkerror import SDKError

        err = Mock(spec=SDKError)
        # Remove raw_response attribute
        del err.raw_response
        err.__str__ = Mock(return_value="rate limit hit")
        err.__class__ = SDKError
        result = _convert_mistral_exception(err)
        assert isinstance(result, RateLimitError)

    def test_unknown_status_falls_to_message_match(self) -> None:
        """Test unknown status code falls to _match_by_error_message."""
        err = _make_sdk_error(400, "server error occurred")
        result = _convert_mistral_exception(err)
        assert isinstance(result, ServerError)

    def test_unknown_error_returned_as_is(self) -> None:
        """Test unrecognized SDKError is returned via _match_by_error_message."""
        err = _make_sdk_error(400, "bad request with no keywords")
        result = _convert_mistral_exception(err)
        # Original mock is returned since no keyword matched
        assert result is err


# ---------------------------------------------------------------------------
# _match_by_error_message
# ---------------------------------------------------------------------------


class TestMatchByErrorMessage:
    """Tests for _match_by_error_message fallback heuristic."""

    def test_rate_limit_keyword(self) -> None:
        """Test 'rate limit' in message → RateLimitError."""
        result = _match_by_error_message(Exception("rate limit exceeded"))
        assert isinstance(result, RateLimitError)

    def test_429_keyword(self) -> None:
        """Test '429' in message → RateLimitError."""
        result = _match_by_error_message(Exception("HTTP 429"))
        assert isinstance(result, RateLimitError)

    def test_quota_keyword(self) -> None:
        """Test 'quota' in message → QuotaExhaustedError."""
        result = _match_by_error_message(Exception("quota exhausted"))
        assert isinstance(result, QuotaExhaustedError)

    def test_500_keyword(self) -> None:
        """Test '500' in message → ServerError."""
        result = _match_by_error_message(Exception("HTTP 500"))
        assert isinstance(result, ServerError)

    def test_502_keyword(self) -> None:
        """Test '502' in message → ServerError."""
        result = _match_by_error_message(Exception("502 Bad Gateway"))
        assert isinstance(result, ServerError)

    def test_503_keyword(self) -> None:
        """Test '503' in message → ServerError."""
        result = _match_by_error_message(Exception("503 Service Unavailable"))
        assert isinstance(result, ServerError)

    def test_504_keyword(self) -> None:
        """Test '504' in message → ServerError."""
        result = _match_by_error_message(Exception("504 Gateway Timeout"))
        assert isinstance(result, ServerError)

    def test_server_error_keyword(self) -> None:
        """Test 'server error' in message → ServerError."""
        result = _match_by_error_message(Exception("server error occurred"))
        assert isinstance(result, ServerError)

    def test_unauthorized_keyword(self) -> None:
        """Test 'unauthorized' in message → AuthenticationError."""
        result = _match_by_error_message(Exception("unauthorized access"))
        assert isinstance(result, AuthenticationError)

    def test_authentication_keyword(self) -> None:
        """Test 'authentication' in message → AuthenticationError."""
        result = _match_by_error_message(Exception("authentication failed"))
        assert isinstance(result, AuthenticationError)

    def test_no_match_returns_original(self) -> None:
        """Test unrecognized message returns original exception."""
        exc = Exception("something completely different")
        result = _match_by_error_message(exc)
        assert result is exc


# ---------------------------------------------------------------------------
# generate() — error propagation
# ---------------------------------------------------------------------------


class TestMistralProviderErrors:
    """Tests for error handling in generate()."""

    @pytest.fixture
    def provider(self) -> MistralProvider:
        """Create MistralProvider with mocked Mistral client."""
        with patch("ai_reviewer.llm.mistral.Mistral"):
            return MistralProvider(api_key="test-key")

    def test_sdk_error_converted(self, provider: MistralProvider) -> None:
        """Test that SDKError is converted via _convert_mistral_exception."""
        from mistralai.client.errors.sdkerror import SDKError

        raw = httpx.Response(status_code=401, text="Unauthorized")
        err = SDKError("Unauthorized", raw)
        provider._client.chat.complete.side_effect = err

        with pytest.raises(AuthenticationError):
            provider.generate("test", response_schema=_TestSchema)

    def test_auth_error_not_retried(self, provider: MistralProvider) -> None:
        """Test that AuthenticationError is not retried (single attempt)."""
        from mistralai.client.errors.sdkerror import SDKError

        raw = httpx.Response(status_code=401, text="Unauthorized")
        err = SDKError("Unauthorized", raw)
        provider._client.chat.complete.side_effect = err

        with pytest.raises(AuthenticationError):
            provider.generate("test", response_schema=_TestSchema)

        assert provider._client.chat.complete.call_count == 1

    @pytest.mark.slow
    def test_server_error_retried(self, provider: MistralProvider) -> None:
        """Test that ServerError triggers retry (multiple attempts)."""
        from mistralai.client.errors.sdkerror import SDKError

        raw = httpx.Response(status_code=500, text="Internal error")
        err = SDKError("Internal error", raw)
        provider._client.chat.complete.side_effect = err

        with pytest.raises(ServerError):
            provider.generate("test", response_schema=_TestSchema)

        assert provider._client.chat.complete.call_count == 3

    @pytest.mark.slow
    def test_httpx_timeout_becomes_server_error(self, provider: MistralProvider) -> None:
        """Test that httpx.TimeoutException → ServerError (retryable)."""
        provider._client.chat.complete.side_effect = httpx.ReadTimeout(
            "The read operation timed out"
        )

        with pytest.raises(ServerError, match="connection error"):
            provider.generate("test", response_schema=_TestSchema)

    @pytest.mark.slow
    def test_httpx_connect_error_becomes_server_error(self, provider: MistralProvider) -> None:
        """Test that httpx.ConnectError → ServerError (retryable)."""
        provider._client.chat.complete.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ServerError, match="connection error"):
            provider.generate("test", response_schema=_TestSchema)

    @pytest.mark.slow
    def test_connection_error_becomes_server_error(self, provider: MistralProvider) -> None:
        """Test that ConnectionError → ServerError (retryable)."""
        provider._client.chat.complete.side_effect = ConnectionError("Connection reset")

        with pytest.raises(ServerError, match="connection error"):
            provider.generate("test", response_schema=_TestSchema)

    @pytest.mark.slow
    def test_os_error_becomes_server_error(self, provider: MistralProvider) -> None:
        """Test that OSError → ServerError (retryable)."""
        provider._client.chat.complete.side_effect = OSError("Network unreachable")

        with pytest.raises(ServerError, match="connection error"):
            provider.generate("test", response_schema=_TestSchema)

    @pytest.mark.slow
    def test_generic_exception_with_retryable_message(self, provider: MistralProvider) -> None:
        """Test that generic exception with server error keyword is converted."""
        provider._client.chat.complete.side_effect = Exception("server error occurred")

        with pytest.raises(ServerError):
            provider.generate("test", response_schema=_TestSchema)

    def test_non_retryable_exception_propagates(self, provider: MistralProvider) -> None:
        """Test that non-retryable exceptions propagate unchanged."""
        provider._client.chat.complete.side_effect = ValueError("Bad input")

        with pytest.raises(ValueError, match="Bad input"):
            provider.generate("test", response_schema=_TestSchema)

    def test_validation_error_logged(
        self, provider: MistralProvider, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that ValidationError gets a specific log message."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"invalid_field": "oops"}',
        )

        with pytest.raises(Exception):  # noqa: B017, PT011
            provider.generate("test", response_schema=_TestSchema)

        assert "Failed to validate Mistral response structure" in caplog.text

    def test_validation_error_not_retried(self, provider: MistralProvider) -> None:
        """Test that Pydantic ValidationError is not retried."""
        provider._client.chat.complete.return_value = _make_chat_response(
            text='{"wrong": "schema"}',
        )

        with pytest.raises(Exception):  # noqa: B017, PT011
            provider.generate("test", response_schema=_TestSchema)

        assert provider._client.chat.complete.call_count == 1
