# GitLab

Detailed guide for integration with GitLab CI.

---

## Tokens {#tokens}

### CI_JOB_TOKEN (automatic)

In GitLab CI, `CI_JOB_TOKEN` is automatically available:

```yaml
variables:
  GITLAB_TOKEN: $CI_JOB_TOKEN
```

**`CI_JOB_TOKEN` limitations:**

| Feature | Status |
|---------|--------|
| Read MR | :white_check_mark: |
| Read diff | :white_check_mark: |
| Post notes | :white_check_mark: |
| Create discussions | :x: |

!!! warning "Limited permissions"
    `CI_JOB_TOKEN` cannot create inline discussions.

    For full functionality, use a Personal Access Token.

### Personal Access Token (recommended) {#get-token}

For **local runs** or **full functionality in CI**, you need a Personal Access Token:

1. Go to `User Settings → Access Tokens → Add new token`
2. Enter the token name (e.g., `ai-code-reviewer`)
3. Select scope: **`api`**
4. Click **Create personal access token**
5. Copy the token and save it as `GITLAB_TOKEN`

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # From CI/CD Variables
```

!!! warning "Save the token"
    GitLab shows the token **only once**. Save it immediately.

!!! info "Personal Access Token vs Project Access Token"
    **Personal Access Token** (PAT) works on **all GitLab plans**, including Free.

    **Project Access Token** is available only on **GitLab Premium/Ultimate**.
    If you are on the Free plan, use a Personal Access Token.

---

## CI/CD Variables

### Adding Variables

`Settings → CI/CD → Variables → Add variable`

| Variable | Value | Options |
|----------|-------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Masked |
| `GITLAB_TOKEN` | PAT (if needed) | Masked |

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
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

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
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
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
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
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
| `CI_JOB_TOKEN` | Automatic token |

You don't need to pass `--project` and `--mr-iid` — they're taken from CI automatically.

---

## Review Result

### Notes (comments)

AI Review posts comments to MR as notes.

### Discussions (inline)

For inline comments, you need a full PAT token (not `CI_JOB_TOKEN`).

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

1. `GOOGLE_API_KEY` variable is set
2. `GITLAB_TOKEN` has sufficient permissions (scope: `api`)
3. Pipeline is running for MR (not for a branch)

### "401 Unauthorized"

**Cause:** Invalid token.

**Solution:**

- Check that the token is not expired
- Check scope (need `api`)

### "403 Forbidden"

**Cause:** Insufficient permissions.

**Solution:**

- Use PAT instead of `CI_JOB_TOKEN`
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

### 1. Use PAT for full functionality

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # PAT, not CI_JOB_TOKEN
```

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
