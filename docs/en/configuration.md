# Configuration

All settings are configured via environment variables.

!!! tip "Migration: `AI_REVIEWER_` prefix"
    Since v1.0.0a7, all environment variables support the `AI_REVIEWER_` prefix (e.g., `AI_REVIEWER_GOOGLE_API_KEY`). Old names (e.g., `GOOGLE_API_KEY`) still work as fallback. We recommend migrating to the new names to avoid conflicts with other tools in org-level CI/CD configurations.

---

## Required Variables

| Variable | Description | Example | How to get |
|----------|-------------|---------|------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Google Gemini API key (comma-separated for multi-key rotation) | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_MISTRAL_API_KEY` | Mistral API key (comma-separated for multi-key rotation) | `sk-...` | [Mistral Console](https://console.mistral.ai/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub token (for GitHub) | `ghp_...` | [Instructions](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab token (for GitLab) | `glpat-...` | [Instructions](gitlab.md#get-token) |

!!! warning "At least one LLM API key required"
    You need at least one LLM API key: `AI_REVIEWER_GOOGLE_API_KEY` **or** `AI_REVIEWER_MISTRAL_API_KEY` (or both).
    The key for the primary provider (set by `AI_REVIEWER_LLM_PROVIDER`) is required.

!!! warning "At least one platform token required"
    You need `AI_REVIEWER_GITHUB_TOKEN` **or** `AI_REVIEWER_GITLAB_TOKEN` depending on the platform.

!!! info "GitLab token types"
    For GitLab, you can use a **Personal Access Token** (works on all plans, including Free)
    or a **Project Access Token** (requires GitLab Premium/Ultimate).

---

## Optional Variables {#optional}

### General

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `AI_REVIEWER_LOG_LEVEL` | Logging level | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_REVIEWER_API_TIMEOUT` | Request timeout (sec) | `60` | 1-300 |

### Language

| Variable | Description | Default | Examples |
|----------|-------------|---------|----------|
| `AI_REVIEWER_LANGUAGE` | Response language | `en` | `uk`, `de`, `es`, `it`, `me` |
| `AI_REVIEWER_LANGUAGE_MODE` | Detection mode | `adaptive` | `adaptive`, `fixed` |

**Language modes:**

- **`adaptive`** (default) — automatically detects language from PR/MR context (description, comments, linked task)
- **`fixed`** — always uses the language from `AI_REVIEWER_LANGUAGE`

!!! tip "ISO 639"
    `AI_REVIEWER_LANGUAGE` accepts any valid ISO 639 code:

    - 2-letter: `en`, `uk`, `de`, `es`, `it`
    - 3-letter: `ukr`, `deu`, `spa`
    - Names: `English`, `Ukrainian`, `German`

### LLM {#llm}

#### Provider Selection

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_LLM_PROVIDER` | Primary LLM provider | `google` |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Fallback provider (used when primary is exhausted) | _(none)_ |

Supported providers: `google`, `mistral`.

When both primary and fallback providers are configured, the system tries all primary provider models first, then all fallback provider models. Example with `LLM_PROVIDER=mistral` and `LLM_FALLBACK_PROVIDER=google`:

```
mistral-large → mistral-small → gemini-2.5-flash → gemini-2.5-flash-lite
```

#### Google Gemini Models

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_GEMINI_MODEL` | Primary Gemini model | `gemini-2.5-flash` |
| `AI_REVIEWER_GEMINI_MODEL_FALLBACK` | Fallback model chain (comma-separated) | `gemini-3.1-flash-preview,...` |

| Model | Description | Cost |
|-------|-------------|------|
| `gemini-2.5-flash` | Fast, stable, reasoning (default) | $0.075 / 1M input |
| `gemini-3.1-flash-preview` | Frontier-class flash (preview) | $0.075 / 1M input |
| `gemini-2.5-flash-lite` | Fastest and cheapest in 2.5 | $0.01875 / 1M input |
| `gemini-2.5-pro` | Most powerful, deep reasoning | $1.25 / 1M input |

:material-link: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

#### Mistral Models

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_MISTRAL_MODEL` | Primary Mistral model | `mistral-large-latest` |
| `AI_REVIEWER_MISTRAL_MODEL_FALLBACK` | Fallback model chain (comma-separated) | _(none)_ |
| `AI_REVIEWER_MISTRAL_API_URL` | Custom API base URL | _(none)_ |

| Model | Description | Context | Cost (input / output) |
|-------|-------------|---------|----------------------|
| `mistral-large-latest` | Most capable, MoE 41B/675B (default) | 256k | $0.50 / $1.50 |
| `mistral-medium-latest` | Balanced performance/cost | 128k | $0.40 / $2.00 |
| `mistral-small-latest` | Fast and cheap, hybrid 6.5B/119B | 256k | $0.15 / $0.60 |
| `codestral-latest` | Optimized for code, FIM support | 128k | $0.30 / $0.90 |
| `devstral-latest` | Coding agent, cheapest Mistral | 256k | $0.10 / $0.30 |

!!! tip "Codestral free tier"
    Codestral has a separate free tier at `https://codestral.mistral.ai` with its own API key.
    Set `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai` and use a key from [codestral.mistral.ai](https://codestral.mistral.ai/).
    The paid Codestral via `api.mistral.ai` does **not** require a custom URL.

:material-link: [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing)

#### Other Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_REVIEW_SPLIT_THRESHOLD` | Char threshold for code+test split review | `30000` |

!!! note "Pricing accuracy"
    Prices are listed as of the release date and may change. Check the provider's pricing page for current information.

!!! tip "Free Tier"
    Both Google Gemini and Mistral offer free tiers sufficient for code review of a team of **4-8 developers**. Combine two providers for maximum reliability.

### Review

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `AI_REVIEWER_REVIEW_MAX_FILES` | Max files in context | `20` | 1-100 |
| `AI_REVIEWER_REVIEW_MAX_DIFF_LINES` | Max diff lines per file | `500` | 1-5000 |
| `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS` | Max MR comment chars in AI prompt | `3000` | 0-20000 |
| `AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS` | Include bot comments in prompt | `true` | true/false |
| `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS` | Post inline comments on lines | `true` | true/false |
| `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE` | Group comments into dialogue threads | `true` | true/false |

!!! info "Discussion context"
    The AI reviewer reads existing MR/PR comments to avoid repeating suggestions
    that were already discussed. Set `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS=0` to disable.

!!! info "Inline comments"
    When `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS=true` (default), issues with file/line info are posted as inline comments on the code, with a short summary as the review body. Set to `false` for a single summary comment.

!!! info "Dialogue threads"
    When `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE=true` (default), comments are grouped into
    conversation threads so the AI understands reply chains. Set to `false` for flat rendering.

### Discovery

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | Enable project discovery before review | `true` | true/false |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | Always post discovery comment (default: only on gaps) | `false` | true/false |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | Discovery pipeline timeout in seconds | `30` | 1-300 |

!!! info "Project Discovery"
    When enabled, AI ReviewBot automatically analyzes your repository (languages, CI pipeline, config files) before each review to provide smarter feedback. Set to `false` to disable. See [Discovery →](discovery.md) for details.

!!! info "Verbose mode"
    When `AI_REVIEWER_DISCOVERY_VERBOSE=true`, the discovery comment is always posted and includes all Attention Zones (well-covered, weakly-covered, not-covered). Default mode only posts when there are gaps or uncovered zones.

### GitLab

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_GITLAB_URL` | GitLab server URL | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    For self-hosted GitLab, set `AI_REVIEWER_GITLAB_URL`:
    ```bash
    export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## .env File

It's convenient to store configuration in `.env`:

```bash
# .env

# LLM provider (pick one or both)
AI_REVIEWER_GOOGLE_API_KEY=AIza...
# AI_REVIEWER_MISTRAL_API_KEY=sk-...
# AI_REVIEWER_LLM_PROVIDER=google
# AI_REVIEWER_LLM_FALLBACK_PROVIDER=mistral

# Platform token
AI_REVIEWER_GITHUB_TOKEN=ghp_...

# Optional
AI_REVIEWER_LANGUAGE=uk
AI_REVIEWER_LANGUAGE_MODE=adaptive
AI_REVIEWER_GEMINI_MODEL=gemini-2.5-flash
AI_REVIEWER_LOG_LEVEL=INFO
```

!!! danger "Security"
    **Never commit `.env` to git!**

    Add to `.gitignore`:
    ```
    .env
    .env.*
    ```

---

## CI/CD Configuration

### GitHub Actions

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
  AI_REVIEWER_GITHUB_TOKEN: ${{ github.token }}  # Automatic
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  # AI_REVIEWER_GOOGLE_API_KEY and AI_REVIEWER_GITLAB_TOKEN
  # are inherited from CI/CD Variables automatically
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

---

## Validation

AI Code Reviewer validates configuration at startup:

### Validation Errors

```
ValidationError: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Solution:** Check that the variable is set correctly.

```
ValidationError: Invalid language code 'xyz'
```

**Solution:** Use a valid ISO 639 code.

```
ValidationError: LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Solution:** Use one of the allowed levels.

---

## Configuration Examples

### Minimal (GitHub)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
```

### Minimal (GitLab)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
```

### Ukrainian language, fixed

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LANGUAGE=uk
export AI_REVIEWER_LANGUAGE_MODE=fixed
```

### Self-hosted GitLab

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
```

### Debug mode

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LOG_LEVEL=DEBUG
```

---

## Configuration Priority

1. **Environment variables** (highest)
2. **`.env` file** in the current directory

---

## Next Step

- [GitHub integration →](github.md)
- [GitLab integration →](gitlab.md)
