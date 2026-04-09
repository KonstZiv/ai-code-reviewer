# GitHub

Детальний гайд для інтеграції з GitHub Actions.

---

## Permissions

### Мінімальні права

```yaml
permissions:
  contents: read        # Читати код
  pull-requests: write  # Писати коментарі
```

### GITHUB_TOKEN в Actions

В GitHub Actions автоматично доступний `GITHUB_TOKEN`:

```yaml
env:
  GITHUB_TOKEN: ${{ github.token }}
```

**Права автоматичного токену:**

| Право | Статус | Примітка |
|-------|--------|----------|
| `contents: read` | :white_check_mark: | За замовчуванням |
| `pull-requests: write` | :white_check_mark: | Потрібно вказати в `permissions` |

!!! warning "Fork PRs"
    Для PR з fork репозиторіїв `GITHUB_TOKEN` має **лише read** права.

    AI Review не зможе постити коментарі для fork PRs.

### Як отримати Personal Access Token {#get-token}

Для **локального запуску** потрібен Personal Access Token (PAT):

1. Перейдіть до `Settings → Developer settings → Personal access tokens`
2. Оберіть **Fine-grained tokens** (рекомендовано) або Classic
3. Натисніть **Generate new token**

**Fine-grained token (рекомендовано):**

| Налаштування | Значення |
|--------------|----------|
| Repository access | Only select repositories → ваш репозиторій |
| Permissions | `Pull requests: Read and write` |

**Classic token:**

| Scope | Опис |
|-------|------|
| `repo` | Повний доступ до репозиторію |

4. Натисніть **Generate token**
5. Скопіюйте токен та збережіть як `GITHUB_TOKEN`

!!! warning "Збережіть токен"
    GitHub показує токен **лише один раз**. Збережіть його одразу.

---

## Triggers

### Рекомендований trigger

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

| Тип | Коли спрацьовує |
|-----|-----------------|
| `opened` | PR створено |
| `synchronize` | Нові коміти в PR |
| `reopened` | PR відкрито знову |

### Фільтрація по файлах

Запускати review тільки для певних файлів:

```yaml
on:
  pull_request:
    paths:
      - '**.py'
      - '**.js'
      - '**.ts'
```

### Фільтрація по гілках

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

---

## Secrets

### Додавання секретів

`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Обов'язковий | Опис |
|--------|--------------|------|
| `AI_REVIEWER_GOOGLE_API_KEY` | :white_check_mark: | Gemini API ключ |

### Використання

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
```

!!! danger "Ніколи не хардкодьте секрети"
    ```yaml
    # ❌ НЕПРАВИЛЬНО
    env:
      AI_REVIEWER_GOOGLE_API_KEY: AIza...

    # ✅ ПРАВИЛЬНО
    env:
      AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    ```

---

## Workflow приклади

### Мінімальний

```yaml
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
```

!!! info "Про `GITHUB_TOKEN`"
    `secrets.GITHUB_TOKEN` — це **автоматичний токен**, який GitHub створює для кожного workflow run. Його **не потрібно** додавати в secrets вручну — він вже доступний.

    Права токена визначаються секцією `permissions` у workflow файлі.

    :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

### З concurrency (рекомендовано)

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
          language: uk
          language_mode: adaptive
```

**Що робить concurrency:**

- Якщо новий коміт пушиться поки review ще йде — старий review скасовується
- Економить ресурси та API calls

### З фільтрацією fork PRs

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    # Не запускати для fork PRs (немає доступу до secrets)
    if: github.event.pull_request.head.repo.full_name == github.repository
```

---

## GitHub Action inputs

| Input | Опис | Default |
|-------|------|---------|
| `google_api_key` | Gemini API ключ | **required** |
| `github_token` | GitHub токен | `${{ github.token }}` |
| `language` | Мова відповідей | `en` |
| `language_mode` | Режим мови | `adaptive` |
| `gemini_model` | Модель Gemini | `gemini-2.5-flash` |
| `log_level` | Рівень логування | `INFO` |
| `review_max_comment_chars` | Макс. символів коментаря MR у промпті | `3000` |
| `review_include_bot_comments` | Включати коментарі ботів у промпт | `true` |
| `review_post_inline_comments` | Публікувати inline коментарі до рядків | `true` |
| `gemini_model_fallback` | Fallback model chain (comma-separated) | `gemini-3.1-flash-preview` |
| `review_enable_dialogue` | Групувати коментарі в діалоги | `true` |
| `discovery_enabled` | Увімкнути project discovery | `true` |
| `discovery_verbose` | Завжди публікувати discovery коментар | `false` |
| `discovery_timeout` | Таймаут discovery в секундах | `30` |

!!! tip "Змінні оточення"
    Action передає inputs у змінні оточення `AI_REVIEWER_*` внутрішньо. При запуску поза Action використовуйте змінні `AI_REVIEWER_*` напряму (старі назви, наприклад `GOOGLE_API_KEY`, все ще працюють як fallback).

---

## Результат review

### Inline comments

AI Review публікує коментарі безпосередньо до рядків коду:

- :red_circle: **CRITICAL** — критичні проблеми (security, bugs)
- :yellow_circle: **WARNING** — рекомендації
- :blue_circle: **INFO** — навчальні нотатки

### Apply Suggestion

Кожен коментар з пропозицією коду має кнопку **"Apply suggestion"**:

```suggestion
fixed_code_here
```

GitHub автоматично рендерить це як інтерактивну кнопку.

### Summary

В кінці review публікується Summary з:

- Загальною статистикою issues
- Метриками (час, токени, вартість)
- Good practices (позитивний фідбек)

---

## Troubleshooting

### Review не постить коментарі

**Перевірте:**

1. `permissions: pull-requests: write` є в workflow
2. `AI_REVIEWER_GOOGLE_API_KEY` секрет встановлено
3. PR не з fork репозиторію

### "Resource not accessible by integration"

**Причина:** Недостатньо прав.

**Рішення:** Додайте permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### Rate limit від Gemini

**Причина:** Перевищено ліміт free tier (15 RPM).

**Рішення:**

- Зачекайте хвилину
- Додайте `concurrency` для скасування старих runs
- Розгляньте paid tier

---

## Best practices

### 1. Завжди використовуйте concurrency

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### 2. Фільтруйте fork PRs

```yaml
if: github.event.pull_request.head.repo.full_name == github.repository
```

### 3. Встановіть timeout

```yaml
jobs:
  review:
    timeout-minutes: 10
```

### 4. Зробіть job non-blocking

```yaml
jobs:
  review:
    continue-on-error: true
```

---

## Наступний крок

- [GitLab інтеграція →](gitlab.md)
- [CLI Reference →](api.md)
