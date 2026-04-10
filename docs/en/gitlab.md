# GitLab

Detailed guide for integration with GitLab CI.

---

## Tokens {#tokens}

### Personal Access Token (PAT) {#get-token}

**Recommended for all GitLab plans** (including Free).

!!! danger "`CI_JOB_TOKEN` does not work"
    GitLab's automatic `CI_JOB_TOKEN` **cannot post comments** to Merge Requests
    (the Notes API requires `api` scope, which `CI_JOB_TOKEN` does not have).
    You **must** use a Personal Access Token or Project Access Token.

**How to create:**

1. Go to **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Fill in the fields:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** set as needed (e.g., 1 year)
    - **Scopes:** check **`api`**
3. Click **Create personal access token**
4. **Copy the token immediately** — GitLab shows it only once!

**How to use in CI:**

1. Go to **Settings → CI/CD → Variables → Add variable**
2. Add variable:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN`
    - **Value:** paste your token
    - **Flags:** check **Masked**, **uncheck Protected**

The variable is automatically available to all jobs — no YAML `variables:` mapping needed.

!!! warning "Uncheck «Protected»!"
    By default GitLab marks new variables as **Protected**. Protected variables are **only available in protected branches** (e.g. `main`).

    MR pipelines run on **unprotected** source branches — so the variable will be empty and you'll get **401 Unauthorized**.

    **Always uncheck «Protected»** for `AI_REVIEWER_GITLAB_TOKEN` and `AI_REVIEWER_GOOGLE_API_KEY`.

!!! warning "Save the token"
    GitLab shows the token **only once**. Save it in a secure location immediately.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Available only on **GitLab Premium** and **Ultimate** plans. A good choice if you prefer a project-scoped token instead of a personal one.

**Advantages over PAT:**

- Scoped to a single project (no access to other projects)
- Can be revoked by project maintainers (no dependency on a specific user)
- Better for teams — not tied to a personal account

**How to create:**

1. Go to **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Fill in the fields:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (minimum required)
    - **Scopes:** check **`api`**
3. Click **Create project access token**
4. **Copy the token immediately**

**How to use in CI:**

Same as PAT — add as CI/CD variable with key `AI_REVIEWER_GITLAB_TOKEN` and check **Masked**, **uncheck Protected**.

The variable is automatically available to all jobs — no YAML `variables:` mapping needed.

!!! info "Which token to choose?"
    | | Personal Access Token | Project Access Token |
    |---|---|---|
    | **Plan** | All (including Free) | Premium/Ultimate only |
    | **Setup** | Manual | Manual |
    | **Scope** | All user's projects | Single project |
    | **Post comments** | :white_check_mark: | :white_check_mark: |
    | **Inline discussions** | :white_check_mark: | :white_check_mark: |
    | **Best for** | Free plan, personal use | Teams on Premium/Ultimate |

---

## CI/CD Variables

### Adding Variables

`Settings → CI/CD → Variables → Add variable`

| Variable | Value | Options |
|----------|-------|---------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API key | :white_check_mark: Masked, :x: **Uncheck** Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | PAT (if needed) | :white_check_mark: Masked, :x: **Uncheck** Protected |

!!! tip "Masked"
    Always enable **Masked** for secrets — they won't be shown in logs.

---

## Triggers

### Recommended Trigger

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

This runs the job only for Merge Request pipelines.

### Alternative Trigger (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — newer syntax, recommended by GitLab.

---

## Job Examples

### Minimal

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

!!! note "CI/CD variables"
    `AI_REVIEWER_GOOGLE_API_KEY` and `AI_REVIEWER_GITLAB_TOKEN` are inherited automatically from project CI/CD variables — no `variables:` section needed.

### Full (recommended)

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  variables:
    AI_REVIEWER_LANGUAGE: uk
    AI_REVIEWER_LANGUAGE_MODE: adaptive
  interruptible: true
```

**What it does:**

- `allow_failure: true` — MR is not blocked if review fails
- `timeout: 10m` — maximum 10 minutes
- `interruptible: true` — can be cancelled on new commit

### With Custom Stage

```yaml
stages:
  - test
  - review
  - deploy

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  needs: []  # Don't wait for previous stages
```

---

## Self-hosted GitLab

### Configuration

```yaml
variables:
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
```

### Docker Registry

If your GitLab doesn't have access to `ghcr.io`, create a mirror:

```bash
# On a machine with access
docker pull ghcr.io/konstziv/ai-code-reviewer:1
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
docker push gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

```yaml
ai-review:
  image: gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

---

## GitLab CI Variables

AI Code Reviewer automatically uses:

| Variable | Description |
|----------|-------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | MR number |
| `CI_SERVER_URL` | GitLab URL |

You don't need to pass `--repo` and `--pr` — they're taken from CI automatically.

---

## Variable-Driven Configuration {#variable-driven}

Use **CI/CD Variables** to switch between LLM providers and models without changing `.gitlab-ci.yml`. This is useful for comparing review quality across different models on the same MR.

### Setup

**CI/CD Variables** (`Settings → CI/CD → Variables`):

| Variable | Description | Flags |
|----------|-------------|-------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API key | :white_check_mark: Masked, :x: Uncheck Protected |
| `AI_REVIEWER_MISTRAL_API_KEY` | Mistral API key | :white_check_mark: Masked, :x: Uncheck Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab token | :white_check_mark: Masked, :x: Uncheck Protected |
| `AI_REVIEWER_LLM_PROVIDER` | Primary provider (`google`, `mistral`) | :x: Uncheck Protected |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Fallback provider | :x: Uncheck Protected |
| `AI_REVIEWER_MISTRAL_MODEL` | Mistral model | :x: Uncheck Protected |
| `AI_REVIEWER_MISTRAL_API_URL` | Custom API URL (for Codestral free tier) | :x: Uncheck Protected |

### Job Configuration

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: review
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  interruptible: true
```

No `variables:` section needed — all `AI_REVIEWER_*` CI/CD variables are inherited automatically.

### Switching Presets

Change CI/CD Variables in the GitLab UI, then **Retry** the pipeline on the same MR:

| Preset | `AI_REVIEWER_LLM_PROVIDER` | `AI_REVIEWER_MISTRAL_MODEL` | `AI_REVIEWER_MISTRAL_API_URL` | `AI_REVIEWER_LLM_FALLBACK_PROVIDER` |
|--------|---------------------------|---------------------------|-------------------------------|-------------------------------------|
| Gemini (default) | `google` | _(empty)_ | _(empty)_ | _(empty)_ |
| Mistral Large | `mistral` | `mistral-large-latest` | _(empty)_ | `google` |
| Codestral free | `mistral` | `codestral-latest` | `https://codestral.mistral.ai` | `google` |
| Devstral | `mistral` | `devstral-latest` | _(empty)_ | `google` |

!!! tip "Codestral free tier key"
    For the "Codestral free" preset, `AI_REVIEWER_MISTRAL_API_KEY` must contain a key from [codestral.mistral.ai](https://codestral.mistral.ai/), not from `console.mistral.ai`.

!!! info "No need to hardcode in YAML"
    Unlike GitHub Actions (where inputs must be mapped explicitly), GitLab CI automatically passes all CI/CD variables as environment variables. Just set them in the UI — the application picks them up via `AI_REVIEWER_*` prefix.

---

## Review Result

### Notes (comments)

AI Review posts comments to MR as notes.

### Discussions (inline)

For inline comments, you need a Personal Access Token (or Project Access Token) with `api` scope.

Inline comments appear directly next to code lines in the diff view.

### Summary

At the end of the review, a Summary note is posted with:

- Overall statistics
- Metrics
- Good practices

---

## Troubleshooting

### Review Not Posting Comments

**Check:**

1. `AI_REVIEWER_GOOGLE_API_KEY` variable is set
2. `AI_REVIEWER_GITLAB_TOKEN` has sufficient permissions (scope: `api`)
3. Pipeline is running for MR (not for a branch)

### "401 Unauthorized"

**Cause:** Invalid token.

**Solution:**

- Check that the token is not expired
- Check scope (need `api`)

### "403 Forbidden"

**Cause:** Insufficient permissions.

**Solution:**

- Ensure you are using a Personal Access Token (or Project Access Token) with `api` scope
- Check that the token has access to the project

### "404 Not Found"

**Cause:** MR not found.

**Solution:**

- Check that the pipeline is running for MR
- Check `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Cause:** API limit exceeded.

**Solution:**

- AI Code Reviewer automatically retries with backoff
- If persistent — wait or increase limits

---

## Best Practices

### 1. Use a Personal Access Token

Create a CI/CD variable named `AI_REVIEWER_GITLAB_TOKEN` with your PAT value — it will be inherited by all jobs automatically.

### 2. Add allow_failure

```yaml
allow_failure: true
```

MR won't be blocked if review fails.

### 3. Set timeout

```yaml
timeout: 10m
```

### 4. Make job interruptible

```yaml
interruptible: true
```

Old review will be cancelled on new commit.

### 5. Don't wait for other stages

```yaml
needs: []
```

Review will start immediately, without waiting for build/test.

---

## Next Step

- [GitHub integration →](github.md)
- [CLI Reference →](api.md)
