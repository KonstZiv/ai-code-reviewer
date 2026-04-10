"""Tests for split review: file classification, partitioning, merging."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from ai_reviewer.core.config import LanguageMode
from ai_reviewer.core.models import (
    CodeIssue,
    FileChange,
    FileChangeType,
    GoodPractice,
    IssueCategory,
    IssueSeverity,
    LinkedTask,
    MergeRequest,
    ReviewContext,
    ReviewMetrics,
    ReviewResult,
    TaskAlignmentStatus,
)
from ai_reviewer.integrations.gemini import (
    _merge_review_results,
    analyze_code_changes,
)
from ai_reviewer.integrations.prompts import (
    build_split_review_prompt,
    is_test_file,
    partition_changes,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _make_change(filename: str) -> FileChange:
    return FileChange(
        filename=filename,
        change_type=FileChangeType.MODIFIED,
        patch="+ some change",
    )


def _make_settings(**overrides: object) -> Mock:
    settings = Mock()
    settings.llm_provider = "google"
    settings.llm_fallback_provider = None
    settings.review_max_files = 20
    settings.review_max_diff_lines = 500
    settings.review_split_threshold = 30_000
    settings.language = "en"
    settings.language_mode = LanguageMode.FIXED
    settings.review_max_comment_chars = 3000
    settings.review_include_bot_comments = True
    settings.review_enable_dialogue = True
    settings.gemini_model = "gemini-test"
    settings.gemini_model_fallback = None
    settings.fallback_models = []
    settings.gemini_fallback_models = []
    settings.google_api_key = Mock()
    settings.google_api_key.get_secret_value.return_value = "test-key"
    settings.google_api_keys = ["test-key"]
    settings.mistral_api_key = None
    settings.mistral_api_keys = []
    settings.mistral_model = "mistral-large-latest"
    settings.mistral_fallback_models = []
    settings.get_provider_model = lambda p: (
        settings.mistral_model if p == "mistral" else settings.gemini_model
    )
    settings.get_provider_fallback_models = lambda p: (
        settings.mistral_fallback_models if p == "mistral" else settings.gemini_fallback_models
    )
    settings.get_provider_api_keys = lambda p: (
        settings.mistral_api_keys if p == "mistral" else settings.google_api_keys
    )
    for k, v in overrides.items():
        setattr(settings, k, v)
    return settings


def _make_context(
    filenames: tuple[str, ...] = ("src/main.py",),
) -> ReviewContext:
    mr = MergeRequest(
        number=1,
        title="Test PR",
        description="Description",
        author="dev",
        source_branch="feat",
        target_branch="main",
        changes=tuple(_make_change(f) for f in filenames),
    )
    task = LinkedTask(identifier="1", title="Task", description="Desc")
    return ReviewContext(mr=mr, tasks=(task,), repository="owner/repo")


def _make_result(  # noqa: PLR0913
    *,
    issues: int = 0,
    summary: str = "",
    code_summary: str = "",
    model_name: str = "test-model",
    prompt_tokens: int = 100,
    completion_tokens: int = 50,
) -> ReviewResult:
    issue_list = tuple(
        CodeIssue(
            file_path=f"file{i}.py",
            line_number=i + 1,
            severity=IssueSeverity.WARNING,
            category=IssueCategory.CODE_QUALITY,
            title=f"Issue {i}",
            description=f"Description {i}",
        )
        for i in range(issues)
    )
    return ReviewResult(
        issues=issue_list,
        summary=summary,
        code_summary=code_summary,
        metrics=ReviewMetrics(
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            api_latency_ms=1000,
            estimated_cost_usd=0.01,
        ),
    )


# ── TestIsTestFile ───────────────────────────────────────────────────


class TestIsTestFile:
    """Test file classification."""

    @pytest.mark.parametrize(
        "filename",
        [
            "tests/test_main.py",
            "tests/unit/test_split.py",
            "test/test_foo.py",
            "src/tests/test_bar.py",
            "spec/models_spec.js",
            "__tests__/App.test.tsx",
            "pkg/handler_test.go",
            "src/utils.test.ts",
            "src/utils.spec.js",
            "tests/conftest.py",
            "conftest.py",
        ],
        ids=lambda f: f.replace("/", "_"),
    )
    def test_positive(self, filename: str) -> None:
        assert is_test_file(filename) is True

    @pytest.mark.parametrize(
        "filename",
        [
            "src/main.py",
            "src/models.py",
            "utils/tester.py",
            "contest.py",
            "src/testing_utils.py",
            "README.md",
            ".github/workflows/tests.yml",
        ],
        ids=lambda f: f.replace("/", "_").replace(".", "_"),
    )
    def test_negative(self, filename: str) -> None:
        assert is_test_file(filename) is False


# ── TestPartitionChanges ─────────────────────────────────────────────


class TestPartitionChanges:
    """Split changes into production and test groups."""

    def test_mixed_files(self) -> None:
        changes = (
            _make_change("src/main.py"),
            _make_change("tests/test_main.py"),
            _make_change("src/utils.py"),
            _make_change("tests/test_utils.py"),
        )
        prod, tests = partition_changes(changes)
        assert len(prod) == 2
        assert len(tests) == 2
        assert all(not is_test_file(c.filename) for c in prod)
        assert all(is_test_file(c.filename) for c in tests)

    def test_all_production(self) -> None:
        changes = (_make_change("src/main.py"), _make_change("src/utils.py"))
        prod, tests = partition_changes(changes)
        assert len(prod) == 2
        assert len(tests) == 0

    def test_all_tests(self) -> None:
        changes = (_make_change("tests/test_a.py"), _make_change("tests/test_b.py"))
        prod, tests = partition_changes(changes)
        assert len(prod) == 0
        assert len(tests) == 2

    def test_empty(self) -> None:
        prod, tests = partition_changes(())
        assert prod == ()
        assert tests == ()


# ── TestMergeReviewResults ───────────────────────────────────────────


class TestMergeReviewResults:
    """Merge results from two review passes."""

    def test_issues_combined(self) -> None:
        code = _make_result(issues=2, summary="Code review")
        test = _make_result(issues=1, summary="Test review")
        merged = _merge_review_results(code, test)
        assert merged.issue_count == 3

    def test_summaries_joined(self) -> None:
        code = _make_result(summary="Code looks good")
        test = _make_result(summary="Tests adequate")
        merged = _merge_review_results(code, test)
        assert "Code looks good" in merged.summary
        assert "Test review:" in merged.summary
        assert "Tests adequate" in merged.summary

    def test_empty_test_summary(self) -> None:
        code = _make_result(summary="Code review done")
        test = _make_result(summary="")
        merged = _merge_review_results(code, test)
        assert merged.summary == "Code review done"

    def test_code_summary_preserved(self) -> None:
        code = _make_result(code_summary="Refactored auth module")
        test = _make_result()
        merged = _merge_review_results(code, test)
        assert merged.code_summary == "Refactored auth module"

    def test_metrics_summed(self) -> None:
        code = _make_result(prompt_tokens=100, completion_tokens=50)
        test = _make_result(prompt_tokens=80, completion_tokens=40)
        merged = _merge_review_results(code, test)
        assert merged.metrics is not None
        assert merged.metrics.prompt_tokens == 180
        assert merged.metrics.completion_tokens == 90
        assert merged.metrics.total_tokens == 270
        assert merged.metrics.api_latency_ms == 2000
        assert merged.metrics.estimated_cost_usd == pytest.approx(0.02)

    def test_good_practices_combined(self) -> None:
        code = ReviewResult(
            good_practices=(GoodPractice(description="Good naming"),),
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        test = ReviewResult(
            good_practices=(GoodPractice(description="Good coverage"),),
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        merged = _merge_review_results(code, test)
        assert len(merged.good_practices) == 2

    def test_task_alignment_both_aligned(self) -> None:
        code = ReviewResult(
            task_alignment=TaskAlignmentStatus.ALIGNED,
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        test = ReviewResult(
            task_alignment=TaskAlignmentStatus.ALIGNED,
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        merged = _merge_review_results(code, test)
        assert merged.task_alignment == TaskAlignmentStatus.ALIGNED

    def test_task_alignment_worst_case_wins(self) -> None:
        code = ReviewResult(
            task_alignment=TaskAlignmentStatus.ALIGNED,
            task_alignment_reasoning="Code looks good",
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        test = ReviewResult(
            task_alignment=TaskAlignmentStatus.MISALIGNED,
            task_alignment_reasoning="Tests don't cover requirement X",
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        merged = _merge_review_results(code, test)
        assert merged.task_alignment == TaskAlignmentStatus.MISALIGNED
        assert "Code looks good" in merged.task_alignment_reasoning
        assert "Tests don't cover requirement X" in merged.task_alignment_reasoning

    def test_task_alignment_insufficient_vs_aligned(self) -> None:
        code = ReviewResult(
            task_alignment=TaskAlignmentStatus.INSUFFICIENT_DATA,
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        test = ReviewResult(
            task_alignment=TaskAlignmentStatus.ALIGNED,
            metrics=ReviewMetrics(model_name="m", prompt_tokens=0, completion_tokens=0),
        )
        merged = _merge_review_results(code, test)
        assert merged.task_alignment == TaskAlignmentStatus.INSUFFICIENT_DATA


# ── TestBuildSplitReviewPrompt ───────────────────────────────────────


class TestBuildSplitReviewPrompt:
    """Split prompt builder."""

    def test_subset_of_files(self) -> None:
        context = _make_context(("src/a.py", "src/b.py", "tests/test_a.py"))
        settings = _make_settings()
        changes = (_make_change("src/a.py"),)
        prompt = build_split_review_prompt(context, settings, changes)
        assert "src/a.py" in prompt
        assert "tests/test_a.py" not in prompt

    def test_code_summary_injected(self) -> None:
        context = _make_context(("tests/test_a.py",))
        settings = _make_settings()
        changes = (_make_change("tests/test_a.py"),)
        prompt = build_split_review_prompt(
            context, settings, changes, code_summary="Refactored auth flow"
        )
        assert "Previously Reviewed Production Code" in prompt
        assert "Refactored auth flow" in prompt
        # Summary should appear BEFORE code changes
        summary_idx = prompt.find("Refactored auth flow")
        code_idx = prompt.find("## Code Changes")
        assert summary_idx < code_idx

    def test_no_summary_no_section(self) -> None:
        context = _make_context(("src/a.py",))
        settings = _make_settings()
        changes = (_make_change("src/a.py"),)
        prompt = build_split_review_prompt(context, settings, changes)
        assert "Previously Reviewed" not in prompt


# ── TestAnalyzeCodeChanges ───────────────────────────────────────────


class TestAnalyzeCodeChanges:
    """Integration tests for analyze_code_changes split logic."""

    @patch("ai_reviewer.integrations.gemini.create_router")
    @patch("ai_reviewer.integrations.gemini._call_llm")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_under_threshold_single_call(
        self,
        mock_build: Mock,
        mock_call: Mock,
        _mock_router: Mock,  # noqa: PT019
    ) -> None:
        """Under threshold -> single LLM call."""
        mock_build.return_value = "x" * 1000  # Under 30K
        mock_call.return_value = _make_result(issues=1, summary="OK")
        settings = _make_settings()
        context = _make_context(("src/main.py", "tests/test_main.py"))

        result = analyze_code_changes(context, settings)

        mock_call.assert_called_once()
        assert result.issue_count == 1

    @patch("ai_reviewer.integrations.gemini.create_router")
    @patch("ai_reviewer.integrations.gemini._call_llm")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_over_threshold_split(
        self,
        mock_build: Mock,
        mock_call: Mock,
        _mock_router: Mock,  # noqa: PT019
    ) -> None:
        """Over threshold with mixed files -> two LLM calls."""
        mock_build.return_value = "x" * 50_000  # Over 30K
        code_result = _make_result(issues=2, summary="Code", code_summary="Auth refactor")
        test_result = _make_result(issues=1, summary="Tests")
        mock_call.side_effect = [code_result, test_result]
        settings = _make_settings()
        context = _make_context(("src/main.py", "tests/test_main.py"))

        result = analyze_code_changes(context, settings)

        assert mock_call.call_count == 2
        assert result.issue_count == 3

    @patch("ai_reviewer.integrations.gemini.create_router")
    @patch("ai_reviewer.integrations.gemini._call_llm")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_over_threshold_all_production_no_split(
        self,
        mock_build: Mock,
        mock_call: Mock,
        _mock_router: Mock,  # noqa: PT019
    ) -> None:
        """Over threshold but all production files -> single call."""
        mock_build.return_value = "x" * 50_000
        mock_call.return_value = _make_result(issues=1)
        settings = _make_settings()
        context = _make_context(("src/main.py", "src/utils.py"))

        result = analyze_code_changes(context, settings)

        mock_call.assert_called_once()
        assert result.issue_count == 1

    @patch("ai_reviewer.integrations.gemini.create_router")
    @patch("ai_reviewer.integrations.gemini._call_llm")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_over_threshold_all_tests_no_split(
        self,
        mock_build: Mock,
        mock_call: Mock,
        _mock_router: Mock,  # noqa: PT019
    ) -> None:
        """Over threshold but all test files -> single call."""
        mock_build.return_value = "x" * 50_000
        mock_call.return_value = _make_result(issues=1)
        settings = _make_settings()
        context = _make_context(("tests/test_a.py", "tests/test_b.py"))

        analyze_code_changes(context, settings)

        mock_call.assert_called_once()
