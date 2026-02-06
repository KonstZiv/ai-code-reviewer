# =============================================================================
# AI Code Reviewer - Multi-stage Dockerfile
# =============================================================================
# Build: docker build -t ai-code-reviewer .
# Run:   docker run --rm -e GOOGLE_API_KEY=... ai-code-reviewer --help
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies with uv
# -----------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Install git (required for GitPython)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock README.md ./

# Install production dependencies only (no dev dependencies)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src ./src

# Install the project itself
RUN uv sync --frozen --no-dev

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.13-slim-bookworm AS runtime

# Labels for container registry
LABEL org.opencontainers.image.title="AI Code Reviewer"
LABEL org.opencontainers.image.description="AI-powered code review for GitHub and GitLab"
LABEL org.opencontainers.image.source="https://github.com/KonstZiv/ai-code-reviewer"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.authors="Kostyantin Zivenko <kos.zivenko@gmail.com>"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code (needed because uv installs in editable mode)
COPY --from=builder /app/src /app/src

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ai-review --help > /dev/null 2>&1 || exit 1

# Default command - runs ai-review
# Using CMD (not ENTRYPOINT) for compatibility with GitLab CI Runner,
# which executes commands via "sh -c" and conflicts with ENTRYPOINT.
CMD ["ai-review"]
