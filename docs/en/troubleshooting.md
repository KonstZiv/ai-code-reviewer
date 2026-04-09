# Troubleshooting

FAQ and solving common problems.

---

## Common Problems

### Action Shows --help Instead of Running

**Symptom:** In CI job logs you see:

```
Usage: ai-review [OPTIONS]
...
╭─ Options ─────────────────────────────────────────────────────────╮
│ --provider  -p      [github|gitlab]  CI provider...              │
```

**Cause:** Using an old Docker image version (before v1.0.0a2).

**Solution:**

Update to the latest version:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1  # Always uses latest v1.x
```

If the problem persists, explicitly specify version:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1.0.0a2  # Or newer
```

---

### Review Not Appearing

**Symptom:** CI job passed successfully, but there are no comments.

**Check:**

1. **CI job logs** — are there errors?
2. **API key** — is `AI_REVIEWER_GOOGLE_API_KEY` valid?
3. **Token** — are there write permissions?
4. **github_token** — is it explicitly passed?

=== "GitHub"

    ```yaml
    permissions:
      contents: read
      pull-requests: write  # ← Required!
    ```

=== "GitLab"

    Make sure `GITLAB_TOKEN` has scope `api`.

---

### "Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short"

**Cause:** Key is not set or is incorrect.

**Solution:**

1. Check that the secret is added in repo settings
2. Check the name (case-sensitive)
3. Check that the key is valid at [Google AI Studio](https://aistudio.google.com/)

---

### "401 Unauthorized" / "403 Forbidden"

**Cause:** Invalid or insufficient token.

=== "GitHub"

    ```yaml
    # Check permissions
    permissions:
      contents: read
      pull-requests: write
    ```

=== "GitLab"

    - Check that the token is not expired
    - Check scope: need `api`
    - Make sure you're using a Project Access Token

---

### "404 Not Found"

**Cause:** PR/MR or repository not found.

**Solution:**

1. Check that PR/MR exists
2. Check repository name
3. Check that token has access to the repository

---

### "429 Too Many Requests" (Rate Limit)

**Cause:** API limit exceeded.

**Gemini Free Tier limits:**

| Limit | Value |
|-------|-------|
| Requests per minute | 15 |
| Tokens per day | 1,000,000 |
| Requests per day | 1,500 |

**Solution:**

1. AI Code Reviewer automatically retries with exponential backoff
2. If the problem persists — wait or switch to paid tier
3. Add `concurrency` to cancel duplicates:

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

---

### "500 Internal Server Error"

**Cause:** Problem on the API side (Google, GitHub, GitLab).

**Solution:**

1. AI Code Reviewer automatically retries (up to 5 attempts)
2. Check service status:
   - [Google Cloud Status](https://status.cloud.google.com/)
   - [GitHub Status](https://www.githubstatus.com/)
   - [GitLab Status](https://status.gitlab.com/)

---

### Review Too Slow

**Cause:** Large PR or slow network.

**Solution:**

1. Reduce PR size
2. Configure limits:

```bash
export REVIEW_MAX_FILES=10
export REVIEW_MAX_DIFF_LINES=300
```

3. Set timeout:

```yaml
# GitHub
timeout-minutes: 10

# GitLab
timeout: 10m
```

---

### Fork PRs Not Getting Review

**Cause:** Secrets are not available for fork PRs (security).

**Solution:**

This is expected behavior. For fork PRs:

1. Maintainer can run review manually
2. Or use `pull_request_target` (be careful with security!)

---

### Wrong Response Language

**Cause:** Incorrect language configuration.

**Solution:**

1. For fixed language:
```bash
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

2. For adaptive language — make sure PR description is written in the desired language

---

## FAQ

### Can I use it without an API key?

**No.** A Google Gemini API key is required. Free tier is sufficient for most projects.

### Is Bitbucket supported?

**No** (not yet). Only GitHub and GitLab.

### Can I use other LLMs (ChatGPT, Claude)?

**No** (in MVP). Support for other LLMs is planned for future versions.

### Is it safe to send code to Google API?

**Important to know:**

- Code is sent to Google Gemini API for analysis
- Review the [Google AI Terms](https://ai.google.dev/terms)
- For sensitive projects, consider self-hosted solutions (in future versions)

### How much does it cost?

**Gemini Flash pricing:**

| Metric | Cost |
|--------|------|
| Input tokens | $0.075 / 1M |
| Output tokens | $0.30 / 1M |

**Approximately:** ~1000 reviews = ~$1

Free tier: ~100 reviews/day for free.

### How to disable review for certain files?

There's no `.ai-reviewerignore` yet. Planned for future versions.

Workaround: filter in workflow:

```yaml
on:
  pull_request:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Can I run it locally?

**Yes:**

```bash
pip install ai-reviewbot
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token
ai-review --provider github --repo owner/repo --pr 123
```

---

## Debugging

### Enable Verbose Logs

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Check Configuration

```bash
# Check that variables are set
echo $AI_REVIEWER_GOOGLE_API_KEY | head -c 10
echo $GITHUB_TOKEN | head -c 10
```

### Test API Call

```bash
# Test Gemini API
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$AI_REVIEWER_GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Get Help

If the problem is not resolved:

1. :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — for bugs
2. :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — for questions

**When creating an issue, include:**

- AI Code Reviewer version (`ai-review --version`)
- CI provider (GitHub/GitLab)
- Logs (with secrets hidden!)
- Steps to reproduce

---

## Next Step

- [Examples →](examples/index.md)
- [Configuration →](configuration.md)
