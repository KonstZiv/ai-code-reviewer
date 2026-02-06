"""Configuration management for AI Code Reviewer.

This module provides configuration loading from environment variables
using pydantic-settings. All sensitive values (tokens, API keys) are
loaded from environment variables and never hardcoded.

This module performs only local validation (format, length, syntax).
Runtime validation (API availability, model existence) is handled by
provider-specific modules (e.g., gemini.py).

Example:
    >>> import os
    >>> os.environ["GOOGLE_API_KEY"] = "AIza_xxxx"
    >>> settings = Settings()
    >>> settings.github_token is None
    True
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Annotated

import iso639
from pydantic import AfterValidator, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LanguageMode(str, Enum):
    """Language detection mode for review responses.

    Attributes:
        ADAPTIVE: Automatically detect language from PR context (description, comments).
        FIXED: Always use the language specified in LANGUAGE setting.
    """

    ADAPTIVE = "adaptive"
    FIXED = "fixed"


# Minimum length for API tokens/keys validation
MIN_SECRET_LENGTH = 10

# Valid log levels
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def _create_secret_validator(
    field_name: str,
    min_length: int = MIN_SECRET_LENGTH,
) -> AfterValidator:
    """Create a validator for secret fields.

    Args:
        field_name: Human-readable field name for error messages.
        min_length: Minimum required length for the secret.

    Returns:
        AfterValidator that checks secret length.
    """

    def validate_secret(v: SecretStr) -> SecretStr:
        """Validate that secret meets minimum length requirement."""
        if len(v.get_secret_value()) < min_length:
            msg = (
                f"{field_name} is too short (minimum {min_length} characters). "
                f"Please provide a valid {field_name}."
            )
            raise ValueError(msg)
        return v

    return AfterValidator(validate_secret)


def _validate_log_level(v: str) -> str:
    """Validate and normalize log level."""
    normalized = v.upper()
    if normalized not in VALID_LOG_LEVELS:
        msg = f"Invalid log level '{v}'. Must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}"
        raise ValueError(msg)
    return normalized


def _validate_language_code(v: str) -> str:
    """Validate and normalize ISO 639 language code.

    Accepts any valid ISO 639 code (639-1, 639-2, 639-3) or language name.
    Normalizes to ISO 639-1 (2-letter) if available, otherwise keeps the original.

    Args:
        v: Language code or name (e.g., "en", "ukr", "Ukrainian", "fra").

    Returns:
        Normalized language code (preferably ISO 639-1).

    Raises:
        ValueError: If the language code is not valid.

    Examples:
        >>> _validate_language_code("en")
        'en'
        >>> _validate_language_code("ukr")
        'uk'
        >>> _validate_language_code("Ukrainian")
        'uk'
    """
    try:
        lang = iso639.Language.match(v)
    except iso639.LanguageNotFoundError as e:
        msg = f"Invalid language code '{v}'. Must be a valid ISO 639 code or language name."
        raise ValueError(msg) from e
    else:
        # Prefer ISO 639-1 (2-letter) if available, otherwise use part3 (3-letter)
        result: str = lang.part1 if lang.part1 else lang.part3
        return result


# Type aliases with validation
GoogleApiKey = Annotated[SecretStr, _create_secret_validator("GOOGLE_API_KEY")]
LogLevel = Annotated[str, AfterValidator(_validate_log_level)]
LanguageCode = Annotated[str, AfterValidator(_validate_language_code)]


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All sensitive values are stored as SecretStr to prevent accidental
    exposure in logs or error messages.

    This class performs only local validation:
    - Secret length checks
    - Log level validation
    - Numeric range validation

    Runtime validation (API connectivity, model availability) should be
    performed explicitly using provider modules (e.g., validate_gemini_setup).

    Attributes:
        github_token: GitHub personal access token for API access.
            Optional. Required only when using GitHub as the provider.
        gitlab_token: GitLab personal access token for API access.
            Optional. Required only when using GitLab as the provider.
        gitlab_url: GitLab server URL (for self-hosted instances).
            Defaults to https://gitlab.com for GitLab.com.
        google_api_key: Google API key for Gemini access.
            Required for AI-powered code analysis.
        gemini_model: Gemini model to use for analysis.
            Defaults to gemini-2.5-flash for cost efficiency.
        log_level: Logging level for the application.
            One of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        review_max_files: Maximum number of files to include in review context.
            Limits context size to avoid token limits.
        review_max_diff_lines: Maximum diff lines per file to include.
            Limits context size for large changes.
        api_timeout: API request timeout in seconds.
            Limits how long to wait for API responses.
        language: Default language for review responses.
            Uses ISO 639-1 codes (en, uk, de, es, etc.).
        language_mode: Language detection mode.
            ADAPTIVE auto-detects from context, FIXED uses the language setting.

    Environment Variables:
        GITHUB_TOKEN: GitHub personal access token (optional, required for GitHub)
        GITLAB_TOKEN: GitLab personal access token (required for GitLab)
        GITLAB_URL: GitLab server URL (default: https://gitlab.com)
        GOOGLE_API_KEY: Google Gemini API key (required)
        GEMINI_MODEL: Model name (default: gemini-2.5-flash)
        LOG_LEVEL: Logging level (default: INFO)
        REVIEW_MAX_FILES: Max files in context (default: 20)
        REVIEW_MAX_DIFF_LINES: Max diff lines per file (default: 500)
        API_TIMEOUT: Request timeout in seconds (default: 60)
        LANGUAGE: Default response language (default: en)
        LANGUAGE_MODE: Detection mode - adaptive or fixed (default: adaptive)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required credentials (validated for minimum length)
    google_api_key: GoogleApiKey = Field(
        ...,
        description="Google API key for Gemini access",
    )

    # Provider-specific credentials (optional - validated at CLI level)
    # Note: We use SecretStr without validator since tokens are optional.
    # Validation is done at CLI level when the corresponding provider is selected.
    github_token: SecretStr | None = Field(
        default=None,
        description="GitHub personal access token for API access",
    )
    gitlab_token: SecretStr | None = Field(
        default=None,
        description="GitLab personal access token for API access",
    )
    gitlab_url: str = Field(
        default="https://gitlab.com",
        description="GitLab server URL (for self-hosted instances)",
    )

    # Optional configuration with defaults
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model to use for analysis",
    )
    log_level: LogLevel = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    review_max_files: int = Field(
        default=20,
        gt=0,
        le=100,
        description="Maximum number of files to include in review context",
    )
    review_max_diff_lines: int = Field(
        default=500,
        gt=0,
        le=5000,
        description="Maximum diff lines per file to include",
    )

    # API timeout configuration
    api_timeout: int = Field(
        default=60,
        gt=0,
        le=300,
        description="API request timeout in seconds",
    )

    # Language configuration
    language: LanguageCode = Field(
        default="en",
        description="Default language for review responses (ISO 639 code or language name)",
    )
    language_mode: LanguageMode = Field(
        default=LanguageMode.ADAPTIVE,
        description="Language detection mode: adaptive (auto-detect) or fixed (use LANGUAGE)",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get application settings from environment.

    This function is cached using lru_cache, so it returns the same
    Settings instance on subsequent calls. Use clear_settings_cache()
    if you need to reload settings (e.g., in tests).

    Returns:
        Settings instance loaded from environment variables.

    Raises:
        pydantic.ValidationError: If required environment variables are missing
            or validation fails.

    Example:
        >>> settings = get_settings()  # doctest: +SKIP
        >>> print(settings.gemini_model)  # doctest: +SKIP
        gemini-2.5-flash
    """
    # pydantic-settings loads required fields from environment variables
    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache.

    Call this function when you need to reload settings from environment,
    typically in tests after modifying environment variables.

    Example:
        >>> clear_settings_cache()
        >>> # Now get_settings() will create a new instance
    """
    get_settings.cache_clear()


__all__ = [
    "MIN_SECRET_LENGTH",
    "VALID_LOG_LEVELS",
    "LanguageMode",
    "Settings",
    "clear_settings_cache",
    "get_settings",
]
