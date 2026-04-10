# AI ReviewBot

[![PyPI version](https://img.shields.io/pypi/v/ai-reviewbot)](https://pypi.org/project/ai-reviewbot/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://github.com/KonstZiv/ai-code-reviewer/actions/workflows/tests.yml/badge.svg)](https://github.com/KonstZiv/ai-code-reviewer/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/KonstZiv/ai-code-reviewer/branch/main/graph/badge.svg)](https://codecov.io/gh/KonstZiv/ai-code-reviewer)

AI-powered code review tool for **GitHub** and **GitLab** that provides intelligent feedback with **inline suggestions** and one-click "Apply" button.

<p align="center">
  <a href="https://konstziv.github.io/ai-code-reviewer/">📚 Documentation</a> •
  <a href="https://konstziv.github.io/ai-code-reviewer/quick-start/">🚀 Quick Start</a> •
  <a href="https://github.com/marketplace/actions/ai-code-reviewer">🛒 GitHub Marketplace</a>
</p>

---

## ✨ Features

- 🤖 **AI-Powered Analysis** — Uses Google Gemini or Mistral AI for deep code understanding
- 💡 **Inline Suggestions** — Comments directly on code lines with GitHub's "Apply suggestion" button
- 🔒 **Security Focus** — Identifies vulnerabilities with severity levels (Critical, Warning, Info)
- 🌍 **Multi-Language** — Responds in your PR/MR language (adaptive mode)
- ✨ **Good Practices** — Highlights what you're doing right, not just issues
- 📊 **Transparent Metrics** — Shows tokens, latency, and estimated cost
- 🦊 **GitHub & GitLab** — Native support for both platforms

## 🔍 Project Discovery

AI ReviewBot automatically analyzes your repository before each review:

- **Languages & frameworks** detected from GitHub/GitLab API
- **CI pipeline** parsed to understand what's already automated (linters, formatters, type checkers)
- **Config files** read to understand project conventions
- **Attention Zones** classify each quality area as ✅ Well Covered, ⚠️ Weakly Covered, or ❌ Not Covered

This means the bot **won't duplicate** feedback that your CI already catches — no formatting nits when you run Prettier, no type errors when you run mypy. Discovery results are **cached** via watch-files, so repeated PRs cost **0 extra tokens**.

Create [`.reviewbot.md`](./examples/.reviewbot.md) in your repo root to customize. You can also run `ai-review discover owner/repo` to preview what the bot sees.

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Enable/disable project discovery |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Always post discovery comment |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Discovery timeout in seconds |

> See [Discovery documentation](https://konstziv.github.io/ai-code-reviewer/discovery/) for details.

## 🚀 Quick Start

### GitHub Actions (Recommended)

```yaml
# .github/workflows/ai-review.yml
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
          # Or use Mistral:
          # mistral_api_key: ${{ secrets.AI_REVIEWER_MISTRAL_API_KEY }}
          # llm_provider: mistral
```

### GitLab CI

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

> **Note:** Set LLM API key (`AI_REVIEWER_GOOGLE_API_KEY` or `AI_REVIEWER_MISTRAL_API_KEY`) and `AI_REVIEWER_GITLAB_TOKEN` as CI/CD variables in Settings.

### PyPI

```bash
pip install ai-reviewbot

# Set environment variables (Google)
export AI_REVIEWER_GOOGLE_API_KEY="your-key"
export AI_REVIEWER_GITHUB_TOKEN="your-token"

# Or use Mistral
# export AI_REVIEWER_MISTRAL_API_KEY="your-key"
# export AI_REVIEWER_LLM_PROVIDER=mistral

# Run review
ai-review --repo owner/repo --pr 123
```

### Docker

```bash
# DockerHub
docker pull koszivdocker/ai-reviewbot:1

# GitHub Container Registry
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

## 📖 Documentation

Full documentation available in **6 languages**:

| Language | Link |
|----------|------|
| 🇬🇧 English | [Documentation](https://konstziv.github.io/ai-code-reviewer/) |
| 🇺🇦 Українська | [Документація](https://konstziv.github.io/ai-code-reviewer/uk/) |
| 🇩🇪 Deutsch | [Dokumentation](https://konstziv.github.io/ai-code-reviewer/de/) |
| 🇪🇸 Español | [Documentación](https://konstziv.github.io/ai-code-reviewer/es/) |
| 🇲🇪 Crnogorski | [Dokumentacija](https://konstziv.github.io/ai-code-reviewer/sr/) |
| 🇮🇹 Italiano | [Documentazione](https://konstziv.github.io/ai-code-reviewer/it/) |

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | — | Google Gemini API key |
| `AI_REVIEWER_MISTRAL_API_KEY` | — | Mistral API key |
| `AI_REVIEWER_LLM_PROVIDER` | `google` | Primary LLM provider (`google`, `mistral`) |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | — | Fallback provider when primary is exhausted |
| `AI_REVIEWER_GITHUB_TOKEN` | — | GitHub token (for GitHub) |
| `AI_REVIEWER_GITLAB_TOKEN` | — | GitLab token (for GitLab) |
| `AI_REVIEWER_LANGUAGE` | `en` | Response language (ISO 639 code) |
| `AI_REVIEWER_LANGUAGE_MODE` | `adaptive` | `adaptive` (detect from PR) or `fixed` |
| `AI_REVIEWER_GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `AI_REVIEWER_MISTRAL_MODEL` | `mistral-large-latest` | Mistral model to use |
| `AI_REVIEWER_MISTRAL_API_URL` | — | Custom Mistral API URL (e.g. `https://codestral.mistral.ai`) |
| `AI_REVIEWER_LOG_LEVEL` | `INFO` | Logging level |
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Enable project discovery before review |

> **Note:** At least one LLM API key is required. Old variable names without `AI_REVIEWER_` prefix still work as fallback.

See [Configuration Guide](https://konstziv.github.io/ai-code-reviewer/configuration/) for all options.

## 🎯 Example Output

The reviewer provides structured feedback with inline suggestions:

### Summary Comment

> **🤖 AI Code Review**
>
> **📊 Summary** — Found 2 issues and 1 good practice.
>
> | Category | Critical | Warning | Info |
> |----------|----------|---------|------|
> | Security | 1 | 0 | 0 |
> | Code Quality | 0 | 1 | 0 |
>
> **✨ Good Practices** — Excellent error handling in `api/handlers.py`
>
> ---
> ⏱️ 1.2s | 🪙 1,540 tokens | 💰 ~$0.002

### Inline Comment with "Apply" Button

> ⚠️ **SQL Injection Risk**
>
> User input is concatenated directly into SQL query.
>
> ```suggestion
> cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
> ```
>
> 💡 **Why this matters:** SQL injection allows attackers to execute arbitrary SQL commands. Always use parameterized queries.
>
> 📚 [Learn more](https://owasp.org/www-community/attacks/SQL_Injection)

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Install dependencies with uv
uv sync --all-groups

# Run tests
uv run pytest

# Run linters
uv run ruff check .
uv run mypy src/

# Build documentation
uv run mkdocs serve
```

## 📦 Installation Options

| Method | Command | Best For |
|--------|---------|----------|
| **GitHub Action** | `uses: KonstZiv/ai-code-reviewer@v1` | GitHub projects |
| **Docker** | `docker pull koszivdocker/ai-reviewbot` | GitLab CI |
| **PyPI** | `pip install ai-reviewbot` | Local testing |

## 💰 Cost Estimate

Using Gemini 2.5 Flash:
- **Input:** $0.075 / 1M tokens
- **Output:** $0.30 / 1M tokens
- **Average review:** ~$0.002 (1,500 tokens)

100 reviews/month ≈ **$0.20**

## 📄 License

Apache 2.0 — See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! See [Contributing Guide](CONTRIBUTING.md).

## 📬 Support

- 🐛 [Report a Bug](https://github.com/KonstZiv/ai-code-reviewer/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/KonstZiv/ai-code-reviewer/issues/new?template=feature_request.md)
- 📚 [Documentation](https://konstziv.github.io/ai-code-reviewer/)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/KonstZiv">Kostyantin Zivenko</a>
</p>
