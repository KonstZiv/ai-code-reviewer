"""Unit tests for CLI module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from ai_reviewer.cli import (
    Provider,
    _format_discovery_output,
    app,
    detect_provider,
    extract_github_context,
)
from ai_reviewer.core.config import clear_settings_cache
from ai_reviewer.discovery.models import AttentionZone, Gap
from tests.helpers import make_profile

runner = CliRunner()


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Clear settings cache before each test."""
    clear_settings_cache()


class TestProvider:
    """Tests for Provider enum."""

    def test_provider_values(self) -> None:
        """Test Provider enum values."""
        assert Provider.GITHUB.value == "github"
        assert Provider.GITLAB.value == "gitlab"

    def test_provider_is_string_enum(self) -> None:
        """Test that Provider is a string enum."""
        assert isinstance(Provider.GITHUB, str)
        assert Provider.GITHUB == "github"


class TestDetectProvider:
    """Tests for detect_provider function."""

    def test_detect_github_from_env(self) -> None:
        """Test GitHub detection from GITHUB_ACTIONS env var."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            result = detect_provider()
            assert result == Provider.GITHUB

    def test_detect_gitlab_from_env(self) -> None:
        """Test GitLab detection from GITLAB_CI env var."""
        with patch.dict(os.environ, {"GITLAB_CI": "true"}, clear=True):
            result = detect_provider()
            assert result == Provider.GITLAB

    def test_detect_no_provider(self) -> None:
        """Test no provider detected when env vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = detect_provider()
            assert result is None

    def test_github_takes_precedence_over_gitlab(self) -> None:
        """Test that GitHub is detected first if both env vars are set."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITLAB_CI": "true"}, clear=True):
            result = detect_provider()
            assert result == Provider.GITHUB

    def test_github_actions_false_not_detected(self) -> None:
        """Test that GITHUB_ACTIONS=false is not detected as GitHub."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}, clear=True):
            result = detect_provider()
            assert result is None

    def test_gitlab_ci_false_not_detected(self) -> None:
        """Test that GITLAB_CI=false is not detected as GitLab."""
        with patch.dict(os.environ, {"GITLAB_CI": "false"}, clear=True):
            result = detect_provider()
            assert result is None


class TestExtractGithubContext:
    """Tests for extract_github_context function."""

    def test_extract_from_event_path_pull_request(self) -> None:
        """Test extracting context from GITHUB_EVENT_PATH for pull_request event."""
        event_data = {"pull_request": {"number": 42}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            event_path = f.name

        try:
            env = {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_EVENT_PATH": event_path,
            }
            with patch.dict(os.environ, env, clear=True):
                repo, pr_number = extract_github_context()
                assert repo == "owner/repo"
                assert pr_number == 42
        finally:
            Path(event_path).unlink()

    def test_extract_from_event_path_issue_comment(self) -> None:
        """Test extracting context from GITHUB_EVENT_PATH for issue_comment event."""
        event_data = {"issue": {"number": 123, "pull_request": {}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            event_path = f.name

        try:
            env = {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_EVENT_PATH": event_path,
            }
            with patch.dict(os.environ, env, clear=True):
                repo, pr_number = extract_github_context()
                assert repo == "owner/repo"
                assert pr_number == 123
        finally:
            Path(event_path).unlink()

    def test_extract_from_github_ref_fallback(self) -> None:
        """Test fallback to GITHUB_REF when event path doesn't have PR info."""
        event_data = {"action": "push"}  # No pull_request key

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            event_path = f.name

        try:
            env = {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_EVENT_PATH": event_path,
                "GITHUB_REF": "refs/pull/99/merge",
            }
            with patch.dict(os.environ, env, clear=True):
                repo, pr_number = extract_github_context()
                assert repo == "owner/repo"
                assert pr_number == 99
        finally:
            Path(event_path).unlink()

    def test_extract_from_github_ref_only(self) -> None:
        """Test extraction using only GITHUB_REF without event file."""
        env = {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_REF": "refs/pull/55/merge",
        }
        with patch.dict(os.environ, env, clear=True):
            repo, pr_number = extract_github_context()
            assert repo == "owner/repo"
            assert pr_number == 55

    def test_missing_repository_raises_error(self) -> None:
        """Test that missing GITHUB_REPOSITORY raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GITHUB_REPOSITORY"):
                extract_github_context()

    def test_missing_pr_context_raises_error(self) -> None:
        """Test that missing PR context raises ValueError."""
        env = {
            "GITHUB_REPOSITORY": "owner/repo",
            # No GITHUB_EVENT_PATH, no GITHUB_REF
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Could not determine PR number"):
                extract_github_context()

    def test_invalid_github_ref_format(self) -> None:
        """Test that invalid GITHUB_REF format raises ValueError."""
        env = {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_REF": "refs/heads/main",  # Not a PR ref
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Could not determine PR number"):
                extract_github_context()

    def test_malformed_event_file_uses_fallback(self) -> None:
        """Test that malformed event file falls back to GITHUB_REF."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            event_path = f.name

        try:
            env = {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_EVENT_PATH": event_path,
                "GITHUB_REF": "refs/pull/77/merge",
            }
            with patch.dict(os.environ, env, clear=True):
                repo, pr_number = extract_github_context()
                assert repo == "owner/repo"
                assert pr_number == 77
        finally:
            Path(event_path).unlink()


class TestCliApp:
    """Tests for CLI app commands."""

    def test_cli_help(self) -> None:
        """Test that --help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AI Code Reviewer" in result.stdout or "review" in result.stdout.lower()

    def test_cli_no_provider_no_args_fails(self) -> None:
        """Test that CLI fails when no provider detected and no args provided."""
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, [])
            assert result.exit_code != 0

    def test_cli_with_provider_github_no_context_fails(self) -> None:
        """Test that CLI fails when GitHub provider but no PR context."""
        env = {
            "GITHUB_ACTIONS": "true",
            # No GITHUB_REPOSITORY or GITHUB_REF
        }
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, [])
            assert result.exit_code != 0

    @patch("ai_reviewer.cli.review_pull_request")
    @patch("ai_reviewer.cli.GitLabClient")
    @patch("ai_reviewer.cli.get_settings")
    def test_cli_successful_gitlab_review(
        self,
        mock_get_settings: MagicMock,
        mock_gitlab_client: MagicMock,
        mock_review: MagicMock,
    ) -> None:
        """Test successful GitLab review execution."""
        mock_settings = MagicMock()
        mock_settings.gitlab_token.get_secret_value.return_value = "glpat-test-token"
        mock_settings.gitlab_url = "https://gitlab.com"
        mock_get_settings.return_value = mock_settings

        mock_provider = MagicMock()
        mock_gitlab_client.return_value = mock_provider

        env = {
            "GITLAB_CI": "true",
            "CI_PROJECT_PATH": "owner/repo",
            "CI_MERGE_REQUEST_IID": "42",
        }
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, [])
            assert result.exit_code == 0

        mock_gitlab_client.assert_called_once_with(
            token="glpat-test-token",
            url="https://gitlab.com",
        )
        mock_review.assert_called_once()

    @patch("ai_reviewer.cli.get_settings")
    def test_cli_github_no_token_fails(self, mock_get_settings: MagicMock) -> None:
        """Test that GitHub provider without token fails."""
        mock_settings = MagicMock()
        mock_settings.github_token = None
        mock_get_settings.return_value = mock_settings

        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_REF": "refs/pull/1/merge",
        }
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, ["--provider", "github"])
            assert result.exit_code == 1
            assert "GITHUB_TOKEN" in result.stdout

    @patch("ai_reviewer.cli.get_settings")
    def test_cli_github_short_token_fails(self, mock_get_settings: MagicMock) -> None:
        """Test that GitHub provider with short token fails."""
        mock_settings = MagicMock()
        mock_settings.github_token.get_secret_value.return_value = "short"
        mock_get_settings.return_value = mock_settings

        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_REF": "refs/pull/1/merge",
        }
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, ["--provider", "github"])
            assert result.exit_code == 1
            assert "too short" in result.stdout

    @patch("ai_reviewer.cli.get_settings")
    def test_cli_gitlab_no_token_fails(self, mock_get_settings: MagicMock) -> None:
        """Test that GitLab provider without token fails."""
        mock_settings = MagicMock()
        mock_settings.gitlab_token = None
        mock_get_settings.return_value = mock_settings

        env = {
            "GITLAB_CI": "true",
            "CI_PROJECT_PATH": "owner/repo",
            "CI_MERGE_REQUEST_IID": "42",
        }
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, ["--provider", "gitlab"])
            assert result.exit_code == 1
            assert "GITLAB_TOKEN" in result.stdout

    @patch("ai_reviewer.cli.get_settings")
    def test_cli_gitlab_no_context_fails(self, mock_get_settings: MagicMock) -> None:
        """Test that GitLab provider without MR context fails."""
        mock_settings = MagicMock()
        mock_settings.gitlab_token.get_secret_value.return_value = "glpat-test-token"
        mock_get_settings.return_value = mock_settings

        env = {"GITLAB_CI": "true"}  # No CI_PROJECT_PATH or CI_MERGE_REQUEST_IID
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, ["--provider", "gitlab"])
            assert result.exit_code == 1

    @patch("ai_reviewer.cli.review_pull_request")
    @patch("ai_reviewer.cli.GitHubClient")
    @patch("ai_reviewer.cli.get_settings")
    def test_cli_successful_github_review(
        self,
        mock_get_settings: MagicMock,
        mock_github_client: MagicMock,
        mock_review: MagicMock,
    ) -> None:
        """Test successful GitHub review execution."""
        mock_settings = MagicMock()
        mock_settings.github_token.get_secret_value.return_value = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_provider = MagicMock()
        mock_github_client.return_value = mock_provider

        event_data = {"pull_request": {"number": 42}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            event_path = f.name

        try:
            env = {
                "GITHUB_ACTIONS": "true",
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_EVENT_PATH": event_path,
                "GITHUB_TOKEN": "ghp_test_token_12345",
                "GOOGLE_API_KEY": "AIza_test_key_12345",
            }
            with patch.dict(os.environ, env, clear=True):
                result = runner.invoke(app, [])
                assert result.exit_code == 0
                mock_github_client.assert_called_once_with(token="test-token")
                mock_review.assert_called_once_with(mock_provider, "owner/repo", 42, mock_settings)
        finally:
            Path(event_path).unlink()

    @patch("ai_reviewer.cli.review_pull_request")
    @patch("ai_reviewer.cli.GitHubClient")
    @patch("ai_reviewer.cli.get_settings")
    def test_cli_with_explicit_args(
        self,
        mock_get_settings: MagicMock,
        mock_github_client: MagicMock,
        mock_review: MagicMock,
    ) -> None:
        """Test CLI with explicit --repo and --pr arguments."""
        mock_settings = MagicMock()
        mock_settings.github_token.get_secret_value.return_value = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_provider = MagicMock()
        mock_github_client.return_value = mock_provider

        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, ["--repo", "custom/repo", "--pr", "123"])
            assert result.exit_code == 0
            mock_review.assert_called_once_with(mock_provider, "custom/repo", 123, mock_settings)

    def test_cli_config_error_exits_with_code_1(self) -> None:
        """Test that configuration error exits with code 1."""
        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_REF": "refs/pull/1/merge",
            # Missing GOOGLE_API_KEY - this should cause config error
        }
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, [])
            assert result.exit_code == 1
            # Should show configuration error message
            output_lower = result.stdout.lower()
            has_error = "error" in output_lower
            has_config = "configuration" in output_lower
            has_validation = "validation" in output_lower
            assert has_error or has_config or has_validation


# ── Discover command ────────────────────────────────────────────────


class TestDiscoverCommand:
    """Tests for 'ai-review discover' subcommand."""

    def test_discover_help(self) -> None:
        """Test that discover --help works and shows expected content."""
        result = runner.invoke(app, ["discover", "--help"])
        assert result.exit_code == 0
        assert "discover" in result.stdout.lower()
        assert "repo" in result.stdout.lower()

    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.cli._create_provider_client")
    @patch("ai_reviewer.cli.get_settings")
    def test_discover_json_output(
        self,
        mock_get_settings: MagicMock,
        mock_create_client: MagicMock,
        mock_create_router: MagicMock,
        mock_orch_cls: MagicMock,
    ) -> None:
        """Test that --json outputs valid JSON."""
        mock_settings = MagicMock()
        mock_settings.google_api_key.get_secret_value.return_value = "test-key"
        mock_settings.google_api_keys = ["test-key"]
        mock_settings.gemini_model = "gemini-test"
        mock_get_settings.return_value = mock_settings

        profile = make_profile(framework="Django 5.1")
        mock_orch_cls.return_value.discover.return_value = profile

        result = runner.invoke(app, ["discover", "owner/repo", "--json"])
        assert result.exit_code == 0, result.stdout
        # Rich Console outputs ANSI; extract JSON from stdout
        # The "Discovering..." line comes before JSON — find the first "{"
        stdout = result.stdout
        json_start = stdout.index("{")
        parsed = json.loads(stdout[json_start:])
        assert parsed["framework"] == "Django 5.1"

    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.cli._create_provider_client")
    @patch("ai_reviewer.cli.get_settings")
    def test_discover_human_output_with_zones(
        self,
        mock_get_settings: MagicMock,
        mock_create_client: MagicMock,
        mock_create_router: MagicMock,
        mock_orch_cls: MagicMock,
    ) -> None:
        """Test human-friendly output includes attention zones."""
        mock_settings = MagicMock()
        mock_settings.google_api_key.get_secret_value.return_value = "test-key"
        mock_settings.google_api_keys = ["test-key"]
        mock_settings.gemini_model = "gemini-test"
        mock_get_settings.return_value = mock_settings

        zones = (
            AttentionZone(area="formatting", status="well_covered", tools=("ruff",), reason="CI"),
            AttentionZone(
                area="security",
                status="not_covered",
                reason="no SAST",
                recommendation="Add bandit",
            ),
        )
        profile = make_profile(framework="FastAPI", attention_zones=zones)
        mock_orch_cls.return_value.discover.return_value = profile

        result = runner.invoke(app, ["discover", "owner/repo"])
        assert result.exit_code == 0
        assert "Attention Zones" in result.stdout
        assert "formatting" in result.stdout
        assert "security" in result.stdout
        assert "Add bandit" in result.stdout

    @patch("ai_reviewer.discovery.DiscoveryOrchestrator")
    @patch("ai_reviewer.llm.router.create_router")
    @patch("ai_reviewer.cli._create_provider_client")
    @patch("ai_reviewer.cli.get_settings")
    def test_discover_verbose_shows_ci_tools(
        self,
        mock_get_settings: MagicMock,
        mock_create_client: MagicMock,
        mock_create_router: MagicMock,
        mock_orch_cls: MagicMock,
    ) -> None:
        """Test that --verbose shows CI tools."""
        from ai_reviewer.discovery.models import DetectedTool, ToolCategory

        mock_settings = MagicMock()
        mock_settings.google_api_key.get_secret_value.return_value = "test-key"
        mock_settings.google_api_keys = ["test-key"]
        mock_settings.gemini_model = "gemini-test"
        mock_get_settings.return_value = mock_settings

        profile = make_profile(
            ci_tools=(DetectedTool(name="ruff", category=ToolCategory.LINTING),),
        )
        mock_orch_cls.return_value.discover.return_value = profile

        result = runner.invoke(app, ["discover", "owner/repo", "--verbose"])
        assert result.exit_code == 0
        assert "CI Tools" in result.stdout
        assert "ruff" in result.stdout

    def test_discover_config_error(self) -> None:
        """Test that missing config causes clean error."""
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["discover", "owner/repo"])
            assert result.exit_code == 1


# ── Format discovery output ─────────────────────────────────────────


class TestFormatDiscoveryOutput:
    """Tests for _format_discovery_output."""

    def test_basic_stack_info(self) -> None:
        """Test that stack info is rendered."""
        profile = make_profile(
            framework="Django 5.1",
            package_manager="uv",
            language_version="3.13",
        )
        output = _format_discovery_output(profile)
        assert "Python" in output
        assert "Django 5.1" in output
        assert "uv" in output
        assert "3.13" in output

    def test_attention_zones_rendered(self) -> None:
        """Test that zones are rendered with emoji."""
        zones = (
            AttentionZone(area="linting", status="well_covered", reason="ruff in CI"),
            AttentionZone(area="security", status="not_covered", reason="missing"),
        )
        profile = make_profile(attention_zones=zones)
        output = _format_discovery_output(profile)
        assert "\u2705" in output
        assert "\u274c" in output
        assert "linting" in output

    def test_gaps_rendered(self) -> None:
        """Test that gaps appear in output."""
        profile = make_profile(
            gaps=(Gap(observation="No tests found", default_assumption="No testing"),),
        )
        output = _format_discovery_output(profile)
        assert "Knowledge Gaps" in output
        assert "No tests found" in output

    def test_fallback_guidance_when_no_zones(self) -> None:
        """Test that skip/focus from guidance is shown when no zones."""
        profile = make_profile(skip=("formatting",), focus=("security",))
        output = _format_discovery_output(profile)
        assert "Skip" in output
        assert "formatting" in output
        assert "Focus" in output
        assert "security" in output

    def test_reviewbot_md_hint(self) -> None:
        """Test that .reviewbot.md hint is always present."""
        profile = make_profile()
        output = _format_discovery_output(profile)
        assert ".reviewbot.md" in output
