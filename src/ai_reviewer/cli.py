"""Command-line interface for AI Code Reviewer.

This module provides the entry point for the application.
It handles automatic detection of CI environments (GitHub Actions, GitLab CI)
and execution of the review process.

Commands:
    ai-review              Run a review (default, backward-compatible).
    ai-review discover     Discover project context without creating an MR.
"""

from __future__ import annotations

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, NoReturn

import typer
from rich.console import Console
from rich.logging import RichHandler

from ai_reviewer.core.config import MIN_SECRET_LENGTH, get_settings
from ai_reviewer.integrations.github import GitHubClient
from ai_reviewer.integrations.gitlab import GitLabClient
from ai_reviewer.reviewer import review_pull_request

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.discovery.models import AttentionZone, ProjectProfile

# Configure rich logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger("ai_reviewer")
console = Console()
app = typer.Typer(add_completion=False)

# Constants for error messages
_ERR_REPO_NOT_FOUND = "GITHUB_REPOSITORY environment variable not found."
_ERR_CONTEXT_NOT_FOUND = (
    "Could not determine PR number from GitHub Actions context. "
    "Ensure this workflow runs on 'pull_request' events."
)
_ERR_GITLAB_PROJECT_NOT_FOUND = "CI_PROJECT_PATH environment variable not found."
_ERR_GITLAB_MR_NOT_FOUND = (
    "Could not determine MR number from GitLab CI context. "
    "Ensure this job runs on merge request pipelines."
)
_ERR_GITHUB_TOKEN_MISSING = (
    "AI_REVIEWER_GITHUB_TOKEN (or GITHUB_TOKEN) environment variable not found. "
    "Please provide a GitHub personal access token."
)
_ERR_GITHUB_TOKEN_SHORT = (
    f"AI_REVIEWER_GITHUB_TOKEN (or GITHUB_TOKEN) is too short "
    f"(minimum {MIN_SECRET_LENGTH} characters)."
)
_ERR_GITLAB_TOKEN_MISSING = (
    "AI_REVIEWER_GITLAB_TOKEN (or GITLAB_TOKEN) environment variable not found. "
    "Please provide a GitLab personal access token."
)
_ERR_GITLAB_TOKEN_SHORT = (
    f"AI_REVIEWER_GITLAB_TOKEN (or GITLAB_TOKEN) is too short "
    f"(minimum {MIN_SECRET_LENGTH} characters)."
)
_MIN_REF_PARTS = 3

# Status emoji for attention zones
_STATUS_EMOJI = {
    "well_covered": "\u2705",
    "weakly_covered": "\u26a0\ufe0f",
    "not_covered": "\u274c",
}


class Provider(str, Enum):
    """Supported CI/CD providers."""

    GITHUB = "github"
    GITLAB = "gitlab"


def detect_provider() -> Provider | None:
    """Detect the CI provider from environment variables.

    Returns:
        Provider enum if detected, None otherwise.
    """
    if os.getenv("GITHUB_ACTIONS") == "true":
        return Provider.GITHUB
    if os.getenv("GITLAB_CI") == "true":
        return Provider.GITLAB
    return None


def extract_github_context() -> tuple[str, int]:
    """Extract repository and PR number from GitHub Actions environment.

    Returns:
        Tuple of (repo_name, pr_number).

    Raises:
        ValueError: If context cannot be extracted.
    """
    # 1. Get Repository
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        raise ValueError(_ERR_REPO_NOT_FOUND)

    # 2. Get PR Number
    # Try getting it from the event payload (most reliable for PR events)
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path:
        try:
            with Path(event_path).open() as f:
                event_data = json.load(f)
                # For pull_request events
                if "pull_request" in event_data:
                    return repo, event_data["pull_request"]["number"]
                # For issue_comment events (if we support triggering by comment)
                if "issue" in event_data and "pull_request" in event_data["issue"]:
                    return repo, event_data["issue"]["number"]
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to read GITHUB_EVENT_PATH: %s", e)

    # Fallback: Try parsing GITHUB_REF (refs/pull/123/merge)
    # This is less reliable as it might not be available in all contexts
    ref = os.getenv("GITHUB_REF", "")
    if "refs/pull/" in ref:
        try:
            # refs/pull/123/merge -> 123
            parts = ref.split("/")
            if len(parts) >= _MIN_REF_PARTS:
                return repo, int(parts[2])
        except ValueError:
            pass

    raise ValueError(_ERR_CONTEXT_NOT_FOUND)


def extract_gitlab_context() -> tuple[str, int]:
    """Extract project path and MR number from GitLab CI environment.

    Returns:
        Tuple of (project_path, mr_iid).

    Raises:
        ValueError: If context cannot be extracted.
    """
    # 1. Get Project Path
    project = os.getenv("CI_PROJECT_PATH")
    if not project:
        raise ValueError(_ERR_GITLAB_PROJECT_NOT_FOUND)

    # 2. Get MR IID (project-level ID)
    # CI_MERGE_REQUEST_IID is available in merge request pipelines
    mr_iid = os.getenv("CI_MERGE_REQUEST_IID")
    if mr_iid:
        try:
            return project, int(mr_iid)
        except ValueError:
            pass

    raise ValueError(_ERR_GITLAB_MR_NOT_FOUND)


def _exit_app(code: int = 0) -> NoReturn:
    """Exit the application with the given status code.

    This helper satisfies linter rules about abstracting raises.
    """
    raise typer.Exit(code=code)


def _create_provider_client(
    provider: Provider,
    settings: Settings,
) -> GitHubClient | GitLabClient:
    """Create provider client, validating token presence and length.

    Args:
        provider: Target provider.
        settings: Application settings.

    Returns:
        Configured provider client.

    Raises:
        typer.Exit: If token is missing or too short.
    """
    if provider == Provider.GITHUB:
        if not settings.github_token:
            console.print(f"[bold red]Configuration Error:[/bold red] {_ERR_GITHUB_TOKEN_MISSING}")
            _exit_app(code=1)
        if len(settings.github_token.get_secret_value()) < MIN_SECRET_LENGTH:
            console.print(f"[bold red]Configuration Error:[/bold red] {_ERR_GITHUB_TOKEN_SHORT}")
            _exit_app(code=1)
        return GitHubClient(token=settings.github_token.get_secret_value())

    # GitLab
    if not settings.gitlab_token:
        console.print(f"[bold red]Configuration Error:[/bold red] {_ERR_GITLAB_TOKEN_MISSING}")
        _exit_app(code=1)
    if len(settings.gitlab_token.get_secret_value()) < MIN_SECRET_LENGTH:
        console.print(f"[bold red]Configuration Error:[/bold red] {_ERR_GITLAB_TOKEN_SHORT}")
        _exit_app(code=1)
    return GitLabClient(
        token=settings.gitlab_token.get_secret_value(),
        url=settings.gitlab_url,
    )


# ── Review command (default / backward-compatible) ──────────────────


@app.callback(invoke_without_command=True)
def main(  # noqa: PLR0912, PLR0915
    ctx: typer.Context,
    provider: Annotated[
        Provider | None,
        typer.Option(
            "--provider",
            "-p",
            help="CI provider (auto-detected if not provided)",
        ),
    ] = None,
    repo: Annotated[
        str | None,
        typer.Option(
            "--repo",
            "-r",
            help="Repository name (e.g. owner/repo). Auto-detected in CI.",
        ),
    ] = None,
    pr: Annotated[
        int | None,
        typer.Option(
            "--pr",
            help="Pull Request number. Auto-detected in CI.",
        ),
    ] = None,
) -> None:
    """AI Code Reviewer — automated code review for pull requests.

    When invoked without a subcommand, runs a review (backward-compatible).
    Use 'ai-review discover' for standalone project discovery.
    """
    # If a subcommand was invoked, skip the default review logic
    if ctx.invoked_subcommand is not None:
        return

    try:
        # 1. Detect Provider
        if not provider:
            provider = detect_provider()
            if provider:
                logger.info("Detected CI Provider: %s", provider.value)
            else:
                if not (repo and pr):
                    console.print(
                        "[bold red]Error:[/bold red] Could not detect CI environment.\n"
                        "Please specify [bold]--provider[/bold], [bold]--repo[/bold], "
                        "and [bold]--pr[/bold] manually."
                    )
                    _exit_app(code=1)
                console.print(
                    "[bold red]Error:[/bold red] Provider not specified and not detected. "
                    "Please use [bold]--provider github[/bold]."
                )
                _exit_app(code=1)

        # 2. Load Configuration
        try:
            settings = get_settings()
        except Exception as e:
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            _exit_app(code=1)

        # 3. Execute based on provider
        if provider == Provider.GITHUB:
            if not settings.github_token:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITHUB_TOKEN_MISSING}"
                )
                _exit_app(code=1)
            elif len(settings.github_token.get_secret_value()) < MIN_SECRET_LENGTH:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITHUB_TOKEN_SHORT}"
                )
                _exit_app(code=1)

            if not repo or not pr:
                try:
                    detected_repo, detected_pr = extract_github_context()
                    repo = repo or detected_repo
                    pr = pr or detected_pr
                    logger.info("Context extracted: %s PR #%s", repo, pr)
                except ValueError as e:
                    console.print(f"[bold red]Context Error:[/bold red] {e}")
                    _exit_app(code=1)

            if repo and pr:
                github_provider = GitHubClient(token=settings.github_token.get_secret_value())
                review_pull_request(github_provider, repo, pr, settings)
            else:
                _exit_app(code=1)

        elif provider == Provider.GITLAB:
            if not settings.gitlab_token:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITLAB_TOKEN_MISSING}"
                )
                _exit_app(code=1)
            elif len(settings.gitlab_token.get_secret_value()) < MIN_SECRET_LENGTH:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITLAB_TOKEN_SHORT}"
                )
                _exit_app(code=1)

            if not repo or not pr:
                try:
                    detected_repo, detected_mr = extract_gitlab_context()
                    repo = repo or detected_repo
                    pr = pr or detected_mr
                    logger.info("Context extracted: %s MR !%s", repo, pr)
                except ValueError as e:
                    console.print(f"[bold red]Context Error:[/bold red] {e}")
                    _exit_app(code=1)

            if repo and pr:
                gitlab_provider = GitLabClient(
                    token=settings.gitlab_token.get_secret_value(),
                    url=settings.gitlab_url,
                )
                review_pull_request(gitlab_provider, repo, pr, settings)
            else:
                _exit_app(code=1)

    except typer.Exit:
        raise
    except Exception:
        logger.exception("Unexpected error")
        _exit_app(code=1)


# ── Discover command ────────────────────────────────────────────────


@app.command()
def discover(
    repo: Annotated[
        str,
        typer.Argument(help="Repository (owner/repo)"),
    ],
    provider: Annotated[
        Provider,
        typer.Option(
            "--provider",
            "-p",
            help="Git provider",
        ),
    ] = Provider.GITHUB,
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output as JSON",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show all details (conventions, CI tools, watch-files)",
        ),
    ] = False,
) -> None:
    """Discover project context without creating a review."""
    from ai_reviewer.discovery import DiscoveryOrchestrator  # noqa: PLC0415
    from ai_reviewer.llm.router import create_router  # noqa: PLC0415

    try:
        settings = get_settings()
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        _exit_app(code=1)

    try:
        client = _create_provider_client(provider, settings)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Provider Error:[/bold red] {e}")
        _exit_app(code=1)

    console.print("[bold]\U0001f50d Discovering project context...[/bold]\n")

    try:
        router = create_router(settings)
        llm = router.create_provider(model=settings.gemini_model)
        orchestrator = DiscoveryOrchestrator(
            repo_provider=client,
            conversation=client,
            llm=llm,
        )
        profile = orchestrator.discover(repo)
    except Exception as e:
        console.print(f"[bold red]Discovery Error:[/bold red] {e}")
        _exit_app(code=1)

    if output_json:
        console.print(profile.model_dump_json(indent=2))
    else:
        console.print(_format_discovery_output(profile, verbose=verbose))


# ── CLI output formatter ────────────────────────────────────────────


def _format_zone_line(zone: AttentionZone) -> str:
    """Format a single attention zone as a CLI line."""
    emoji = _STATUS_EMOJI.get(zone.status, "\u2022")
    tools_str = f" ({', '.join(zone.tools)})" if zone.tools else ""
    line = f"  {emoji} {zone.area}{tools_str}"
    if zone.reason:
        line += f" \u2014 {zone.reason}"
    return line


def _format_stack_section(profile: ProjectProfile) -> list[str]:
    """Format the stack/profile header section."""
    lines: list[str] = ["\U0001f4cb Project Profile:"]
    pd = profile.platform_data
    stack = f"  Stack: {pd.primary_language}"
    if profile.framework:
        stack += f" ({profile.framework})"
    if profile.language_version:
        stack += f" {profile.language_version}"
    lines.append(stack)
    if profile.package_manager:
        lines.append(f"  Package manager: {profile.package_manager}")
    if profile.layout:
        lines.append(f"  Layout: {profile.layout}")
    return lines


def _format_zones_section(profile: ProjectProfile) -> list[str]:
    """Format attention zones or fallback guidance."""
    lines: list[str] = []
    if profile.attention_zones:
        lines.append("")
        lines.append("\U0001f527 Attention Zones:")
        for zone in profile.attention_zones:
            lines.append(_format_zone_line(zone))
            if zone.recommendation:
                lines.append(f"     \U0001f4a1 {zone.recommendation}")
    else:
        g = profile.guidance
        if g.skip_in_review:
            lines.append(f"\n  Skip: {'; '.join(g.skip_in_review)}")
        if g.focus_in_review:
            lines.append(f"\n  Focus: {'; '.join(g.focus_in_review)}")
    return lines


def _format_verbose_sections(profile: ProjectProfile) -> list[str]:
    """Format verbose-only sections (CI tools, conventions)."""
    lines: list[str] = []
    if profile.ci_insights and profile.ci_insights.detected_tools:
        lines.append("")
        lines.append("\u2699\ufe0f  CI Tools:")
        for tool in profile.ci_insights.detected_tools:
            lines.append(f"  \u2022 {tool.name} [{tool.category}]")
    if profile.guidance.conventions:
        lines.append("")
        lines.append("\U0001f4dd Conventions:")
        for c in profile.guidance.conventions:
            lines.append(f"  {c}")
    return lines


def _format_discovery_output(profile: ProjectProfile, *, verbose: bool = False) -> str:
    """Format ProjectProfile as human-friendly CLI output.

    Args:
        profile: Discovery result.
        verbose: Show additional details (conventions, CI tools, watch-files).

    Returns:
        Multi-line string with emoji-rich formatting.
    """
    lines = _format_stack_section(profile)
    lines.extend(_format_zones_section(profile))

    if verbose:
        lines.extend(_format_verbose_sections(profile))

    if profile.gaps:
        lines.append("")
        lines.append("\u2753 Knowledge Gaps:")
        for gap in profile.gaps:
            lines.append(f"  \u2022 {gap.observation}")

    lines.append("")
    lines.append("\U0001f4a1 Create .reviewbot.md to customize review behavior.")
    return "\n".join(lines)


if __name__ == "__main__":
    app()
