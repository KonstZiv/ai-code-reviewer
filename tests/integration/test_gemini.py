"""Integration tests for Gemini integration layer (backward compatibility)."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock
from pydantic import SecretStr

from ai_reviewer.core.config import Settings
from ai_reviewer.core.models import (
    CodeIssue,
    IssueCategory,
    IssueSeverity,
    MergeRequest,
    ReviewContext,
    ReviewResult,
    TaskAlignmentStatus,
)
from ai_reviewer.integrations.gemini import (
    DEFAULT_MODEL,
    DEFAULT_PRICING,
    GEMINI_PRICING,
    GeminiClient,
    analyze_code_changes,
    calculate_cost,
)
from ai_reviewer.utils.retry import (
    AllModelsFailedError,
    AuthenticationError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
)


class TestGeminiClientDeprecation:
    """Tests for deprecated GeminiClient wrapper."""

    @patch("ai_reviewer.llm.gemini.genai.Client")
    def test_deprecation_warning(self, mock_client_cls: MagicMock) -> None:
        """Test that GeminiClient emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            GeminiClient(SecretStr("test-key"))
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "GeminiClient is deprecated" in str(w[0].message)
            assert "GeminiProvider" in str(w[0].message)

    @patch("ai_reviewer.llm.gemini.genai.Client")
    def test_generate_review_delegates_to_provider(self, mock_client_cls: MagicMock) -> None:
        """Test that generate_review delegates to GeminiProvider."""
        # Setup mock response
        mock_response = Mock()
        expected_result = ReviewResult(
            issues=(
                CodeIssue(
                    category=IssueCategory.SECURITY,
                    severity=IssueSeverity.CRITICAL,
                    title="SQL Injection",
                    description="Unsafe query",
                ),
            ),
            task_alignment=TaskAlignmentStatus.ALIGNED,
            summary="Code looks good but has one issue.",
        )
        mock_response.text = expected_result.model_dump_json()
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 1000
        mock_response.usage_metadata.candidates_token_count = 500
        mock_response.usage_metadata.total_token_count = 1500

        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            client = GeminiClient(SecretStr("test-key"))

        result = client.generate_review("Test prompt")

        assert isinstance(result, ReviewResult)
        assert len(result.issues) == 1
        assert result.issues[0].title == "SQL Injection"
        assert result.metrics is not None
        assert result.metrics.model_name == DEFAULT_MODEL
        assert result.metrics.prompt_tokens == 1000
        assert result.metrics.completion_tokens == 500

    @patch("ai_reviewer.llm.gemini.genai.Client")
    def test_generate_review_handles_missing_metadata(self, mock_client_cls: MagicMock) -> None:
        """Test that generate_review handles missing usage_metadata."""
        mock_response = Mock()
        mock_response.text = ReviewResult(summary="LGTM").model_dump_json()
        mock_response.usage_metadata = None
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            client = GeminiClient(SecretStr("test-key"))

        result = client.generate_review("Test prompt")

        assert result.metrics is not None
        assert result.metrics.prompt_tokens == 0
        assert result.metrics.completion_tokens == 0
        assert result.metrics.estimated_cost_usd == 0.0


class TestAnalyzeCodeChanges:
    """Tests for analyze_code_changes orchestration function."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        """Create mock settings."""
        settings = Mock(spec=Settings)
        settings.google_api_key = SecretStr("test-key")
        settings.google_api_keys = ["test-key"]
        settings.gemini_model = "gemini-pro"
        settings.gemini_model_fallback = "gemini-2.5-flash"
        settings.fallback_models = ["gemini-2.5-flash"]
        settings.review_max_files = 5
        settings.review_max_diff_lines = 10
        settings.review_split_threshold = 30_000
        return settings

    @pytest.fixture
    def mock_context(self) -> ReviewContext:
        """Create mock review context."""
        mr = Mock(spec=MergeRequest)
        mr.number = 123
        mr.title = "Test PR"
        mr.description = "Desc"
        mr.changes = []

        context = Mock(spec=ReviewContext)
        context.mr = mr
        context.tasks = ()
        return context

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_analyze_flow(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test the full analysis flow delegates to RotatingGeminiProvider."""
        mock_build_prompt.return_value = "Constructed Prompt"

        expected_result = ReviewResult(summary="LGTM")
        mock_response = Mock()
        mock_response.content = expected_result
        mock_response.model_name = "gemini-pro"
        mock_response.prompt_tokens = 100
        mock_response.completion_tokens = 50
        mock_response.total_tokens = 150
        mock_response.latency_ms = 42
        mock_response.estimated_cost_usd = 0.001

        mock_provider_cls.return_value.generate.return_value = mock_response

        result = analyze_code_changes(mock_context, mock_settings)

        assert isinstance(result, ReviewResult)
        assert result.summary == "LGTM"
        assert result.metrics is not None
        assert result.metrics.model_name == "gemini-pro"
        assert result.metrics.prompt_tokens == 100

        mock_build_prompt.assert_called_once_with(mock_context, mock_settings)

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_fallback_on_server_error(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test that ServerError on primary triggers fallback model."""
        mock_build_prompt.return_value = "prompt"

        primary = Mock()
        fallback = Mock()
        mock_provider_cls.side_effect = [primary, fallback]

        primary.generate.side_effect = ServerError("503 overloaded")

        expected = ReviewResult(summary="Fallback OK")
        mock_resp = Mock()
        mock_resp.content = expected
        mock_resp.model_name = "gemini-2.5-flash"
        mock_resp.prompt_tokens = 80
        mock_resp.completion_tokens = 40
        mock_resp.total_tokens = 120
        mock_resp.latency_ms = 100
        mock_resp.estimated_cost_usd = 0.001
        fallback.generate.return_value = mock_resp

        result = analyze_code_changes(mock_context, mock_settings)

        assert result.summary == "Fallback OK"
        assert result.metrics is not None
        assert result.metrics.model_name == "gemini-2.5-flash"
        assert result.metrics.fallback_reason is not None
        assert "ServerError" in result.metrics.fallback_reason
        assert mock_provider_cls.call_count == 2

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_fallback_on_rate_limit(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test that RateLimitError on primary triggers fallback model."""
        mock_build_prompt.return_value = "prompt"

        primary = Mock()
        fallback = Mock()
        mock_provider_cls.side_effect = [primary, fallback]

        primary.generate.side_effect = RateLimitError("429 quota")

        expected = ReviewResult(summary="OK")
        mock_resp = Mock()
        mock_resp.content = expected
        mock_resp.model_name = "gemini-2.5-flash"
        mock_resp.prompt_tokens = 0
        mock_resp.completion_tokens = 0
        mock_resp.total_tokens = 0
        mock_resp.latency_ms = 0
        mock_resp.estimated_cost_usd = 0.0
        fallback.generate.return_value = mock_resp

        result = analyze_code_changes(mock_context, mock_settings)

        assert result.metrics is not None
        assert "RateLimitError" in result.metrics.fallback_reason  # type: ignore[operator]

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_no_fallback_on_auth_error(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test that AuthenticationError is NOT caught for fallback."""
        mock_build_prompt.return_value = "prompt"
        mock_provider_cls.return_value.generate.side_effect = AuthenticationError("Invalid API key")

        with pytest.raises(AuthenticationError):
            analyze_code_changes(mock_context, mock_settings)

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_no_fallback_when_disabled(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test that ServerError propagates when fallback is disabled."""
        mock_build_prompt.return_value = "prompt"
        mock_settings.gemini_model_fallback = None
        mock_settings.fallback_models = []
        mock_provider_cls.return_value.generate.side_effect = ServerError("503")

        with pytest.raises(ServerError):
            analyze_code_changes(mock_context, mock_settings)

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_primary_success_no_fallback_reason(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test that successful primary has no fallback_reason in metrics."""
        mock_build_prompt.return_value = "prompt"

        expected = ReviewResult(summary="OK")
        mock_resp = Mock()
        mock_resp.content = expected
        mock_resp.model_name = "gemini-pro"
        mock_resp.prompt_tokens = 0
        mock_resp.completion_tokens = 0
        mock_resp.total_tokens = 0
        mock_resp.latency_ms = 0
        mock_resp.estimated_cost_usd = 0.0
        mock_provider_cls.return_value.generate.return_value = mock_resp

        result = analyze_code_changes(mock_context, mock_settings)

        assert result.metrics is not None
        assert result.metrics.fallback_reason is None

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_all_models_exhausted_raises_all_models_failed(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test AllModelsFailedError with is_quota=True when all models hit quota."""
        mock_build_prompt.return_value = "prompt"

        primary = Mock()
        fallback = Mock()
        mock_provider_cls.side_effect = [primary, fallback]

        primary.generate.side_effect = QuotaExhaustedError("primary quota exceeded")
        fallback.generate.side_effect = QuotaExhaustedError("fallback quota exceeded")

        with pytest.raises(AllModelsFailedError, match="All 2 model") as exc_info:
            analyze_code_changes(mock_context, mock_settings)
        assert exc_info.value.is_quota is True

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_all_models_exhausted_server_error_not_quota(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test AllModelsFailedError with is_quota=False on mixed errors."""
        mock_build_prompt.return_value = "prompt"

        primary = Mock()
        fallback = Mock()
        mock_provider_cls.side_effect = [primary, fallback]

        primary.generate.side_effect = ServerError("503 overloaded")
        fallback.generate.side_effect = ServerError("503 overloaded")

        with pytest.raises(
            AllModelsFailedError, match=r"gemini-pro.*gemini-2\.5-flash"
        ) as exc_info:
            analyze_code_changes(mock_context, mock_settings)
        assert exc_info.value.is_quota is False

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_all_models_exhausted_message_contains_model_names(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test that the error message names both primary and fallback models."""
        mock_build_prompt.return_value = "prompt"

        primary = Mock()
        fallback = Mock()
        mock_provider_cls.side_effect = [primary, fallback]

        primary.generate.side_effect = QuotaExhaustedError("exhausted")
        fallback.generate.side_effect = ServerError("503 overloaded")

        with pytest.raises(AllModelsFailedError, match=r"gemini-pro.*gemini-2\.5-flash"):
            analyze_code_changes(mock_context, mock_settings)

    @patch("ai_reviewer.integrations.gemini.RotatingGeminiProvider")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_fallback_non_retriable_error_propagates_directly(
        self,
        mock_build_prompt: MagicMock,
        mock_provider_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test that non-retriable fallback errors propagate without wrapping."""
        mock_build_prompt.return_value = "prompt"

        primary = Mock()
        fallback = Mock()
        mock_provider_cls.side_effect = [primary, fallback]

        primary.generate.side_effect = ServerError("503")
        fallback.generate.side_effect = AuthenticationError("bad key")

        with pytest.raises(AuthenticationError):
            analyze_code_changes(mock_context, mock_settings)


class TestReExports:
    """Tests for backward-compatible re-exports."""

    def test_calculate_cost_reexported(self) -> None:
        """Test that calculate_cost is re-exported from integrations.gemini."""
        cost = calculate_cost("gemini-2.5-flash", 1_000_000, 500_000)
        assert cost == pytest.approx(0.075 + 0.15)

    def test_gemini_pricing_reexported(self) -> None:
        """Test that GEMINI_PRICING is re-exported."""
        assert "gemini-3.1-flash-preview" in GEMINI_PRICING

    def test_default_model_reexported(self) -> None:
        """Test that DEFAULT_MODEL is re-exported."""
        assert DEFAULT_MODEL == "gemini-2.5-flash"

    def test_default_pricing_reexported(self) -> None:
        """Test that DEFAULT_PRICING is re-exported."""
        assert "input" in DEFAULT_PRICING
        assert "output" in DEFAULT_PRICING


class TestGeminiClientErrorHandling:
    """Tests for error handling via deprecated GeminiClient."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Mock google.genai.Client."""
        with patch("ai_reviewer.llm.gemini.genai.Client") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_genai_client: MagicMock) -> GeminiClient:
        """Create GeminiClient instance with mocked backend."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return GeminiClient(SecretStr("test-key"))

    def test_rate_limit_raises_error(self, client: GeminiClient) -> None:
        """Test that ResourceExhausted raises RateLimitError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import RateLimitError

        client._provider._client.models.generate_content.side_effect = (
            google_exceptions.ResourceExhausted("Quota exceeded")
        )

        with pytest.raises(RateLimitError):
            client.generate_review("Test prompt")

    def test_auth_error_raises_error(self, client: GeminiClient) -> None:
        """Test that Unauthenticated raises AuthenticationError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import AuthenticationError

        client._provider._client.models.generate_content.side_effect = (
            google_exceptions.Unauthenticated("Invalid API key")
        )

        with pytest.raises(AuthenticationError):
            client.generate_review("Test prompt")

    def test_forbidden_raises_error(self, client: GeminiClient) -> None:
        """Test that PermissionDenied raises ForbiddenError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import ForbiddenError

        client._provider._client.models.generate_content.side_effect = (
            google_exceptions.PermissionDenied("Access denied")
        )

        with pytest.raises(ForbiddenError):
            client.generate_review("Test prompt")

    def test_server_error_raises_error(self, client: GeminiClient) -> None:
        """Test that InternalServerError raises ServerError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import ServerError

        client._provider._client.models.generate_content.side_effect = (
            google_exceptions.InternalServerError("Internal error")
        )

        with pytest.raises(ServerError):
            client.generate_review("Test prompt")
