"""Unit tests for GeminiProvider."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import httpx
import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock
from google.api_core import exceptions as google_exceptions
from google.genai import types
from pydantic import BaseModel

from ai_reviewer.llm.base import LLMResponse
from ai_reviewer.llm.gemini import (
    DEFAULT_MODEL,
    DEFAULT_PRICING,
    GEMINI_PRICING,
    GeminiProvider,
    _convert_google_exception,
    calculate_cost,
)
from ai_reviewer.utils.retry import (
    AuthenticationError,
    ForbiddenError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
)


class _TestSchema(BaseModel):
    """Minimal Pydantic model for testing structured output."""

    answer: str
    score: int = 0


# ---------------------------------------------------------------------------
# GeminiProvider init
# ---------------------------------------------------------------------------


class TestGeminiProviderInit:
    """Tests for GeminiProvider initialization."""

    @patch("ai_reviewer.llm.gemini.genai.Client")
    def test_default_model(self, mock_client_cls: MagicMock) -> None:
        """Test provider initializes with default model."""
        provider = GeminiProvider(api_key="key")
        assert provider.model_name == DEFAULT_MODEL
        mock_client_cls.assert_called_once_with(
            api_key="key",
            http_options=types.HttpOptions(timeout=300_000),
        )

    @patch("ai_reviewer.llm.gemini.genai.Client")
    def test_custom_model(self, mock_client_cls: MagicMock) -> None:
        """Test provider initializes with custom model."""
        provider = GeminiProvider(api_key="key", model_name="gemini-1.5-pro")
        assert provider.model_name == "gemini-1.5-pro"


# ---------------------------------------------------------------------------
# generate() — structured response
# ---------------------------------------------------------------------------


class TestGeminiProviderGenerateStructured:
    """Tests for generate() with response_schema."""

    @pytest.fixture
    def provider(self) -> GeminiProvider:
        """Create GeminiProvider with mocked google.genai.Client."""
        with patch("ai_reviewer.llm.gemini.genai.Client"):
            return GeminiProvider(api_key="test-key")

    def test_returns_parsed_model(self, provider: GeminiProvider) -> None:
        """Test that generate() returns parsed Pydantic model in content."""
        mock_response = Mock()
        mock_response.text = '{"answer": "yes", "score": 42}'
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.total_token_count = 150
        provider._client.models.generate_content.return_value = mock_response

        result = provider.generate("test", response_schema=_TestSchema)

        assert isinstance(result, LLMResponse)
        assert isinstance(result.content, _TestSchema)
        assert result.content.answer == "yes"
        assert result.content.score == 42

    def test_token_counting(self, provider: GeminiProvider) -> None:
        """Test that token counts are extracted from usage metadata."""
        mock_response = Mock()
        mock_response.text = '{"answer": "ok"}'
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 200
        mock_response.usage_metadata.candidates_token_count = 80
        mock_response.usage_metadata.total_token_count = 280
        provider._client.models.generate_content.return_value = mock_response

        result = provider.generate("test", response_schema=_TestSchema)

        assert result.prompt_tokens == 200
        assert result.completion_tokens == 80
        assert result.total_tokens == 280
        assert result.model_name == DEFAULT_MODEL

    def test_missing_usage_metadata(self, provider: GeminiProvider) -> None:
        """Test graceful handling when usage_metadata is None."""
        mock_response = Mock()
        mock_response.text = '{"answer": "ok"}'
        mock_response.usage_metadata = None
        provider._client.models.generate_content.return_value = mock_response

        result = provider.generate("test", response_schema=_TestSchema)

        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0
        assert result.estimated_cost_usd == 0.0

    def test_partial_usage_metadata(self, provider: GeminiProvider) -> None:
        """Test handling when some usage_metadata fields are None."""
        mock_response = Mock()
        mock_response.text = '{"answer": "ok"}'
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = None
        mock_response.usage_metadata.total_token_count = 100
        provider._client.models.generate_content.return_value = mock_response

        result = provider.generate("test", response_schema=_TestSchema)

        assert result.prompt_tokens == 100
        assert result.completion_tokens == 0
        assert result.total_tokens == 100

    def test_cost_estimation(self, provider: GeminiProvider) -> None:
        """Test that estimated cost is calculated correctly."""
        mock_response = Mock()
        mock_response.text = '{"answer": "ok"}'
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 1_000_000
        mock_response.usage_metadata.candidates_token_count = 500_000
        mock_response.usage_metadata.total_token_count = 1_500_000
        provider._client.models.generate_content.return_value = mock_response

        result = provider.generate("test", response_schema=_TestSchema)

        expected = calculate_cost(DEFAULT_MODEL, 1_000_000, 500_000)
        assert result.estimated_cost_usd == pytest.approx(expected)

    def test_empty_response_text_raises(self, provider: GeminiProvider) -> None:
        """Test that empty response text raises ValueError."""
        mock_response = Mock()
        mock_response.text = ""
        provider._client.models.generate_content.return_value = mock_response

        with pytest.raises(ValueError, match="could not be parsed"):
            provider.generate("test", response_schema=_TestSchema)

    def test_none_response_text_raises(self, provider: GeminiProvider) -> None:
        """Test that None response text raises ValueError."""
        mock_response = Mock()
        mock_response.text = None
        provider._client.models.generate_content.return_value = mock_response

        with pytest.raises(ValueError, match="could not be parsed"):
            provider.generate("test", response_schema=_TestSchema)

    def test_safety_blocked_response_raises(self, provider: GeminiProvider) -> None:
        """Test that safety-blocked response gives a specific error message."""
        mock_response = Mock()
        # Simulate SDK behavior: accessing .text raises ValueError with 'safety'
        type(mock_response).text = property(
            fget=Mock(side_effect=ValueError("response was blocked due to safety settings"))
        )
        provider._client.models.generate_content.return_value = mock_response

        with pytest.raises(ValueError, match="blocked by safety filters"):
            provider.generate("test", response_schema=_TestSchema)

    def test_system_prompt_passed_to_config(self, provider: GeminiProvider) -> None:
        """Test that system_prompt is set in GenerateContentConfig."""
        mock_response = Mock()
        mock_response.text = '{"answer": "ok"}'
        mock_response.usage_metadata = None
        provider._client.models.generate_content.return_value = mock_response

        provider.generate(
            "test",
            system_prompt="You are a reviewer",
            response_schema=_TestSchema,
        )

        call_kwargs = provider._client.models.generate_content.call_args.kwargs
        assert call_kwargs["config"].system_instruction == "You are a reviewer"
        assert call_kwargs["config"].response_mime_type == "application/json"
        assert call_kwargs["config"].response_schema == _TestSchema

    def test_contents_passed_as_list(self, provider: GeminiProvider) -> None:
        """Test that contents is passed as [prompt] (list)."""
        mock_response = Mock()
        mock_response.text = '{"answer": "ok"}'
        mock_response.usage_metadata = None
        provider._client.models.generate_content.return_value = mock_response

        provider.generate("my prompt", response_schema=_TestSchema)

        call_kwargs = provider._client.models.generate_content.call_args.kwargs
        assert call_kwargs["contents"] == ["my prompt"]


# ---------------------------------------------------------------------------
# generate() — raw text response
# ---------------------------------------------------------------------------


class TestGeminiProviderGenerateRawText:
    """Tests for generate() without response_schema (raw text)."""

    @pytest.fixture
    def provider(self) -> GeminiProvider:
        """Create GeminiProvider with mocked google.genai.Client."""
        with patch("ai_reviewer.llm.gemini.genai.Client"):
            return GeminiProvider(api_key="test-key")

    def test_returns_raw_text(self, provider: GeminiProvider) -> None:
        """Test that generate() returns raw text when no schema is given."""
        mock_response = Mock()
        mock_response.text = "Plain text answer"
        mock_response.usage_metadata = None
        provider._client.models.generate_content.return_value = mock_response

        result = provider.generate("test")

        assert isinstance(result, LLMResponse)
        assert result.content == "Plain text answer"

    def test_no_json_mime_type(self, provider: GeminiProvider) -> None:
        """Test that response_mime_type is not set for raw text."""
        mock_response = Mock()
        mock_response.text = "text"
        mock_response.usage_metadata = None
        provider._client.models.generate_content.return_value = mock_response

        provider.generate("test")

        call_kwargs = provider._client.models.generate_content.call_args.kwargs
        assert call_kwargs["config"].response_mime_type is None
        assert call_kwargs["config"].response_schema is None


# ---------------------------------------------------------------------------
# Error conversion
# ---------------------------------------------------------------------------


class TestConvertGoogleException:
    """Tests for _convert_google_exception."""

    def test_resource_exhausted_becomes_rate_limit(self) -> None:
        """Test ResourceExhausted → RateLimitError (per-minute quota)."""
        exc = google_exceptions.ResourceExhausted("Quota exceeded")
        result = _convert_google_exception(exc)
        assert isinstance(result, RateLimitError)

    def test_daily_quota_becomes_quota_exhausted(self) -> None:
        """Test ResourceExhausted with PerDay quotaId → QuotaExhaustedError."""
        msg = (
            "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, "
            "'message': 'You exceeded your current quota', "
            "'details': [{'@type': 'QuotaFailure', "
            "'violations': [{'quotaMetric': 'generate_content_free_tier_requests', "
            "'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', "
            "'quotaValue': '20'}]}]}}"
        )
        exc = google_exceptions.ResourceExhausted(msg)
        result = _convert_google_exception(exc)
        assert isinstance(result, QuotaExhaustedError)
        assert result.quota_id == "GenerateRequestsPerDayPerProjectPerModel-FreeTier"

    def test_free_tier_quota_becomes_quota_exhausted(self) -> None:
        """Test ResourceExhausted with FreeTier quotaId → QuotaExhaustedError."""
        msg = "'quotaId': 'SomeFreeTierQuota'"
        exc = google_exceptions.ResourceExhausted(msg)
        result = _convert_google_exception(exc)
        assert isinstance(result, QuotaExhaustedError)

    def test_unauthenticated_becomes_auth_error(self) -> None:
        """Test Unauthenticated → AuthenticationError."""
        exc = google_exceptions.Unauthenticated("Bad key")
        result = _convert_google_exception(exc)
        assert isinstance(result, AuthenticationError)

    def test_permission_denied_becomes_forbidden(self) -> None:
        """Test PermissionDenied → ForbiddenError."""
        exc = google_exceptions.PermissionDenied("No access")
        result = _convert_google_exception(exc)
        assert isinstance(result, ForbiddenError)

    def test_internal_server_error_becomes_server_error(self) -> None:
        """Test InternalServerError → ServerError."""
        exc = google_exceptions.InternalServerError("Oops")
        result = _convert_google_exception(exc)
        assert isinstance(result, ServerError)

    def test_service_unavailable_becomes_server_error(self) -> None:
        """Test ServiceUnavailable → ServerError."""
        exc = google_exceptions.ServiceUnavailable("Down")
        result = _convert_google_exception(exc)
        assert isinstance(result, ServerError)

    def test_deadline_exceeded_becomes_server_error(self) -> None:
        """Test DeadlineExceeded → ServerError."""
        exc = google_exceptions.DeadlineExceeded("Timeout")
        result = _convert_google_exception(exc)
        assert isinstance(result, ServerError)

    def test_rate_limit_in_message_becomes_rate_limit(self) -> None:
        """Test fallback: 'rate limit' in error message → RateLimitError."""
        exc = Exception("Rate limit exceeded for project")
        result = _convert_google_exception(exc)
        assert isinstance(result, RateLimitError)

    def test_429_in_message_becomes_rate_limit(self) -> None:
        """Test fallback: '429' in error message → RateLimitError."""
        exc = Exception("HTTP 429 Too Many Requests")
        result = _convert_google_exception(exc)
        assert isinstance(result, RateLimitError)

    def test_429_daily_in_message_becomes_quota_exhausted(self) -> None:
        """Test fallback: '429' with PerDay quotaId → QuotaExhaustedError."""
        exc = Exception(
            "429 quota exceeded, 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'"
        )
        result = _convert_google_exception(exc)
        assert isinstance(result, QuotaExhaustedError)

    def test_500_in_message_becomes_server_error(self) -> None:
        """Test fallback: '500' in error message → ServerError."""
        exc = Exception("HTTP 500 Internal Server Error")
        result = _convert_google_exception(exc)
        assert isinstance(result, ServerError)

    def test_504_in_message_becomes_server_error(self) -> None:
        """Test fallback: '504' in error message → ServerError."""
        exc = Exception("504 DEADLINE_EXCEEDED")
        result = _convert_google_exception(exc)
        assert isinstance(result, ServerError)

    def test_deadline_in_message_becomes_server_error(self) -> None:
        """Test fallback: 'deadline' in error message → ServerError."""
        exc = Exception("Deadline expired before operation could complete")
        result = _convert_google_exception(exc)
        assert isinstance(result, ServerError)

    def test_unknown_exception_returned_as_is(self) -> None:
        """Test that unrecognized exceptions are returned unchanged."""
        exc = ValueError("Something else")
        result = _convert_google_exception(exc)
        assert result is exc

    def test_elif_prevents_overwrite(self) -> None:
        """Test that isinstance match is not overwritten by string fallback.

        ResourceExhausted containing '500' in its message should remain
        RateLimitError, not be overwritten to ServerError.
        """
        exc = google_exceptions.ResourceExhausted("Quota 500 requests/min exceeded")
        result = _convert_google_exception(exc)
        assert isinstance(result, RateLimitError)


# ---------------------------------------------------------------------------
# generate() — error propagation
# ---------------------------------------------------------------------------


class TestGeminiProviderErrors:
    """Tests for error handling in generate()."""

    @pytest.fixture
    def provider(self) -> GeminiProvider:
        """Create GeminiProvider with mocked google.genai.Client."""
        with patch("ai_reviewer.llm.gemini.genai.Client"):
            return GeminiProvider(api_key="test-key")

    @pytest.mark.slow
    def test_google_api_error_converted(self, provider: GeminiProvider) -> None:
        """Test that GoogleAPIError is converted via _convert_google_exception."""
        provider._client.models.generate_content.side_effect = google_exceptions.ResourceExhausted(
            "Quota exceeded"
        )
        with pytest.raises(RateLimitError):
            provider.generate("test", response_schema=_TestSchema)

    def test_auth_error_not_retried(self, provider: GeminiProvider) -> None:
        """Test that AuthenticationError propagates (not retried)."""
        provider._client.models.generate_content.side_effect = google_exceptions.Unauthenticated(
            "Invalid key"
        )
        with pytest.raises(AuthenticationError):
            provider.generate("test", response_schema=_TestSchema)

    @pytest.mark.slow
    def test_generic_exception_with_retryable_message(self, provider: GeminiProvider) -> None:
        """Test that generic exception with rate limit message is converted."""
        provider._client.models.generate_content.side_effect = Exception(
            "Rate limit exceeded for project"
        )
        with pytest.raises(RateLimitError):
            provider.generate("test", response_schema=_TestSchema)

    @pytest.mark.slow
    def test_genai_server_error_becomes_retryable(self, provider: GeminiProvider) -> None:
        """Test that google.genai.errors.ServerError → our ServerError (retryable).

        This covers 504 DEADLINE_EXCEEDED and other server-side errors from
        the genai SDK (distinct from google.api_core.exceptions).
        """
        from google.genai.errors import ServerError as GenaiServerError

        provider._client.models.generate_content.side_effect = GenaiServerError(
            504,
            {"error": {"message": "Deadline expired before operation could complete"}},
        )
        with pytest.raises(ServerError, match="Gemini"):
            provider.generate("test", response_schema=_TestSchema)

    @pytest.mark.slow
    def test_genai_client_error_converted(self, provider: GeminiProvider) -> None:
        """Test that google.genai.errors.ClientError is converted via _convert_google_exception."""
        from google.genai.errors import ClientError as GenaiClientError

        provider._client.models.generate_content.side_effect = GenaiClientError(
            429,
            {"error": {"message": "Rate limit exceeded"}},
        )
        with pytest.raises(RateLimitError):
            provider.generate("test", response_schema=_TestSchema)

    def test_daily_quota_not_retried(self, provider: GeminiProvider) -> None:
        """Test that daily quota 429 raises QuotaExhaustedError without retry."""
        from google.genai.errors import ClientError as GenaiClientError

        msg = (
            "429 RESOURCE_EXHAUSTED. 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'"
        )
        provider._client.models.generate_content.side_effect = GenaiClientError(
            429,
            {"error": {"message": msg}},
        )
        with pytest.raises(QuotaExhaustedError):
            provider.generate("test", response_schema=_TestSchema)
        # QuotaExhaustedError is not RetryableError → only 1 attempt
        assert provider._client.models.generate_content.call_count == 1

    @pytest.mark.slow
    def test_httpx_timeout_becomes_server_error(self, provider: GeminiProvider) -> None:
        """Test that httpx.ReadTimeout → ServerError (retryable)."""
        provider._client.models.generate_content.side_effect = httpx.ReadTimeout(
            "The read operation timed out"
        )
        with pytest.raises(ServerError, match="connection error"):
            provider.generate("test", response_schema=_TestSchema)

    def test_non_retryable_exception_propagates(self, provider: GeminiProvider) -> None:
        """Test that non-retryable exceptions propagate unchanged."""
        provider._client.models.generate_content.side_effect = ValueError("Bad input")
        with pytest.raises(ValueError, match="Bad input"):
            provider.generate("test", response_schema=_TestSchema)

    def test_validation_error_logged_specifically(
        self, provider: GeminiProvider, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that ValidationError gets a specific log message, not generic."""
        mock_response = Mock()
        mock_response.text = '{"invalid_field": "oops"}'
        mock_response.usage_metadata = None
        provider._client.models.generate_content.return_value = mock_response

        with pytest.raises(Exception):  # noqa: B017, PT011
            provider.generate("test", response_schema=_TestSchema)

        assert "Failed to validate Gemini response structure" in caplog.text


# ---------------------------------------------------------------------------
# calculate_cost
# ---------------------------------------------------------------------------


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_known_model(self) -> None:
        """Test cost for a known model."""
        cost = calculate_cost("gemini-2.5-flash", 1_000_000, 500_000)
        expected = 0.075 + (0.30 * 0.5)
        assert cost == pytest.approx(expected)

    def test_unknown_model_uses_default(self) -> None:
        """Test that unknown model uses DEFAULT_PRICING."""
        cost = calculate_cost("unknown-model", 1_000_000, 500_000)
        expected = DEFAULT_PRICING["input"] + (DEFAULT_PRICING["output"] * 0.5)
        assert cost == pytest.approx(expected)

    def test_zero_tokens(self) -> None:
        """Test cost with zero tokens."""
        cost = calculate_cost("gemini-2.5-flash", 0, 0)
        assert cost == 0.0

    def test_pricing_table_has_expected_models(self) -> None:
        """Test that GEMINI_PRICING contains expected models."""
        expected = [
            "gemini-3.1-flash-preview",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        for model in expected:
            assert model in GEMINI_PRICING
            assert "input" in GEMINI_PRICING[model]
            assert "output" in GEMINI_PRICING[model]
