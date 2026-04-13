# AI Code Reviewer - Integration Examples

This directory contains example configurations for integrating AI Code Reviewer into your CI/CD pipelines.

## Quick Start

### GitHub Actions

1. Copy `github-workflow.yml` to `.github/workflows/ai-review.yml` in your repository
2. Add `AI_REVIEWER_GOOGLE_API_KEY` to your repository secrets (Settings → Secrets → Actions)
3. Create a pull request to see AI Code Review in action

### GitLab CI

1. Add `AI_REVIEWER_GOOGLE_API_KEY` to your CI/CD variables (Settings → CI/CD → Variables)
2. Include the template in your `.gitlab-ci.yml`:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/KonstZiv/ai-code-reviewer/main/examples/gitlab-ci.yml'
```

Or copy the job from `gitlab-ci.yml` to your pipeline.

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_LANGUAGE` | Response language (ISO 639 code) | `en` |
| `AI_REVIEWER_LANGUAGE_MODE` | `adaptive` (detect from PR) or `fixed` | `adaptive` |
| `AI_REVIEWER_GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `AI_REVIEWER_LOG_LEVEL` | Logging verbosity | `INFO` |
| `AI_REVIEWER_DISCOVERY_ENABLED` | Enable project discovery | `true` |

> **Note:** Old variable names without `AI_REVIEWER_` prefix still work as fallback.

## Project Discovery

AI ReviewBot automatically analyzes your repository before each review to understand your stack, CI pipeline, and conventions. See [`.reviewbot.md`](.reviewbot.md) for an example configuration file.

## Docker Usage

You can also run the reviewer directly with Docker:

```bash
# Pull the image
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Run with environment variables
docker run --rm \
  -e AI_REVIEWER_GITHUB_TOKEN="ghp_xxx" \
  -e AI_REVIEWER_GOOGLE_API_KEY="xxx" \
  -e GITHUB_REPOSITORY="owner/repo" \
  -e GITHUB_REF="refs/pull/123/merge" \
  ghcr.io/konstziv/ai-code-reviewer:1
```

## Supported Platforms

| Platform | Method | Token |
|----------|--------|-------|
| GitHub | GitHub Action | `GITHUB_TOKEN` (automatic) |
| GitLab | Docker image | Project Access Token (`AI_REVIEWER_GITLAB_TOKEN`) |

## Troubleshooting

### GitHub: "Resource not accessible by integration"

The default `GITHUB_TOKEN` may lack permissions. Create a Personal Access Token with `repo` scope and add it as `GH_TOKEN` secret.

### GitLab: "403 Forbidden"

Create a Project Access Token with `api` scope and add it as `AI_REVIEWER_GITLAB_TOKEN` variable.

### Rate Limiting

Both GitHub and GitLab have API rate limits. The reviewer automatically handles rate limiting with retries and backoff.

## Examples

### Multi-language Support

```yaml
# Respond in Ukrainian
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    language: 'uk'
    language_mode: 'fixed'
```

### Using Different Model

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    gemini_model: 'gemini-2.5-flash'
```

## Cost Estimation

The reviewer displays estimated costs in the review footer. Typical costs:

| Model | ~2000 tokens | ~10000 tokens |
|-------|--------------|---------------|
| gemini-2.5-flash | ~$0.0002 | ~$0.001 |
| gemini-3-flash-preview | ~$0.0002 | ~$0.001 |
| gemini-2.5-pro | ~$0.005 | ~$0.025 |
