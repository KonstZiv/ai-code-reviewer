# Швидкий старт

Запустіть AI Code Reviewer за 5 хвилин на GitHub або GitLab.

---

## Крок 1: Оберіть LLM-провайдера та отримайте API ключ

AI Reviewer підтримує декілька LLM-провайдерів. Оберіть один (або використовуйте обидва для fallback):

=== "Google Gemini (за замовчуванням)"

    1. Перейдіть на [Google AI Studio](https://aistudio.google.com/)
    2. Увійдіть з Google акаунтом
    3. Натисніть **"Get API key"** → **"Create API key"**
    4. Скопіюйте ключ (він починається з `AIza...`)

    !!! tip "Безкоштовний рівень"
        Gemini API має безкоштовний рівень: 15 запитів на хвилину, достатньо для більшості команд з 4-8 розробників.

=== "Mistral AI"

    1. Перейдіть на [Mistral Console](https://console.mistral.ai/)
    2. Зареєструйтесь або увійдіть
    3. Перейдіть до **API Keys** → **Create new key**
    4. Скопіюйте ключ (він починається з `sk-...`)

    !!! tip "Безкоштовний рівень"
        Mistral пропонує безкоштовний рівень для експериментів. Після реєстрації ви отримуєте безкоштовні API-кредити для випробування всіх моделей. Актуальні ліміти: [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing).

    !!! tip "Безкоштовний Codestral"
        Codestral (модель для коду) має власний безкоштовний рівень з **окремим endpoint і ключем**:

        1. Перейдіть на [codestral.mistral.ai](https://codestral.mistral.ai/)
        2. Згенеруйте Codestral API ключ
        3. Встановіть `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai`
        4. Встановіть `AI_REVIEWER_MISTRAL_MODEL=codestral-latest`

        Цей ключ працює **тільки** з `codestral-latest` на Codestral endpoint.

=== "Обидва (Mistral основний + Google fallback)"

    Отримайте **обидва ключі** за інструкціями вище. Це дає вам:

    - Mistral як основну модель (напр. `mistral-large-latest`)
    - Google Gemini як автоматичний fallback, якщо Mistral недоступний

    Це найнадійніша конфігурація для production.

!!! warning "Збережіть ключ"
    API ключі показуються лише один раз. Збережіть їх у безпечному місці.

---

## Крок 2: Додайте секрети у репозиторій

=== "GitHub"

    **Шлях:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    === "Google only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ваш Gemini ключ (`AIza...`) |

    === "Mistral only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ваш Mistral ключ (`sk-...`) |

    === "Обидва провайдери"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ваш Mistral ключ (`sk-...`) |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ваш Gemini ключ (`AIza...`) |

    Натисніть **"Add secret"** для кожного.

    ??? info "Детальна інструкція з скріншотами"
        1. Відкрийте ваш репозиторій на GitHub
        2. Натисніть **Settings** (шестерня у верхньому меню)
        3. У лівому меню знайдіть **Secrets and variables** → **Actions**
        4. Натисніть зелену кнопку **New repository secret**
        5. Введіть ім'я та вставте ваш ключ
        6. Натисніть **Add secret**
        7. Повторіть для кожного секрету

    :material-book-open-variant: [Офіційна документація GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Для GitLab також потрібен **GitLab токен** для публікації коментарів.

    ### Крок 2a: Створіть GitLab токен

    === "Personal Access Token (всі плани, включаючи Free)"

        **Шлях:** Аватар користувача → `Edit profile` → `Access Tokens`

        | Поле | Значення |
        |------|----------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Оберіть дату (макс. 1 рік) |
        | **Scopes** | :white_check_mark: `api` |

        Натисніть **"Create personal access token"** → **Скопіюйте токен** (показується лише раз!)

        !!! warning "Коментарі будуть від вашого імені"
            Personal Access Token прив'язаний до вашого облікового запису. Всі коментарі ревʼю будуть опубліковані від вашого імені.

        :material-book-open-variant: [GitLab Docs: Personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

    === "Project Access Token (Premium/Ultimate)"

        !!! note "Потрібні права Maintainer"
            Для створення Project Access Token потрібна роль **Maintainer** або **Owner** у проєкті.

            :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

        **Шлях:** Project → `Settings` → `Access Tokens`

        | Поле | Значення |
        |------|----------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Оберіть дату (макс. 1 рік) |
        | **Role** | `Developer` |
        | **Scopes** | :white_check_mark: `api` |

        Натисніть **"Create project access token"** → **Скопіюйте токен** (показується лише раз!)

        :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Крок 2b: Додайте змінні в CI/CD

    **Шлях:** Project → `Settings` → `CI/CD` → `Variables`

    === "Google only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ваш Gemini ключ | :white_check_mark: Mask, :x: Зніміть Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Токен з кроку 2a | :white_check_mark: Mask, :x: Зніміть Protected |

    === "Mistral only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ваш Mistral ключ | :white_check_mark: Mask, :x: Зніміть Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Токен з кроку 2a | :white_check_mark: Mask, :x: Зніміть Protected |

    === "Обидва провайдери"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ваш Mistral ключ | :white_check_mark: Mask, :x: Зніміть Protected |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ваш Gemini ключ | :white_check_mark: Mask, :x: Зніміть Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Токен з кроку 2a | :white_check_mark: Mask, :x: Зніміть Protected |

    !!! warning "Зніміть «Protected»!"
        За замовчуванням GitLab позначає нові змінні як **Protected**. Protected змінні **доступні лише в захищених гілках** (наприклад, `main`), але MR pipeline запускається на **незахищених** source гілках — змінна буде порожньою і ви отримаєте **401 Unauthorized**.

    !!! danger "`CI_JOB_TOKEN` не працює"
        Автоматичний `CI_JOB_TOKEN` від GitLab **не може постити коментарі** до Merge Requests.
        Ви **повинні** створити Personal Access Token (або Project Access Token на Premium+).

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Крок 3: Додайте AI Review у CI {#ci-setup}

=== "GitHub"

    Створіть файл `.github/workflows/ai-review.yml`:

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

    === "Обидва (Mistral основний)"

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

        !!! note "Ключ Codestral"
            Використовуйте ключ з [codestral.mistral.ai](https://codestral.mistral.ai/), а не звичайний Mistral API ключ.

    !!! info "Про `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` — це **автоматичний токен**, який GitHub створює для кожного workflow run. Його **не потрібно** додавати в secrets вручну — він вже доступний.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

=== "GitLab"

    Створіть або оновіть `.gitlab-ci.yml`:

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

        CI/CD змінні `AI_REVIEWER_GOOGLE_API_KEY` та `AI_REVIEWER_GITLAB_TOKEN` з кроку 2b наслідуються автоматично.

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

        CI/CD змінні `AI_REVIEWER_MISTRAL_API_KEY` та `AI_REVIEWER_GITLAB_TOKEN` з кроку 2b наслідуються автоматично.

    === "Обидва (Mistral основний)"

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

        Всі три CI/CD змінні (`AI_REVIEWER_MISTRAL_API_KEY`, `AI_REVIEWER_GOOGLE_API_KEY`, `AI_REVIEWER_GITLAB_TOKEN`) з кроку 2b наслідуються автоматично.

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

        CI/CD змінні `AI_REVIEWER_MISTRAL_API_KEY` (використовуйте ключ Codestral) та `AI_REVIEWER_GITLAB_TOKEN` з Кроку 2b доступні автоматично.

---

## Крок 4: Перевірте результат

Тепер AI Review буде запускатись автоматично при:

| Платформа | Подія |
|-----------|-------|
| **GitHub** | Створення PR, нові коміти в PR, reopening PR |
| **GitLab** | Створення MR, нові коміти в MR |

### Що ви побачите

Після завершення CI job, в PR/MR з'являться:

- **Inline коментарі** — прив'язані до конкретних рядків коду
- **Кнопка "Apply suggestion"** — для швидкого застосування виправлень (GitHub)
- **Summary коментар** — загальний огляд з метриками

Кожен коментар містить:

- :red_circle: / :yellow_circle: / :blue_circle: Severity badge
- Опис проблеми
- Пропозицію виправлення
- Collapsible секцію "Чому це важливо?"

У підвалі коментаря вказано, яку модель і провайдера було використано:

> _Model: Google / gemini-2.5-flash | Tokens: 1,234 | Latency: 2.3s | Est. cost: $0.0012_

---

## Troubleshooting

### Review не з'являється?

Перевірте чеклист:

- [ ] API ключ додано як секрет? (`AI_REVIEWER_GOOGLE_API_KEY` або `AI_REVIEWER_MISTRAL_API_KEY`)
- [ ] `llm_provider` встановлено правильно, якщо використовується Mistral? (за замовчуванням `google`)
- [ ] `github_token` передано явно? (для GitHub)
- [ ] Для GitLab: `AI_REVIEWER_GITLAB_TOKEN` встановлено як Personal Access Token?
- [ ] CI job завершився успішно? (перевірте логи)
- [ ] Для GitHub: є `permissions: pull-requests: write`?
- [ ] Для fork PRs: секрети недоступні — це очікувана поведінка

### Rate limit?

- **Gemini** free tier: 15 запитів на хвилину
- **Mistral** free tier: актуальні ліміти на [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing)

Зачекайте хвилину та спробуйте знову, або налаштуйте [fallback-провайдера](configuration.md#llm).

:point_right: [Всі проблеми та рішення →](troubleshooting.md)

---

## Що далі?

| Задача | Документ |
|--------|----------|
| Налаштувати мову відповідей | [Конфігурація](configuration.md) |
| Розширені налаштування LLM-провайдерів | [Конфігурація → LLM](configuration.md#llm) |
| Перемикання моделей без зміни коду | [GitHub → Конфігурація через Variables](github.md#variable-driven) |
| Розширені налаштування GitHub | [GitHub Guide](github.md) |
| Розширені налаштування GitLab | [GitLab Guide](gitlab.md) |
| Приклади workflows | [Приклади](examples/index.md) |
