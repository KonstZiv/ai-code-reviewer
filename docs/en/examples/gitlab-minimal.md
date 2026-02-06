# GitLab: Minimal Example

The simplest configuration for GitLab CI.

---

## Step 1: Add a Variable

`Settings → CI/CD → Variables → Add variable`

| Name | Value | Options |
|------|-------|---------|
| `GOOGLE_API_KEY` | Your Gemini API key | Masked |

---

## Step 2: Add a Job

`.gitlab-ci.yml`:

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

---

## Step 3: Create an MR

Done! AI review will appear as comments on the MR.

---

## What's Included

| Feature | Status |
|---------|--------|
| Notes on MR | :white_check_mark: |
| Language adaptivity | :white_check_mark: (adaptive) |
| Metrics | :white_check_mark: |
| Auto-retry | :white_check_mark: |

---

## Limitations

| Limitation | Solution |
|------------|----------|
| `CI_JOB_TOKEN` is limited | Use PAT |
| No inline discussions | Need PAT with scope `api` |
| MR blocked on error | Add `allow_failure: true` |

!!! info "PAT vs Project Access Token"
    **Personal Access Token** (PAT) works on **all GitLab plans**, including Free.

    **Project Access Token** requires **GitLab Premium/Ultimate**.
    For the Free plan, always use a Personal Access Token.

---

## Next Step

:point_right: [Advanced example →](gitlab-advanced.md)
