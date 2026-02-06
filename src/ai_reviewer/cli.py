"""Command-line interface for AI Code Reviewer.

This module provides the entry point for the application.
It handles automatic detection of CI environments (GitHub Actions, GitLab CI)
and execution of the review process.
"""

from __future__ import annotations

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.logging import RichHandler

from ai_reviewer.core.config import MIN_SECRET_LENGTH, get_settings
from ai_reviewer.integrations.github import GitHubClient
from ai_reviewer.integrations.gitlab import GitLabClient
from ai_reviewer.reviewer import review_pull_request

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
    "GITHUB_TOKEN environment variable not found. Please provide a GitHub personal access token."
)
_ERR_GITHUB_TOKEN_SHORT = f"GITHUB_TOKEN is too short (minimum {MIN_SECRET_LENGTH} characters)."
_ERR_GITLAB_TOKEN_MISSING = (
    "GITLAB_TOKEN environment variable not found. Please provide a GitLab personal access token."
)
_ERR_GITLAB_TOKEN_SHORT = f"GITLAB_TOKEN is too short (minimum {MIN_SECRET_LENGTH} characters)."
_MIN_REF_PARTS = 3


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


@app.command()
def main(  # noqa: PLR0912, PLR0915
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
    """Run AI Code Reviewer.

    Automatically detects CI environment and reviews the current Pull Request.
    Can also be run manually by providing arguments.
    """
    try:
        # 1. Detect Provider
        if not provider:
            provider = detect_provider()
            if provider:
                logger.info("Detected CI Provider: %s", provider.value)
            else:
                # If not detected and not provided, we can't proceed unless
                # arguments are explicitly provided (manual run mode)
                if not (repo and pr):
                    console.print(
                        "[bold red]Error:[/bold red] Could not detect CI environment.\n"
                        "Please specify [bold]--provider[/bold], [bold]--repo[/bold], "
                        "and [bold]--pr[/bold] manually."
                    )
                    _exit_app(code=1)
                # Default to GitHub if manual args provided but no provider?
                # Or force user to specify provider. Let's force provider for clarity.
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
            # We can't use _exit_app here easily because we need to chain the exception
            # or just log and exit.
            # To satisfy TRY301, we could wrap this too, but let's see.
            # Actually, raising from e is good practice.
            # Let's just call _exit_app and log the error before.
            _exit_app(code=1)

        # 3. Execute based on provider
        if provider == Provider.GITHUB:
            # Check for GitHub token
            if not settings.github_token:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITHUB_TOKEN_MISSING}"
                )
                _exit_app(code=1)
            if len(settings.github_token.get_secret_value()) < MIN_SECRET_LENGTH:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITHUB_TOKEN_SHORT}"
                )
                _exit_app(code=1)

            # Auto-detect context if missing
            if not repo or not pr:
                try:
                    detected_repo, detected_pr = extract_github_context()
                    repo = repo or detected_repo
                    pr = pr or detected_pr
                    logger.info("Context extracted: %s PR #%s", repo, pr)
                except ValueError as e:
                    console.print(f"[bold red]Context Error:[/bold red] {e}")
                    _exit_app(code=1)

            # Run Review
            if repo and pr:
                # Create provider instance and run review
                github_provider = GitHubClient(token=settings.github_token.get_secret_value())
                review_pull_request(github_provider, repo, pr, settings)
            else:
                # Should be unreachable due to checks above
                _exit_app(code=1)

        elif provider == Provider.GITLAB:
            # Check for GitLab token
            if not settings.gitlab_token:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITLAB_TOKEN_MISSING}"
                )
                _exit_app(code=1)
            if len(settings.gitlab_token.get_secret_value()) < MIN_SECRET_LENGTH:
                console.print(
                    f"[bold red]Configuration Error:[/bold red] {_ERR_GITLAB_TOKEN_SHORT}"
                )
                _exit_app(code=1)

            # Auto-detect context if missing
            if not repo or not pr:
                try:
                    detected_repo, detected_mr = extract_gitlab_context()
                    repo = repo or detected_repo
                    pr = pr or detected_mr
                    logger.info("Context extracted: %s MR !%s", repo, pr)
                except ValueError as e:
                    console.print(f"[bold red]Context Error:[/bold red] {e}")
                    _exit_app(code=1)

            # Run Review
            if repo and pr:
                # Create provider instance and run review
                gitlab_provider = GitLabClient(
                    token=settings.gitlab_token.get_secret_value(),
                    url=settings.gitlab_url,
                )
                review_pull_request(gitlab_provider, repo, pr, settings)
            else:
                # Should be unreachable due to checks above
                _exit_app(code=1)

    except typer.Exit:
        # Re-raise typer.Exit to not catch it in the general exception handler
        raise
    except Exception:
        logger.exception("Unexpected error")
        _exit_app(code=1)


if __name__ == "__main__":
    app()
