"""Shared test helpers for building discovery models and mock objects.

Provides factory functions used across unit, integration, and E2E tests
to construct ProjectProfile, mock Settings, and related objects with
sensible defaults.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from pydantic import SecretStr

from ai_reviewer.core.config import LanguageMode, Settings
from ai_reviewer.discovery.models import (
    AutomatedChecks,
    CIInsights,
    PlatformData,
    ProjectProfile,
    ReviewGuidance,
)


def make_profile(**kw: Any) -> ProjectProfile:  # noqa: ANN401
    """Build a ProjectProfile with sensible defaults, overridable via kwargs.

    Supports shorthand kwargs for common fields:
        - ``ci_tools``: tuple of DetectedTool (builds CIInsights automatically).
        - ``ci_provider``: CI provider name for AutomatedChecks.
        - ``ci_file_path``: CI config file path (default: ``.github/workflows/ci.yml``).
        - ``skip``, ``focus``: tuples for ReviewGuidance.
        - ``language``: primary language name (default: ``Python``).
        - ``file_tree``: file paths in the repository.
        - ``framework``, ``language_version``, ``package_manager``: stack details.
        - ``gaps``: tuple of Gap objects.

    Example::

        profile = make_profile(
            ci_tools=(DetectedTool(name="ruff", category=ToolCategory.LINTING),),
            gaps=(Gap(observation="No tests", default_assumption="None"),),
        )
    """
    ci_tools = kw.pop("ci_tools", ())
    ci_provider = kw.pop("ci_provider", None)
    ci_file_path = kw.pop("ci_file_path", ".github/workflows/ci.yml")
    skip = kw.pop("skip", ())
    focus = kw.pop("focus", ())
    language = kw.pop("language", "Python")
    file_tree = kw.pop("file_tree", ("src/main.py",))

    attention_zones = kw.pop("attention_zones", ())

    ci = CIInsights(ci_file_path=ci_file_path, detected_tools=ci_tools) if ci_tools else None
    return ProjectProfile(
        platform_data=PlatformData(
            languages={language: 100.0},
            primary_language=language,
            file_tree=file_tree,
        ),
        ci_insights=ci,
        framework=kw.pop("framework", None),
        language_version=kw.pop("language_version", None),
        package_manager=kw.pop("package_manager", None),
        automated_checks=AutomatedChecks(ci_provider=ci_provider),
        guidance=ReviewGuidance(skip_in_review=skip, focus_in_review=focus),
        gaps=kw.pop("gaps", ()),
        attention_zones=attention_zones,
    )


def make_mock_settings(**overrides: object) -> Mock:
    """Build a mock Settings with all required attributes.

    Returns a ``Mock(spec=Settings)`` pre-configured with sensible defaults
    for every attribute that production code touches.  Use ``overrides`` to
    change individual values::

        settings = make_mock_settings(discovery_enabled=False, language="uk")
    """
    settings = Mock(spec=Settings)
    settings.google_api_key = SecretStr("test-key-for-unit-tests")
    settings.google_api_keys = ["test-key-for-unit-tests"]
    settings.gemini_model = "gemini-test"
    settings.gemini_model_fallback = "gemini-2.5-flash"
    settings.fallback_models = ["gemini-2.5-flash"]
    settings.review_max_files = 20
    settings.review_max_diff_lines = 500
    settings.review_split_threshold = 30_000
    settings.review_max_comment_chars = 3000
    settings.review_include_bot_comments = True
    settings.review_post_inline_comments = True
    settings.review_enable_dialogue = True
    settings.language = "en"
    settings.language_mode = LanguageMode.FIXED
    settings.discovery_enabled = True
    settings.discovery_verbose = False
    settings.discovery_timeout = 30
    for k, v in overrides.items():
        setattr(settings, k, v)
    return settings
