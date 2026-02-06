"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from ai_reviewer.core.config import (
    LanguageMode,
    Settings,
    clear_settings_cache,
    get_settings,
)


class TestSettings:
    """Tests for Settings class."""

    @pytest.fixture
    def minimal_env(self) -> dict[str, str]:
        """Return minimal required environment variables."""
        return {
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }

    @pytest.fixture
    def full_env(self) -> dict[str, str]:
        """Return all environment variables with custom values."""
        return {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
            "GEMINI_MODEL": "gemini-1.5-pro",
            "LOG_LEVEL": "DEBUG",
            "REVIEW_MAX_FILES": "50",
            "REVIEW_MAX_DIFF_LINES": "1000",
        }

    def test_create_settings_with_minimal_env(self, minimal_env: dict[str, str]) -> None:
        """Test creating settings with only required env vars."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()

            assert settings.github_token is None
            assert settings.google_api_key.get_secret_value() == "AIza_test_key_12345"
            # Check defaults
            assert settings.gemini_model == "gemini-2.5-flash"
            assert settings.log_level == "INFO"
            assert settings.review_max_files == 20
            assert settings.review_max_diff_lines == 500

    def test_create_settings_with_full_env(self, full_env: dict[str, str]) -> None:
        """Test creating settings with all env vars."""
        with patch.dict(os.environ, full_env, clear=True):
            settings = Settings()

            assert settings.gemini_model == "gemini-1.5-pro"
            assert settings.log_level == "DEBUG"
            assert settings.review_max_files == 50
            assert settings.review_max_diff_lines == 1000

    def test_github_token_default_none(self) -> None:
        """Test that github_token is None by default when not provided."""
        env = {"GOOGLE_API_KEY": "AIza_test_key_12345"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.github_token is None

    def test_github_token_from_env(self) -> None:
        """Test that github_token loads correctly when provided."""
        env = {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.github_token is not None
            assert settings.github_token.get_secret_value() == "ghp_test_token_12345"

    def test_missing_google_api_key_raises_error(self) -> None:
        """Test that missing GOOGLE_API_KEY raises ValidationError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "google_api_key" in str(exc_info.value).lower()

    def test_github_token_short_value_accepted(self) -> None:
        """Test that short GITHUB_TOKEN is accepted at Settings level.

        Length validation is done at CLI level, not in Settings.
        """
        env = {
            "GITHUB_TOKEN": "short",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.github_token is not None
            assert settings.github_token.get_secret_value() == "short"

    def test_google_api_key_too_short_raises_error(self) -> None:
        """Test that short GOOGLE_API_KEY raises ValidationError."""
        env = {
            "GOOGLE_API_KEY": "short",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "too short" in str(exc_info.value).lower()

    def test_invalid_log_level_raises_error(self, minimal_env: dict[str, str]) -> None:
        """Test that invalid LOG_LEVEL raises ValidationError."""
        env = {**minimal_env, "LOG_LEVEL": "INVALID"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            error_msg = str(exc_info.value).lower()
            assert "log_level" in error_msg or "invalid" in error_msg

    def test_log_level_case_insensitive(self, minimal_env: dict[str, str]) -> None:
        """Test that LOG_LEVEL is case insensitive."""
        for level in ["debug", "Debug", "DEBUG", "dEbUg"]:
            env = {**minimal_env, "LOG_LEVEL": level}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.log_level == "DEBUG"

    def test_all_valid_log_levels(self, minimal_env: dict[str, str]) -> None:
        """Test all valid log levels are accepted."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            env = {**minimal_env, "LOG_LEVEL": level}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.log_level == level

    def test_review_max_files_validation(self, minimal_env: dict[str, str]) -> None:
        """Test REVIEW_MAX_FILES validation."""
        # Zero is invalid
        env = {**minimal_env, "REVIEW_MAX_FILES": "0"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Negative is invalid
        env = {**minimal_env, "REVIEW_MAX_FILES": "-1"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Over 100 is invalid
        env = {**minimal_env, "REVIEW_MAX_FILES": "101"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Boundary value should be accepted
        env = {**minimal_env, "REVIEW_MAX_FILES": "100"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.review_max_files == 100

    def test_review_max_diff_lines_validation(self, minimal_env: dict[str, str]) -> None:
        """Test REVIEW_MAX_DIFF_LINES validation."""
        # Zero is invalid
        env = {**minimal_env, "REVIEW_MAX_DIFF_LINES": "0"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Over 5000 is invalid
        env = {**minimal_env, "REVIEW_MAX_DIFF_LINES": "5001"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Boundary value should be accepted
        env = {**minimal_env, "REVIEW_MAX_DIFF_LINES": "5000"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.review_max_diff_lines == 5000

    def test_secrets_are_hidden(self) -> None:
        """Test that secrets are not exposed in string representation."""
        env = {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

            # Check that secrets are SecretStr
            assert isinstance(settings.github_token, SecretStr)
            assert isinstance(settings.google_api_key, SecretStr)

            # Check that str/repr don't expose secrets
            settings_str = str(settings)
            settings_repr = repr(settings)

            assert "ghp_test_token_12345" not in settings_str
            assert "ghp_test_token_12345" not in settings_repr
            assert "AIza_test_key_12345" not in settings_str
            assert "AIza_test_key_12345" not in settings_repr

    def test_secrets_hidden_when_github_token_none(self, minimal_env: dict[str, str]) -> None:
        """Test that secrets are not exposed when github_token is None."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()

            assert settings.github_token is None
            # String representation should not cause errors
            settings_str = str(settings)
            settings_repr = repr(settings)
            assert "AIza_test_key_12345" not in settings_str
            assert "AIza_test_key_12345" not in settings_repr

    def test_extra_env_vars_ignored(self, minimal_env: dict[str, str]) -> None:
        """Test that extra environment variables are ignored."""
        env = {**minimal_env, "UNKNOWN_VAR": "some_value"}
        with patch.dict(os.environ, env, clear=True):
            # Should not raise
            settings = Settings()
            assert not hasattr(settings, "unknown_var")


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """Test that get_settings returns a Settings instance."""
        env = {
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        clear_settings_cache()
        with patch.dict(os.environ, env, clear=True):
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_returns_same_cached_instance(self) -> None:
        """Test that get_settings returns the same cached instance."""
        env = {
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        clear_settings_cache()
        with patch.dict(os.environ, env, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()
            # Same object due to lru_cache
            assert settings1 is settings2
            # And same values
            assert settings1.gemini_model == settings2.gemini_model

    def test_get_settings_raises_on_missing_env(self) -> None:
        """Test that get_settings raises when env vars are missing."""
        clear_settings_cache()
        with patch.dict(os.environ, {}, clear=True), pytest.raises(ValidationError):
            get_settings()

    def test_clear_settings_cache_allows_new_instance(self) -> None:
        """Test that clear_settings_cache allows creating new instance."""
        env = {
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        clear_settings_cache()
        with patch.dict(os.environ, env, clear=True):
            settings1 = get_settings()
            clear_settings_cache()
            settings2 = get_settings()
            # Different objects after cache clear
            assert settings1 is not settings2
            # But same values
            assert settings1.gemini_model == settings2.gemini_model


class TestLanguageMode:
    """Tests for LanguageMode enum."""

    def test_language_mode_values(self) -> None:
        """Test LanguageMode enum values."""
        assert LanguageMode.ADAPTIVE.value == "adaptive"
        assert LanguageMode.FIXED.value == "fixed"

    def test_language_mode_is_string_enum(self) -> None:
        """Test that LanguageMode is a string enum."""
        assert isinstance(LanguageMode.ADAPTIVE, str)
        assert LanguageMode.ADAPTIVE == "adaptive"


class TestNewSettings:
    """Tests for new Settings fields."""

    @pytest.fixture
    def minimal_env(self) -> dict[str, str]:
        """Return minimal required environment variables."""
        return {
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }

    def test_api_timeout_default(self, minimal_env: dict[str, str]) -> None:
        """Test api_timeout has default value of 60."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()
            assert settings.api_timeout == 60

    def test_api_timeout_from_env(self, minimal_env: dict[str, str]) -> None:
        """Test api_timeout can be set from environment."""
        env = {**minimal_env, "API_TIMEOUT": "120"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.api_timeout == 120

    def test_api_timeout_validation_min(self, minimal_env: dict[str, str]) -> None:
        """Test api_timeout must be greater than 0."""
        env = {**minimal_env, "API_TIMEOUT": "0"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

    def test_api_timeout_validation_max(self, minimal_env: dict[str, str]) -> None:
        """Test api_timeout must be <= 300."""
        env = {**minimal_env, "API_TIMEOUT": "301"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

    def test_api_timeout_boundary_values(self, minimal_env: dict[str, str]) -> None:
        """Test api_timeout boundary values are accepted."""
        # Minimum valid value
        env = {**minimal_env, "API_TIMEOUT": "1"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.api_timeout == 1

        # Maximum valid value
        env = {**minimal_env, "API_TIMEOUT": "300"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.api_timeout == 300

    def test_language_default(self, minimal_env: dict[str, str]) -> None:
        """Test language has default value of 'en'."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()
            assert settings.language == "en"

    def test_language_from_env(self, minimal_env: dict[str, str]) -> None:
        """Test language can be set from environment."""
        env = {**minimal_env, "LANGUAGE": "uk"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.language == "uk"

    def test_language_mode_default(self, minimal_env: dict[str, str]) -> None:
        """Test language_mode has default value of ADAPTIVE."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()
            assert settings.language_mode == LanguageMode.ADAPTIVE

    def test_language_mode_from_env_adaptive(self, minimal_env: dict[str, str]) -> None:
        """Test language_mode can be set to adaptive from environment."""
        env = {**minimal_env, "LANGUAGE_MODE": "adaptive"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.language_mode == LanguageMode.ADAPTIVE

    def test_language_mode_from_env_fixed(self, minimal_env: dict[str, str]) -> None:
        """Test language_mode can be set to fixed from environment."""
        env = {**minimal_env, "LANGUAGE_MODE": "fixed"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.language_mode == LanguageMode.FIXED

    def test_language_mode_invalid_raises_error(self, minimal_env: dict[str, str]) -> None:
        """Test that invalid language_mode raises ValidationError."""
        env = {**minimal_env, "LANGUAGE_MODE": "invalid"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

    def test_gitlab_token_default_none(self, minimal_env: dict[str, str]) -> None:
        """Test gitlab_token is None by default."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()
            assert settings.gitlab_token is None

    def test_gitlab_token_from_env(self, minimal_env: dict[str, str]) -> None:
        """Test gitlab_token can be set from environment."""
        env = {**minimal_env, "GITLAB_TOKEN": "glpat-test_token_12345"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.gitlab_token is not None
            assert settings.gitlab_token.get_secret_value() == "glpat-test_token_12345"

    def test_gitlab_token_is_secret(self, minimal_env: dict[str, str]) -> None:
        """Test gitlab_token is a SecretStr when set."""
        env = {**minimal_env, "GITLAB_TOKEN": "glpat-test_token_12345"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert isinstance(settings.gitlab_token, SecretStr)
            # Secret should not appear in string representation
            settings_str = str(settings)
            assert "glpat-test_token_12345" not in settings_str

    def test_gitlab_url_default(self, minimal_env: dict[str, str]) -> None:
        """Test gitlab_url has default value of 'https://gitlab.com'."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()
            assert settings.gitlab_url == "https://gitlab.com"

    def test_gitlab_url_from_env(self, minimal_env: dict[str, str]) -> None:
        """Test gitlab_url can be set from environment."""
        env = {**minimal_env, "GITLAB_URL": "https://gitlab.example.com"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.gitlab_url == "https://gitlab.example.com"


class TestLanguageValidation:
    """Tests for ISO 639 language code validation."""

    @pytest.fixture
    def minimal_env(self) -> dict[str, str]:
        """Return minimal required environment variables."""
        return {
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }

    def test_language_default_en(self, minimal_env: dict[str, str]) -> None:
        """Test language has default value of 'en'."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()
            assert settings.language == "en"

    def test_language_iso639_1_code(self, minimal_env: dict[str, str]) -> None:
        """Test ISO 639-1 (2-letter) codes are accepted."""
        for code in ["en", "uk", "de", "fr", "es", "ja", "zh"]:
            env = {**minimal_env, "LANGUAGE": code}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.language == code

    def test_language_iso639_3_code_normalized(self, minimal_env: dict[str, str]) -> None:
        """Test ISO 639-3 (3-letter) codes are normalized to ISO 639-1."""
        # ukr -> uk, deu -> de, fra -> fr
        test_cases = [
            ("ukr", "uk"),
            ("deu", "de"),
            ("fra", "fr"),
            ("eng", "en"),
            ("spa", "es"),
        ]
        for input_code, expected in test_cases:
            env = {**minimal_env, "LANGUAGE": input_code}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.language == expected

    def test_language_name_normalized(self, minimal_env: dict[str, str]) -> None:
        """Test language names are normalized to ISO 639-1 codes."""
        test_cases = [
            ("Ukrainian", "uk"),
            ("English", "en"),
            ("German", "de"),
            ("French", "fr"),
            ("Spanish", "es"),
        ]
        for input_name, expected in test_cases:
            env = {**minimal_env, "LANGUAGE": input_name}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.language == expected

    def test_language_invalid_code_raises_error(self, minimal_env: dict[str, str]) -> None:
        """Test that invalid language code raises ValidationError."""
        env = {**minimal_env, "LANGUAGE": "invalid"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "language" in str(exc_info.value).lower()

    def test_language_empty_string_raises_error(self, minimal_env: dict[str, str]) -> None:
        """Test that empty language code raises ValidationError."""
        env = {**minimal_env, "LANGUAGE": ""}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_language_gibberish_raises_error(self, minimal_env: dict[str, str]) -> None:
        """Test that gibberish language code raises ValidationError."""
        env = {**minimal_env, "LANGUAGE": "xyz123"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_language_iso639_3_no_part1_kept(self, minimal_env: dict[str, str]) -> None:
        """Test ISO 639-3 codes without ISO 639-1 equivalent are kept as-is."""
        # 'yue' is Cantonese - has ISO 639-3 but no ISO 639-1
        env = {**minimal_env, "LANGUAGE": "yue"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            # Cantonese doesn't have ISO 639-1, so keep ISO 639-3
            assert settings.language == "yue"
