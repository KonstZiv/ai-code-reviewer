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
from pydantic import AfterValidator, AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LanguageMode(str, Enum):
    """Language detection mode for review responses.

    Attributes:
        ADAPTIVE: Automatically detect language from PR context (description, comments).
        FIXED: Always use the language specified in LANGUAGE setting.
    """

    ADAPTIVE = "adaptive"
    FIXED = "fixed"


# Bot display name used in all user-facing comments
BOT_NAME = "AI ReviewBot"

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
MistralApiKey = Annotated[SecretStr, _create_secret_validator("MISTRAL_API_KEY")]
LogLevel = Annotated[str, AfterValidator(_validate_log_level)]
LanguageCode = Annotated[str, AfterValidator(_validate_language_code)]

# Supported LLM providers (keep in sync with llm.models.Operator)
SUPPORTED_LLM_PROVIDERS = frozenset({"google", "mistral"})


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
            Defaults to gemini-2.5-flash for reliability and quota.
        log_level: Logging level for the application.
            One of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        review_max_files: Maximum number of files to include in review context.
            Limits context size to avoid token limits.
        review_max_diff_lines: Maximum diff lines per file to include.
            Limits context size for large changes.
        review_split_threshold: Prompt char count above which the review is
            split into separate code and test passes.
        api_timeout: API request timeout in seconds.
            Limits how long to wait for API responses.
        language: Default language for review responses.
            Uses ISO 639-1 codes (en, uk, de, es, etc.).
        language_mode: Language detection mode.
            ADAPTIVE auto-detects from context, FIXED uses the language setting.
        review_post_inline_comments: Post inline comments on specific lines.
            When True, issues with file/line info are posted as inline comments.

    Environment Variables (AI_REVIEWER_* preferred, old names as fallback):
        AI_REVIEWER_GOOGLE_API_KEY / GOOGLE_API_KEY: Google Gemini API key (required)
        AI_REVIEWER_GITHUB_TOKEN / GITHUB_TOKEN: GitHub personal access token
        AI_REVIEWER_GITLAB_TOKEN / GITLAB_TOKEN: GitLab personal access token
        AI_REVIEWER_GITLAB_URL / GITLAB_URL: GitLab server URL
        AI_REVIEWER_GEMINI_MODEL / GEMINI_MODEL: Model name
        AI_REVIEWER_GEMINI_MODEL_FALLBACK / GEMINI_MODEL_FALLBACK: Fallback model
        AI_REVIEWER_LOG_LEVEL / LOG_LEVEL: Logging level
        AI_REVIEWER_REVIEW_MAX_FILES / REVIEW_MAX_FILES: Max files in context
        AI_REVIEWER_REVIEW_MAX_DIFF_LINES / REVIEW_MAX_DIFF_LINES: Max diff lines
        AI_REVIEWER_API_TIMEOUT / API_TIMEOUT: Request timeout in seconds
        AI_REVIEWER_LANGUAGE / LANGUAGE: Default response language
        AI_REVIEWER_LANGUAGE_MODE / LANGUAGE_MODE: Detection mode
        AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS / REVIEW_MAX_COMMENT_CHARS: Max comment chars
        AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS / REVIEW_INCLUDE_BOT_COMMENTS: Include bots
        AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS / REVIEW_POST_INLINE_COMMENTS: Inline comments
        AI_REVIEWER_REVIEW_ENABLE_DIALOGUE / REVIEW_ENABLE_DIALOGUE: Dialogue threading
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # ── LLM provider selection ──────────────────────────────────────
    llm_provider: str = Field(
        default="google",
        validation_alias=AliasChoices("AI_REVIEWER_LLM_PROVIDER", "LLM_PROVIDER"),
        description="Primary LLM provider (google, mistral)",
    )
    llm_fallback_provider: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_REVIEWER_LLM_FALLBACK_PROVIDER", "LLM_FALLBACK_PROVIDER"),
        description="Fallback LLM provider used when primary is exhausted",
    )

    # ── Google / Gemini credentials ──────────────────────────────
    google_api_key: GoogleApiKey | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_REVIEWER_GOOGLE_API_KEY", "GOOGLE_API_KEY"),
        description="Google API key for Gemini access (comma-separated for rotation)",
    )

    # ── Mistral credentials ──────────────────────────────────────
    mistral_api_key: MistralApiKey | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_REVIEWER_MISTRAL_API_KEY", "MISTRAL_API_KEY"),
        description="Mistral API key (comma-separated for rotation)",
    )

    # Provider-specific credentials (optional - validated at CLI level)
    # Note: We use SecretStr without validator since tokens are optional.
    # Validation is done at CLI level when the corresponding provider is selected.
    github_token: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_REVIEWER_GITHUB_TOKEN", "GITHUB_TOKEN"),
        description="GitHub personal access token for API access",
    )
    gitlab_token: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_REVIEWER_GITLAB_TOKEN", "GITLAB_TOKEN"),
        description="GitLab personal access token for API access",
    )
    gitlab_url: str = Field(
        default="https://gitlab.com",
        validation_alias=AliasChoices("AI_REVIEWER_GITLAB_URL", "GITLAB_URL"),
        description="GitLab server URL (for self-hosted instances)",
    )

    # Optional configuration with defaults
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices("AI_REVIEWER_GEMINI_MODEL", "GEMINI_MODEL"),
        description="Gemini model to use for analysis",
    )
    gemini_model_fallback: str | None = Field(
        default="gemini-3-flash-preview,gemini-2.5-flash-lite,gemini-3.1-flash-lite-preview",
        validation_alias=AliasChoices("AI_REVIEWER_GEMINI_MODEL_FALLBACK", "GEMINI_MODEL_FALLBACK"),
        description="Comma-separated fallback model chain (empty to disable)",
    )

    # Mistral model configuration
    mistral_model: str = Field(
        default="mistral-large-latest",
        validation_alias=AliasChoices("AI_REVIEWER_MISTRAL_MODEL", "MISTRAL_MODEL"),
        description="Mistral model to use for analysis",
    )
    mistral_model_fallback: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AI_REVIEWER_MISTRAL_MODEL_FALLBACK", "MISTRAL_MODEL_FALLBACK"
        ),
        description="Comma-separated Mistral fallback model chain",
    )
    mistral_api_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_REVIEWER_MISTRAL_API_URL", "MISTRAL_API_URL"),
        description="Custom Mistral API base URL (e.g. https://codestral.mistral.ai)",
    )

    log_level: LogLevel = Field(
        default="INFO",
        validation_alias=AliasChoices("AI_REVIEWER_LOG_LEVEL", "LOG_LEVEL"),
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    review_max_files: int = Field(
        default=20,
        gt=0,
        le=100,
        validation_alias=AliasChoices("AI_REVIEWER_REVIEW_MAX_FILES", "REVIEW_MAX_FILES"),
        description="Maximum number of files to include in review context",
    )
    review_max_diff_lines: int = Field(
        default=500,
        gt=0,
        le=5000,
        validation_alias=AliasChoices("AI_REVIEWER_REVIEW_MAX_DIFF_LINES", "REVIEW_MAX_DIFF_LINES"),
        description="Maximum diff lines per file to include",
    )
    review_split_threshold: int = Field(
        default=30_000,
        gt=0,
        le=200_000,
        validation_alias=AliasChoices(
            "AI_REVIEWER_REVIEW_SPLIT_THRESHOLD", "REVIEW_SPLIT_THRESHOLD"
        ),
        description="Prompt char count above which review is split into code + tests",
    )

    # API timeout configuration
    api_timeout: int = Field(
        default=60,
        gt=0,
        le=300,
        validation_alias=AliasChoices("AI_REVIEWER_API_TIMEOUT", "API_TIMEOUT"),
        description="API request timeout in seconds",
    )

    # Language configuration
    language: LanguageCode = Field(
        default="en",
        validation_alias=AliasChoices("AI_REVIEWER_LANGUAGE", "LANGUAGE"),
        description="Default language for review responses (ISO 639 code or language name)",
    )
    language_mode: LanguageMode = Field(
        default=LanguageMode.ADAPTIVE,
        validation_alias=AliasChoices("AI_REVIEWER_LANGUAGE_MODE", "LANGUAGE_MODE"),
        description="Language detection mode: adaptive (auto-detect) or fixed (use LANGUAGE)",
    )

    # Comment inclusion in prompt
    review_max_comment_chars: int = Field(
        default=3000,
        ge=0,
        le=20000,
        validation_alias=AliasChoices(
            "AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS", "REVIEW_MAX_COMMENT_CHARS"
        ),
        description="Max total chars of MR comments in review prompt (0 to disable)",
    )
    review_include_bot_comments: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS", "REVIEW_INCLUDE_BOT_COMMENTS"
        ),
        description="Include bot comments in review prompt (to avoid repeating AI suggestions)",
    )

    # Dialogue threading
    review_enable_dialogue: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AI_REVIEWER_REVIEW_ENABLE_DIALOGUE", "REVIEW_ENABLE_DIALOGUE"
        ),
        description="Group comments into threaded dialogues in AI prompt",
    )

    # Discovery
    discovery_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AI_REVIEWER_DISCOVERY_ENABLED", "DISCOVERY_ENABLED"),
        description="Enable project discovery before review",
    )
    discovery_verbose: bool = Field(
        default=False,
        validation_alias=AliasChoices("AI_REVIEWER_DISCOVERY_VERBOSE", "DISCOVERY_VERBOSE"),
        description="Always post discovery comment (default: only on gaps)",
    )
    discovery_timeout: int = Field(
        default=30,
        gt=0,
        le=300,
        validation_alias=AliasChoices("AI_REVIEWER_DISCOVERY_TIMEOUT", "DISCOVERY_TIMEOUT"),
        description="Discovery pipeline timeout in seconds",
    )

    # Inline comments
    review_post_inline_comments: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS", "REVIEW_POST_INLINE_COMMENTS"
        ),
        description="Post inline comments on specific lines instead of a single summary",
    )

    @property
    def google_api_keys(self) -> list[str]:
        """Parse comma-separated API keys from google_api_key.

        Returns:
            List of individual API key strings (empty if key not set).
        """
        if not self.google_api_key:
            return []
        raw = self.google_api_key.get_secret_value()
        return [k.strip() for k in raw.split(",") if k.strip()]

    @property
    def mistral_api_keys(self) -> list[str]:
        """Parse comma-separated API keys from mistral_api_key.

        Returns:
            List of individual API key strings (empty if key not set).
        """
        if not self.mistral_api_key:
            return []
        raw = self.mistral_api_key.get_secret_value()
        return [k.strip() for k in raw.split(",") if k.strip()]

    @property
    def fallback_models(self) -> list[str]:
        """Parse comma-separated fallback model names for the primary provider.

        Returns:
            List of model name strings (may be empty if fallback disabled).
        """
        fallback_str = self._get_provider_model_fallback(self.llm_provider)
        if not fallback_str:
            return []
        return [m.strip() for m in fallback_str.split(",") if m.strip()]

    @property
    def mistral_fallback_models(self) -> list[str]:
        """Parse comma-separated Mistral fallback model names.

        Returns:
            List of model name strings (may be empty).
        """
        if not self.mistral_model_fallback:
            return []
        return [m.strip() for m in self.mistral_model_fallback.split(",") if m.strip()]

    @property
    def gemini_fallback_models(self) -> list[str]:
        """Parse comma-separated Gemini fallback model names.

        Returns:
            List of model name strings (may be empty).
        """
        if not self.gemini_model_fallback:
            return []
        return [m.strip() for m in self.gemini_model_fallback.split(",") if m.strip()]

    def get_provider_model(self, provider: str) -> str:
        """Return the primary model name for a given provider.

        Args:
            provider: Provider identifier (``"google"`` or ``"mistral"``).

        Returns:
            Model name string.
        """
        if provider == "mistral":
            return self.mistral_model
        return self.gemini_model

    def get_provider_fallback_models(self, provider: str) -> list[str]:
        """Return fallback model names for a given provider.

        Args:
            provider: Provider identifier (``"google"`` or ``"mistral"``).

        Returns:
            List of fallback model name strings (may be empty).
        """
        if provider == "mistral":
            return self.mistral_fallback_models
        return self.gemini_fallback_models

    def get_provider_api_keys(self, provider: str) -> list[str]:
        """Return API keys for a given provider.

        Args:
            provider: Provider identifier (``"google"`` or ``"mistral"``).

        Returns:
            List of API key strings (may be empty).
        """
        if provider == "mistral":
            return self.mistral_api_keys
        return self.google_api_keys

    def _get_provider_model_fallback(self, provider: str) -> str | None:
        """Return raw fallback string for a provider."""
        if provider == "mistral":
            return self.mistral_model_fallback
        return self.gemini_model_fallback

    @model_validator(mode="after")
    def _validate_provider_keys(self) -> Settings:
        """Validate that the primary provider has API keys configured."""
        # Validate individual Google key lengths
        for key in self.google_api_keys:
            if len(key) < MIN_SECRET_LENGTH:
                msg = (
                    f"One of the GOOGLE_API_KEY values is too short "
                    f"(minimum {MIN_SECRET_LENGTH} characters). "
                    f"Key ending '...{key[-4:]}' is only {len(key)} characters."
                )
                raise ValueError(msg)
        # Validate individual Mistral key lengths
        for key in self.mistral_api_keys:
            if len(key) < MIN_SECRET_LENGTH:
                msg = (
                    f"One of the MISTRAL_API_KEY values is too short "
                    f"(minimum {MIN_SECRET_LENGTH} characters). "
                    f"Key ending '...{key[-4:]}' is only {len(key)} characters."
                )
                raise ValueError(msg)
        # Primary provider must have keys
        primary_keys = self.get_provider_api_keys(self.llm_provider)
        if not primary_keys:
            msg = (
                f"Primary LLM provider '{self.llm_provider}' has no API keys. "
                f"Set AI_REVIEWER_{self.llm_provider.upper()}_API_KEY "
                f"(or AI_REVIEWER_GOOGLE_API_KEY for Google)."
            )
            raise ValueError(msg)
        return self


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
    "BOT_NAME",
    "MIN_SECRET_LENGTH",
    "VALID_LOG_LEVELS",
    "LanguageMode",
    "Settings",
    "clear_settings_cache",
    "get_settings",
]
