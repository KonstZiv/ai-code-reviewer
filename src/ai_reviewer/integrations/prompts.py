"""Prompt engineering for AI Code Reviewer.

This module handles the construction of prompts for the LLM, including:
- Formatting merge request data
- Formatting linked task data
- Formatting and truncating file diffs
- Language-adaptive response generation
- Constructing the final system and user prompts
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING

from ai_reviewer.core.models import CommentAuthorType, CommentType
from ai_reviewer.discovery.diff_analysis import (
    analyze_diff_languages,
    detect_deps_changes,
    format_deps_change_context,
    format_diff_language_context,
)
from ai_reviewer.utils.language import build_language_instruction

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import Comment, FileChange, ReviewContext

# System prompt defining the AI's role and output format
SYSTEM_PROMPT = """You are an expert Senior Software Engineer and Code Review Mentor.
Your task is to review a Pull Request (Merge Request) and provide helpful, educational feedback.

## Your Role
Act as a supportive mentor who helps developers grow. Be constructive, specific, and encouraging.
Balance criticism with recognition of good work.

## Analysis Categories

### 1. Code Issues (issues array)
Find issues across these categories with appropriate severity:

**Categories:**
- `security`: Vulnerabilities (SQL injection, XSS, secrets exposure, auth bypass)
- `code_quality`: Bugs, code smells, maintainability problems
- `architecture`: Design issues, SOLID violations, coupling problems
- `performance`: Inefficiencies, N+1 queries, memory leaks
- `testing`: Missing tests, poor test coverage, test antipatterns

**Severity Levels:**
- `critical`: Must fix before merge (security vulnerabilities, breaking bugs)
- `warning`: Should fix (code quality issues, potential bugs)
- `info`: Suggestions for improvement (educational, minor enhancements)

**For each issue, provide:**
- `title`: Short, clear title (e.g., "SQL Injection in user query")
- `description`: What's wrong and why
- `file_path` + `line_number`: Exact location (when applicable)
- `existing_code`: The problematic code snippet
- `proposed_code`: Your suggested fix (enables "Apply Suggestion" button!)
- `why_matters`: Educational explanation for junior developers
- `learn_more_url`: Link to documentation (OWASP, Python docs, etc.)

### 2. Good Practices (good_practices array)
Recognize what the developer did well! This motivates and reinforces good habits.
Look for: clean code, good naming, proper error handling, good tests, security awareness.

### 3. Task Alignment
- `ALIGNED`: Code implements the requirements correctly
- `MISALIGNED`: Code doesn't match requirements or misses key parts
- `INSUFFICIENT_DATA`: No task linked or task description too vague

## Output Format
Return valid JSON matching this **exact** structure and types:
```json
{
  "issues": [
    {
      "category": "security|code_quality|architecture|performance|testing",
      "severity": "critical|warning|info",
      "title": "string (required)",
      "description": "string (required)",
      "file_path": "string or null",
      "line_number": 42,
      "existing_code": "string or null",
      "proposed_code": "string or null",
      "why_matters": "string or null",
      "learn_more_url": "string or null"
    }
  ],
  "good_practices": [
    {
      "description": "string (required)",
      "file_path": "string or null",
      "line_number": 42
    }
  ],
  "task_alignment": "aligned|misaligned|insufficient_data",
  "task_alignment_reasoning": "Brief explanation",
  "summary": "2-3 sentence overview of the review",
  "detected_language": "ISO 639-1 code (e.g., en, uk, de)"
}
```
**IMPORTANT:** `line_number` must be an integer or null — never a string. \
`category` and `severity` must be one of the listed enum values exactly.

## Important Guidelines
- Be specific: Always include file paths and line numbers when possible
- Be actionable: Provide `proposed_code` for issues that can be fixed
- Be educational: Explain WHY something matters, not just WHAT is wrong
- Be balanced: Find at least one good practice if the code isn't terrible
- Be context-aware: Read the "Existing Discussion" section carefully. Do NOT repeat \
issues that were already discussed or intentionally rejected. Comments marked [BOT] \
are from previous AI reviews
- Be dialogue-aware: Comments may be grouped into threaded conversations (replies \
indented with "> "). Understand the full thread context before commenting. If a \
discussion thread already reached a resolution, do not reopen it
- Respond in the language specified in the user prompt

## Project Context Awareness

If a "Project Context" section is provided in the user prompt:
- Respect automated checks. Do NOT comment on issues that CI tools already handle.
- If "## SKIP in review" is present, do NOT comment on those areas — they are \
enforced by CI.
- If "## FOCUS in review" is present, prioritize those areas — they lack automation.
- If "## CHECK and improve" is present, verify quality and suggest improvements \
following the recommendations.
- If compact format is used ("Skip:" / "Focus:"), follow the same logic.
- Follow any listed "Conventions" when evaluating code style.
"""


# Maximum characters per individual comment in the prompt
_MAX_SINGLE_COMMENT_CHARS = 500


def _truncate_comment_body(body: str, max_chars: int = _MAX_SINGLE_COMMENT_CHARS) -> str:
    """Truncate a comment body to max_chars, preserving word boundaries.

    Args:
        body: The comment body text.
        max_chars: Maximum allowed characters.

    Returns:
        Truncated body with ellipsis if needed.
    """
    # Normalize whitespace
    text = " ".join(body.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rsplit(" ", 1)[0] + "..."


def _format_comment_for_prompt(comment: Comment) -> str:
    """Format a single comment for inclusion in the prompt.

    Args:
        comment: The comment to format.

    Returns:
        Formatted comment string like:
        - [BOT] @author [2024-01-15 10:30] (at file:42): body text
    """
    parts: list[str] = ["- "]

    if comment.author_type == CommentAuthorType.BOT:
        parts.append("[BOT] ")

    parts.append(f"@{comment.author}")

    if comment.created_at is not None:
        parts.append(f" [{comment.created_at:%Y-%m-%d %H:%M}]")

    if comment.file_path and comment.line_number:
        parts.append(f" (at {comment.file_path}:{comment.line_number})")
    elif comment.file_path:
        parts.append(f" (at {comment.file_path})")

    body = _truncate_comment_body(comment.body)
    parts.append(f": {body}")

    return "".join(parts)


def _render_general_comments(
    comments: list[Comment],
    chars_used: int,
    max_chars: int,
) -> tuple[list[str], int, int]:
    """Render general discussion comments within budget.

    Args:
        comments: Sorted list of general comments.
        chars_used: Characters already consumed by prior sections.
        max_chars: Maximum total characters allowed.

    Returns:
        Tuple of (lines, omitted_count, updated_chars_used).
    """
    lines: list[str] = []
    omitted = 0
    for comment in comments:
        line = _format_comment_for_prompt(comment)
        if chars_used + len(line) > max_chars:
            omitted += 1
            continue
        lines.append(line)
        chars_used += len(line)
    return lines, omitted, chars_used


def _render_inline_comments(
    comments: list[Comment],
    chars_used: int,
    max_chars: int,
) -> tuple[list[str], int, int]:
    """Render inline comments grouped by file within budget.

    Args:
        comments: Sorted list of inline comments.
        chars_used: Characters already consumed by prior sections.
        max_chars: Maximum total characters allowed.

    Returns:
        Tuple of (lines, omitted_count, updated_chars_used).
    """
    by_file: dict[str, list[Comment]] = defaultdict(list)
    no_file: list[Comment] = []
    for c in comments:
        if c.file_path:
            by_file[c.file_path].append(c)
        else:
            no_file.append(c)

    all_groups = list(by_file.items())
    if no_file:
        all_groups.append(("(unknown file)", no_file))

    lines: list[str] = []
    omitted = 0
    for file_path, file_comments in all_groups:
        file_header = f"\n**{file_path}:**"
        if chars_used + len(file_header) > max_chars:
            omitted += len(file_comments)
            continue
        lines.append(file_header)
        chars_used += len(file_header)

        for comment in file_comments:
            line = _format_comment_for_prompt(comment)
            if chars_used + len(line) > max_chars:
                omitted += 1
                continue
            lines.append(line)
            chars_used += len(line)

    return lines, omitted, chars_used


def _group_comments_into_threads(
    comments: list[Comment],
) -> list[list[Comment]]:
    """Group comments into threads based on thread_id.

    Comments with the same thread_id are grouped together and sorted by created_at.
    Comments with no thread_id are each placed in their own single-comment thread.
    Threads are sorted by the created_at of their first (root) comment.

    Args:
        comments: Flat list of comments.

    Returns:
        List of threads, where each thread is a list of comments sorted chronologically.
    """
    threads: dict[str, list[Comment]] = defaultdict(list)
    standalone: list[list[Comment]] = []

    for comment in comments:
        if comment.thread_id:
            threads[comment.thread_id].append(comment)
        else:
            standalone.append([comment])

    def _sort_key(c: Comment) -> str:
        return c.created_at.isoformat() if c.created_at else ""

    # Sort comments within each thread by time
    sorted_threads: list[list[Comment]] = []
    for thread_comments in threads.values():
        thread_comments.sort(key=_sort_key)
        sorted_threads.append(thread_comments)

    # Sort threads by root comment time
    sorted_threads.sort(key=lambda t: _sort_key(t[0]))
    standalone.sort(key=lambda t: _sort_key(t[0]))

    return [*sorted_threads, *standalone]


def _format_thread_for_prompt(
    thread: list[Comment],
    chars_used: int,
    max_chars: int,
) -> tuple[list[str], int, int]:
    """Format a single thread for the prompt.

    The root comment is rendered normally; replies are indented with "  > ".

    Args:
        thread: List of comments in one thread (sorted chronologically).
        chars_used: Characters already consumed.
        max_chars: Maximum total characters.

    Returns:
        Tuple of (lines, omitted_count, updated_chars_used).
    """
    lines: list[str] = []
    omitted = 0

    for i, comment in enumerate(thread):
        formatted = _format_comment_for_prompt(comment)
        if i > 0:
            # Indent replies: strip leading "- " and prepend "  > "
            formatted = "  > " + formatted.removeprefix("- ")

        if chars_used + len(formatted) > max_chars:
            omitted += 1
            continue
        lines.append(formatted)
        chars_used += len(formatted)

    return lines, omitted, chars_used


def _render_general_comments_threaded(
    comments: list[Comment],
    chars_used: int,
    max_chars: int,
) -> tuple[list[str], int, int]:
    """Render general discussion comments with threading within budget.

    Args:
        comments: Sorted list of general comments.
        chars_used: Characters already consumed.
        max_chars: Maximum total characters.

    Returns:
        Tuple of (lines, omitted_count, updated_chars_used).
    """
    threads = _group_comments_into_threads(comments)
    lines: list[str] = []
    total_omitted = 0

    for thread in threads:
        thread_lines, omitted, chars_used = _format_thread_for_prompt(thread, chars_used, max_chars)
        lines.extend(thread_lines)
        total_omitted += omitted

    return lines, total_omitted, chars_used


def _render_inline_comments_threaded(
    comments: list[Comment],
    chars_used: int,
    max_chars: int,
) -> tuple[list[str], int, int]:
    """Render inline comments with threading, grouped by file, within budget.

    Args:
        comments: Sorted list of inline comments.
        chars_used: Characters already consumed.
        max_chars: Maximum total characters.

    Returns:
        Tuple of (lines, omitted_count, updated_chars_used).
    """
    by_file: dict[str, list[Comment]] = defaultdict(list)
    no_file: list[Comment] = []
    for c in comments:
        if c.file_path:
            by_file[c.file_path].append(c)
        else:
            no_file.append(c)

    all_groups = list(by_file.items())
    if no_file:
        all_groups.append(("(unknown file)", no_file))

    lines: list[str] = []
    total_omitted = 0

    for file_path, file_comments in all_groups:
        file_header = f"\n**{file_path}:**"
        if chars_used + len(file_header) > max_chars:
            total_omitted += len(file_comments)
            continue
        lines.append(file_header)
        chars_used += len(file_header)

        threads = _group_comments_into_threads(file_comments)
        for thread in threads:
            thread_lines, omitted, chars_used = _format_thread_for_prompt(
                thread, chars_used, max_chars
            )
            lines.extend(thread_lines)
            total_omitted += omitted

    return lines, total_omitted, chars_used


def _build_comments_section(
    comments: tuple[Comment, ...],
    max_total_chars: int,
    include_bot: bool,
    *,
    enable_dialogue: bool = True,
) -> str | None:
    """Build the comments section for the review prompt.

    Groups comments into General Discussion and Inline Code Discussion.
    When enable_dialogue is True, comments are grouped into threads.
    Applies truncation: individual comments capped at 500 chars,
    total capped at max_total_chars, oldest dropped first.

    Args:
        comments: Tuple of Comment objects from the MR.
        max_total_chars: Maximum total characters for the section.
        include_bot: Whether to include bot comments.
        enable_dialogue: Group comments into threaded dialogues.

    Returns:
        Formatted comments section string, or None if no comments to show.
    """
    if not comments or max_total_chars == 0:
        return None

    filtered = [c for c in comments if include_bot or c.author_type != CommentAuthorType.BOT]
    if not filtered:
        return None

    def _sort_key(c: Comment) -> str:
        return c.created_at.isoformat() if c.created_at else ""

    general = sorted(
        (c for c in filtered if c.type == CommentType.ISSUE),
        key=_sort_key,
    )
    inline = sorted(
        (c for c in filtered if c.type != CommentType.ISSUE),
        key=_sort_key,
    )

    chars_used = 0
    section_parts: list[str] = []

    if general:
        render_general = (
            _render_general_comments_threaded if enable_dialogue else _render_general_comments
        )
        lines, omitted, chars_used = render_general(general, chars_used, max_total_chars)
        if lines or omitted:
            section_parts.append("### General Discussion")
            if omitted:
                section_parts.append(f"[... {omitted} older comments omitted]")
            section_parts.extend(lines)

    if inline:
        render_inline = (
            _render_inline_comments_threaded if enable_dialogue else _render_inline_comments
        )
        lines, omitted, chars_used = render_inline(inline, chars_used, max_total_chars)
        if lines or omitted:
            section_parts.append("\n### Inline Code Discussion")
            if omitted:
                section_parts.append(f"[... {omitted} older comments omitted]")
            section_parts.extend(lines)

    if not section_parts:
        return None

    header = (
        "## Existing Discussion\n"
        "The following comments have already been posted on this MR.\n"
        "DO NOT repeat suggestions that were already discussed or rejected.\n"
    )
    return header + "\n".join(section_parts)


def _format_file_change(change: FileChange, max_lines: int) -> str:
    """Format a single file change with truncation logic.

    Args:
        change: The file change object.
        max_lines: Maximum number of diff lines to include.

    Returns:
        Formatted string representation of the file change.
    """
    header = f"File: {change.filename} ({change.change_type.value})"

    if change.patch is None:
        return f"{header}\n[Binary or large file - content skipped]"

    lines = change.patch.splitlines()
    if len(lines) > max_lines:
        truncated_patch = "\n".join(lines[:max_lines])
        skipped = len(lines) - max_lines
        return f"{header}\n{truncated_patch}\n... [Diff truncated, {skipped} lines skipped]"

    return f"{header}\n{change.patch}"


def _build_mr_aware_context(context: ReviewContext) -> str:
    """Build MR-specific context from diff analysis.

    Detects language mismatch and dependency changes, returns prompt
    sections (or empty string if nothing noteworthy).
    """
    if not context.mr.changes:
        return ""

    parts: list[str] = []

    # Language mismatch
    repo_langs = context.project_profile.platform_data.languages if context.project_profile else {}
    diff_lang = analyze_diff_languages(context.mr.changes, repo_langs)
    if diff_lang and not diff_lang.matches_repo:
        parts.append(format_diff_language_context(diff_lang))

    # Dependency changes
    deps = detect_deps_changes(context.mr.changes)
    if deps:
        parts.append(format_deps_change_context(deps))

    return "".join(parts)


def build_review_prompt(context: ReviewContext, settings: Settings) -> str:
    """Construct the full user prompt for the review.

    Args:
        context: The review context (MR, task, etc.).
        settings: Application settings for limits.

    Returns:
        The constructed prompt string.
    """
    parts = []

    # 0. Language Instruction (first, so it's prominent)
    language_instruction = build_language_instruction(context, settings)
    parts.append(f"## Language\n{language_instruction}")

    # 0.5. Project Context (from Discovery)
    if context.project_profile:
        parts.append("\n## Project Context")
        parts.append(context.project_profile.to_prompt_context())

    # 0.6. MR-aware diff analysis (language mismatch + dep changes)
    mr_context = _build_mr_aware_context(context)
    if mr_context:
        parts.append(mr_context)

    # 1. Linked Task Context
    if len(context.tasks) == 1:
        parts.append("\n## Linked Task")
        parts.append(f"Title: {context.tasks[0].title}")
        parts.append(f"Description:\n{context.tasks[0].description}")
    elif len(context.tasks) > 1:
        parts.append("\n## Linked Tasks")
        for i, task in enumerate(context.tasks, 1):
            parts.append(f"### Task {i}: {task.title}")
            parts.append(f"Description:\n{task.description}")
    else:
        parts.append("\n## Linked Task")
        parts.append("No linked task provided.")

    # 2. Merge Request Context
    parts.append("\n## Merge Request")
    parts.append(f"Title: {context.mr.title}")
    parts.append(f"Description:\n{context.mr.description}")

    # 3. Existing Discussion (between MR context and Code Changes)
    comments_section = _build_comments_section(
        context.mr.comments,
        max_total_chars=settings.review_max_comment_chars,
        include_bot=settings.review_include_bot_comments,
        enable_dialogue=settings.review_enable_dialogue,
    )
    if comments_section:
        parts.append(f"\n{comments_section}")

    # 4. Code Changes
    parts.append("\n## Code Changes")

    # Filter and limit files
    files_to_process = context.mr.changes[: settings.review_max_files]
    skipped_files_count = len(context.mr.changes) - len(files_to_process)

    for change in files_to_process:
        parts.append(_format_file_change(change, settings.review_max_diff_lines))
        parts.append("---")

    if skipped_files_count > 0:
        parts.append(f"\n... [Skipped {skipped_files_count} more files due to limit]")

    return "\n".join(parts)


# ── Split review support ─────────────────────────────────────────────

_TEST_FILE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)spec/"),
    re.compile(r"(^|/)__tests__/"),
    re.compile(r"/test_[^/]+$"),
    re.compile(r"/[^/]+_test\.[^/]+$"),
    re.compile(r"/[^/]+\.test\.[^/]+$"),
    re.compile(r"/[^/]+\.spec\.[^/]+$"),
    re.compile(r"(^|/)conftest\.py$"),
)


def is_test_file(filename: str) -> bool:
    """Determine whether a file path is a test file.

    Args:
        filename: Relative file path from repository root.

    Returns:
        True if the file matches common test file patterns.
    """
    return any(p.search(filename) for p in _TEST_FILE_PATTERNS)


def partition_changes(
    changes: tuple[FileChange, ...],
) -> tuple[tuple[FileChange, ...], tuple[FileChange, ...]]:
    """Split file changes into production code and test files.

    Args:
        changes: All file changes from the MR.

    Returns:
        Tuple of (production_changes, test_changes).
    """
    prod: list[FileChange] = []
    tests: list[FileChange] = []
    for change in changes:
        if is_test_file(change.filename):
            tests.append(change)
        else:
            prod.append(change)
    return tuple(prod), tuple(tests)


CODE_SUMMARY_INSTRUCTION = """

## Additional Instruction: Code Summary
In your response, include a `code_summary` field: a compressed 200-500 character \
description of the production code changes, key decisions, and patterns. \
This will be provided to a second review pass that analyzes test files.\
"""

_CODE_SUMMARY_SECTION = """\

## Previously Reviewed Production Code
The following is a compressed summary of the production code changes \
that were reviewed in a prior pass. Use this to understand the context \
when reviewing tests.

{code_summary}
"""


def build_split_review_prompt(
    context: ReviewContext,
    settings: Settings,
    changes: tuple[FileChange, ...],
    *,
    code_summary: str = "",
) -> str:
    """Build a review prompt for a subset of file changes.

    Same structure as ``build_review_prompt`` but operates on an explicit
    set of changes and optionally prepends a code summary section.

    Args:
        context: The full review context.
        settings: Application settings.
        changes: Subset of file changes to include.
        code_summary: Summary from prior code review pass (empty for first pass).

    Returns:
        The constructed prompt string.
    """
    mr_subset = context.mr.model_copy(update={"changes": changes})
    ctx_subset = context.model_copy(update={"mr": mr_subset})

    prompt = build_review_prompt(ctx_subset, settings)

    if code_summary:
        marker = "\n## Code Changes"
        idx = prompt.find(marker)
        if idx != -1:
            section = _CODE_SUMMARY_SECTION.format(code_summary=code_summary)
            prompt = prompt[:idx] + section + prompt[idx:]

    return prompt
