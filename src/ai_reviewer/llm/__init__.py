"""LLM provider abstractions for AI Code Reviewer.

Public API:
    - ``LLMProvider`` — abstract base class for LLM backends.
    - ``LLMResponse`` — generic response wrapper with token/cost metrics.
    - ``KeyPool`` — round-robin pool of API keys.
    - ``RotatingGeminiProvider`` — Gemini provider with multi-key rotation.
    - ``Operator`` — LLM provider operator enum.
    - ``ModelTag`` — model capability/cost tag enum.
    - ``ModelCard`` — immutable model descriptor with pricing.
    - ``ModelRegistry`` — queryable model registry.
    - ``LLMRouter`` — model resolution and provider creation.
"""

from ai_reviewer.llm.base import LLMProvider, LLMResponse
from ai_reviewer.llm.key_pool import KeyPool, RotatingGeminiProvider
from ai_reviewer.llm.models import ModelCard, ModelTag, Operator
from ai_reviewer.llm.router import LLMRouter, ModelNotFoundError, ModelRegistry, create_router

__all__ = [
    "KeyPool",
    "LLMProvider",
    "LLMResponse",
    "LLMRouter",
    "ModelCard",
    "ModelNotFoundError",
    "ModelRegistry",
    "ModelTag",
    "Operator",
    "RotatingGeminiProvider",
    "create_router",
]
