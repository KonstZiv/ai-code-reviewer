# GitLab

Детальний гайд для інтеграції з GitLab CI.

---

## Токени {#tokens}

### Personal Access Token (PAT) {#get-token}

**Рекомендовано для всіх планів GitLab** (включаючи Free).

!!! danger "`CI_JOB_TOKEN` не працює"
    Автоматичний `CI_JOB_TOKEN` від GitLab **не може постити коментарі** до Merge Requests
    (Notes API потребує scope `api`, якого `CI_JOB_TOKEN` не має).
    Ви **повинні** використовувати Personal Access Token або Project Access Token.

**Як створити:**

1. Перейдіть до **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Заповніть поля:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** встановіть за потреби (наприклад, 1 рік)
    - **Scopes:** оберіть **`api`**
3. Натисніть **Create personal access token**
4. **Скопіюйте токен одразу** — GitLab показує його лише один раз!

**Як використовувати в CI:**

1. Перейдіть до **Settings → CI/CD → Variables → Add variable**
2. Додайте змінну:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN`
    - **Value:** вставте ваш токен
    - **Flags:** увімкніть **Masked**, :x: **зніміть** Protected

    The variable is automatically available to all jobs — no YAML `variables:` mapping needed.

!!! warning "Зніміть «Protected»!"
    За замовчуванням GitLab позначає нові змінні як **Protected**. Protected змінні **доступні лише в захищених гілках** (наприклад, `main`).

    MR pipeline запускається на **незахищених** source гілках — тому змінна буде порожньою і ви отримаєте **401 Unauthorized**.

    **Завжди знімайте «Protected»** для `AI_REVIEWER_GITLAB_TOKEN` та `AI_REVIEWER_GOOGLE_API_KEY`.

!!! warning "Збережіть токен"
    GitLab показує токен **лише один раз**. Збережіть його в безпечному місці одразу.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Доступний лише на планах **GitLab Premium** та **Ultimate**. Гарний вибір, якщо ви хочете токен, прив'язаний до проєкту, а не до особистого акаунту.

**Переваги над PAT:**

- Обмежений одним проєктом (немає доступу до інших проєктів)
- Може бути відкликаний мейнтейнерами проєкту (немає залежності від конкретного користувача)
- Краще для команд — не прив'язаний до персонального акаунту

**Як створити:**

1. Перейдіть до **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Заповніть поля:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (мінімально необхідна роль)
    - **Scopes:** оберіть **`api`**
3. Натисніть **Create project access token**
4. **Скопіюйте токен одразу**

**Як використовувати в CI:**

Так само як PAT — додайте як `AI_REVIEWER_GITLAB_TOKEN` в CI/CD Variables:

1. **Key:** `AI_REVIEWER_GITLAB_TOKEN`
2. **Value:** вставте ваш Project Access Token

!!! info "Який токен обрати?"
    | | Personal Access Token | Project Access Token |
    |---|---|---|
    | **План** | Всі (включаючи Free) | Лише Premium/Ultimate |
    | **Налаштування** | Ручне | Ручне |
    | **Область дії** | Всі проєкти користувача | Один проєкт |
    | **Постити коментарі** | :white_check_mark: | :white_check_mark: |
    | **Inline коментарі** | :white_check_mark: | :white_check_mark: |
    | **Найкраще для** | Free план, особисте використання | Команди на Premium/Ultimate |

---

## CI/CD Variables

### Додавання змінних

`Settings → CI/CD → Variables → Add variable`

| Змінна | Значення | Опції |
|--------|----------|-------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API ключ | :white_check_mark: Masked, :x: **Uncheck** Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | PAT (якщо потрібен) | :white_check_mark: Masked, :x: **Uncheck** Protected |

!!! tip "Masked"
    Завжди вмикайте **Masked** для секретів — вони не будуть показані в логах.

---

## Triggers

### Рекомендований trigger

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Це запускає job тільки для Merge Request pipelines.

### Альтернативний trigger (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — новіший синтаксис, рекомендований GitLab.

---

## Job приклади

### Мінімальний

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

CI/CD змінні `AI_REVIEWER_GOOGLE_API_KEY` та `AI_REVIEWER_GITLAB_TOKEN` наслідуються автоматично.

### Повний (рекомендовано)

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

**Що робить:**

- `allow_failure: true` — MR не блокується якщо review failed
- `timeout: 10m` — максимум 10 хвилин
- `interruptible: true` — можна скасувати при новому коміті

### З кастомним stage

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
  needs: []  # Не чекати на попередні stages
```

---

## Self-hosted GitLab

### Конфігурація

```yaml
variables:
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
```

### Docker registry

Якщо ваш GitLab не має доступу до `ghcr.io`, створіть mirror:

```bash
# На машині з доступом
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

## GitLab CI змінні

AI Code Reviewer автоматично використовує:

| Змінна | Опис |
|--------|------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | Номер MR |
| `CI_SERVER_URL` | URL GitLab |

Вам не потрібно передавати `--repo` та `--pr` — вони беруться з CI автоматично.

---

## Конфігурація через змінні CI/CD {#variable-driven}

Використовуйте **CI/CD Variables** для перемикання між LLM-провайдерами та моделями без зміни `.gitlab-ci.yml`. Це зручно для порівняння якості рев'ю різних моделей на одному MR.

### Налаштування

**CI/CD Variables** (`Settings → CI/CD → Variables`):

| Змінна | Опис | Прапорці |
|--------|------|----------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API ключ | :white_check_mark: Masked, :x: Зняти Protected |
| `AI_REVIEWER_MISTRAL_API_KEY` | Mistral API ключ | :white_check_mark: Masked, :x: Зняти Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab токен | :white_check_mark: Masked, :x: Зняти Protected |
| `AI_REVIEWER_LLM_PROVIDER` | Основний провайдер (`google`, `mistral`) | :x: Зняти Protected |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Fallback-провайдер | :x: Зняти Protected |
| `AI_REVIEWER_MISTRAL_MODEL` | Модель Mistral | :x: Зняти Protected |
| `AI_REVIEWER_MISTRAL_API_URL` | Кастомний URL API (для Codestral free tier) | :x: Зняти Protected |

### Конфігурація job

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

Секція `variables:` не потрібна — всі `AI_REVIEWER_*` CI/CD змінні успадковуються автоматично.

### Перемикання пресетів

Змініть CI/CD Variables в GitLab UI, потім натисніть **Retry** на pipeline того ж MR:

| Пресет | `AI_REVIEWER_LLM_PROVIDER` | `AI_REVIEWER_MISTRAL_MODEL` | `AI_REVIEWER_MISTRAL_API_URL` | `AI_REVIEWER_LLM_FALLBACK_PROVIDER` |
|--------|---------------------------|---------------------------|-------------------------------|-------------------------------------|
| Gemini (за замовчуванням) | `google` | _(немає)_ | _(немає)_ | _(немає)_ |
| Mistral Large | `mistral` | `mistral-large-latest` | _(немає)_ | `google` |
| Codestral free | `mistral` | `codestral-latest` | `https://codestral.mistral.ai` | `google` |
| Devstral | `mistral` | `devstral-latest` | _(немає)_ | `google` |

!!! tip "Ключ для Codestral free tier"
    Для пресету "Codestral free" `AI_REVIEWER_MISTRAL_API_KEY` має містити ключ з [codestral.mistral.ai](https://codestral.mistral.ai/), а не з `console.mistral.ai`.

!!! info "Не потрібно прописувати в YAML"
    На відміну від GitHub Actions (де inputs треба мапити явно), GitLab CI автоматично передає всі CI/CD змінні як змінні оточення. Просто задайте їх в UI — додаток підхопить через префікс `AI_REVIEWER_*`.

---

## Результат review

### Notes (коментарі)

AI Review публікує коментарі до MR як notes.

### Discussions (inline)

Для inline коментарів потрібен PAT або Project Access Token.

Inline коментарі з'являються безпосередньо біля рядків коду в diff view.

### Summary

В кінці review публікується Summary note з:

- Загальною статистикою
- Метриками
- Good practices

---

## Troubleshooting

### Review не постить коментарі

**Перевірте:**

1. `AI_REVIEWER_GOOGLE_API_KEY` змінна встановлена
2. `AI_REVIEWER_GITLAB_TOKEN` має достатньо прав (scope: `api`)
3. Pipeline запущено для MR (не для гілки)

### "401 Unauthorized"

**Причина:** Невалідний токен.

**Рішення:**

- Перевірте що токен не expired
- Перевірте scope (потрібен `api`)

### "403 Forbidden"

**Причина:** Недостатньо прав.

**Рішення:**

- Перевірте що використовуєте PAT або Project Access Token (не `CI_JOB_TOKEN`)
- Перевірте що токен має доступ до проєкту

### "404 Not Found"

**Причина:** MR не знайдено.

**Рішення:**

- Перевірте що pipeline запущено для MR
- Перевірте `CI_MERGE_REQUEST_IID`

### Rate limit (429)

**Причина:** Перевищено ліміт API.

**Рішення:**

- AI Code Reviewer автоматично retry з backoff
- Якщо постійно — зачекайте або збільште ліміти

---

## Best practices

### 1. Використовуйте PAT для повної функціональності

### 2. Додайте allow_failure

```yaml
allow_failure: true
```

MR не буде заблоковано якщо review failed.

### 3. Встановіть timeout

```yaml
timeout: 10m
```

### 4. Зробіть job interruptible

```yaml
interruptible: true
```

При новому коміті старий review буде скасовано.

### 5. Не чекайте на інші stages

```yaml
needs: []
```

Review запуститься одразу, не чекаючи на build/test.

---

## Наступний крок

- [GitHub інтеграція →](github.md)
- [CLI Reference →](api.md)
