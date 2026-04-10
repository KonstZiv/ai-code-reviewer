"""Default catalog of known LLM models across all operators.

This module contains the static model registry data. Pricing and context
windows reflect the state as of April 2026. Update this file when
providers change their offerings.

Usage::

    from ai_reviewer.llm.catalog import DEFAULT_CATALOG
    from ai_reviewer.llm.router import ModelRegistry

    registry = ModelRegistry(DEFAULT_CATALOG)
"""

from __future__ import annotations

from ai_reviewer.llm.models import ModelCard, ModelTag, Operator

# Convenience aliases to reduce line noise in the catalog below.
_H = ModelTag.HEAVY
_L = ModelTag.LIGHT
_C = ModelTag.CODING
_CH = ModelTag.CHEAP
_DA = ModelTag.DEEP_ANALYSIS
_F = ModelTag.FAST
_SO = ModelTag.STRUCTURED_OUTPUT
_LC = ModelTag.LARGE_CONTEXT

DEFAULT_CATALOG: tuple[ModelCard, ...] = (
    # ── Google Gemini ──────────────────────────────────────────
    ModelCard(
        name="gemini-2.5-flash",
        operator=Operator.GOOGLE,
        tags=frozenset({_L, _C, _F, _CH, _SO, _LC}),
        context_window=1_048_576,
        input_price_per_mtok=0.075,
        output_price_per_mtok=0.30,
        is_default=True,
    ),
    ModelCard(
        name="gemini-2.5-flash-lite",
        operator=Operator.GOOGLE,
        tags=frozenset({_L, _CH, _F}),
        context_window=1_048_576,
        input_price_per_mtok=0.01875,
        output_price_per_mtok=0.075,
    ),
    ModelCard(
        name="gemini-2.5-pro",
        operator=Operator.GOOGLE,
        tags=frozenset({_H, _C, _DA, _SO, _LC}),
        context_window=1_048_576,
        input_price_per_mtok=1.25,
        output_price_per_mtok=5.00,
    ),
    ModelCard(
        name="gemini-2.0-flash",
        operator=Operator.GOOGLE,
        tags=frozenset({_L, _F, _SO}),
        context_window=1_048_576,
        input_price_per_mtok=0.10,
        output_price_per_mtok=0.40,
    ),
    ModelCard(
        name="gemini-3.1-flash-preview",
        operator=Operator.GOOGLE,
        tags=frozenset({_L, _F, _SO, _LC}),
        context_window=1_048_576,
        input_price_per_mtok=0.075,
        output_price_per_mtok=0.30,
    ),
    ModelCard(
        name="gemini-3.1-flash-lite-preview",
        operator=Operator.GOOGLE,
        tags=frozenset({_L, _CH, _F}),
        context_window=1_048_576,
        input_price_per_mtok=0.01875,
        output_price_per_mtok=0.075,
    ),
    ModelCard(
        name="gemini-3.1-pro-preview",
        operator=Operator.GOOGLE,
        tags=frozenset({_H, _DA, _SO, _LC}),
        context_window=1_048_576,
        input_price_per_mtok=1.25,
        output_price_per_mtok=5.00,
    ),
    # ── Anthropic ──────────────────────────────────────────────
    ModelCard(
        name="claude-sonnet-4-6",
        operator=Operator.ANTHROPIC,
        tags=frozenset({_H, _C, _SO, _LC}),
        context_window=200_000,
        input_price_per_mtok=3.00,
        output_price_per_mtok=15.00,
        is_default=True,
    ),
    ModelCard(
        name="claude-opus-4-6",
        operator=Operator.ANTHROPIC,
        tags=frozenset({_H, _C, _DA, _SO, _LC}),
        context_window=200_000,
        input_price_per_mtok=15.00,
        output_price_per_mtok=75.00,
    ),
    ModelCard(
        name="claude-haiku-4-5",
        operator=Operator.ANTHROPIC,
        tags=frozenset({_L, _F, _CH, _SO}),
        context_window=200_000,
        input_price_per_mtok=0.80,
        output_price_per_mtok=4.00,
    ),
    # ── Mistral ────────────────────────────────────────────────
    ModelCard(
        name="mistral-large-latest",
        operator=Operator.MISTRAL,
        tags=frozenset({_H, _C, _DA, _SO, _LC}),
        context_window=256_000,
        input_price_per_mtok=0.50,
        output_price_per_mtok=1.50,
        is_default=True,
    ),
    ModelCard(
        name="mistral-medium-latest",
        operator=Operator.MISTRAL,
        tags=frozenset({_H, _C, _SO}),
        context_window=128_000,
        input_price_per_mtok=0.40,
        output_price_per_mtok=2.00,
    ),
    ModelCard(
        name="mistral-small-latest",
        operator=Operator.MISTRAL,
        tags=frozenset({_L, _F, _CH, _SO, _LC}),
        context_window=256_000,
        input_price_per_mtok=0.15,
        output_price_per_mtok=0.60,
    ),
    ModelCard(
        name="codestral-latest",
        operator=Operator.MISTRAL,
        tags=frozenset({_C, _L, _F, _SO}),
        context_window=128_000,
        input_price_per_mtok=0.30,
        output_price_per_mtok=0.90,
    ),
    ModelCard(
        name="devstral-latest",
        operator=Operator.MISTRAL,
        tags=frozenset({_C, _L, _CH, _F, _SO, _LC}),
        context_window=256_000,
        input_price_per_mtok=0.10,
        output_price_per_mtok=0.30,
    ),
    # ── DeepSeek ───────────────────────────────────────────────
    ModelCard(
        name="deepseek-chat",
        operator=Operator.DEEPSEEK,
        tags=frozenset({_L, _C, _CH, _F, _SO}),
        context_window=128_000,
        input_price_per_mtok=0.27,
        output_price_per_mtok=1.10,
        is_default=True,
    ),
    ModelCard(
        name="deepseek-reasoner",
        operator=Operator.DEEPSEEK,
        tags=frozenset({_H, _DA, _C}),
        context_window=128_000,
        input_price_per_mtok=0.55,
        output_price_per_mtok=2.19,
        supports_structured=False,
    ),
)

__all__ = ["DEFAULT_CATALOG"]
