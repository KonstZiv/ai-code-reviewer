# GitHub

Detailed guide for integration with GitHub Actions.

---

## Permissions

### Minimum Permissions

```yaml
permissions:
  contents: read        # Read code
  pull-requests: write  # Post comments
```

### GITHUB_TOKEN in Actions

In GitHub Actions, `GITHUB_TOKEN` is automatically available:

```yaml
env:
  GITHUB_TOKEN: ${{ github.token }}
```

**Automatic token permissions:**

| Permission | Status | Note |
|------------|--------|------|
| `contents: read` | :white_check_mark: | Default |
| `pull-requests: write` | :white_check_mark: | Must be specified in `permissions` |

!!! warning "Fork PRs"
    For PRs from fork repositories, `GITHUB_TOKEN` has **read-only** permissions.

    AI Review cannot post comments for fork PRs.

### How to Get a Personal Access Token {#get-token}

For **local runs**, you need a Personal Access Token (PAT):

1. Go to `Settings → Developer settings → Personal access tokens`
2. Choose **Fine-grained tokens** (recommended) or Classic
3. Click **Generate new token**

**Fine-grained token (recommended):**

| Setting | Value |
|---------|-------|
| Repository access | Only select repositories → your repository |
| Permissions | `Pull requests: Read and write` |

**Classic token:**

| Scope | Description |
|-------|-------------|
| `repo` | Full access to repository |

4. Click **Generate token**
5. Copy the token and save it as `GITHUB_TOKEN`

!!! warning "Save the token"
    GitHub shows the token **only once**. Save it immediately.

---

## Triggers

### Recommended Trigger

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

| Type | When it triggers |
|------|-----------------|
| `opened` | PR created |
| `synchronize` | New commits in PR |
| `reopened` | PR reopened |

### File Filtering

Run review only for specific files:

```yaml
on:
  pull_request:
    paths:
      - '**.py'
      - '**.js'
      - '**.ts'
```

### Branch Filtering

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

---

## Secrets

### Adding Secrets

`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Required | Description |
|--------|----------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | :white_check_mark: | Gemini API key |

### Usage

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
```

!!! danger "Never hardcode secrets"
    ```yaml
    # ❌ WRONG
    env:
      AI_REVIEWER_GOOGLE_API_KEY: AIza...

    # ✅ CORRECT
    env:
      AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    ```

---

## Workflow Examples

### Minimal

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
```

!!! info "About `GITHUB_TOKEN`"
    `secrets.GITHUB_TOKEN` is an **automatic token** that GitHub creates for each workflow run. You **don't need** to add it to secrets manually — it's already available.

    Token permissions are defined by the `permissions` section in the workflow file.

    :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

### With Concurrency (recommended)

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    if: github.event.pull_request.head.repo.full_name == github.repository
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
          language: uk
          language_mode: adaptive
```

**What concurrency does:**

- If a new commit is pushed while review is still running — the old review is cancelled
- Saves resources and API calls

### With Fork PR Filtering

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    # Don't run for fork PRs (no access to secrets)
    if: github.event.pull_request.head.repo.full_name == github.repository
```

---

## GitHub Action Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `google_api_key` | Gemini API key | **required** |
| `github_token` | GitHub token | `${{ github.token }}` |
| `language` | Response language | `en` |
| `language_mode` | Language mode | `adaptive` |
| `gemini_model` | Gemini model | `gemini-2.5-flash` |
| `gemini_model_fallback` | Fallback model chain (comma-separated) | `gemini-3.1-flash-preview` |
| `log_level` | Log level | `INFO` |
| `review_max_comment_chars` | Max MR comment chars in prompt | `3000` |
| `review_include_bot_comments` | Include bot comments in prompt | `true` |
| `review_post_inline_comments` | Post inline comments on lines | `true` |
| `review_enable_dialogue` | Group comments into dialogues | `true` |
| `discovery_enabled` | Enable project discovery | `true` |
| `discovery_verbose` | Always post discovery comment | `false` |
| `discovery_timeout` | Discovery timeout in seconds | `30` |

!!! tip "Environment variables"
    The Action maps inputs to `AI_REVIEWER_*` environment variables internally. When running outside the Action, use `AI_REVIEWER_*` env vars directly (old names like `GOOGLE_API_KEY` still work as fallback).

---

## Review Result

### Inline Comments

AI Review posts comments directly on code lines:

- :red_circle: **CRITICAL** — critical issues (security, bugs)
- :yellow_circle: **WARNING** — recommendations
- :blue_circle: **INFO** — educational notes

### Apply Suggestion

Each comment with a code suggestion has an **"Apply suggestion"** button:

```suggestion
fixed_code_here
```

GitHub automatically renders this as an interactive button.

### Summary

At the end of the review, a Summary is posted with:

- Overall issue statistics
- Metrics (time, tokens, cost)
- Good practices (positive feedback)

---

## Troubleshooting

### Review Not Posting Comments

**Check:**

1. `permissions: pull-requests: write` is in the workflow
2. `AI_REVIEWER_GOOGLE_API_KEY` secret is set
3. PR is not from a fork repository

### "Resource not accessible by integration"

**Cause:** Insufficient permissions.

**Solution:** Add permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### Rate Limit from Gemini

**Cause:** Free tier limit exceeded (15 RPM).

**Solution:**

- Wait a minute
- Add `concurrency` to cancel old runs
- Consider paid tier

---

## Best Practices

### 1. Always use concurrency

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### 2. Filter fork PRs

```yaml
if: github.event.pull_request.head.repo.full_name == github.repository
```

### 3. Set timeout

```yaml
jobs:
  review:
    timeout-minutes: 10
```

### 4. Make job non-blocking

```yaml
jobs:
  review:
    continue-on-error: true
```

---

## Next Step

- [GitLab integration →](gitlab.md)
- [CLI Reference →](api.md)
