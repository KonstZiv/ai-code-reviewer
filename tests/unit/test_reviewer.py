"""Unit tests for reviewer module."""

from unittest.mock import MagicMock, Mock, patch

from pydantic import SecretStr

from ai_reviewer.core.config import LanguageMode, Settings
from ai_reviewer.core.models import (
    CodeIssue,
    FileChange,
    FileChangeType,
    GoodPractice,
    IssueCategory,
    IssueSeverity,
    ReviewResult,
    TaskAlignmentStatus,
)
from ai_reviewer.discovery.comment import DISCOVERY_COMMENT_HEADING
from ai_reviewer.discovery.models import Gap
from ai_reviewer.integrations.base import GitProvider
from ai_reviewer.reviewer import (
    _build_review_submission,
    _post_discovery_comment,
    _post_error_comment,
    _run_discovery,
)
from tests.helpers import make_profile


class TestBuildReviewSubmission:
    """Tests for _build_review_submission."""

    def test_all_inline_issues(self) -> None:
        """Test that issues with file_path and line_number become inline comments."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="SQL Injection",
            description="Use parameterized query",
            file_path="db.py",
            line_number=10,
            proposed_code="safe_code()",
        )
        result = ReviewResult(issues=(issue,), summary="Found issues")

        submission = _build_review_submission(result, "en")

        assert len(submission.line_comments) == 1
        assert submission.line_comments[0].path == "db.py"
        assert submission.line_comments[0].line == 10
        assert submission.line_comments[0].suggestion == "safe_code()"
        assert "SQL Injection" in submission.line_comments[0].body

    def test_all_fallback_issues(self) -> None:
        """Test that issues without file/line are in summary only."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="General issue",
            description="Description here",
        )
        result = ReviewResult(issues=(issue,), summary="Found issues")

        submission = _build_review_submission(result, "en")

        assert len(submission.line_comments) == 0
        assert "General issue" in submission.summary

    def test_mixed_issues_partition(self) -> None:
        """Test that mixed issues are correctly partitioned."""
        inline = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Inline Issue",
            description="Desc",
            file_path="src/main.py",
            line_number=5,
        )
        fallback = CodeIssue(
            category=IssueCategory.ARCHITECTURE,
            severity=IssueSeverity.INFO,
            title="Fallback Issue",
            description="Desc",
        )
        result = ReviewResult(issues=(inline, fallback), summary="Review")

        submission = _build_review_submission(result, None)

        assert len(submission.line_comments) == 1
        assert submission.line_comments[0].path == "src/main.py"
        assert "Fallback Issue" in submission.summary
        assert "Inline Issue" not in submission.summary

    def test_empty_issues(self) -> None:
        """Test with no issues at all."""
        result = ReviewResult(summary="Clean code")

        submission = _build_review_submission(result, "en")

        assert len(submission.line_comments) == 0
        assert "Clean code" in submission.summary

    def test_issue_with_file_but_no_line_is_fallback(self) -> None:
        """Test that issue with file_path but no line_number is fallback."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="No line",
            description="Has file but no line",
            file_path="main.py",
            line_number=None,
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert len(submission.line_comments) == 0
        assert "No line" in submission.summary

    def test_issue_with_line_but_no_file_is_fallback(self) -> None:
        """Test that issue with line_number but no file_path is fallback."""
        # CodeIssue with line_number requires ge=1, and file_path=None
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="No file",
            description="Has line but no file",
            file_path=None,
            line_number=5,
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert len(submission.line_comments) == 0
        assert "No file" in submission.summary

    def test_suggestion_mapping(self) -> None:
        """Test that proposed_code maps to suggestion on LineComment."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Fix code",
            description="Desc",
            file_path="app.py",
            line_number=42,
            proposed_code="better_code()",
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert submission.line_comments[0].suggestion == "better_code()"

    def test_no_suggestion_when_absent(self) -> None:
        """Test that LineComment has no suggestion when proposed_code is None."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Fix code",
            description="Desc",
            file_path="app.py",
            line_number=42,
        )
        result = ReviewResult(issues=(issue,))

        submission = _build_review_submission(result, None)

        assert submission.line_comments[0].suggestion is None

    def test_summary_includes_good_practices(self) -> None:
        """Test that good practices appear in summary."""
        practice = GoodPractice(description="Nice type hints", file_path="models.py")
        result = ReviewResult(good_practices=(practice,), summary="Good")

        submission = _build_review_submission(result, None)

        assert "Nice type hints" in submission.summary

    def test_summary_includes_task_alignment(self) -> None:
        """Test that task alignment appears in summary."""
        result = ReviewResult(
            summary="Review",
            task_alignment=TaskAlignmentStatus.ALIGNED,
            task_alignment_reasoning="Matches task",
        )

        submission = _build_review_submission(result, None)

        assert "✅ Aligned" in submission.summary
        assert "Matches task" in submission.summary

    def test_event_defaults_to_comment(self) -> None:
        """Test that submission event defaults to COMMENT."""
        result = ReviewResult(summary="Test")

        submission = _build_review_submission(result, None)

        assert submission.event == "COMMENT"

    def test_valid_line_stays_inline(self) -> None:
        """Test that issue with line in diff remains inline."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Bug",
            description="Desc",
            file_path="app.py",
            line_number=10,
        )
        result = ReviewResult(issues=(issue,), summary="Review")
        changes = (
            FileChange(
                filename="app.py",
                change_type=FileChangeType.MODIFIED,
                patch="@@ -8,4 +8,5 @@\n ctx\n ctx\n+new\n ctx\n ctx\n",
            ),
        )

        submission = _build_review_submission(result, None, changes)

        assert len(submission.line_comments) == 1
        assert submission.line_comments[0].line == 10

    def test_invalid_line_demoted_to_summary(self) -> None:
        """Test that issue with line outside diff is demoted to fallback."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Bug",
            description="Desc",
            file_path="app.py",
            line_number=99,
        )
        result = ReviewResult(issues=(issue,), summary="Review")
        changes = (
            FileChange(
                filename="app.py",
                change_type=FileChangeType.MODIFIED,
                patch="@@ -8,3 +8,3 @@\n ctx\n-old\n+new\n",
            ),
        )

        submission = _build_review_submission(result, None, changes)

        assert len(submission.line_comments) == 0
        assert "Bug" in submission.summary

    def test_no_changes_skips_validation(self) -> None:
        """Test that empty changes tuple skips validation (backward compat)."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Bug",
            description="Desc",
            file_path="app.py",
            line_number=99,
        )
        result = ReviewResult(issues=(issue,), summary="Review")

        submission = _build_review_submission(result, None)

        assert len(submission.line_comments) == 1

    def test_file_not_in_changes_demoted(self) -> None:
        """Test that issue referencing a file not in changes is demoted."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Issue",
            description="Desc",
            file_path="other.py",
            line_number=5,
        )
        result = ReviewResult(issues=(issue,), summary="Review")
        changes = (
            FileChange(
                filename="app.py",
                change_type=FileChangeType.MODIFIED,
                patch="@@ -1,2 +1,2 @@\n-old\n+new\n ctx\n",
            ),
        )

        submission = _build_review_submission(result, None, changes)

        assert len(submission.line_comments) == 0
        assert "Issue" in submission.summary


# ── Helpers ──────────────────────────────────────────────────────────


def _make_settings() -> Mock:
    """Build a mock Settings object with all required attributes."""
    settings = Mock(spec=Settings)
    settings.google_api_key = SecretStr("test-key")
    settings.google_api_keys = ["test-key"]
    settings.gemini_model = "gemini-pro"
    settings.gemini_model_fallback = "gemini-2.5-flash"
    settings.fallback_models = ["gemini-2.5-flash"]
    settings.discovery_enabled = True
    settings.discovery_timeout = 30
    settings.language_mode = LanguageMode.FIXED
    settings.language = "en"
    return settings


# ── TestRunDiscovery ─────────────────────────────────────────────────


class TestRunDiscovery:
    """Tests for _run_discovery."""

    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    def test_success_returns_profile(
        self,
        mock_orch_cls: MagicMock,
        mock_create_router: MagicMock,
    ) -> None:
        """Test that successful discovery returns a ProjectProfile."""
        profile = make_profile()
        mock_orch_cls.return_value.discover.return_value = profile
        provider = MagicMock(spec=GitProvider)
        settings = _make_settings()

        result = _run_discovery(provider, "owner/repo", 1, settings)

        assert result is profile
        mock_orch_cls.return_value.discover.assert_called_once_with("owner/repo", 1)

    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    def test_failure_returns_none(
        self,
        mock_orch_cls: MagicMock,
        mock_create_router: MagicMock,
    ) -> None:
        """Test that discovery failure returns None (fail-open)."""
        mock_orch_cls.return_value.discover.side_effect = RuntimeError("API down")
        provider = MagicMock(spec=GitProvider)
        settings = _make_settings()

        result = _run_discovery(provider, "owner/repo", 1, settings)

        assert result is None

    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    def test_router_creates_provider_with_correct_model(
        self,
        mock_orch_cls: MagicMock,
        mock_create_router: MagicMock,
    ) -> None:
        """Test that router creates provider with the model from settings."""
        profile = make_profile()
        mock_orch_cls.return_value.discover.return_value = profile
        provider = MagicMock(spec=GitProvider)
        settings = _make_settings()

        _run_discovery(provider, "owner/repo", 1, settings)

        mock_create_router.assert_called_once_with(settings)
        mock_router = mock_create_router.return_value
        mock_router.create_provider.assert_called_once_with(model="gemini-pro")

    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    def test_provider_passed_as_repo_and_conversation(
        self,
        mock_orch_cls: MagicMock,
        mock_create_router: MagicMock,
    ) -> None:
        """Test that provider is used for both repo_provider and conversation."""
        profile = make_profile()
        mock_orch_cls.return_value.discover.return_value = profile
        provider = MagicMock(spec=GitProvider)
        settings = _make_settings()

        _run_discovery(provider, "owner/repo", 1, settings)

        call_kwargs = mock_orch_cls.call_args
        assert call_kwargs.kwargs["repo_provider"] is provider
        assert call_kwargs.kwargs["conversation"] is provider

    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    def test_timeout_returns_none(
        self,
        mock_orch_cls: MagicMock,
        mock_create_router: MagicMock,
    ) -> None:
        """Test that discovery timeout returns None (fail-open)."""
        import time

        def slow_discover(*_args: object, **_kwargs: object) -> None:
            time.sleep(5)

        mock_orch_cls.return_value.discover.side_effect = slow_discover
        provider = MagicMock(spec=GitProvider)
        settings = _make_settings()
        settings.discovery_timeout = 1

        result = _run_discovery(provider, "owner/repo", 1, settings)

        assert result is None

    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    def test_timeout_uses_settings_value(
        self,
        mock_orch_cls: MagicMock,
        mock_create_router: MagicMock,
    ) -> None:
        """Test that discovery_timeout from settings is used."""
        profile = make_profile()
        mock_orch_cls.return_value.discover.return_value = profile
        provider = MagicMock(spec=GitProvider)
        settings = _make_settings()
        settings.discovery_timeout = 120

        result = _run_discovery(provider, "owner/repo", 1, settings)

        assert result is profile


# ── TestPostDiscoveryComment ─────────────────────────────────────────


class TestPostDiscoveryComment:
    """Tests for _post_discovery_comment."""

    def test_posts_when_should_post(self) -> None:
        """Test that comment is posted when should_post returns True."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        provider = MagicMock(spec=GitProvider)

        _post_discovery_comment(provider, "owner/repo", 1, profile)

        provider.post_comment.assert_called_once()
        args, _ = provider.post_comment.call_args
        assert args[0] == "owner/repo"
        assert args[1] == 1
        assert DISCOVERY_COMMENT_HEADING in args[2]

    def test_skips_when_no_gaps(self) -> None:
        """Test that comment is NOT posted when profile has no gaps (silent mode)."""
        profile = make_profile(gaps=())
        provider = MagicMock(spec=GitProvider)

        _post_discovery_comment(provider, "owner/repo", 1, profile)

        provider.post_comment.assert_not_called()

    def test_skips_when_duplicate_exists(self) -> None:
        """Test that duplicate comment is not posted."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        provider = MagicMock(spec=GitProvider)
        existing = (f"{DISCOVERY_COMMENT_HEADING}\nold content",)

        _post_discovery_comment(
            provider,
            "owner/repo",
            1,
            profile,
            existing_comments=existing,
        )

        provider.post_comment.assert_not_called()

    def test_skips_when_reviewbot_md_present(self) -> None:
        """Test that comment is not posted when .reviewbot.md exists."""
        profile = make_profile(
            file_tree=("src/main.py", ".reviewbot.md"),
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        provider = MagicMock(spec=GitProvider)

        _post_discovery_comment(provider, "owner/repo", 1, profile)

        provider.post_comment.assert_not_called()

    def test_fail_open_on_provider_error(self) -> None:
        """Test that provider error is swallowed (fail-open)."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        provider = MagicMock(spec=GitProvider)
        provider.post_comment.side_effect = RuntimeError("API error")

        # Should not raise
        _post_discovery_comment(provider, "owner/repo", 1, profile)

    def test_language_passed_to_formatter(self) -> None:
        """Test that language parameter is forwarded to format_discovery_comment."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        provider = MagicMock(spec=GitProvider)

        _post_discovery_comment(
            provider,
            "owner/repo",
            1,
            profile,
            language="ru",
        )

        args, _ = provider.post_comment.call_args
        comment_body = args[2]
        # Russian disclaimer should be present
        assert "россиянин" in comment_body

    def test_language_none_no_disclaimer(self) -> None:
        """Test that no disclaimer when language is None."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        provider = MagicMock(spec=GitProvider)

        _post_discovery_comment(provider, "owner/repo", 1, profile, language=None)

        args, _ = provider.post_comment.call_args
        assert "россиянин" not in args[2]


class TestPostErrorComment:
    """Tests for _post_error_comment."""

    def test_generic_error_uses_review_failed_heading(self) -> None:
        """Test that generic exceptions produce 'Review Failed' comment."""
        provider = MagicMock(spec=GitProvider)

        _post_error_comment(provider, "owner/repo", 1, RuntimeError("something broke"))

        args, _ = provider.post_comment.call_args
        comment = args[2]
        assert "Review Failed" in comment
        assert "something broke" in comment

    def test_all_models_failed_quota_uses_quota_heading(self) -> None:
        """Test AllModelsFailedError with is_quota=True shows 'Quota Exhausted'."""
        from ai_reviewer.utils.retry import AllModelsFailedError

        provider = MagicMock(spec=GitProvider)
        error = AllModelsFailedError("All 2 model(s) failed", is_quota=True)

        _post_error_comment(provider, "owner/repo", 1, error)

        args, _ = provider.post_comment.call_args
        comment = args[2]
        assert "Quota Exhausted" in comment
        assert "Gemini API plan" in comment

    def test_all_models_failed_server_error_uses_unavailable_heading(self) -> None:
        """Test AllModelsFailedError with is_quota=False shows 'All Models Unavailable'."""
        from ai_reviewer.utils.retry import AllModelsFailedError

        provider = MagicMock(spec=GitProvider)
        error = AllModelsFailedError("All 2 model(s) failed: ServerError", is_quota=False)

        _post_error_comment(provider, "owner/repo", 1, error)

        args, _ = provider.post_comment.call_args
        comment = args[2]
        assert "All Models Unavailable" in comment
        assert "server errors or rate limits" in comment
        assert "Review Failed" not in comment

    def test_quota_comment_does_not_say_review_failed(self) -> None:
        """Test that quota comment uses softer wording, not 'Review Failed'."""
        from ai_reviewer.utils.retry import AllModelsFailedError

        provider = MagicMock(spec=GitProvider)

        _post_error_comment(provider, "owner/repo", 1, AllModelsFailedError("quota", is_quota=True))

        args, _ = provider.post_comment.call_args
        assert "Review Failed" not in args[2]

    def test_provider_failure_is_swallowed(self) -> None:
        """Test that post_comment failure is logged, not raised."""
        provider = MagicMock(spec=GitProvider)
        provider.post_comment.side_effect = RuntimeError("API down")

        _post_error_comment(provider, "owner/repo", 1, RuntimeError("original"))
