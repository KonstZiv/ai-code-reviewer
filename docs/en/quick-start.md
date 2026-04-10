# Quick Start

Get AI Code Reviewer running in 5 minutes on GitHub or GitLab.

---

## Step 1: Choose Your LLM Provider & Get an API Key

AI Reviewer supports multiple LLM providers. Pick one (or use both for fallback):

=== "Google Gemini (default)"

    1. Go to [Google AI Studio](https://aistudio.google.com/)
    2. Sign in with your Google account
    3. Click **"Get API key"** → **"Create API key"**
    4. Copy the key (it starts with `AIza...`)

    !!! tip "Free tier"
        Gemini API has a generous free tier: 15 requests per minute, sufficient for most teams of 4-8 developers.

=== "Mistral AI"

    1. Go to [Mistral Console](https://console.mistral.ai/)
    2. Sign up or sign in
    3. Navigate to **API Keys** → **Create new key**
    4. Copy the key (it starts with `sk-...`)

    !!! tip "Free tier"
        Mistral offers a free tier for experimentation. After signing up, you get free API credits to try all models. Check [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing) for current limits.

    !!! tip "Codestral free tier"
        Codestral (a code-specialized model) has its own free tier with a **separate endpoint and key**:

        1. Go to [codestral.mistral.ai](https://codestral.mistral.ai/)
        2. Generate a Codestral API key
        3. Set `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai`
        4. Set `AI_REVIEWER_MISTRAL_MODEL=codestral-latest`

        This key works **only** with `codestral-latest` at the Codestral endpoint.

=== "Both (Mistral primary + Google fallback)"

    Get **both keys** using the instructions above. This gives you:

    - Mistral as the primary model (e.g. `mistral-large-latest`)
    - Google Gemini as automatic fallback if Mistral is unavailable

    This is the most reliable setup for production use.

!!! warning "Save the key"
    API keys are shown only once. Save them in a secure place.

---

## Step 2: Add Secrets to Your Repository

=== "GitHub"

    **Path:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    === "Google only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Your Gemini key (`AIza...`) |

    === "Mistral only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Your Mistral key (`sk-...`) |

    === "Both providers"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Your Mistral key (`sk-...`) |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Your Gemini key (`AIza...`) |

    Click **"Add secret"** for each one.

    ??? info "Detailed instructions with screenshots"
        1. Open your repository on GitHub
        2. Click **Settings** (gear icon in the top menu)
        3. In the left menu find **Secrets and variables** → **Actions**
        4. Click the green **New repository secret** button
        5. Enter the name and paste your key
        6. Click **Add secret**
        7. Repeat for each secret

    :material-book-open-variant: [Official GitHub documentation: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    For GitLab you also need a **GitLab token** for posting comments.

    ### Step 2a: Create a GitLab Token

    === "Personal Access Token (All plans, including Free)"

        **Path:** User avatar → `Edit profile` → `Access Tokens`

        | Field | Value |
        |-------|-------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Choose a date (max 1 year) |
        | **Scopes** | :white_check_mark: `api` |

        Click **"Create personal access token"** → **Copy the token** (shown only once!)

        !!! warning "Comments will appear under your username"
            A Personal Access Token is tied to your account. All review comments will be posted on your behalf.

        :material-book-open-variant: [GitLab Docs: Personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

    === "Project Access Token (Premium/Ultimate)"

        !!! note "Maintainer rights required"
            To create a Project Access Token you need the **Maintainer** or **Owner** role in the project.

            :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

        **Path:** Project → `Settings` → `Access Tokens`

        | Field | Value |
        |-------|-------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Choose a date (max 1 year) |
        | **Role** | `Developer` |
        | **Scopes** | :white_check_mark: `api` |

        Click **"Create project access token"** → **Copy the token** (shown only once!)

        :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Step 2b: Add Variables to CI/CD

    **Path:** Project → `Settings` → `CI/CD` → `Variables`

    === "Google only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Your Gemini key | :white_check_mark: Mask, :x: Uncheck Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token from step 2a | :white_check_mark: Mask, :x: Uncheck Protected |

    === "Mistral only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Your Mistral key | :white_check_mark: Mask, :x: Uncheck Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token from step 2a | :white_check_mark: Mask, :x: Uncheck Protected |

    === "Both providers"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Your Mistral key | :white_check_mark: Mask, :x: Uncheck Protected |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Your Gemini key | :white_check_mark: Mask, :x: Uncheck Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token from step 2a | :white_check_mark: Mask, :x: Uncheck Protected |

    !!! warning "Uncheck «Protected»!"
        By default GitLab marks new variables as **Protected**. Protected variables are **only available in protected branches** (e.g. `main`), but MR pipelines run on **unprotected** source branches — the variable will be empty and you'll get **401 Unauthorized**.

    !!! danger "`CI_JOB_TOKEN` does not work"
        GitLab's automatic `CI_JOB_TOKEN` **cannot post comments** to Merge Requests.
        You **must** create a Personal Access Token (or Project Access Token on Premium+).

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Step 3: Add AI Review to CI {#ci-setup}

=== "GitHub"

    Create file `.github/workflows/ai-review.yml`:

    === "Google only"

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
        ```

    === "Mistral only"

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
                  mistral_api_key: ${{ secrets.AI_REVIEWER_MISTRAL_API_KEY }}
                  llm_provider: mistral
        ```

    === "Both (Mistral primary)"

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
                  mistral_api_key: ${{ secrets.AI_REVIEWER_MISTRAL_API_KEY }}
                  google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
                  llm_provider: mistral
                  llm_fallback_provider: google
        ```

    === "Codestral free tier"

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
                  mistral_api_key: ${{ secrets.AI_REVIEWER_MISTRAL_API_KEY }}
                  llm_provider: mistral
                  mistral_model: codestral-latest
                  mistral_api_url: https://codestral.mistral.ai
        ```

        !!! note "Codestral key"
            Use the key from [codestral.mistral.ai](https://codestral.mistral.ai/), not the regular Mistral API key.

    !!! info "About `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` is an **automatic token** that GitHub creates for each workflow run. You **don't need** to add it to secrets manually — it's already available.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

=== "GitLab"

    Create or update `.gitlab-ci.yml`:

    === "Google only"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        CI/CD variables `AI_REVIEWER_GOOGLE_API_KEY` and `AI_REVIEWER_GITLAB_TOKEN` from Step 2b are available automatically.

    === "Mistral only"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          variables:
            AI_REVIEWER_LLM_PROVIDER: mistral
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        CI/CD variables `AI_REVIEWER_MISTRAL_API_KEY` and `AI_REVIEWER_GITLAB_TOKEN` from Step 2b are available automatically.

    === "Both (Mistral primary)"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          variables:
            AI_REVIEWER_LLM_PROVIDER: mistral
            AI_REVIEWER_LLM_FALLBACK_PROVIDER: google
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        All three CI/CD variables (`AI_REVIEWER_MISTRAL_API_KEY`, `AI_REVIEWER_GOOGLE_API_KEY`, `AI_REVIEWER_GITLAB_TOKEN`) from Step 2b are available automatically.

    === "Codestral free tier"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          variables:
            AI_REVIEWER_LLM_PROVIDER: mistral
            AI_REVIEWER_MISTRAL_MODEL: codestral-latest
            AI_REVIEWER_MISTRAL_API_URL: https://codestral.mistral.ai
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        CI/CD variables `AI_REVIEWER_MISTRAL_API_KEY` (use Codestral key) and `AI_REVIEWER_GITLAB_TOKEN` from Step 2b are available automatically.

---

## Step 4: Check the Result

Now AI Review will run automatically on:

| Platform | Event |
|----------|-------|
| **GitHub** | PR creation, new commits in PR, reopening PR |
| **GitLab** | MR creation, new commits in MR |

### What You'll See

After the CI job completes, the PR/MR will have:

- **Inline comments** — attached to specific code lines
- **"Apply suggestion" button** — for quick fixes (GitHub)
- **Summary comment** — general overview with metrics

Each comment contains:

- :red_circle: / :yellow_circle: / :blue_circle: Severity badge
- Problem description
- Fix suggestion
- Collapsible "Why does this matter?" section

The footer shows which model and provider was used:

> _Model: Google / gemini-2.5-flash | Tokens: 1,234 | Latency: 2.3s | Est. cost: $0.0012_

---

## Troubleshooting

### Review not appearing?

Check the checklist:

- [ ] Is the API key added as a secret? (`AI_REVIEWER_GOOGLE_API_KEY` or `AI_REVIEWER_MISTRAL_API_KEY`)
- [ ] Is `llm_provider` set correctly if using Mistral? (default is `google`)
- [ ] Is `github_token` passed explicitly? (for GitHub)
- [ ] For GitLab: is `AI_REVIEWER_GITLAB_TOKEN` set to a Personal Access Token?
- [ ] Did the CI job complete successfully? (check logs)
- [ ] For GitHub: do you have `permissions: pull-requests: write`?
- [ ] For fork PRs: secrets are not available — this is expected behavior

### Rate limit?

- **Gemini** free tier: 15 requests per minute
- **Mistral** free tier: check [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing) for current limits

Wait a minute and try again, or configure a [fallback provider](configuration.md#llm).

:point_right: [All issues and solutions →](troubleshooting.md)

---

## What's Next?

| Task | Document |
|------|----------|
| Configure response language | [Configuration](configuration.md) |
| Advanced LLM provider settings | [Configuration → LLM](configuration.md#llm) |
| Switch models without changing code | [GitHub → Variable-Driven Config](github.md#variable-driven) |
| Advanced GitHub settings | [GitHub Guide](github.md) |
| Advanced GitLab settings | [GitLab Guide](gitlab.md) |
| Workflow examples | [Examples](examples/index.md) |
