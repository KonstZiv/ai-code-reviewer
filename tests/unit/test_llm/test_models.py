"""Tests for LLM router data types: Operator, ModelTag, ModelCard."""

from __future__ import annotations

import dataclasses

import pytest

from ai_reviewer.llm.models import ModelCard, ModelTag, Operator

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_card(**overrides: object) -> ModelCard:
    """Build a ModelCard with sensible defaults; override any field."""
    defaults: dict[str, object] = {
        "name": "test-model",
        "operator": Operator.GOOGLE,
        "tags": frozenset({ModelTag.LIGHT}),
        "context_window": 128_000,
        "input_price_per_mtok": 1.0,
        "output_price_per_mtok": 3.0,
    }
    defaults.update(overrides)
    return ModelCard(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------


class TestOperator:
    """Tests for the Operator enum."""

    def test_values(self) -> None:
        """All four operators have expected string values."""
        assert Operator.GOOGLE == "google"
        assert Operator.ANTHROPIC == "anthropic"
        assert Operator.DEEPSEEK == "deepseek"
        assert Operator.MISTRAL == "mistral"

    def test_member_count(self) -> None:
        """Exactly four operators exist."""
        assert len(Operator) == 4

    def test_is_str(self) -> None:
        """Operator values are plain strings (str, Enum pattern)."""
        assert isinstance(Operator.GOOGLE, str)
        assert isinstance(Operator.GOOGLE, Operator)


# ---------------------------------------------------------------------------
# ModelTag
# ---------------------------------------------------------------------------


class TestModelTag:
    """Tests for the ModelTag enum."""

    def test_values(self) -> None:
        """All tags have expected lowercase string values."""
        expected = {
            "heavy",
            "light",
            "coding",
            "cheap",
            "deep_analysis",
            "fast",
            "structured_output",
            "large_context",
        }
        actual = {tag.value for tag in ModelTag}
        assert actual == expected

    def test_member_count(self) -> None:
        """Eight tags exist."""
        assert len(ModelTag) == 8

    def test_is_str(self) -> None:
        """Tag values are plain strings."""
        assert isinstance(ModelTag.CODING, str)


# ---------------------------------------------------------------------------
# ModelCard
# ---------------------------------------------------------------------------


class TestModelCard:
    """Tests for ModelCard frozen dataclass."""

    def test_frozen(self) -> None:
        """Assigning to an attribute raises FrozenInstanceError."""
        card = _make_card()
        with pytest.raises(dataclasses.FrozenInstanceError):
            card.name = "other"  # type: ignore[misc]

    def test_defaults(self) -> None:
        """Default optional fields have expected values."""
        card = _make_card()
        assert card.is_default is False
        assert card.supports_structured is True
        assert card.deprecated is False

    def test_replace_produces_new_card(self) -> None:
        """dataclasses.replace() creates a new card with changed fields."""
        card = _make_card(deprecated=False)
        updated = dataclasses.replace(card, deprecated=True)
        assert updated.deprecated is True
        assert card.deprecated is False
        assert updated is not card

    # -- matches_tags --

    def test_matches_tags_exact(self) -> None:
        """Card matches when tags are exactly equal."""
        tags = frozenset({ModelTag.LIGHT, ModelTag.FAST})
        card = _make_card(tags=tags)
        assert card.matches_tags(tags) is True

    def test_matches_tags_subset(self) -> None:
        """Card with extra tags still matches a subset."""
        card = _make_card(tags=frozenset({ModelTag.LIGHT, ModelTag.FAST, ModelTag.CODING}))
        assert card.matches_tags(frozenset({ModelTag.LIGHT})) is True

    def test_matches_tags_superset_fails(self) -> None:
        """Card with fewer tags does NOT match a superset request."""
        card = _make_card(tags=frozenset({ModelTag.LIGHT}))
        assert card.matches_tags(frozenset({ModelTag.LIGHT, ModelTag.FAST})) is False

    def test_matches_tags_empty(self) -> None:
        """Any card matches an empty tag set (vacuous truth)."""
        card = _make_card(tags=frozenset({ModelTag.HEAVY}))
        assert card.matches_tags(frozenset()) is True

    def test_matches_tags_disjoint(self) -> None:
        """Card does NOT match completely disjoint tags."""
        card = _make_card(tags=frozenset({ModelTag.LIGHT}))
        assert card.matches_tags(frozenset({ModelTag.HEAVY})) is False

    # -- calculate_cost --

    def test_calculate_cost_known_values(self) -> None:
        """Verify cost calculation with known input."""
        card = _make_card(input_price_per_mtok=0.075, output_price_per_mtok=0.30)
        # 1M input + 500K output
        cost = card.calculate_cost(input_tokens=1_000_000, output_tokens=500_000)
        expected = 0.075 + 0.15  # 0.225
        assert cost == pytest.approx(expected)

    def test_calculate_cost_zero_tokens(self) -> None:
        """Zero tokens yield zero cost."""
        card = _make_card(input_price_per_mtok=10.0, output_price_per_mtok=30.0)
        assert card.calculate_cost(input_tokens=0, output_tokens=0) == 0.0

    def test_calculate_cost_small_request(self) -> None:
        """Small token counts produce fractional costs."""
        card = _make_card(input_price_per_mtok=1.0, output_price_per_mtok=3.0)
        # 1000 input + 500 output
        cost = card.calculate_cost(input_tokens=1000, output_tokens=500)
        expected = 0.001 + 0.0015  # 0.0025
        assert cost == pytest.approx(expected)
