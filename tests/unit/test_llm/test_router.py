"""Tests for LLM router: ModelRegistry, LLMRouter, gemini_factory, catalog."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from ai_reviewer.llm.catalog import DEFAULT_CATALOG
from ai_reviewer.llm.models import ModelCard, ModelTag, Operator
from ai_reviewer.llm.router import (
    LLMRouter,
    ModelNotFoundError,
    ModelRegistry,
    _pick_best,
    create_router,
    gemini_factory,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_T = ModelTag


def _card(**overrides: object) -> ModelCard:
    """Build a ModelCard with compact defaults; override any field."""
    defaults: dict[str, object] = {
        "name": "test-model",
        "operator": Operator.GOOGLE,
        "tags": frozenset({_T.LIGHT}),
        "context_window": 128_000,
        "input_price_per_mtok": 1.0,
        "output_price_per_mtok": 3.0,
    }
    defaults.update(overrides)
    return ModelCard(**defaults)  # type: ignore[arg-type]


def _registry(*cards: ModelCard) -> ModelRegistry:
    """Build a ModelRegistry from positional cards."""
    return ModelRegistry(cards)


# ---------------------------------------------------------------------------
# ModelRegistry
# ---------------------------------------------------------------------------


class TestModelRegistry:
    """Tests for ModelRegistry query and mutation methods."""

    # -- size / operators --

    def test_size_empty(self) -> None:
        """Empty registry has size 0."""
        assert _registry().size == 0

    def test_size_with_cards(self) -> None:
        """Size reflects total cards including deprecated."""
        reg = _registry(
            _card(name="a"),
            _card(name="b", deprecated=True),
        )
        assert reg.size == 2

    def test_operators_excludes_deprecated(self) -> None:
        """Operators property excludes operators with only deprecated models."""
        reg = _registry(
            _card(name="g", operator=Operator.GOOGLE),
            _card(name="m", operator=Operator.MISTRAL, deprecated=True),
        )
        assert reg.operators == frozenset({Operator.GOOGLE})

    # -- register --

    def test_register_new(self) -> None:
        """register() adds a new card."""
        reg = _registry()
        reg.register(_card(name="new"))
        assert reg.size == 1

    def test_register_replaces(self) -> None:
        """register() replaces card with same name."""
        reg = _registry(_card(name="x", input_price_per_mtok=1.0))
        reg.register(_card(name="x", input_price_per_mtok=99.0))
        assert reg.size == 1
        assert reg.get("x").input_price_per_mtok == 99.0

    # -- get --

    def test_get_happy(self) -> None:
        """get() returns exact card by name."""
        card = _card(name="flash")
        reg = _registry(card)
        assert reg.get("flash") is card

    def test_get_returns_deprecated(self) -> None:
        """get() returns even deprecated cards."""
        card = _card(name="old", deprecated=True)
        reg = _registry(card)
        assert reg.get("old") is card

    def test_get_not_found(self) -> None:
        """get() raises ModelNotFoundError for unknown name."""
        reg = _registry()
        with pytest.raises(ModelNotFoundError, match="name='missing'"):
            reg.get("missing")

    # -- by_operator --

    def test_by_operator(self) -> None:
        """Returns only cards for specified operator."""
        g = _card(name="g", operator=Operator.GOOGLE)
        m = _card(name="m", operator=Operator.MISTRAL)
        reg = _registry(g, m)
        assert reg.by_operator(Operator.GOOGLE) == (g,)

    def test_by_operator_excludes_deprecated(self) -> None:
        """Deprecated cards are filtered out."""
        active = _card(name="active", operator=Operator.GOOGLE)
        dead = _card(name="dead", operator=Operator.GOOGLE, deprecated=True)
        reg = _registry(active, dead)
        assert reg.by_operator(Operator.GOOGLE) == (active,)

    def test_by_operator_empty(self) -> None:
        """Returns empty tuple for operator with no cards."""
        reg = _registry(_card(name="g", operator=Operator.GOOGLE))
        assert reg.by_operator(Operator.MISTRAL) == ()

    # -- by_tags --

    def test_by_tags_single(self) -> None:
        """Filter by one tag."""
        coding = _card(name="c", tags=frozenset({_T.CODING, _T.LIGHT}))
        heavy = _card(name="h", tags=frozenset({_T.HEAVY}))
        reg = _registry(coding, heavy)
        assert reg.by_tags(frozenset({_T.CODING})) == (coding,)

    def test_by_tags_multiple_and_logic(self) -> None:
        """Multiple tags require ALL to match."""
        both = _card(name="both", tags=frozenset({_T.CODING, _T.CHEAP}))
        only_coding = _card(name="coding", tags=frozenset({_T.CODING}))
        reg = _registry(both, only_coding)
        assert reg.by_tags(frozenset({_T.CODING, _T.CHEAP})) == (both,)

    def test_by_tags_excludes_deprecated(self) -> None:
        """Deprecated cards are filtered out even if tags match."""
        active = _card(name="a", tags=frozenset({_T.CODING}))
        dead = _card(name="d", tags=frozenset({_T.CODING}), deprecated=True)
        reg = _registry(active, dead)
        assert reg.by_tags(frozenset({_T.CODING})) == (active,)

    # -- by_operator_and_tags --

    def test_by_operator_and_tags(self) -> None:
        """Intersection of operator + tags."""
        g_coding = _card(name="gc", operator=Operator.GOOGLE, tags=frozenset({_T.CODING}))
        m_coding = _card(name="mc", operator=Operator.MISTRAL, tags=frozenset({_T.CODING}))
        g_heavy = _card(name="gh", operator=Operator.GOOGLE, tags=frozenset({_T.HEAVY}))
        reg = _registry(g_coding, m_coding, g_heavy)
        result = reg.by_operator_and_tags(Operator.GOOGLE, frozenset({_T.CODING}))
        assert result == (g_coding,)

    # -- default_for --

    def test_default_for_happy(self) -> None:
        """Returns the is_default=True card."""
        default = _card(name="d", operator=Operator.GOOGLE, is_default=True)
        other = _card(name="o", operator=Operator.GOOGLE)
        reg = _registry(other, default)
        assert reg.default_for(Operator.GOOGLE) is default

    def test_default_for_not_found(self) -> None:
        """Raises ModelNotFoundError when no default exists."""
        reg = _registry(_card(name="a", operator=Operator.GOOGLE))
        with pytest.raises(ModelNotFoundError, match="default"):
            reg.default_for(Operator.GOOGLE)

    def test_default_for_skips_deprecated(self) -> None:
        """Deprecated default is skipped."""
        dead_default = _card(name="d", operator=Operator.GOOGLE, is_default=True, deprecated=True)
        reg = _registry(dead_default)
        with pytest.raises(ModelNotFoundError):
            reg.default_for(Operator.GOOGLE)

    # -- sync_availability --

    def test_sync_marks_deprecated(self) -> None:
        """Models not in available set get deprecated=True."""
        reg = _registry(
            _card(name="keep", operator=Operator.GOOGLE),
            _card(name="remove", operator=Operator.GOOGLE),
        )
        changed = reg.sync_availability(Operator.GOOGLE, frozenset({"keep"}))
        assert changed == 1
        assert reg.get("keep").deprecated is False
        assert reg.get("remove").deprecated is True

    def test_sync_unmarks_deprecated(self) -> None:
        """Models in available set get deprecated=False."""
        reg = _registry(_card(name="revived", operator=Operator.GOOGLE, deprecated=True))
        changed = reg.sync_availability(Operator.GOOGLE, frozenset({"revived"}))
        assert changed == 1
        assert reg.get("revived").deprecated is False

    def test_sync_other_operators_unchanged(self) -> None:
        """Other operators are not affected."""
        m_card = _card(name="m", operator=Operator.MISTRAL)
        reg = _registry(m_card)
        changed = reg.sync_availability(Operator.GOOGLE, frozenset())
        assert changed == 0
        assert reg.get("m").deprecated is False

    def test_sync_no_change_returns_zero(self) -> None:
        """Returns 0 when nothing changes."""
        reg = _registry(_card(name="a", operator=Operator.GOOGLE))
        changed = reg.sync_availability(Operator.GOOGLE, frozenset({"a"}))
        assert changed == 0


# ---------------------------------------------------------------------------
# _pick_best
# ---------------------------------------------------------------------------


class TestPickBest:
    """Tests for the _pick_best scoring function."""

    def test_prefers_default(self) -> None:
        """Default model wins over cheaper non-default."""
        default = _card(
            name="d",
            is_default=True,
            input_price_per_mtok=5.0,
            output_price_per_mtok=10.0,
        )
        cheap = _card(
            name="c",
            is_default=False,
            input_price_per_mtok=0.1,
            output_price_per_mtok=0.1,
        )
        assert _pick_best((default, cheap)) is default

    def test_prefers_cheaper_among_non_defaults(self) -> None:
        """Lower total price wins when no default present."""
        expensive = _card(
            name="e",
            input_price_per_mtok=10.0,
            output_price_per_mtok=30.0,
        )
        budget = _card(
            name="b",
            input_price_per_mtok=0.1,
            output_price_per_mtok=0.3,
        )
        assert _pick_best((expensive, budget)) is budget

    def test_context_window_tiebreaker(self) -> None:
        """Same price → larger context wins."""
        small_ctx = _card(
            name="s",
            input_price_per_mtok=1.0,
            output_price_per_mtok=3.0,
            context_window=32_000,
        )
        big_ctx = _card(
            name="b",
            input_price_per_mtok=1.0,
            output_price_per_mtok=3.0,
            context_window=1_000_000,
        )
        assert _pick_best((small_ctx, big_ctx)) is big_ctx

    def test_single_candidate(self) -> None:
        """Single candidate is returned as-is."""
        card = _card(name="solo")
        assert _pick_best((card,)) is card


# ---------------------------------------------------------------------------
# LLMRouter
# ---------------------------------------------------------------------------


class TestLLMRouter:
    """Tests for LLMRouter resolution and provider creation."""

    @pytest.fixture
    def router(self) -> LLMRouter:
        """Router with two operators, one factory registered."""
        g_default = _card(
            name="gemini-flash",
            operator=Operator.GOOGLE,
            tags=frozenset({_T.LIGHT, _T.CODING, _T.FAST}),
            is_default=True,
        )
        g_pro = _card(
            name="gemini-pro",
            operator=Operator.GOOGLE,
            tags=frozenset({_T.HEAVY, _T.CODING, _T.DEEP_ANALYSIS}),
        )
        m_default = _card(
            name="mistral-large",
            operator=Operator.MISTRAL,
            tags=frozenset({_T.HEAVY, _T.CODING}),
            is_default=True,
        )
        registry = _registry(g_default, g_pro, m_default)
        r = LLMRouter(registry)
        r.register_operator(
            Operator.GOOGLE,
            factory=Mock(),
            api_keys=["key1"],
        )
        return r

    # -- resolve --

    def test_resolve_by_exact_name(self, router: LLMRouter) -> None:
        """Exact model name lookup."""
        card = router.resolve(model="gemini-flash")
        assert card.name == "gemini-flash"

    def test_resolve_by_operator_only(self, router: LLMRouter) -> None:
        """Operator only → returns default."""
        card = router.resolve(operator=Operator.GOOGLE)
        assert card.name == "gemini-flash"
        assert card.is_default is True

    def test_resolve_by_tags_only(self, router: LLMRouter) -> None:
        """Tags only → best across all operators."""
        card = router.resolve(tags=frozenset({_T.HEAVY, _T.CODING}))
        # Both gemini-pro and mistral-large match; pick_best decides
        assert card.name in {"gemini-pro", "mistral-large"}

    def test_resolve_by_operator_and_tags(self, router: LLMRouter) -> None:
        """Combined operator + tags filter."""
        card = router.resolve(operator=Operator.GOOGLE, tags=frozenset({_T.HEAVY}))
        assert card.name == "gemini-pro"

    def test_resolve_no_criteria_raises(self, router: LLMRouter) -> None:
        """ValueError when all params are None."""
        with pytest.raises(ValueError, match="At least one"):
            router.resolve()

    def test_resolve_not_found_raises(self, router: LLMRouter) -> None:
        """ModelNotFoundError for impossible query."""
        with pytest.raises(ModelNotFoundError):
            router.resolve(model="nonexistent")

    def test_resolve_operator_tags_not_found(self, router: LLMRouter) -> None:
        """ModelNotFoundError when no models match operator+tags."""
        with pytest.raises(ModelNotFoundError, match=r"operator.*tags"):
            router.resolve(operator=Operator.GOOGLE, tags=frozenset({_T.CHEAP}))

    def test_resolve_tags_not_found(self, router: LLMRouter) -> None:
        """ModelNotFoundError when no models match tags across operators."""
        with pytest.raises(ModelNotFoundError, match="tags"):
            router.resolve(tags=frozenset({_T.LARGE_CONTEXT}))

    # -- available_operators --

    def test_available_operators(self, router: LLMRouter) -> None:
        """Only operators with factory AND keys are available."""
        assert router.available_operators == frozenset({Operator.GOOGLE})

    def test_available_operators_empty_keys(self) -> None:
        """Operator with empty key list is not available."""
        reg = _registry(_card(name="g", operator=Operator.GOOGLE, is_default=True))
        r = LLMRouter(reg)
        r.register_operator(Operator.GOOGLE, factory=Mock(), api_keys=[])
        assert r.available_operators == frozenset()

    # -- create_provider --

    def test_create_provider_happy(self, router: LLMRouter) -> None:
        """Resolves model and calls factory."""
        mock_factory = router._factories[Operator.GOOGLE]
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm

        llm = router.create_provider(operator=Operator.GOOGLE)

        mock_factory.assert_called_once()
        call_args = mock_factory.call_args
        assert call_args[0][0].name == "gemini-flash"
        assert call_args[0][1] == ["key1"]
        assert llm is mock_llm

    def test_create_provider_no_factory(self) -> None:
        """NotImplementedError when no factory registered."""
        reg = _registry(_card(name="m", operator=Operator.MISTRAL, is_default=True))
        r = LLMRouter(reg)
        with pytest.raises(NotImplementedError, match="factory"):
            r.create_provider(operator=Operator.MISTRAL)

    def test_create_provider_no_keys(self) -> None:
        """ValueError when no API keys configured."""
        reg = _registry(_card(name="m", operator=Operator.MISTRAL, is_default=True))
        r = LLMRouter(reg)
        r._factories[Operator.MISTRAL] = Mock()
        with pytest.raises(ValueError, match="API keys"):
            r.create_provider(operator=Operator.MISTRAL)


# ---------------------------------------------------------------------------
# gemini_factory
# ---------------------------------------------------------------------------


class TestGeminiFactory:
    """Tests for the built-in gemini_factory function."""

    @patch("ai_reviewer.llm.gemini.GeminiProvider")
    def test_single_key_creates_gemini_provider(self, mock_cls: MagicMock) -> None:
        """Single key → plain GeminiProvider."""
        card = _card(name="gemini-flash", operator=Operator.GOOGLE)
        gemini_factory(card, ["key1"])
        mock_cls.assert_called_once_with(api_key="key1", model_name="gemini-flash")

    @patch("ai_reviewer.llm.key_pool.RotatingGeminiProvider")
    @patch("ai_reviewer.llm.key_pool.KeyPool")
    def test_multi_key_creates_rotating_provider(
        self,
        mock_pool_cls: MagicMock,
        mock_rotating_cls: MagicMock,
    ) -> None:
        """Multiple keys → RotatingGeminiProvider with KeyPool."""
        card = _card(name="gemini-pro", operator=Operator.GOOGLE)
        gemini_factory(card, ["k1", "k2", "k3"])
        mock_pool_cls.assert_called_once_with(["k1", "k2", "k3"])
        mock_rotating_cls.assert_called_once_with(
            key_pool=mock_pool_cls.return_value,
            model_name="gemini-pro",
        )

    @patch("ai_reviewer.llm.gemini.GeminiProvider")
    def test_model_name_from_card(self, mock_cls: MagicMock) -> None:
        """Factory passes the card's name as model_name."""
        card = _card(name="gemini-2.5-flash", operator=Operator.GOOGLE)
        gemini_factory(card, ["key"])
        assert mock_cls.call_args.kwargs["model_name"] == "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# DEFAULT_CATALOG validation
# ---------------------------------------------------------------------------


class TestDefaultCatalog:
    """Structural validation of the default model catalog."""

    def test_not_empty(self) -> None:
        """Catalog is not empty."""
        assert len(DEFAULT_CATALOG) > 0

    def test_no_duplicate_names(self) -> None:
        """All model names are unique."""
        names = [c.name for c in DEFAULT_CATALOG]
        assert len(names) == len(set(names))

    def test_all_operators_represented(self) -> None:
        """Every Operator enum member has at least one model."""
        present = {c.operator for c in DEFAULT_CATALOG}
        assert present == set(Operator)

    def test_one_default_per_operator(self) -> None:
        """Exactly one is_default=True model per operator."""
        defaults: dict[Operator, list[str]] = {}
        for card in DEFAULT_CATALOG:
            if card.is_default:
                defaults.setdefault(card.operator, []).append(card.name)

        for op in Operator:
            models = defaults.get(op, [])
            assert len(models) == 1, f"{op.value}: expected 1 default, got {models}"

    def test_prices_non_negative(self) -> None:
        """All prices are non-negative."""
        for card in DEFAULT_CATALOG:
            assert card.input_price_per_mtok >= 0, f"{card.name}: negative input price"
            assert card.output_price_per_mtok >= 0, f"{card.name}: negative output price"

    def test_context_windows_positive(self) -> None:
        """All context windows are positive."""
        for card in DEFAULT_CATALOG:
            assert card.context_window > 0, f"{card.name}: non-positive context"

    def test_tags_not_empty(self) -> None:
        """Every model has at least one tag."""
        for card in DEFAULT_CATALOG:
            assert len(card.tags) > 0, f"{card.name}: no tags"

    def test_registry_round_trip(self) -> None:
        """Catalog can be loaded into a registry and queried."""
        reg = ModelRegistry(DEFAULT_CATALOG)
        assert reg.size == len(DEFAULT_CATALOG)
        for op in Operator:
            default = reg.default_for(op)
            assert default.is_default is True


# ---------------------------------------------------------------------------
# create_router
# ---------------------------------------------------------------------------


class TestCreateRouter:
    """Tests for the create_router() settings bridge."""

    @staticmethod
    def _settings(
        google_keys: list[str] | None = None,
        mistral_keys: list[str] | None = None,
        mistral_api_url: str | None = None,
    ) -> Mock:
        """Build mock settings with provider key helpers."""
        s = Mock()
        s.google_api_keys = google_keys or []
        s.mistral_api_keys = mistral_keys or []
        s.mistral_api_url = mistral_api_url

        def _get_keys(provider: str) -> list[str]:
            if provider == "mistral":
                return s.mistral_api_keys
            return s.google_api_keys

        s.get_provider_api_keys = _get_keys
        return s

    def test_returns_router_with_google_registered(self) -> None:
        """Router has Google operator available after creation."""
        settings = self._settings(google_keys=["test-key"])

        router = create_router(settings)

        assert isinstance(router, LLMRouter)
        assert Operator.GOOGLE in router.available_operators

    def test_google_factory_is_gemini_factory(self) -> None:
        """The registered factory for Google is gemini_factory."""
        settings = self._settings(google_keys=["test-key"])

        router = create_router(settings)

        assert router._factories[Operator.GOOGLE] is gemini_factory

    def test_api_keys_from_settings(self) -> None:
        """API keys come from settings.google_api_keys."""
        settings = self._settings(google_keys=["k1", "k2"])

        router = create_router(settings)

        assert router._api_keys[Operator.GOOGLE] == ["k1", "k2"]

    def test_registry_has_catalog_models(self) -> None:
        """Registry is populated from DEFAULT_CATALOG."""
        settings = self._settings(google_keys=["test-key"])

        router = create_router(settings)

        assert router.registry.size == len(DEFAULT_CATALOG)

    def test_mistral_registered_when_keys_present(self) -> None:
        """Mistral operator is registered when keys are configured."""
        from ai_reviewer.llm.router import mistral_factory

        settings = self._settings(mistral_keys=["sk-test"])

        router = create_router(settings)

        assert Operator.MISTRAL in router.available_operators
        assert router._factories[Operator.MISTRAL] is mistral_factory

    def test_mistral_custom_url_uses_partial(self) -> None:
        """Mistral factory becomes partial when mistral_api_url is set."""
        from functools import partial

        settings = self._settings(
            mistral_keys=["sk-test"],
            mistral_api_url="https://codestral.mistral.ai",
        )

        router = create_router(settings)

        factory = router._factories[Operator.MISTRAL]
        assert isinstance(factory, partial)
        assert factory.keywords == {"server_url": "https://codestral.mistral.ai"}

    def test_both_providers_registered(self) -> None:
        """Both Google and Mistral registered when both have keys."""
        settings = self._settings(google_keys=["gk"], mistral_keys=["mk"])

        router = create_router(settings)

        assert router.available_operators == frozenset(
            {Operator.GOOGLE, Operator.MISTRAL},
        )

    def test_no_operator_without_keys(self) -> None:
        """Operator without keys is not registered."""
        settings = self._settings()

        router = create_router(settings)

        assert router.available_operators == frozenset()
