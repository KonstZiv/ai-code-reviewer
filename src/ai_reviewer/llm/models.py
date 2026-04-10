"""Data types for the LLM router: operators, model tags, and model cards.

This module defines the core value objects used by the router layer to
describe, query, and select LLM models across multiple providers.

Typical usage::

    from ai_reviewer.llm.models import ModelCard, ModelTag, Operator

    card = ModelCard(
        name="gemini-2.5-flash",
        operator=Operator.GOOGLE,
        tags=frozenset({ModelTag.LIGHT, ModelTag.CODING, ModelTag.FAST}),
        context_window=1_048_576,
        input_price_per_mtok=0.075,
        output_price_per_mtok=0.30,
        is_default=True,
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class Operator(str, Enum):
    """LLM provider operator (company).

    Each operator corresponds to an API provider that hosts one or more
    language models.
    """

    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"


@unique
class ModelTag(str, Enum):
    """Capability or cost tag for model selection.

    Tags enable fuzzy model selection: callers request tags like
    ``{CODING, CHEAP}`` and the router picks the best matching model.
    """

    HEAVY = "heavy"
    """Pro-tier model, highest quality output."""

    LIGHT = "light"
    """Flash-tier model, low cost and fast."""

    CODING = "coding"
    """Optimized for code generation and understanding."""

    CHEAP = "cheap"
    """Lowest per-token cost in its class."""

    DEEP_ANALYSIS = "deep_analysis"
    """Extended reasoning, chain-of-thought capable."""

    FAST = "fast"
    """Low latency, suited for interactive use."""

    STRUCTURED_OUTPUT = "structured_output"
    """Native JSON schema / structured output support."""

    LARGE_CONTEXT = "large_context"
    """200K+ token context window."""


@dataclass(frozen=True)
class ModelCard:
    """Immutable descriptor for a single LLM model.

    Each card carries metadata, pricing, and capability tags.
    The ``frozen=True`` constraint ensures cards are safe to share
    across threads and can be used as dict keys.

    Attributes:
        name: Model identifier string (e.g. ``"gemini-2.5-flash"``).
        operator: The provider company.
        tags: Frozenset of capability/cost tags.
        context_window: Maximum input token count.
        input_price_per_mtok: Price per 1 million input tokens (USD).
        output_price_per_mtok: Price per 1 million output tokens (USD).
        is_default: Whether this is the default model for its operator.
        supports_structured: Whether native JSON schema output is supported.
        deprecated: Whether the model has been marked unavailable.
    """

    name: str
    operator: Operator
    tags: frozenset[ModelTag]
    context_window: int
    input_price_per_mtok: float
    output_price_per_mtok: float
    is_default: bool = False
    supports_structured: bool = True
    deprecated: bool = False

    def matches_tags(self, required: frozenset[ModelTag]) -> bool:
        """Check if this model has ALL of the required tags.

        Args:
            required: Tags that must all be present (AND logic).

        Returns:
            True if every tag in *required* is in this card's tags.
            An empty *required* set always returns True.
        """
        return required <= self.tags

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for a request.

        Args:
            input_tokens: Number of input tokens consumed.
            output_tokens: Number of output tokens generated.

        Returns:
            Estimated cost in USD.
        """
        input_cost = (input_tokens / 1_000_000) * self.input_price_per_mtok
        output_cost = (output_tokens / 1_000_000) * self.output_price_per_mtok
        return input_cost + output_cost


__all__ = [
    "ModelCard",
    "ModelTag",
    "Operator",
]
