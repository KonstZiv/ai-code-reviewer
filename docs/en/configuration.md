# Configuration

All settings are configured via environment variables.

!!! tip "Migration: `AI_REVIEWER_` prefix"
    Since v1.0.0a7, all environment variables support the `AI_REVIEWER_` prefix (e.g., `AI_REVIEWER_GOOGLE_API_KEY`). Old names (e.g., `GOOGLE_API_KEY`) still work as fallback. We recommend migrating to the new names to avoid conflicts with other tools in org-level CI/CD configurations.

---

## Required Variables

| Variable | Description | Example | How to get |
|----------|-------------|---------|------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Google Gemini API key (comma-separated for multi-key rotation) | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub token (for GitHub) | `ghp_...` | [Instructions](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab token (for GitLab) | `glpat-...` | [Instructions](gitlab.md#get-token) |

!!! warning "At least one provider token required"
    You need `AI_REVIEWER_GITHUB_TOKEN` **or** `AI_REVIEWER_GITLAB_TOKEN` depending on the platform.
    These tokens are **provider-specific** — only one is required, matching the platform you use.

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

### LLM

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_GEMINI_MODEL` | Gemini model | `gemini-2.5-flash` |
| `AI_REVIEWER_GEMINI_MODEL_FALLBACK` | Fallback model chain (comma-separated) | `gemini-3.1-flash-preview` |
| `AI_REVIEWER_REVIEW_SPLIT_THRESHOLD` | Char threshold for code+test split review | `30000` |

**Available models:**

| Model | Description | Cost |
|-------|-------------|------|
| `gemini-2.5-flash` | Fast, stable, reasoning (default) | $0.075 / 1M input |
| `gemini-3.1-flash-preview` | Frontier-class flash (preview) | $0.075 / 1M input |
| `gemini-2.5-flash-lite` | Fastest and cheapest in 2.5 | $0.01875 / 1M input |
| `gemini-2.5-pro` | Most powerful, deep reasoning | $1.25 / 1M input |

!!! note "Pricing accuracy"
    Prices are listed as of the release date and may change.

    Current information: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Pay attention to the **Free Tier** when using certain models.

    In the vast majority of cases, the free limit is sufficient for code review of a team of **4-8 developers**.

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
AI_REVIEWER_GOOGLE_API_KEY=AIza...
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
