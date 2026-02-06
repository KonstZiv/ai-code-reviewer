# Configuration

All settings are configured via environment variables.

---

## Required Variables

| Variable | Description | Example | How to get |
|----------|-------------|---------|------------|
| `GOOGLE_API_KEY` | Google Gemini API key | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub token (for GitHub) | `ghp_...` | [Instructions](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab token (for GitLab) | `glpat-...` | [Instructions](gitlab.md#get-token) |

!!! warning "At least one provider token required"
    You need `GITHUB_TOKEN` **or** `GITLAB_TOKEN` depending on the platform.
    These tokens are **provider-specific** — only one is required, matching the platform you use.

!!! info "GitLab token types"
    For GitLab, you can use a **Personal Access Token** (works on all plans, including Free)
    or a **Project Access Token** (requires GitLab Premium/Ultimate).

---

## Optional Variables {#optional}

### General

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `LOG_LEVEL` | Logging level | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `API_TIMEOUT` | Request timeout (sec) | `60` | 1-300 |

### Language

| Variable | Description | Default | Examples |
|----------|-------------|---------|----------|
| `LANGUAGE` | Response language | `en` | `uk`, `de`, `es`, `it`, `me` |
| `LANGUAGE_MODE` | Detection mode | `adaptive` | `adaptive`, `fixed` |

**Language modes:**

- **`adaptive`** (default) — automatically detects language from PR/MR context (description, comments, linked task)
- **`fixed`** — always uses the language from `LANGUAGE`

!!! tip "ISO 639"
    `LANGUAGE` accepts any valid ISO 639 code:

    - 2-letter: `en`, `uk`, `de`, `es`, `it`
    - 3-letter: `ukr`, `deu`, `spa`
    - Names: `English`, `Ukrainian`, `German`

### LLM

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_MODEL` | Gemini model | `gemini-2.5-flash` |

**Available models:**

| Model | Description | Cost |
|-------|-------------|------|
| `gemini-2.5-flash` | Fast, cheap | $0.075 / 1M input |
| `gemini-2.0-flash` | Previous version | $0.075 / 1M input |
| `gemini-1.5-pro` | More powerful | $1.25 / 1M input |

!!! note "Pricing accuracy"
    Prices are listed as of the release date and may change.

    Current information: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Pay attention to the **Free Tier** when using certain models.

    In the vast majority of cases, the free limit is sufficient for code review of a team of **4-8 developers**.

### Review

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `REVIEW_MAX_FILES` | Max files in context | `20` | 1-100 |
| `REVIEW_MAX_DIFF_LINES` | Max diff lines per file | `500` | 1-5000 |

### GitLab

| Variable | Description | Default |
|----------|-------------|---------|
| `GITLAB_URL` | GitLab server URL | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    For self-hosted GitLab, set `GITLAB_URL`:
    ```bash
    export GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## .env File

It's convenient to store configuration in `.env`:

```bash
# .env
GOOGLE_API_KEY=AIza...
GITHUB_TOKEN=ghp_...

# Optional
LANGUAGE=uk
LANGUAGE_MODE=adaptive
GEMINI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
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
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GITHUB_TOKEN: ${{ github.token }}  # Automatic
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  GOOGLE_API_KEY: $GOOGLE_API_KEY  # From CI/CD Variables
  # GITLAB_TOKEN: $CI_JOB_TOKEN   # Automatic (limited)
  GITLAB_TOKEN: $GITLAB_TOKEN      # Or PAT for full permissions
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

---

## Validation

AI Code Reviewer validates configuration at startup:

### Validation Errors

```
ValidationError: GOOGLE_API_KEY is too short (minimum 10 characters)
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
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
```

### Minimal (GitLab)

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
```

### Ukrainian language, fixed

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

### Self-hosted GitLab

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
export GITLAB_URL=https://gitlab.mycompany.com
```

### Debug mode

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LOG_LEVEL=DEBUG
```

---

## Configuration Priority

1. **Environment variables** (highest)
2. **`.env` file** in the current directory

---

## Next Step

- [GitHub integration →](github.md)
- [GitLab integration →](gitlab.md)
