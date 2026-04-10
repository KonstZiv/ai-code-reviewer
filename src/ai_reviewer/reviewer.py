"""Main reviewer logic for AI Code Reviewer.

This module orchestrates the entire review process:
1. Fetching data from Git provider
2. Analyzing code with AI (Gemini)
3. Formatting and posting results

The reviewer is provider-agnostic and works with any GitProvider implementation.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TYPE_CHECKING

from ai_reviewer.core.config import BOT_NAME
from ai_reviewer.core.formatter import (
    format_inline_comment,
    format_review_comment,
    format_review_summary,
)
from ai_reviewer.core.models import CommentAuthorType, ReviewContext
from ai_reviewer.discovery.comment import (
    format_discovery_comment,
    should_post_discovery_comment,
)
from ai_reviewer.integrations.base import LineComment, ReviewSubmission, parse_diff_valid_lines
from ai_reviewer.integrations.gemini import analyze_code_changes
from ai_reviewer.utils.language import get_language_for_review
from ai_reviewer.utils.retry import AllModelsFailedError, QuotaExhaustedError

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import CodeIssue, FileChange, ReviewResult
    from ai_reviewer.discovery.models import ProjectProfile
    from ai_reviewer.integrations.base import GitProvider

logger = logging.getLogger(__name__)


def _build_review_submission(
    result: ReviewResult,
    language: str | None,
    changes: tuple[FileChange, ...] = (),
) -> ReviewSubmission:
    """Build a ReviewSubmission by partitioning issues into inline and fallback.

    Issues with both file_path and line_number (>= 1) become inline comments,
    **provided** the line number exists in the diff. Issues whose line is
    outside the diff are demoted to the summary (fallback) so that the
    GitHub Review API does not reject them with 422.

    Args:
        result: The structured review result from AI analysis.
        language: ISO 639 language code for formatting.
        changes: File changes from the MR (used for diff-line validation).
            When empty, validation is skipped (backward compatibility).

    Returns:
        ReviewSubmission with summary and inline line comments.
    """
    # Build valid-line lookup from diff patches
    valid_lines_by_file: dict[str, frozenset[int]] = {}
    for change in changes:
        valid_lines_by_file[change.filename] = parse_diff_valid_lines(change.patch)

    inline_issues: list[CodeIssue] = []
    fallback_issues: list[CodeIssue] = []

    for issue in result.issues:
        if issue.file_path and issue.line_number and issue.line_number >= 1:
            # Validate line against diff when change data is available
            if valid_lines_by_file:
                file_lines = valid_lines_by_file.get(issue.file_path, frozenset())
                if issue.line_number not in file_lines:
                    logger.warning(
                        "Line %d not in diff for %s, demoting to summary",
                        issue.line_number,
                        issue.file_path,
                    )
                    fallback_issues.append(issue)
                    continue
            inline_issues.append(issue)
        else:
            fallback_issues.append(issue)

    # Build inline line comments
    line_comments: list[LineComment] = []
    for issue in inline_issues:
        body = format_inline_comment(issue, language)
        line_comments.append(
            LineComment(
                path=issue.file_path,  # type: ignore[arg-type]  # guarded above
                line=issue.line_number,  # type: ignore[arg-type]  # guarded above
                body=body,
                suggestion=issue.proposed_code,
            )
        )

    summary = format_review_summary(result, tuple(fallback_issues), language)

    return ReviewSubmission(
        summary=summary,
        line_comments=tuple(line_comments),
    )


def review_pull_request(
    provider: GitProvider,
    repo_name: str,
    mr_id: int,
    settings: Settings,
) -> None:
    """Perform a full AI code review on a pull/merge request.

    This function orchestrates the entire review process using the provided
    Git provider. It is provider-agnostic and works with any GitProvider
    implementation (GitHub, GitLab, etc.).

    Args:
        provider: Git provider instance for API interactions.
        repo_name: Repository identifier (e.g., 'owner/repo' for GitHub).
        mr_id: Merge/Pull request number.
        settings: Application settings.
    """
    try:
        logger.info("Starting review for MR #%s in %s", mr_id, repo_name)

        # 0. Discovery step (fail-open)
        profile = (
            _run_discovery(provider, repo_name, mr_id, settings)
            if settings.discovery_enabled
            else None
        )

        # 1. Fetch MR data
        mr = provider.get_merge_request(repo_name, mr_id)
        if not mr:
            logger.error("Could not fetch MR data (likely rate limit exceeded). Aborting.")
            return

        logger.info("Fetched MR: %s", mr.title)

        # 2. Get linked tasks (multi-strategy discovery)
        tasks = provider.get_linked_tasks(repo_name, mr.number, mr.source_branch)
        if tasks:
            logger.info(
                "Found %d linked task(s): %s",
                len(tasks),
                ", ".join(t.identifier for t in tasks),
            )
        else:
            logger.info("No linked tasks found")

        # 3. Build context (needed for language detection)
        context = ReviewContext(mr=mr, tasks=tasks, repository=repo_name, project_profile=profile)
        language = get_language_for_review(context, settings)

        # 3.5. Post discovery comment (fail-open, after language is known)
        if profile:
            existing_bot = tuple(
                c.body for c in mr.comments if c.author_type == CommentAuthorType.BOT
            )
            _post_discovery_comment(
                provider,
                repo_name,
                mr_id,
                profile,
                existing_comments=existing_bot,
                language=language,
                verbose=settings.discovery_verbose,
            )

        # 4. Analyze with AI
        result = analyze_code_changes(context, settings)

        # 5. Find last bot comment for duplicate detection
        last_bot_comment = None
        for comment in reversed(mr.comments):
            if comment.author_type == CommentAuthorType.BOT:
                last_bot_comment = comment
                break

        # 6. Post results
        if settings.review_post_inline_comments:
            submission = _build_review_submission(result, result.detected_language, mr.changes)

            # Duplicate detection: compare summary only
            if last_bot_comment and last_bot_comment.body.strip() == submission.summary.strip():
                logger.info("Duplicate summary detected. Skipping publication.")
                return

            provider.submit_review(repo_name, mr_id, submission)
            logger.info("Review completed successfully (inline comments)")
        else:
            # Legacy behavior: single summary comment via post_comment
            comment_body = format_review_comment(result, language=result.detected_language)

            if last_bot_comment and last_bot_comment.body.strip() == comment_body.strip():
                logger.info("Duplicate comment detected. Skipping publication.")
                return

            provider.post_comment(repo_name, mr_id, comment_body)
            logger.info("Review completed successfully")

    except Exception as e:
        logger.exception("AI Review failed")
        # Fail Open strategy: Try to post a failure comment, but don't crash the CI hard
        # unless it's a critical configuration error.
        _post_error_comment(provider, repo_name, mr_id, e)


def _post_discovery_comment(  # noqa: PLR0913
    provider: GitProvider,
    repo_name: str,
    mr_id: int,
    profile: ProjectProfile,
    *,
    existing_comments: tuple[str, ...] = (),
    language: str | None = None,
    verbose: bool = False,
) -> None:
    """Post discovery summary comment if appropriate.

    Checks whether the comment should be posted (no duplicate, no .reviewbot.md)
    and posts it. Failures are logged and swallowed (fail-open).

    Args:
        provider: Git provider instance.
        repo_name: Repository identifier.
        mr_id: Merge/Pull request number.
        profile: Discovery profile to summarize.
        existing_comments: Bodies of existing bot comments (for duplicate detection).
        language: ISO 639 language code for comment formatting.
        verbose: Always post discovery comment (not just on gaps).
    """
    try:
        if not should_post_discovery_comment(profile, existing_comments, verbose=verbose):
            logger.debug("Discovery comment skipped (duplicate or .reviewbot.md present)")
            return

        comment = format_discovery_comment(profile, verbose=verbose, language=language)
        if comment is None:
            logger.debug("Discovery comment is empty, skipping")
            return
        provider.post_comment(repo_name, mr_id, comment)
        logger.info("Posted discovery comment")
    except Exception:
        logger.warning("Failed to post discovery comment", exc_info=True)


def _run_discovery(
    provider: GitProvider,
    repo_name: str,
    mr_id: int,
    settings: Settings,
) -> ProjectProfile | None:
    """Run the Discovery pipeline, fail-open on any error.

    Args:
        provider: Git provider (triple inheritance: Git + Repository + Conversation).
        repo_name: Repository identifier.
        mr_id: Merge/Pull request number.
        settings: Application settings.

    Returns:
        ProjectProfile if discovery succeeds, None otherwise.
    """
    from ai_reviewer.discovery import DiscoveryOrchestrator  # noqa: PLC0415
    from ai_reviewer.llm.router import create_router  # noqa: PLC0415

    try:
        router = create_router(settings)
        llm = router.create_provider(model=settings.gemini_model)
        # GitHubClient/GitLabClient implement RepositoryProvider + ConversationProvider
        # via triple inheritance, so the cast is safe at runtime.
        discovery = DiscoveryOrchestrator(
            repo_provider=provider,  # type: ignore[arg-type]
            conversation=provider,  # type: ignore[arg-type]
            llm=llm,
        )
        timeout = settings.discovery_timeout
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(discovery.discover, repo_name, mr_id)
            profile = future.result(timeout=timeout)
        tool_count = len(profile.ci_insights.detected_tools) if profile.ci_insights else 0
        logger.info(
            "Discovery: %s project, %d CI tool(s)",
            profile.platform_data.primary_language,
            tool_count,
        )
    except FuturesTimeoutError:
        logger.warning("Discovery timed out after %ds, continuing without profile", timeout)
        return None
    except Exception:
        logger.warning("Discovery failed, continuing without profile", exc_info=True)
        return None
    else:
        return profile


def _post_error_comment(
    provider: GitProvider,
    repo_name: str,
    mr_id: int,
    error: Exception,
) -> None:
    """Attempt to post an error comment to the MR.

    Args:
        provider: Git provider instance.
        repo_name: Repository identifier.
        mr_id: Merge/Pull request number.
        error: The exception that caused the failure.
    """
    try:
        if isinstance(error, AllModelsFailedError) and error.is_quota:
            error_msg = (
                f"## \u26a0\ufe0f {BOT_NAME}: API Quota Exhausted\n\n"
                "All configured Gemini models have exceeded their API quota.\n"
                f"**Details:** `{error!s}`\n\n"
                "**What to do:**\n"
                "- Wait for quota to reset (usually resets daily)\n"
                "- Upgrade your [Gemini API plan](https://ai.google.dev/pricing)\n"
                "- Re-run this workflow once quota is available\n"
            )
        elif isinstance(error, (AllModelsFailedError, QuotaExhaustedError)):
            error_msg = (
                f"## \u26a0\ufe0f {BOT_NAME}: All Models Unavailable\n\n"
                "All configured Gemini models failed (server errors or rate limits).\n"
                f"**Details:** `{error!s}`\n\n"
                "**What to do:**\n"
                "- Check [Gemini API status](https://status.cloud.google.com/)\n"
                "- Re-run this workflow in a few minutes\n"
                "- If the issue persists, check your "
                "[API quota](https://ai.google.dev/pricing)\n"
            )
        else:
            error_msg = (
                f"## \u274c {BOT_NAME}: Review Failed\n\n"
                "The AI reviewer encountered an error while processing this PR.\n"
                f"**Error:** `{error!s}`\n\n"
                "_Please check the CI logs for more details._"
            )
        provider.post_comment(repo_name, mr_id, error_msg)
    except Exception:
        logger.exception("Failed to post error comment")
