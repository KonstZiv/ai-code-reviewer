# GitLab: Advanced Example

Production-ready configuration with all best practices.

---

## Step 1: Create a Personal Access Token (PAT)

`User Settings → Access Tokens → Add new token`

| Field | Value |
|-------|-------|
| Name | `ai-code-reviewer` |
| Scopes | `api` |
| Expiration | As needed |

!!! info "Free plan"
    **Personal Access Token** works on **all GitLab plans**, including Free.

    **Project Access Token** is only available on **GitLab Premium/Ultimate**.

---

## Step 2: Add Variables

`Settings → CI/CD → Variables`

| Name | Value | Options |
|------|-------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Masked |
| `GITLAB_TOKEN` | PAT from Step 1 | Masked |

---

## Step 3: Add a Job

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - review

# ... other jobs ...

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1

  script:
    - ai-review

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

  # Don't block MR if review fails
  allow_failure: true

  # Timeout protection
  timeout: 10m

  # Can be cancelled on new commit
  interruptible: true

  # Don't wait for other stages
  needs: []

  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
```

---

## What's Included

| Feature | Status | Description |
|---------|--------|-------------|
| Inline discussions | :white_check_mark: | With PAT token |
| Non-blocking | :white_check_mark: | `allow_failure: true` |
| Timeout | :white_check_mark: | 10 minutes |
| Interruptible | :white_check_mark: | Cancelled on new commit |
| Parallel run | :white_check_mark: | `needs: []` |
| Custom language | :white_check_mark: | `LANGUAGE: uk` |

---

## Variations

### Self-hosted GitLab

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    GITLAB_URL: https://gitlab.mycompany.com
```

### With Custom Docker Registry

```yaml
ai-review:
  # If ghcr.io is not accessible
  image: registry.mycompany.com/devops/ai-code-reviewer:latest
```

### With DEBUG Logs

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LOG_LEVEL: DEBUG
```

### Only for Specific Branches

```yaml
ai-review:
  # ...
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: always
    - if: $CI_MERGE_REQUEST_TARGET_BRANCH_NAME == "main"
      when: always
```

---

## CI_JOB_TOKEN vs PAT

| Feature | CI_JOB_TOKEN | PAT |
|---------|--------------|-----|
| Read MR | :white_check_mark: | :white_check_mark: |
| Post notes | :white_check_mark: | :white_check_mark: |
| Inline discussions | :x: | :white_check_mark: |
| Requires setup | :x: | :white_check_mark: |

**Recommendation:** Use a Personal Access Token for full functionality. It works on all GitLab plans, including Free.

---

## Troubleshooting

### Review Not Posting Comments

1. Check job logs
2. Check that `GITLAB_TOKEN` has scope `api`
3. Check that pipeline is running for MR

### "401 Unauthorized"

Token is invalid or expired. Create a new PAT.

### "403 Forbidden"

Token doesn't have access to the project. Check permissions.

---

## Full .gitlab-ci.yml Example

```yaml
stages:
  - lint
  - test
  - review
  - deploy

lint:
  stage: lint
  image: python:3.13
  script:
    - pip install ruff
    - ruff check .

test:
  stage: test
  image: python:3.13
  script:
    - pip install pytest
    - pytest

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  interruptible: true
  needs: []
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Next Step

:point_right: [Configuration →](../configuration.md)
