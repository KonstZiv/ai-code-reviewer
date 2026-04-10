"""Formatter for AI Code Review results.

This module handles the conversion of structured ReviewResult objects
into human-readable Markdown for GitHub/GitLab comments.

Two formats are provided:
1. Full review comment (format_review_comment) - for PR summary
2. Inline comment (format_inline_comment) - compact format for line comments
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_reviewer.core.config import BOT_NAME
from ai_reviewer.core.models import (
    IssueCategory,
    IssueSeverity,
    TaskAlignmentStatus,
)

if TYPE_CHECKING:
    from ai_reviewer.core.models import CodeIssue, GoodPractice, ReviewResult

# Severity icons and labels
SEVERITY_ICONS: dict[IssueSeverity, str] = {
    IssueSeverity.CRITICAL: "🔴",
    IssueSeverity.WARNING: "🟡",
    IssueSeverity.INFO: "💡",
}

SEVERITY_LABELS: dict[IssueSeverity, str] = {
    IssueSeverity.CRITICAL: "Critical",
    IssueSeverity.WARNING: "Warning",
    IssueSeverity.INFO: "Suggestion",
}

# Category icons and labels
CATEGORY_ICONS: dict[IssueCategory, str] = {
    IssueCategory.SECURITY: "🔒",
    IssueCategory.CODE_QUALITY: "📝",
    IssueCategory.ARCHITECTURE: "🏗️",
    IssueCategory.PERFORMANCE: "⚡",
    IssueCategory.TESTING: "🧪",
}

CATEGORY_LABELS: dict[IssueCategory, str] = {
    IssueCategory.SECURITY: "Security",
    IssueCategory.CODE_QUALITY: "Code Quality",
    IssueCategory.ARCHITECTURE: "Architecture",
    IssueCategory.PERFORMANCE: "Performance",
    IssueCategory.TESTING: "Testing",
}

# Task alignment icons
ALIGNMENT_ICONS: dict[TaskAlignmentStatus, str] = {
    TaskAlignmentStatus.ALIGNED: "✅",
    TaskAlignmentStatus.MISALIGNED: "❌",
    TaskAlignmentStatus.INSUFFICIENT_DATA: "⚠️",
}

# Russian language codes (ISO 639-1 and 639-3)
RUSSIAN_LANGUAGE_CODES = frozenset({"ru", "rus"})

# Disclaimer message for Russian language reviews
RUSSIAN_DISCLAIMER = (
    "\n<sub>каждый россиянин, имеющий честь, должен делать все для возвращения "
    "украденного/уничтоженного его страной в других странах и учить этому своих детей. "
    "Слава Украине!</sub>"
)


def is_russian_language(language_code: str | None) -> bool:
    """Check if the given language code represents Russian.

    Args:
        language_code: ISO 639 language code (e.g., "ru", "rus").

    Returns:
        True if the language is Russian, False otherwise.
    """
    if language_code is None:
        return False
    return language_code.lower() in RUSSIAN_LANGUAGE_CODES


def _format_summary_card(result: ReviewResult) -> str:
    """Format the summary statistics card.

    Args:
        result: The review result.

    Returns:
        Markdown table with issue counts.
    """
    counts = (
        f"| {result.critical_count} | {result.warning_count} "
        f"| {result.info_count} | {result.good_practice_count} |"
    )
    lines = [
        "| 🔴 Critical | 🟡 Warnings | 💡 Suggestions | ✨ Good Practices |",
        "|:-----------:|:-----------:|:--------------:|:-----------------:|",
        counts,
    ]
    return "\n".join(lines)


def _format_suggestion_block(proposed_code: str) -> str:
    """Format code as GitHub suggestion block.

    Args:
        proposed_code: The suggested code replacement.

    Returns:
        Markdown suggestion block that renders as "Apply suggestion" button.
    """
    return f"```suggestion\n{proposed_code}\n```"


def _format_learning_section(issue: CodeIssue) -> str:
    """Format the collapsible learning section for an issue.

    Args:
        issue: The code issue with educational content.

    Returns:
        Collapsible details block with why_matters and learn_more_url.
    """
    if not issue.why_matters and not issue.learn_more_url:
        return ""

    parts = ["<details>", "<summary>💡 Why is this important?</summary>", ""]

    if issue.why_matters:
        parts.append(issue.why_matters)

    if issue.learn_more_url:
        parts.append(f"\n📚 [Learn more]({issue.learn_more_url})")

    parts.extend(["", "</details>"])
    return "\n".join(parts)


def _format_issue_full(issue: CodeIssue) -> str:
    """Format a single issue for the full review comment.

    Args:
        issue: The code issue to format.

    Returns:
        Formatted markdown for the issue.
    """
    severity_icon = SEVERITY_ICONS.get(issue.severity, "❓")

    parts = [f"### {severity_icon} {issue.title}"]

    # Location
    if issue.file_path:
        location = f"`{issue.file_path}"
        if issue.line_number:
            location += f":{issue.line_number}"
        location += "`"
        parts.append(f"**File:** {location}")

    parts.append("")

    # Description
    parts.append(issue.description)

    # Code suggestion (Before/After or just suggestion)
    if issue.proposed_code:
        parts.append("")
        if issue.existing_code:
            parts.append("**Before:**")
            parts.append(f"```\n{issue.existing_code}\n```")
            parts.append("**After:**")
        parts.append(_format_suggestion_block(issue.proposed_code))

    # Learning section
    learning = _format_learning_section(issue)
    if learning:
        parts.append("")
        parts.append(learning)

    return "\n".join(parts)


def _format_good_practice(practice: GoodPractice) -> str:
    """Format a single good practice.

    Args:
        practice: The good practice to format.

    Returns:
        Formatted markdown line.
    """
    location = ""
    if practice.file_path:
        location = f" (`{practice.file_path}"
        if practice.line_number:
            location += f":{practice.line_number}"
        location += "`)"

    return f"- ✨ {practice.description}{location}"


def format_review_comment(result: ReviewResult, language: str | None = None) -> str:
    """Format review result as a full Markdown comment.

    This is the main formatting function for PR/MR summary comments.
    Creates a comprehensive review with all sections.

    Args:
        result: The structured review result.
        language: ISO 639 language code. If Russian, adds disclaimer.

    Returns:
        Markdown string ready for posting.
    """
    parts = [f"# \U0001f916 {BOT_NAME}"]

    # Summary section
    parts.append("\n## 📊 Summary")
    parts.append(_format_summary_card(result))

    if result.summary:
        parts.append("")
        parts.append(result.summary)

    # Group issues by category
    issues_by_category: dict[IssueCategory, list[CodeIssue]] = {}
    for issue in result.issues:
        if issue.category not in issues_by_category:
            issues_by_category[issue.category] = []
        issues_by_category[issue.category].append(issue)

    # Sort categories by severity of their most critical issue
    def category_priority(cat: IssueCategory) -> int:
        issues = issues_by_category.get(cat, [])
        if not issues:
            return 999
        severities = [i.severity for i in issues]
        if IssueSeverity.CRITICAL in severities:
            return 0
        if IssueSeverity.WARNING in severities:
            return 1
        return 2

    # Render issues by category
    category_order = [
        IssueCategory.SECURITY,
        IssueCategory.CODE_QUALITY,
        IssueCategory.ARCHITECTURE,
        IssueCategory.PERFORMANCE,
        IssueCategory.TESTING,
    ]
    sorted_categories = sorted(
        [c for c in category_order if c in issues_by_category],
        key=category_priority,
    )

    for category in sorted_categories:
        issues = issues_by_category[category]
        cat_icon = CATEGORY_ICONS.get(category, "📋")
        cat_label = CATEGORY_LABELS.get(category, category.value)

        parts.append(f"\n## {cat_icon} {cat_label}")

        # Sort issues within category by severity
        sorted_issues = sorted(
            issues,
            key=lambda i: (
                0
                if i.severity == IssueSeverity.CRITICAL
                else 1
                if i.severity == IssueSeverity.WARNING
                else 2
            ),
        )

        for issue in sorted_issues:
            parts.append("")
            parts.append(_format_issue_full(issue))

    # Good Practices section
    if result.good_practices:
        parts.append("\n## ✨ Good Practices")
        parts.append("")
        for practice in result.good_practices:
            parts.append(_format_good_practice(practice))

    # Task Alignment section
    parts.append("\n## 📋 Task Alignment")
    alignment_icon = ALIGNMENT_ICONS.get(result.task_alignment, "❓")
    alignment_label = result.task_alignment.value.replace("_", " ").title()
    parts.append(f"**Status:** {alignment_icon} {alignment_label}")

    if result.task_alignment_reasoning:
        parts.append("")
        parts.append(result.task_alignment_reasoning)

    # Russian language disclaimer
    if is_russian_language(language):
        parts.append(RUSSIAN_DISCLAIMER)

    # Footer with metrics
    parts.append("\n---")

    footer_parts = [f"_Generated by [{BOT_NAME}](https://github.com/KonstZiv/ai-code-reviewer)_"]

    if result.metrics:
        model_label = result.metrics.model_name
        if result.metrics.operator:
            model_label = f"{result.metrics.operator} / {model_label}"
        metrics_info = (
            f"_Model: {model_label} | "
            f"Tokens: {result.metrics.total_tokens:,} | "
            f"Latency: {result.metrics.latency_formatted} | "
            f"Est. cost: {result.metrics.cost_formatted}_"
        )
        footer_parts.append(metrics_info)
        if result.metrics.fallback_reason:
            footer_parts.append(f"_Fallback: {result.metrics.fallback_reason}_")

    parts.extend(footer_parts)

    return "\n".join(parts)


def format_review_summary(  # noqa: PLR0912
    result: ReviewResult,
    fallback_issues: tuple[CodeIssue, ...],
    language: str | None = None,
) -> str:
    """Format review result as a summary comment for use with inline comments.

    This produces a short review body when inline comments handle per-line issues.
    Only issues WITHOUT file_path/line_number (fallback issues) are included here;
    issues that go inline are omitted.

    Args:
        result: The structured review result.
        fallback_issues: Issues that cannot be posted inline (missing file/line).
        language: ISO 639 language code. If Russian, adds disclaimer.

    Returns:
        Markdown string ready for posting as review body.
    """
    parts = [f"# \U0001f916 {BOT_NAME}"]

    # Summary section
    parts.append("\n## 📊 Summary")
    parts.append(_format_summary_card(result))

    if result.summary:
        parts.append("")
        parts.append(result.summary)

    # Fallback issues section (only issues without file/line)
    if fallback_issues:
        # Group by category
        issues_by_category: dict[IssueCategory, list[CodeIssue]] = {}
        for issue in fallback_issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)

        category_order = [
            IssueCategory.SECURITY,
            IssueCategory.CODE_QUALITY,
            IssueCategory.ARCHITECTURE,
            IssueCategory.PERFORMANCE,
            IssueCategory.TESTING,
        ]

        for category in category_order:
            if category not in issues_by_category:
                continue
            issues = issues_by_category[category]
            cat_icon = CATEGORY_ICONS.get(category, "📋")
            cat_label = CATEGORY_LABELS.get(category, category.value)

            parts.append(f"\n## {cat_icon} {cat_label}")

            sorted_issues = sorted(
                issues,
                key=lambda i: (
                    0
                    if i.severity == IssueSeverity.CRITICAL
                    else 1
                    if i.severity == IssueSeverity.WARNING
                    else 2
                ),
            )

            for issue in sorted_issues:
                parts.append("")
                parts.append(_format_issue_full(issue))

    # Good Practices section
    if result.good_practices:
        parts.append("\n## ✨ Good Practices")
        parts.append("")
        for practice in result.good_practices:
            parts.append(_format_good_practice(practice))

    # Task Alignment section
    parts.append("\n## 📋 Task Alignment")
    alignment_icon = ALIGNMENT_ICONS.get(result.task_alignment, "❓")
    alignment_label = result.task_alignment.value.replace("_", " ").title()
    parts.append(f"**Status:** {alignment_icon} {alignment_label}")

    if result.task_alignment_reasoning:
        parts.append("")
        parts.append(result.task_alignment_reasoning)

    # Russian language disclaimer
    if is_russian_language(language):
        parts.append(RUSSIAN_DISCLAIMER)

    # Footer with metrics
    parts.append("\n---")

    footer_parts = [f"_Generated by [{BOT_NAME}](https://github.com/KonstZiv/ai-code-reviewer)_"]

    if result.metrics:
        model_label = result.metrics.model_name
        if result.metrics.operator:
            model_label = f"{result.metrics.operator} / {model_label}"
        metrics_info = (
            f"_Model: {model_label} | "
            f"Tokens: {result.metrics.total_tokens:,} | "
            f"Latency: {result.metrics.latency_formatted} | "
            f"Est. cost: {result.metrics.cost_formatted}_"
        )
        footer_parts.append(metrics_info)
        if result.metrics.fallback_reason:
            footer_parts.append(f"_Fallback: {result.metrics.fallback_reason}_")

    parts.extend(footer_parts)

    return "\n".join(parts)


def format_inline_comment(issue: CodeIssue, language: str | None = None) -> str:
    """Format a code issue as a compact inline comment.

    This is used for line-level comments on specific code.
    Format is intentionally compact to avoid cluttering the diff view.

    Args:
        issue: The code issue to format.
        language: ISO 639 language code. If Russian, adds disclaimer.

    Returns:
        Compact markdown string for inline comment.
    """
    severity_icon = SEVERITY_ICONS.get(issue.severity, "❓")

    parts = [f"{severity_icon} **{issue.title}**"]

    # Short description
    parts.append("")
    parts.append(issue.description)

    # Note: suggestion block is NOT added here — it is appended by
    # LineComment.format_body_with_suggestion() to avoid duplication.

    # Compact learning hint (just the URL if available)
    if issue.learn_more_url:
        parts.append("")
        parts.append(f"📚 [Learn more]({issue.learn_more_url})")

    # Russian disclaimer (compact version)
    if is_russian_language(language):
        parts.append(RUSSIAN_DISCLAIMER)

    return "\n".join(parts)


__all__ = [
    "RUSSIAN_DISCLAIMER",
    "format_inline_comment",
    "format_review_comment",
    "format_review_summary",
    "is_russian_language",
]
