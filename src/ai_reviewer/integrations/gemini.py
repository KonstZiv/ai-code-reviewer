"""Gemini integration for AI Code Reviewer (compatibility layer).

This module provides backward-compatible entry points that delegate to
:mod:`ai_reviewer.llm.gemini`. New code should use ``GeminiProvider``
directly.

.. deprecated::
    ``GeminiClient`` is deprecated and will be removed in v1.0.0 stable.
    Use :class:`ai_reviewer.llm.gemini.GeminiProvider` instead.
"""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

from ai_reviewer.core.models import ReviewMetrics, ReviewResult, TaskAlignmentStatus
from ai_reviewer.integrations.prompts import (
    CODE_SUMMARY_INSTRUCTION,
    SYSTEM_PROMPT,
    build_review_prompt,
    build_split_review_prompt,
    partition_changes,
)
from ai_reviewer.llm.gemini import (
    DEFAULT_MODEL,
    DEFAULT_PRICING,
    GEMINI_PRICING,
    GeminiProvider,
    calculate_cost,
)
from ai_reviewer.llm.router import create_router
from ai_reviewer.utils.retry import (
    AllModelsFailedError,
    NotFoundError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
)

if TYPE_CHECKING:
    from pydantic import SecretStr

    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import FileChange, ReviewContext
    from ai_reviewer.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API.

    .. deprecated::
        Use :class:`ai_reviewer.llm.gemini.GeminiProvider` instead.
        ``GeminiClient`` will be removed in v1.0.0 stable.

    Attributes:
        client: The underlying GeminiProvider.
        model_name: The name of the model to use.
    """

    def __init__(self, api_key: SecretStr, model_name: str = DEFAULT_MODEL) -> None:
        """Initialize Gemini client.

        Args:
            api_key: Google API key.
            model_name: Model name to use.
        """
        warnings.warn(
            "GeminiClient is deprecated and will be removed in v1.0.0 stable. "
            "Use ai_reviewer.llm.gemini.GeminiProvider instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._provider = GeminiProvider(
            api_key=api_key.get_secret_value(),
            model_name=model_name,
        )
        self.model_name = model_name
        logger.debug("GeminiClient initialized with model %s (deprecated)", model_name)

    def generate_review(self, prompt: str) -> ReviewResult:
        """Generate a code review from the given prompt.

        Args:
            prompt: The user prompt containing code changes and context.

        Returns:
            Structured review result with metrics.
        """
        response = self._provider.generate(
            prompt,
            system_prompt=SYSTEM_PROMPT,
            response_schema=ReviewResult,
        )

        result = response.content
        assert isinstance(result, ReviewResult)  # guaranteed by response_schema

        metrics = ReviewMetrics(
            model_name=response.model_name,
            operator="Google",
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            api_latency_ms=response.latency_ms,
            estimated_cost_usd=response.estimated_cost_usd,
        )

        return result.model_copy(update={"metrics": metrics})


# ── Public API ────────────────────────────────────────────────────────


def analyze_code_changes(context: ReviewContext, settings: Settings) -> ReviewResult:
    """Analyze code changes using Gemini with automatic model fallback.

    When the prompt exceeds ``settings.review_split_threshold`` characters
    and the MR contains both production and test files, the review is
    performed in two sequential LLM requests:

    1. Production code (with ``code_summary`` instruction).
    2. Test files (with the ``code_summary`` as context).

    Args:
        context: The review context (MR, task, etc.).
        settings: Application settings.

    Returns:
        The review result with attached metrics.
    """
    logger.info("Starting code analysis for PR #%s", context.mr.number)

    # 1. Build full prompt to measure size
    prompt = build_review_prompt(context, settings)
    logger.debug("Generated prompt of length %d chars", len(prompt))

    # 2. Check if splitting is needed
    if len(prompt) > settings.review_split_threshold:
        prod_changes, test_changes = partition_changes(context.mr.changes)
        if prod_changes and test_changes:
            logger.info(
                "Prompt size %d > threshold %d; splitting review: "
                "%d production file(s), %d test file(s)",
                len(prompt),
                settings.review_split_threshold,
                len(prod_changes),
                len(test_changes),
            )
            return _analyze_split(context, settings, prod_changes, test_changes)

    # 3. Single-pass review (under threshold or all-one-type)
    return _analyze_single(settings, prompt)


# ── Internal helpers ──────────────────────────────────────────────────


def _build_fallback_chain(
    settings: Settings,
) -> list[tuple[str, str]]:
    """Build model fallback chain from settings.

    Returns a list of ``(model_name, operator_label)`` tuples. The primary
    provider's models come first, followed by the fallback provider's
    models (if configured).

    Args:
        settings: Application settings.

    Returns:
        Ordered list of (model, operator_label) to try.
    """
    chain: list[tuple[str, str]] = []

    # Primary provider models
    primary = settings.llm_provider
    primary_label = primary.capitalize()
    primary_model = settings.get_provider_model(primary)
    primary_fallbacks = settings.get_provider_fallback_models(primary)
    for m in [primary_model, *primary_fallbacks]:
        chain.append((m, primary_label))

    # Fallback provider models (if configured and different from primary)
    fallback = settings.llm_fallback_provider
    if fallback and fallback != primary:
        fb_label = fallback.capitalize()
        fb_model = settings.get_provider_model(fallback)
        fb_fallbacks = settings.get_provider_fallback_models(fallback)
        for m in [fb_model, *fb_fallbacks]:
            chain.append((m, fb_label))

    return chain


def _call_llm(
    router: LLMRouter,
    settings: Settings,
    prompt: str,
    system_prompt: str,
) -> ReviewResult:
    """Call LLM with cross-provider model fallback chain.

    Strategy: try each model in order (primary provider models first,
    then fallback provider models), using the router to create the
    appropriate provider per model.

    Args:
        router: Configured LLM router.
        settings: Application settings.
        prompt: User prompt.
        system_prompt: System prompt.

    Returns:
        ReviewResult with metrics attached.

    Raises:
        AllModelsFailedError: When all models in the chain fail.
        ServerError: When primary fails and no fallback is configured.
        RateLimitError: When primary fails and no fallback is configured.
        QuotaExhaustedError: When primary fails and no fallback is configured.
    """
    chain = _build_fallback_chain(settings)
    failures: list[tuple[str, Exception]] = []
    fallback_reason: str | None = None

    for model_name, operator_label in chain:
        try:
            provider = router.create_provider(model=model_name)
            response = provider.generate(
                prompt,
                system_prompt=system_prompt,
                response_schema=ReviewResult,
            )
            break  # success
        except (ServerError, RateLimitError, QuotaExhaustedError, NotFoundError) as err:
            failures.append((model_name, err))
            logger.warning(
                "Model %s (%s) failed (%s: %s). %d model(s) remaining.",
                model_name,
                operator_label,
                type(err).__name__,
                str(err)[:120],
                len(chain) - len(failures),
            )
            if len(failures) == 1:
                fallback_reason = f"{model_name} \u2192 {type(err).__name__}"
    else:
        # All models exhausted
        if len(failures) == 1:
            raise failures[0][1]
        details = ", ".join(f"{m} ({type(e).__name__})" for m, e in failures)
        is_quota = all(isinstance(e, QuotaExhaustedError) for _, e in failures)
        msg = f"All {len(failures)} model(s) failed: {details}"
        raise AllModelsFailedError(
            msg,
            is_quota=is_quota,
        ) from failures[-1][1]

    result = response.content
    assert isinstance(result, ReviewResult)  # guaranteed by response_schema

    metrics = ReviewMetrics(
        model_name=response.model_name,
        operator=operator_label,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.total_tokens,
        api_latency_ms=response.latency_ms,
        estimated_cost_usd=response.estimated_cost_usd,
        fallback_reason=fallback_reason,
    )

    return result.model_copy(update={"metrics": metrics})


def _analyze_single(
    settings: Settings,
    prompt: str,
) -> ReviewResult:
    """Perform single-pass review.

    Args:
        settings: Application settings.
        prompt: Pre-built review prompt.

    Returns:
        Review result with metrics.
    """
    router = create_router(settings)
    result = _call_llm(router, settings, prompt, SYSTEM_PROMPT)
    logger.info("Analysis complete. Found %d issues.", result.issue_count)
    return result


def _analyze_split(
    context: ReviewContext,
    settings: Settings,
    prod_changes: tuple[FileChange, ...],
    test_changes: tuple[FileChange, ...],
) -> ReviewResult:
    """Perform two-pass split review: production code then tests.

    Pass 1 reviews production code and generates a compressed summary.
    Pass 2 reviews test files using that summary as context.

    Args:
        context: Full review context.
        settings: Application settings.
        prod_changes: Production file changes.
        test_changes: Test file changes.

    Returns:
        Merged review result from both passes.
    """
    router = create_router(settings)

    # Pass 1: Production code with code_summary instruction
    code_prompt = build_split_review_prompt(context, settings, prod_changes)
    system_with_summary = SYSTEM_PROMPT + CODE_SUMMARY_INSTRUCTION

    code_result = _call_llm(router, settings, code_prompt, system_with_summary)
    logger.info(
        "Code pass complete: %d issue(s), summary %d chars",
        code_result.issue_count,
        len(code_result.code_summary),
    )

    # Pass 2: Test files with code_summary context
    test_prompt = build_split_review_prompt(
        context, settings, test_changes, code_summary=code_result.code_summary
    )
    test_result = _call_llm(router, settings, test_prompt, SYSTEM_PROMPT)
    logger.info("Test pass complete: %d issue(s)", test_result.issue_count)

    return _merge_review_results(code_result, test_result)


def _merge_review_results(
    code_result: ReviewResult,
    test_result: ReviewResult,
) -> ReviewResult:
    """Merge ReviewResult from code and test review passes.

    Args:
        code_result: Result from reviewing production code.
        test_result: Result from reviewing test files.

    Returns:
        Combined ReviewResult with merged issues, practices, and metrics.
    """
    merged_metrics = _merge_metrics(code_result.metrics, test_result.metrics)

    combined_summary = code_result.summary
    if test_result.summary:
        combined_summary = f"{code_result.summary}\n\n**Test review:** {test_result.summary}"

    merged_alignment = _merge_task_alignment(code_result.task_alignment, test_result.task_alignment)
    merged_reasoning = "\n".join(
        r for r in (code_result.task_alignment_reasoning, test_result.task_alignment_reasoning) if r
    )

    return ReviewResult(
        issues=code_result.issues + test_result.issues,
        good_practices=code_result.good_practices + test_result.good_practices,
        task_alignment=merged_alignment,
        task_alignment_reasoning=merged_reasoning,
        summary=combined_summary,
        code_summary=code_result.code_summary,
        detected_language=code_result.detected_language,
        reviewed_at=code_result.reviewed_at,
        metrics=merged_metrics,
    )


# Worst-case wins: MISALIGNED < INSUFFICIENT_DATA < ALIGNED
_ALIGNMENT_PRIORITY: dict[TaskAlignmentStatus, int] = {
    TaskAlignmentStatus.MISALIGNED: 0,
    TaskAlignmentStatus.INSUFFICIENT_DATA: 1,
    TaskAlignmentStatus.ALIGNED: 2,
}


def _merge_task_alignment(
    code_alignment: TaskAlignmentStatus,
    test_alignment: TaskAlignmentStatus,
) -> TaskAlignmentStatus:
    """Pick the worst-case task alignment from two review passes."""
    code_prio = _ALIGNMENT_PRIORITY.get(code_alignment, 1)
    test_prio = _ALIGNMENT_PRIORITY.get(test_alignment, 1)
    return code_alignment if code_prio <= test_prio else test_alignment


def _merge_metrics(
    code_metrics: ReviewMetrics | None,
    test_metrics: ReviewMetrics | None,
) -> ReviewMetrics | None:
    """Sum metrics from two review passes."""
    if code_metrics and test_metrics:
        return ReviewMetrics(
            model_name=code_metrics.model_name,
            operator=code_metrics.operator,
            prompt_tokens=code_metrics.prompt_tokens + test_metrics.prompt_tokens,
            completion_tokens=code_metrics.completion_tokens + test_metrics.completion_tokens,
            total_tokens=code_metrics.total_tokens + test_metrics.total_tokens,
            api_latency_ms=code_metrics.api_latency_ms + test_metrics.api_latency_ms,
            estimated_cost_usd=code_metrics.estimated_cost_usd + test_metrics.estimated_cost_usd,
            fallback_reason=code_metrics.fallback_reason or test_metrics.fallback_reason,
        )
    return code_metrics or test_metrics


# Re-exports for backward compatibility
__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PRICING",
    "GEMINI_PRICING",
    "GeminiClient",
    "analyze_code_changes",
    "calculate_cost",
]
