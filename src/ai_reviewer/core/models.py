"""Core data models for AI Code Reviewer.

This module defines Pydantic models for representing merge requests,
linked tasks, review context, and review results.

All datetime fields must be timezone-aware (have tzinfo set).
All models are frozen (immutable) to prevent accidental mutations.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - required at runtime for Pydantic
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from ai_reviewer.discovery.models import ProjectProfile


def _validate_timezone_aware(v: datetime | None, field_name: str) -> datetime | None:
    """Validate that datetime is timezone-aware.

    Args:
        v: The datetime value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated datetime value.

    Raises:
        ValueError: If datetime is naive (no timezone info).
    """
    if v is not None and v.tzinfo is None:
        msg = f"{field_name} must be timezone-aware (e.g., use datetime.now(timezone.utc))"
        raise ValueError(msg)
    return v


class CommentAuthorType(str, Enum):
    """Type of comment author."""

    USER = "user"
    BOT = "bot"


class CommentType(str, Enum):
    """Type of comment (general issue comment or code review comment)."""

    ISSUE = "issue"
    REVIEW = "review"


class FileChangeType(str, Enum):
    """Type of file change in a merge request."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class Comment(BaseModel):
    """A comment on a merge request.

    Attributes:
        author: The username of the comment author.
        author_type: Whether the author is a user or bot.
        body: The content of the comment.
        type: The type of comment (issue or review).
        created_at: When the comment was created (must be timezone-aware).
        file_path: File path for inline comments (None for general comments).
        line_number: Line number for inline comments (None for general comments).
        comment_id: Platform-specific comment ID (str for portability).
        parent_comment_id: ID of the parent comment for threading.
        thread_id: Thread/discussion ID grouping related comments.
    """

    model_config = ConfigDict(frozen=True)

    author: str = Field(..., min_length=1, description="Username of the comment author")
    author_type: CommentAuthorType = Field(
        default=CommentAuthorType.USER, description="Type of author (user or bot)"
    )
    body: str = Field(..., description="Content of the comment")
    type: CommentType = Field(..., description="Type of comment (issue or review)")
    created_at: datetime | None = Field(default=None, description="When the comment was created")
    file_path: str | None = Field(default=None, description="File path for inline comments")
    line_number: int | None = Field(
        default=None, ge=1, description="Line number for inline comments"
    )
    comment_id: str | None = Field(default=None, description="Platform-specific comment ID")
    parent_comment_id: str | None = Field(
        default=None, description="ID of the parent comment (for threading)"
    )
    thread_id: str | None = Field(
        default=None, description="Thread/discussion ID grouping related comments"
    )

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone(cls, v: datetime | None) -> datetime | None:
        """Ensure created_at is timezone-aware."""
        return _validate_timezone_aware(v, "created_at")


class FileChange(BaseModel):
    """A file change in a merge request.

    Attributes:
        filename: Path to the changed file.
        change_type: Type of change (added, modified, deleted, renamed).
        additions: Number of lines added.
        deletions: Number of lines deleted.
        patch: The diff patch content (may be None for binary files).
        previous_filename: Previous filename if renamed.
    """

    model_config = ConfigDict(frozen=True)

    filename: str = Field(..., min_length=1, description="Path to the changed file")
    change_type: FileChangeType = Field(..., description="Type of change")
    additions: int = Field(default=0, ge=0, description="Number of lines added")
    deletions: int = Field(default=0, ge=0, description="Number of lines deleted")
    patch: str | None = Field(default=None, description="Diff patch content")
    previous_filename: str | None = Field(default=None, description="Previous filename if renamed")

    @field_validator("previous_filename")
    @classmethod
    def validate_previous_filename(cls, v: str | None) -> str | None:
        """Validate that empty previous_filename is converted to None."""
        if v is not None and v.strip() == "":
            return None
        return v


class MergeRequest(BaseModel):
    """A merge request (pull request) to be reviewed.

    Attributes:
        number: The MR/PR number.
        title: Title of the merge request.
        description: Body/description of the merge request.
        author: Username of the MR author.
        source_branch: The branch being merged from.
        target_branch: The branch being merged into.
        comments: List of comments on the MR.
        changes: List of file changes in the MR.
        url: URL to the merge request.
        created_at: When the MR was created (must be timezone-aware).
        updated_at: When the MR was last updated (must be timezone-aware).
    """

    model_config = ConfigDict(frozen=True)

    number: int = Field(..., gt=0, description="MR/PR number")
    title: str = Field(..., min_length=1, description="Title of the merge request")
    description: str = Field(default="", description="Body/description of the merge request")
    author: str = Field(..., min_length=1, description="Username of the MR author")
    source_branch: str = Field(..., min_length=1, description="Branch being merged from")
    target_branch: str = Field(..., min_length=1, description="Branch being merged into")
    comments: tuple[Comment, ...] = Field(default=(), description="Comments on the MR")
    changes: tuple[FileChange, ...] = Field(default=(), description="File changes in the MR")
    url: str | None = Field(default=None, description="URL to the merge request")
    created_at: datetime | None = Field(default=None, description="When the MR was created")
    updated_at: datetime | None = Field(default=None, description="When the MR was last updated")

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_datetime_timezone(cls, v: datetime | None) -> datetime | None:
        """Ensure datetime fields are timezone-aware."""
        return _validate_timezone_aware(v, "created_at/updated_at")

    @property
    def total_additions(self) -> int:
        """Calculate total lines added across all file changes."""
        return sum(change.additions for change in self.changes)

    @property
    def total_deletions(self) -> int:
        """Calculate total lines deleted across all file changes."""
        return sum(change.deletions for change in self.changes)

    @property
    def files_changed(self) -> int:
        """Get the number of files changed."""
        return len(self.changes)


class LinkedTask(BaseModel):
    """A task/issue linked to a merge request.

    Attributes:
        identifier: The task identifier (e.g., issue number or external ID).
        title: Title of the task.
        description: Description/body of the task.
        url: URL to the task (optional).
    """

    model_config = ConfigDict(frozen=True)

    identifier: str = Field(..., min_length=1, description="Task identifier")
    title: str = Field(..., min_length=1, description="Title of the task")
    description: str = Field(default="", description="Description of the task")
    url: str | None = Field(default=None, description="URL to the task")


class ReviewContext(BaseModel):
    """Context for performing a code review.

    Combines the merge request data with linked tasks
    and optional project profile to provide full context for the AI reviewer.

    Attributes:
        mr: The merge request to review.
        tasks: Linked tasks discovered via all strategies.
        repository: Repository name in owner/repo format.
        project_profile: Discovery profile for project context.
    """

    model_config = ConfigDict(frozen=True)

    mr: MergeRequest = Field(..., description="The merge request to review")
    tasks: tuple[LinkedTask, ...] = Field(default=(), description="Linked tasks")
    repository: str = Field(..., min_length=1, description="Repository name (owner/repo)")
    project_profile: ProjectProfile | None = Field(
        default=None, description="Discovery profile for project context"
    )

    @field_validator("repository")
    @classmethod
    def validate_repository_format(cls, v: str) -> str:
        """Validate repository is in owner/repo or namespace/subgroup/.../repo format."""
        _min_segments = 2
        parts = v.split("/")
        if len(parts) < _min_segments or not all(parts):
            msg = "Repository must be in 'owner/repo' format (nested namespaces allowed)"
            raise ValueError(msg)
        return v

    @property
    def has_linked_tasks(self) -> bool:
        """Check if any tasks are linked to this review context."""
        return bool(self.tasks)


class IssueSeverity(str, Enum):
    """Severity level of a code issue.

    CRITICAL: Must fix - security vulnerabilities, breaking changes.
    WARNING: Should fix - code quality, potential bugs.
    INFO: Suggestion - educational, minor improvements.
    """

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    """Category of a code issue."""

    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    TESTING = "testing"


class CodeIssue(BaseModel):
    """A code issue found during review.

    Unified model for all types of issues (security, quality, etc.)
    with support for inline suggestions and educational content.

    Attributes:
        category: The category of the issue.
        severity: How critical the issue is.
        title: Short title of the issue.
        description: Detailed description of the issue.
        file_path: File where the issue was found.
        line_number: Line number where the issue was found.
        existing_code: The problematic code snippet (for Before/After).
        proposed_code: Suggested replacement code (for Apply Suggestion).
        why_matters: Educational explanation of why this matters.
        learn_more_url: URL to documentation or resources.
    """

    model_config = ConfigDict(frozen=True)

    category: IssueCategory = Field(..., description="Category of the issue")
    severity: IssueSeverity = Field(..., description="Severity level")
    title: str = Field(..., min_length=1, description="Short title of the issue")
    description: str = Field(..., min_length=1, description="Detailed description")
    file_path: str | None = Field(default=None, description="File where found")
    line_number: int | None = Field(default=None, ge=1, description="Line number")
    existing_code: str | None = Field(default=None, description="Problematic code snippet")
    proposed_code: str | None = Field(default=None, description="Suggested replacement code")
    why_matters: str | None = Field(default=None, description="Educational explanation")
    learn_more_url: str | None = Field(default=None, description="URL to learn more")

    @property
    def has_suggestion(self) -> bool:
        """Check if this issue has a code suggestion."""
        return self.proposed_code is not None

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical issue."""
        return self.severity == IssueSeverity.CRITICAL

    @property
    def is_security(self) -> bool:
        """Check if this is a security issue."""
        return self.category == IssueCategory.SECURITY


class GoodPractice(BaseModel):
    """A good practice noticed during review.

    Used to provide positive feedback and motivation to developers.

    Attributes:
        description: What was done well.
        file_path: File where the good practice was found.
        line_number: Line number (optional).
    """

    model_config = ConfigDict(frozen=True)

    description: str = Field(..., min_length=1, description="What was done well")
    file_path: str | None = Field(default=None, description="File where found")
    line_number: int | None = Field(default=None, ge=1, description="Line number")


class TaskAlignmentStatus(str, Enum):
    """Status of task alignment check."""

    ALIGNED = "aligned"
    MISALIGNED = "misaligned"
    INSUFFICIENT_DATA = "insufficient_data"


# Formatting thresholds for metrics display
_COST_PRECISION_THRESHOLD = 0.01  # Below this, show 4 decimal places
_LATENCY_MS_THRESHOLD = 1000  # Above this, show in seconds


class ReviewMetrics(BaseModel):
    """Metrics collected during the review process.

    Captures token usage, timing, and cost estimation for observability.

    Attributes:
        model_name: The AI model used for the review.
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens used (prompt + completion).
        api_latency_ms: API call latency in milliseconds.
        estimated_cost_usd: Estimated cost in USD based on current pricing.
    """

    model_config = ConfigDict(frozen=True)

    model_name: str = Field(..., min_length=1, description="AI model used")
    operator: str | None = Field(default=None, description="LLM operator (e.g. Google, Anthropic)")
    prompt_tokens: int = Field(default=0, ge=0, description="Tokens in prompt")
    completion_tokens: int = Field(default=0, ge=0, description="Tokens in completion")
    total_tokens: int = Field(default=0, ge=0, description="Total tokens used")
    api_latency_ms: int = Field(default=0, ge=0, description="API latency in milliseconds")
    estimated_cost_usd: float = Field(default=0.0, ge=0.0, description="Estimated cost in USD")
    fallback_reason: str | None = Field(
        default=None,
        description="Why fallback model was used (None = primary succeeded)",
    )

    @property
    def cost_formatted(self) -> str:
        """Format cost as a human-readable string."""
        if self.estimated_cost_usd < _COST_PRECISION_THRESHOLD:
            return f"${self.estimated_cost_usd:.4f}"
        return f"${self.estimated_cost_usd:.2f}"

    @property
    def latency_formatted(self) -> str:
        """Format latency as a human-readable string."""
        if self.api_latency_ms < _LATENCY_MS_THRESHOLD:
            return f"{self.api_latency_ms}ms"
        seconds = self.api_latency_ms / _LATENCY_MS_THRESHOLD
        return f"{seconds:.1f}s"


class ReviewResult(BaseModel):
    """Result of an AI code review.

    Attributes:
        issues: List of code issues found during review.
        good_practices: List of good practices noticed.
        task_alignment: Whether code changes align with the linked task.
        task_alignment_reasoning: Explanation of task alignment assessment.
        summary: Brief summary of the review.
        detected_language: ISO 639 language code detected/used for the review.
        reviewed_at: When the review was performed (must be timezone-aware).
        metrics: Performance metrics from the review process.
    """

    model_config = ConfigDict(frozen=True)

    issues: tuple[CodeIssue, ...] = Field(default=(), description="Code issues found")
    good_practices: tuple[GoodPractice, ...] = Field(
        default=(), description="Good practices noticed"
    )
    task_alignment: TaskAlignmentStatus = Field(
        default=TaskAlignmentStatus.INSUFFICIENT_DATA,
        description="Task alignment status",
    )
    task_alignment_reasoning: str = Field(
        default="", description="Explanation of task alignment assessment"
    )
    summary: str = Field(default="", description="Brief summary of the review")
    code_summary: str = Field(
        default="",
        description="Compressed summary of code changes for cross-referencing test review",
    )
    detected_language: str = Field(
        default="en", description="ISO 639 language code used for the review"
    )
    reviewed_at: datetime | None = Field(default=None, description="When the review was performed")
    metrics: ReviewMetrics | None = Field(
        default=None, description="Performance metrics from the review"
    )

    @field_validator("reviewed_at")
    @classmethod
    def validate_reviewed_at_timezone(cls, v: datetime | None) -> datetime | None:
        """Ensure reviewed_at is timezone-aware."""
        return _validate_timezone_aware(v, "reviewed_at")

    @property
    def has_critical_issues(self) -> bool:
        """Check if any critical issues were found."""
        return any(issue.is_critical for issue in self.issues)

    @property
    def has_security_issues(self) -> bool:
        """Check if any security issues were found."""
        return any(issue.is_security for issue in self.issues)

    @property
    def critical_count(self) -> int:
        """Get number of critical issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL)

    @property
    def warning_count(self) -> int:
        """Get number of warning issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Get number of info/suggestion issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.INFO)

    @property
    def issue_count(self) -> int:
        """Get total number of issues."""
        return len(self.issues)

    @property
    def good_practice_count(self) -> int:
        """Get total number of good practices."""
        return len(self.good_practices)

    @property
    def matches_task(self) -> bool | None:
        """Check if code changes match the linked task.

        This is a tri-state property for task alignment assessment:

        Returns:
            True: Task and code changes are aligned.
            False: Code changes contradict or don't match the task.
            None: Insufficient context to determine alignment
                  (e.g., no linked task, unclear task description).
        """
        if self.task_alignment == TaskAlignmentStatus.ALIGNED:
            return True
        if self.task_alignment == TaskAlignmentStatus.MISALIGNED:
            return False
        return None


# Deferred model rebuild — resolves forward reference to ProjectProfile
# which cannot be imported at module level due to circular dependency:
# core.models → discovery.models → discovery.__init__ → orchestrator → conversation → core.models
def _rebuild_models() -> None:
    """Rebuild ReviewContext to resolve forward references."""
    from ai_reviewer.discovery.models import ProjectProfile  # noqa: PLC0415

    ReviewContext.model_rebuild(_types_namespace={"ProjectProfile": ProjectProfile})


_rebuild_models()
del _rebuild_models  # keep module namespace clean


# Public API - explicitly define what should be imported from this module
__all__ = [
    "CodeIssue",
    "Comment",
    "CommentAuthorType",
    "CommentType",
    "FileChange",
    "FileChangeType",
    "GoodPractice",
    "IssueCategory",
    "IssueSeverity",
    "LinkedTask",
    "MergeRequest",
    "ReviewContext",
    "ReviewMetrics",
    "ReviewResult",
    "TaskAlignmentStatus",
]
