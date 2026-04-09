# Конфігурація

Всі налаштування через environment variables.

!!! tip "Міграція: префікс `AI_REVIEWER_`"
    Починаючи з v1.0.0a7, всі змінні оточення підтримують префікс `AI_REVIEWER_` (напр., `AI_REVIEWER_GOOGLE_API_KEY`). Старі імена (напр., `GOOGLE_API_KEY`) працюють як fallback. Рекомендуємо мігрувати на нові імена для уникнення конфліктів з іншими інструментами в CI/CD конфігураціях на рівні організації.

---

## Обов'язкові змінні

| Змінна | Опис | Приклад | Як отримати |
|--------|------|---------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | API ключ Google Gemini (через кому для ротації ключів) | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub токен (для GitHub) | `ghp_...` | [Інструкція](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab токен (для GitLab) | `glpat-...` | [Інструкція](gitlab.md#get-token) |

!!! warning "Мінімум один токен провайдера"
    Потрібен `AI_REVIEWER_GITHUB_TOKEN` **або** `AI_REVIEWER_GITLAB_TOKEN` залежно від платформи.
    Ці токени **специфічні для провайдера** — потрібен лише один, відповідний до платформи, яку ви використовуєте.

!!! info "Типи токенів GitLab"
    Для GitLab можна використовувати **Personal Access Token** (працює на всіх планах, включаючи Free)
    або **Project Access Token** (потребує GitLab Premium/Ultimate).

---

## Опціональні змінні {#optional}

### Загальні

| Змінна | Опис | Default | Діапазон |
|--------|------|---------|----------|
| `AI_REVIEWER_LOG_LEVEL` | Рівень логування | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_REVIEWER_API_TIMEOUT` | Таймаут запитів (сек) | `60` | 1-300 |

### Мова

| Змінна | Опис | Default | Приклади |
|--------|------|---------|----------|
| `AI_REVIEWER_LANGUAGE` | Мова відповідей | `en` | `uk`, `de`, `es`, `it`, `me` |
| `AI_REVIEWER_LANGUAGE_MODE` | Режим визначення | `adaptive` | `adaptive`, `fixed` |

**Режими мови:**

- **`adaptive`** (default) — автоматично визначає мову з контексту PR/MR (опис, коментарі, linked task)
- **`fixed`** — завжди використовує мову з `AI_REVIEWER_LANGUAGE`

!!! tip "ISO 639"
    `AI_REVIEWER_LANGUAGE` приймає будь-який валідний ISO 639 код:

    - 2-літерні: `en`, `uk`, `de`, `es`, `it`
    - 3-літерні: `ukr`, `deu`, `spa`
    - Назви: `English`, `Ukrainian`, `German`

### LLM

| Змінна | Опис | Default |
|--------|------|---------|
| `AI_REVIEWER_GEMINI_MODEL` | Модель Gemini | `gemini-2.5-flash` |
| `AI_REVIEWER_GEMINI_MODEL_FALLBACK` | Ланцюжок fallback-моделей (через кому) | `gemini-3.1-flash-preview` |
| `AI_REVIEWER_REVIEW_SPLIT_THRESHOLD` | Поріг символів для split review (код+тести окремо) | `30000` |

**Доступні моделі:**

| Модель | Опис | Ціна |
|--------|------|------|
| `gemini-2.5-flash` | Швидка, стабільна, з reasoning (за замовчуванням) | $0.075 / 1M input |
| `gemini-3.1-flash-preview` | Frontier-клас flash (preview) | $0.075 / 1M input |
| `gemini-2.5-flash-lite` | Найшвидша і найдешевша в 2.5 | $0.01875 / 1M input |
| `gemini-2.5-pro` | Найпотужніша, з глибоким reasoning | $1.25 / 1M input |

!!! note "Актуальність цін"
    Вартості вказані на день релізу і можуть змінюватись.

    Актуальна інформація: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Звертайте увагу на **Free Tier** у використанні певних моделей.

    У переважній більшості випадків безкоштовного ліміту достатньо для code review команди **4-8 розробників**.

### Review

| Змінна | Опис | Default | Діапазон |
|--------|------|---------|----------|
| `AI_REVIEWER_REVIEW_MAX_FILES` | Макс. файлів у контексті | `20` | 1-100 |
| `AI_REVIEWER_REVIEW_MAX_DIFF_LINES` | Макс. рядків diff на файл | `500` | 1-5000 |
| `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS` | Макс. символів коментарів MR у промпті | `3000` | 0-20000 |
| `AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS` | Включати коментарі ботів у промпт | `true` | true/false |
| `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS` | Публікувати inline коментарі на рядках | `true` | true/false |
| `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE` | Групувати коментарі у діалогові потоки | `true` | true/false |

!!! info "Контекст обговорення"
    AI-рев'ювер читає існуючі коментарі MR/PR, щоб не повторювати пропозиції,
    які вже обговорювались. Встановіть `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS=0` для вимкнення.

!!! info "Inline коментарі"
    Коли `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS=true` (default), issues з інформацією про файл/рядок публікуються як inline коментарі до коду, з коротким summary як тілом ревʼю. Встановіть `false` для одного summary коментаря.

!!! info "Діалогові потоки"
    Коли `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE=true` (default), коментарі групуються у
    діалогові потоки, щоб AI розумів ланцюжки відповідей. Встановіть `false` для плоского відображення.

### Discovery

| Змінна | Опис | Default | Діапазон |
|--------|------|---------|----------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | Увімкнути аналіз проєкту перед ревʼю | `true` | true/false |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | Завжди постити коментар discovery (default: тільки при прогалинах) | `false` | true/false |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | Таймаут discovery pipeline у секундах | `30` | 1-300 |

!!! info "Аналіз проєкту"
    Коли увімкнено, AI ReviewBot автоматично аналізує ваш репозиторій (мови, CI pipeline, конфіг-файли) перед кожним ревʼю для розумнішого зворотного звʼязку. Встановіть `false` для вимкнення. Деталі: [Discovery →](discovery.md).

!!! info "Verbose mode"
    Коли `AI_REVIEWER_DISCOVERY_VERBOSE=true`, коментар discovery завжди поститься і включає всі Attention Zones (Well Covered, Weakly Covered, Not Covered). Default режим постить тільки коли є прогалини або непокриті зони.

### GitLab

| Змінна | Опис | Default |
|--------|------|---------|
| `AI_REVIEWER_GITLAB_URL` | URL GitLab сервера | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    Для self-hosted GitLab встановіть `AI_REVIEWER_GITLAB_URL`:
    ```bash
    export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## Файл .env

Зручно зберігати конфігурацію в `.env`:

```bash
# .env
AI_REVIEWER_GOOGLE_API_KEY=AIza...
AI_REVIEWER_GITHUB_TOKEN=ghp_...

# Optional
AI_REVIEWER_LANGUAGE=uk
AI_REVIEWER_LANGUAGE_MODE=adaptive
AI_REVIEWER_GEMINI_MODEL=gemini-2.5-flash
AI_REVIEWER_LOG_LEVEL=INFO
```

!!! danger "Безпека"
    **Ніколи не комітьте `.env` в git!**

    Додайте до `.gitignore`:
    ```
    .env
    .env.*
    ```

---

## CI/CD конфігурація

### GitHub Actions

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
  AI_REVIEWER_GITHUB_TOKEN: ${{ github.token }}  # Автоматичний
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  # AI_REVIEWER_GOOGLE_API_KEY та AI_REVIEWER_GITLAB_TOKEN
  # успадковуються з CI/CD Variables автоматично
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

---

## Валідація

AI Code Reviewer валідує конфігурацію при старті:

### Помилки валідації

```
ValidationError: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Рішення:** Перевірте що змінна встановлена коректно.

```
ValidationError: Invalid language code 'xyz'
```

**Рішення:** Використовуйте валідний ISO 639 код.

```
ValidationError: LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Рішення:** Використовуйте один з дозволених рівнів.

---

## Приклади конфігурацій

### Мінімальна (GitHub)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
```

### Мінімальна (GitLab)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
```

### Українська мова, фіксована

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LANGUAGE=uk
export AI_REVIEWER_LANGUAGE_MODE=fixed
```

### Self-hosted GitLab

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
```

### Debug режим

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LOG_LEVEL=DEBUG
```

---

## Пріоритет конфігурації

1. **Environment variables** (найвищий)
2. **Файл `.env`** в поточній директорії

---

## Наступний крок

- [GitHub інтеграція →](github.md)
- [GitLab інтеграція →](gitlab.md)
