"""End-to-end tests for the review workflow."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import SecretStr

from ai_reviewer.core.config import LanguageMode, Settings
from ai_reviewer.core.formatter import format_review_summary
from ai_reviewer.core.models import (
    CodeIssue,
    Comment,
    CommentAuthorType,
    CommentType,
    IssueCategory,
    IssueSeverity,
    LinkedTask,
    MergeRequest,
    ReviewResult,
    TaskAlignmentStatus,
)
from ai_reviewer.discovery.comment import DISCOVERY_COMMENT_HEADING
from ai_reviewer.discovery.models import Gap
from ai_reviewer.integrations.base import GitProvider
from ai_reviewer.reviewer import review_pull_request
from tests.helpers import make_profile


class TestReviewFlow:
    """E2E tests for review_pull_request."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        """Create mock settings."""
        settings = Mock(spec=Settings)
        settings.github_token = SecretStr("gh-token")
        settings.google_api_key = SecretStr("ai-key")
        settings.google_api_keys = ["ai-key"]
        settings.gemini_model = "gemini-pro"
        settings.gemini_model_fallback = "gemini-2.5-flash"
        settings.fallback_models = ["gemini-2.5-flash"]
        settings.review_max_files = 5
        settings.review_max_diff_lines = 10
        settings.review_max_comment_chars = 3000
        settings.review_split_threshold = 30_000
        settings.review_include_bot_comments = True
        settings.review_enable_dialogue = True
        settings.review_post_inline_comments = True
        settings.discovery_enabled = False
        settings.language_mode = LanguageMode.FIXED
        settings.language = "en"
        return settings

    @pytest.fixture
    def mock_mr(self) -> MergeRequest:
        """Create a mock MergeRequest."""
        return MergeRequest(
            number=1,
            title="Test PR",
            description="Fixes #123",
            author="dev",
            source_branch="feat",
            target_branch="main",
            comments=(),
            changes=(),
        )

    @pytest.fixture
    def mock_provider(self) -> MagicMock:
        """Create a mock GitProvider."""
        return MagicMock(spec=GitProvider)

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    def test_successful_review(
        self,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test a successful review flow with inline comments enabled."""
        # Setup provider mock
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = (LinkedTask(identifier="123", title="Task"),)

        # Setup Gemini analysis mock
        mock_analyze.return_value = ReviewResult(
            summary="LGTM",
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )

        # Execute
        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # Verify
        mock_provider.get_merge_request.assert_called_once_with("owner/repo", 1)
        mock_provider.get_linked_tasks.assert_called_once()
        mock_analyze.assert_called_once()
        mock_provider.submit_review.assert_called_once()

        # Check submission content
        args, _ = mock_provider.submit_review.call_args
        submission = args[2]
        assert "AI ReviewBot" in submission.summary
        assert "LGTM" in submission.summary
        assert "✅ Aligned" in submission.summary

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    def test_duplicate_comment_skipped(
        self,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test that duplicate summary is skipped (inline mode)."""
        # Setup analysis result
        result = ReviewResult(summary="LGTM")
        mock_analyze.return_value = result

        # Build expected summary (inline mode: no issues → all fallback → empty)
        expected_summary = format_review_summary(result, (), None)

        existing_comment = Comment(
            author="bot",
            author_type=CommentAuthorType.BOT,
            body=expected_summary,
            type=CommentType.ISSUE,
        )

        # Update MR with existing comment
        mr_with_comment = MergeRequest(
            number=mock_mr.number,
            title=mock_mr.title,
            author=mock_mr.author,
            source_branch=mock_mr.source_branch,
            target_branch=mock_mr.target_branch,
            comments=(existing_comment,),
            changes=(),
        )

        mock_provider.get_merge_request.return_value = mr_with_comment
        mock_provider.get_linked_tasks.return_value = ()

        # Execute
        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # Verify submit_review was NOT called
        mock_provider.submit_review.assert_not_called()

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    def test_error_handling_posts_comment(
        self,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test that errors result in an error comment."""
        # Setup provider mock
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = ()

        # Setup analysis to fail
        mock_analyze.side_effect = Exception("Gemini API Error")

        # Execute
        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # Verify error comment posted
        mock_provider.post_comment.assert_called_once()
        args, _ = mock_provider.post_comment.call_args
        assert "AI ReviewBot: Review Failed" in args[2]
        assert "Gemini API Error" in args[2]

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    def test_inline_disabled_uses_post_comment(
        self,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test that disabling inline comments falls back to post_comment."""
        mock_settings.review_post_inline_comments = False
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = ()

        mock_analyze.return_value = ReviewResult(
            summary="LGTM",
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        mock_provider.post_comment.assert_called_once()
        mock_provider.submit_review.assert_not_called()

        args, _ = mock_provider.post_comment.call_args
        assert "AI ReviewBot" in args[2]

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    def test_successful_review_with_inline_issues(
        self,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test that issues with file/line become inline comments."""
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = ()

        issue_inline = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="SQL Injection",
            description="Use parameterized query",
            file_path="db.py",
            line_number=10,
            proposed_code="cursor.execute(sql, params)",
        )
        issue_fallback = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.INFO,
            title="General note",
            description="Consider refactoring",
        )

        mock_analyze.return_value = ReviewResult(
            summary="Found issues",
            issues=(issue_inline, issue_fallback),
        )

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        mock_provider.submit_review.assert_called_once()
        args, _ = mock_provider.submit_review.call_args
        submission = args[2]

        # Inline issue becomes a line comment
        assert len(submission.line_comments) == 1
        assert submission.line_comments[0].path == "db.py"
        assert submission.line_comments[0].line == 10

        # Fallback issue is in summary, not inline
        assert "General note" in submission.summary
        # Inline issue should NOT be in summary
        assert "SQL Injection" not in submission.summary

    def test_rate_limit_abort(
        self,
        mock_provider: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test that workflow aborts if PR cannot be fetched (rate limit)."""
        mock_provider.get_merge_request.return_value = None  # Simulate rate limit

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # Verify no further calls
        mock_provider.get_linked_tasks.assert_not_called()
        mock_provider.post_comment.assert_not_called()


# ── TestDiscoveryIntegration ────────────────────────────────────────


class TestDiscoveryIntegration:
    """E2E tests for review_pull_request with discovery_enabled=True."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        """Create mock settings with discovery enabled."""
        settings = Mock(spec=Settings)
        settings.github_token = SecretStr("gh-token")
        settings.google_api_key = SecretStr("ai-key")
        settings.google_api_keys = ["ai-key"]
        settings.gemini_model = "gemini-pro"
        settings.gemini_model_fallback = "gemini-2.5-flash"
        settings.fallback_models = ["gemini-2.5-flash"]
        settings.review_max_files = 5
        settings.review_max_diff_lines = 10
        settings.review_max_comment_chars = 3000
        settings.review_include_bot_comments = True
        settings.review_enable_dialogue = True
        settings.review_split_threshold = 30_000
        settings.review_post_inline_comments = True
        settings.discovery_enabled = True
        settings.discovery_verbose = False
        settings.discovery_timeout = 30
        settings.language_mode = LanguageMode.FIXED
        settings.language = "en"
        return settings

    @pytest.fixture
    def mock_mr(self) -> MergeRequest:
        """Create a mock MergeRequest."""
        return MergeRequest(
            number=1,
            title="Test PR",
            description="Fixes #123",
            author="dev",
            source_branch="feat",
            target_branch="main",
            comments=(),
            changes=(),
        )

    @pytest.fixture
    def mock_provider(self) -> MagicMock:
        """Create a mock GitProvider."""
        return MagicMock(spec=GitProvider)

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    @patch("ai_reviewer.reviewer._run_discovery")
    def test_discovery_success_posts_comment_then_review(
        self,
        mock_run_discovery: MagicMock,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test full flow: discovery succeeds with gaps → posts discovery comment + review."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        mock_run_discovery.return_value = profile
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = ()
        mock_analyze.return_value = ReviewResult(summary="LGTM")

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # Discovery comment posted via post_comment
        mock_provider.post_comment.assert_called_once()
        comment_body = mock_provider.post_comment.call_args[0][2]
        assert DISCOVERY_COMMENT_HEADING in comment_body

        # Review submitted via submit_review
        mock_provider.submit_review.assert_called_once()

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    @patch("ai_reviewer.reviewer._run_discovery")
    def test_discovery_failure_still_completes_review(
        self,
        mock_run_discovery: MagicMock,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test that discovery failure (returns None) does not block review."""
        mock_run_discovery.return_value = None
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = ()
        mock_analyze.return_value = ReviewResult(summary="LGTM")

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # No discovery comment posted
        mock_provider.post_comment.assert_not_called()
        # Review still submitted
        mock_provider.submit_review.assert_called_once()

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    @patch("ai_reviewer.reviewer._run_discovery")
    def test_discovery_no_gaps_skips_comment(
        self,
        mock_run_discovery: MagicMock,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test silent mode: discovery succeeds but no gaps → no discovery comment."""
        profile = make_profile(gaps=())  # No gaps
        mock_run_discovery.return_value = profile
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = ()
        mock_analyze.return_value = ReviewResult(summary="LGTM")

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # No discovery comment (silent mode)
        mock_provider.post_comment.assert_not_called()
        # Review still submitted
        mock_provider.submit_review.assert_called_once()

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    @patch("ai_reviewer.reviewer._run_discovery")
    def test_discovery_duplicate_comment_not_posted(
        self,
        mock_run_discovery: MagicMock,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test that duplicate discovery comment is not posted."""
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        mock_run_discovery.return_value = profile

        # MR already has a discovery comment
        existing_comment = Comment(
            author="bot",
            author_type=CommentAuthorType.BOT,
            body=f"{DISCOVERY_COMMENT_HEADING}\nold content",
            type=CommentType.ISSUE,
        )
        mr = MergeRequest(
            number=1,
            title="Test PR",
            author="dev",
            source_branch="feat",
            target_branch="main",
            comments=(existing_comment,),
            changes=(),
        )
        mock_provider.get_merge_request.return_value = mr
        mock_provider.get_linked_tasks.return_value = ()
        mock_analyze.return_value = ReviewResult(summary="LGTM")

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # No discovery comment posted (duplicate)
        mock_provider.post_comment.assert_not_called()
        # Review still submitted
        mock_provider.submit_review.assert_called_once()

    @patch("ai_reviewer.reviewer.analyze_code_changes")
    @patch("ai_reviewer.reviewer._run_discovery")
    def test_discovery_with_language_ru(
        self,
        mock_run_discovery: MagicMock,
        mock_analyze: MagicMock,
        mock_provider: MagicMock,
        mock_mr: MergeRequest,
        mock_settings: Settings,
    ) -> None:
        """Test that Russian language adds disclaimer to discovery comment."""
        mock_settings.language = "ru"
        profile = make_profile(
            gaps=(Gap(observation="No tests", default_assumption="No testing"),),
        )
        mock_run_discovery.return_value = profile
        mock_provider.get_merge_request.return_value = mock_mr
        mock_provider.get_linked_tasks.return_value = ()
        mock_analyze.return_value = ReviewResult(summary="LGTM")

        review_pull_request(mock_provider, "owner/repo", 1, mock_settings)

        # Discovery comment should include Russian disclaimer
        comment_body = mock_provider.post_comment.call_args[0][2]
        assert "россиянин" in comment_body
