"""LLM model registry, router, and provider factories.

The router resolves model selection requests (by operator, tags, or exact
name) into concrete ``LLMProvider`` instances.  The registry is a pure
data layer with no I/O; provider creation is delegated to per-operator
factory callables.

Typical usage::

    from ai_reviewer.llm.catalog import DEFAULT_CATALOG
    from ai_reviewer.llm.models import ModelTag, Operator
    from ai_reviewer.llm.router import LLMRouter, ModelRegistry, gemini_factory

    registry = ModelRegistry(DEFAULT_CATALOG)
    router = LLMRouter(registry)
    router.register_operator(
        Operator.GOOGLE,
        factory=gemini_factory,
        api_keys=["AIza..."],
    )

    llm = router.create_provider(tags=frozenset({ModelTag.CODING, ModelTag.CHEAP}))
    response = llm.generate("Review this code", response_schema=ReviewResult)
"""

from __future__ import annotations

import dataclasses
import logging
from functools import partial
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel

from ai_reviewer.llm.base import LLMProvider
from ai_reviewer.llm.key_pool import _mask_key
from ai_reviewer.utils.retry import (
    AuthenticationError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ai_reviewer.llm.base import LLMResponse
    from ai_reviewer.llm.key_pool import KeyPool
    from ai_reviewer.llm.models import ModelCard, ModelTag, Operator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ModelNotFoundError(LookupError):
    """No model matched the query criteria.

    Attributes:
        query: Human-readable description of the failed query.
    """

    def __init__(self, query: str) -> None:
        super().__init__(f"No model found matching: {query}")
        self.query = query


# ---------------------------------------------------------------------------
# ProviderFactory protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ProviderFactory(Protocol):
    """Callable that creates an ``LLMProvider`` from a model card and keys.

    Implementations should handle single-key and multi-key scenarios
    (e.g. returning a rotating provider when multiple keys are given).
    """

    def __call__(self, card: ModelCard, api_keys: list[str]) -> LLMProvider:
        """Create a configured LLM provider.

        Args:
            card: The resolved model descriptor.
            api_keys: One or more API keys for the operator.

        Returns:
            A ready-to-use LLMProvider instance.
        """
        ...


# ---------------------------------------------------------------------------
# ModelRegistry
# ---------------------------------------------------------------------------


class ModelRegistry:
    """Queryable collection of ``ModelCard`` instances.

    The registry stores cards by name and supports filtering by operator,
    tags, or both.  Deprecated models are excluded from filter queries but
    can still be retrieved by exact name via ``get()``.

    Args:
        cards: Initial set of model cards to register.
    """

    def __init__(self, cards: Iterable[ModelCard] = ()) -> None:
        self._cards: dict[str, ModelCard] = {}
        for card in cards:
            self._cards[card.name] = card

    @property
    def size(self) -> int:
        """Return total number of registered models (including deprecated)."""
        return len(self._cards)

    @property
    def operators(self) -> frozenset[Operator]:
        """Return all operators that have at least one non-deprecated model."""
        return frozenset(c.operator for c in self._cards.values() if not c.deprecated)

    def register(self, card: ModelCard) -> None:
        """Add or replace a model card in the registry.

        Args:
            card: The model card to register.
        """
        self._cards[card.name] = card

    def get(self, name: str) -> ModelCard:
        """Look up a model by exact name.

        Unlike filter methods, ``get()`` returns deprecated models too.

        Args:
            name: The model identifier string.

        Returns:
            The matching ModelCard.

        Raises:
            ModelNotFoundError: If no model with that name exists.
        """
        card = self._cards.get(name)
        if card is None:
            query = f"name={name!r}"
            raise ModelNotFoundError(query)
        return card

    def by_operator(self, operator: Operator) -> tuple[ModelCard, ...]:
        """Return all non-deprecated models for the given operator.

        Args:
            operator: The provider operator to filter by.

        Returns:
            Tuple of matching cards (may be empty).
        """
        return tuple(c for c in self._cards.values() if c.operator == operator and not c.deprecated)

    def by_tags(self, tags: frozenset[ModelTag]) -> tuple[ModelCard, ...]:
        """Return all non-deprecated models matching ALL given tags.

        Args:
            tags: Required tags (AND logic).

        Returns:
            Tuple of matching cards (may be empty).
        """
        return tuple(c for c in self._cards.values() if c.matches_tags(tags) and not c.deprecated)

    def by_operator_and_tags(
        self,
        operator: Operator,
        tags: frozenset[ModelTag],
    ) -> tuple[ModelCard, ...]:
        """Return non-deprecated models matching operator AND all tags.

        Args:
            operator: The provider operator.
            tags: Required tags (AND logic).

        Returns:
            Tuple of matching cards (may be empty).
        """
        return tuple(
            c
            for c in self._cards.values()
            if c.operator == operator and c.matches_tags(tags) and not c.deprecated
        )

    def default_for(self, operator: Operator) -> ModelCard:
        """Return the default model for the given operator.

        Args:
            operator: The provider operator.

        Returns:
            The ModelCard with ``is_default=True`` for that operator.

        Raises:
            ModelNotFoundError: If no non-deprecated default exists.
        """
        for card in self._cards.values():
            if card.operator == operator and card.is_default and not card.deprecated:
                return card
        query = f"default for operator={operator.value!r}"
        raise ModelNotFoundError(query)

    def sync_availability(
        self,
        operator: Operator,
        available_names: frozenset[str],
    ) -> int:
        """Update deprecated flags based on provider-reported availability.

        Models belonging to *operator* whose name is NOT in
        *available_names* are marked ``deprecated=True``.  Models that
        ARE in the set are marked ``deprecated=False`` (un-deprecation).
        Models of other operators are unchanged.

        Args:
            operator: The operator whose models to check.
            available_names: Set of currently available model names.

        Returns:
            Number of cards whose ``deprecated`` flag was changed.
        """
        changed = 0
        for name, card in list(self._cards.items()):
            if card.operator != operator:
                continue
            should_deprecate = name not in available_names
            if should_deprecate != card.deprecated:
                self._cards[name] = dataclasses.replace(card, deprecated=should_deprecate)
                changed += 1
        return changed


# ---------------------------------------------------------------------------
# LLMRouter
# ---------------------------------------------------------------------------


class LLMRouter:
    """Route model requests to the appropriate LLM provider.

    Resolution priority for ``resolve()``:

    1. Exact model name (``model`` given) -- ignores operator/tags.
    2. Operator + tags -- picks best match among filtered candidates.
    3. Operator only -- returns operator's default model.
    4. Tags only -- picks best match across all operators.

    Args:
        registry: The model registry to query.
    """

    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry
        self._factories: dict[Operator, ProviderFactory] = {}
        self._api_keys: dict[Operator, list[str]] = {}

    @property
    def registry(self) -> ModelRegistry:
        """Return the underlying model registry."""
        return self._registry

    @property
    def available_operators(self) -> frozenset[Operator]:
        """Operators that have both a registered factory and API keys."""
        return frozenset(
            op
            for op in self._registry.operators
            if op in self._factories and op in self._api_keys and self._api_keys[op]
        )

    def register_operator(
        self,
        operator: Operator,
        *,
        factory: ProviderFactory,
        api_keys: list[str],
    ) -> None:
        """Register a factory and API keys for an operator.

        Args:
            operator: The operator to register.
            factory: Callable that creates LLMProvider instances.
            api_keys: One or more API key strings.
        """
        self._factories[operator] = factory
        self._api_keys[operator] = list(api_keys)

    def resolve(
        self,
        *,
        model: str | None = None,
        operator: Operator | None = None,
        tags: frozenset[ModelTag] | None = None,
    ) -> ModelCard:
        """Resolve a model card based on the given criteria.

        Args:
            model: Exact model name to look up.
            operator: Filter by operator.
            tags: Filter by tags (AND logic).

        Returns:
            The resolved ModelCard.

        Raises:
            ModelNotFoundError: If no model matches the criteria.
            ValueError: If none of model/operator/tags are specified.
        """
        # Priority 1: exact model name
        if model is not None:
            return self._registry.get(model)

        # Priority 2: operator + tags
        if operator is not None and tags is not None:
            candidates = self._registry.by_operator_and_tags(operator, tags)
            if not candidates:
                tag_str = ", ".join(t.value for t in sorted(tags, key=lambda t: t.value))
                query = f"operator={operator.value!r}, tags={{{tag_str}}}"
                raise ModelNotFoundError(query)
            return _pick_best(candidates)

        # Priority 3: operator only → default
        if operator is not None:
            return self._registry.default_for(operator)

        # Priority 4: tags only → best across all operators
        if tags is not None:
            candidates = self._registry.by_tags(tags)
            if not candidates:
                tag_str = ", ".join(t.value for t in sorted(tags, key=lambda t: t.value))
                query = f"tags={{{tag_str}}}"
                raise ModelNotFoundError(query)
            return _pick_best(candidates)

        msg = "At least one of model, operator, or tags must be specified"
        raise ValueError(msg)

    def create_provider(
        self,
        *,
        model: str | None = None,
        operator: Operator | None = None,
        tags: frozenset[ModelTag] | None = None,
    ) -> LLMProvider:
        """Resolve a model and create a configured LLMProvider.

        Args:
            model: Exact model name.
            operator: Filter by operator.
            tags: Filter by tags.

        Returns:
            A configured LLMProvider ready for ``generate()`` calls.

        Raises:
            ModelNotFoundError: If no model matches.
            NotImplementedError: If no factory registered for the operator.
            ValueError: If no API keys configured for the operator.
        """
        card = self.resolve(model=model, operator=operator, tags=tags)

        if card.operator not in self._factories:
            msg = f"No factory registered for operator {card.operator.value!r}"
            raise NotImplementedError(msg)

        keys = self._api_keys.get(card.operator)
        if not keys:
            msg = f"No API keys configured for operator {card.operator.value!r}"
            raise ValueError(msg)

        factory = self._factories[card.operator]

        logger.debug(
            "Creating provider: model=%s, operator=%s, keys=%d",
            card.name,
            card.operator.value,
            len(keys),
        )

        return factory(card, keys)


# ---------------------------------------------------------------------------
# Scoring / selection
# ---------------------------------------------------------------------------


def _pick_best(candidates: tuple[ModelCard, ...]) -> ModelCard:
    """Pick the best model from a set of candidates.

    Strategy (in order of priority):
    1. Prefer ``is_default=True`` models.
    2. Prefer cheaper models (lower total price per 1M tokens).
    3. Prefer larger context windows (tie-breaker).

    Args:
        candidates: Non-empty tuple of candidate models.

    Returns:
        The best candidate according to the scoring strategy.
    """

    def _score(card: ModelCard) -> tuple[int, float, int]:
        return (
            0 if card.is_default else 1,
            card.input_price_per_mtok + card.output_price_per_mtok,
            -card.context_window,
        )

    return min(candidates, key=_score)


# ---------------------------------------------------------------------------
# Built-in factories
# ---------------------------------------------------------------------------


def gemini_factory(card: ModelCard, api_keys: list[str]) -> LLMProvider:
    """Create a Google Gemini provider from a model card and API keys.

    Uses ``RotatingGeminiProvider`` when multiple keys are provided,
    plain ``GeminiProvider`` for a single key.

    Args:
        card: Model descriptor (must be a Google operator card).
        api_keys: One or more Google API keys.

    Returns:
        A configured LLMProvider.
    """
    from ai_reviewer.llm.gemini import GeminiProvider  # noqa: PLC0415
    from ai_reviewer.llm.key_pool import KeyPool, RotatingGeminiProvider  # noqa: PLC0415

    if len(api_keys) == 1:
        return GeminiProvider(api_key=api_keys[0], model_name=card.name)
    pool = KeyPool(api_keys)
    return RotatingGeminiProvider(key_pool=pool, model_name=card.name)


def mistral_factory(
    card: ModelCard,
    api_keys: list[str],
    *,
    server_url: str | None = None,
) -> LLMProvider:
    """Create a Mistral provider from a model card and API keys.

    Uses key rotation when multiple keys are provided, mirroring the
    Gemini pattern with ``KeyPool``.

    Args:
        card: Model descriptor (must be a Mistral operator card).
        api_keys: One or more Mistral API keys.
        server_url: Custom API base URL (e.g. ``https://codestral.mistral.ai``).

    Returns:
        A configured LLMProvider.
    """
    from ai_reviewer.llm.key_pool import KeyPool  # noqa: PLC0415
    from ai_reviewer.llm.mistral import MistralProvider  # noqa: PLC0415

    def _build(key: str) -> MistralProvider:
        return MistralProvider(api_key=key, model_name=card.name, server_url=server_url)

    if len(api_keys) == 1:
        return _build(api_keys[0])
    pool = KeyPool(api_keys)
    return _RotatingProvider(pool, _build)


class _RotatingProvider(LLMProvider):
    """Generic key-rotating wrapper for any LLM provider.

    For each key the underlying provider is allowed to exhaust its
    ``@with_retry`` budget.  If it still fails with a rotatable error,
    the next key is tried.
    """

    _ROTATABLE = (QuotaExhaustedError, AuthenticationError, RateLimitError, ServerError)

    def __init__(
        self,
        key_pool: KeyPool,
        provider_builder: Callable[[str], LLMProvider],
    ) -> None:
        self._key_pool = key_pool
        self._builder = provider_builder
        self._model_name_str = ""

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return self._model_name_str

    def generate[T: BaseModel](  # type: ignore[override]
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: type[T] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse[T] | LLMResponse[str]:
        """Generate with key rotation on transient errors."""
        last_error: Exception | None = None

        for key in self._key_pool:
            provider = self._builder(key)
            self._model_name_str = provider.model_name
            try:
                return provider.generate(
                    prompt,
                    system_prompt=system_prompt,
                    response_schema=response_schema,
                    temperature=temperature,
                )
            except self._ROTATABLE as exc:
                last_error = exc
                logger.warning(
                    "Key %s failed on model %s (%s), rotating",
                    _mask_key(key),
                    provider.model_name,
                    type(exc).__name__,
                )

        assert last_error is not None
        raise last_error


# ---------------------------------------------------------------------------
# Settings → Router bridge
# ---------------------------------------------------------------------------

# Mapping from provider string → (Operator, factory)
_PROVIDER_REGISTRY: dict[str, tuple[str, ProviderFactory]] = {
    "google": ("GOOGLE", gemini_factory),
    "mistral": ("MISTRAL", mistral_factory),
}


def create_router(settings: object) -> LLMRouter:
    """Build an ``LLMRouter`` pre-configured from application settings.

    Registers all operators whose API keys are present in settings.

    Args:
        settings: Application ``Settings`` instance.  Typed as ``object``
            to avoid a compile-time dependency on ``core.config``.

    Returns:
        A ready-to-use LLMRouter with available operators registered.
    """
    from ai_reviewer.llm.catalog import DEFAULT_CATALOG  # noqa: PLC0415
    from ai_reviewer.llm.models import Operator  # noqa: PLC0415

    registry = ModelRegistry(DEFAULT_CATALOG)
    router = LLMRouter(registry)

    for provider_name, (op_attr, factory) in _PROVIDER_REGISTRY.items():
        keys = settings.get_provider_api_keys(provider_name)  # type: ignore[attr-defined]
        if keys:
            operator = Operator(getattr(Operator, op_attr))
            effective_factory: ProviderFactory = factory
            if provider_name == "mistral":
                url: str | None = getattr(settings, "mistral_api_url", None)
                if url:
                    effective_factory = partial(mistral_factory, server_url=url)
            router.register_operator(operator, factory=effective_factory, api_keys=keys)

    return router


__all__ = [
    "LLMRouter",
    "ModelNotFoundError",
    "ModelRegistry",
    "ProviderFactory",
    "create_router",
    "gemini_factory",
    "mistral_factory",
]
