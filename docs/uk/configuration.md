# Конфігурація

Всі налаштування через environment variables.

---

## Обов'язкові змінні

| Змінна | Опис | Приклад | Як отримати |
|--------|------|---------|-------------|
| `GOOGLE_API_KEY` | API ключ Google Gemini | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub токен (для GitHub) | `ghp_...` | [Інструкція](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab токен (для GitLab) | `glpat-...` | [Інструкція](gitlab.md#get-token) |

!!! warning "Мінімум один токен провайдера"
    Потрібен `GITHUB_TOKEN` **або** `GITLAB_TOKEN` залежно від платформи.
    Ці токени **специфічні для провайдера** — потрібен лише один, відповідний до платформи, яку ви використовуєте.

!!! info "Типи токенів GitLab"
    Для GitLab можна використовувати **Personal Access Token** (працює на всіх планах, включаючи Free)
    або **Project Access Token** (потребує GitLab Premium/Ultimate).

---

## Опціональні змінні {#optional}

### Загальні

| Змінна | Опис | Default | Діапазон |
|--------|------|---------|----------|
| `LOG_LEVEL` | Рівень логування | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `API_TIMEOUT` | Таймаут запитів (сек) | `60` | 1-300 |

### Мова

| Змінна | Опис | Default | Приклади |
|--------|------|---------|----------|
| `LANGUAGE` | Мова відповідей | `en` | `uk`, `de`, `es`, `it`, `me` |
| `LANGUAGE_MODE` | Режим визначення | `adaptive` | `adaptive`, `fixed` |

**Режими мови:**

- **`adaptive`** (default) — автоматично визначає мову з контексту PR/MR (опис, коментарі, linked task)
- **`fixed`** — завжди використовує мову з `LANGUAGE`

!!! tip "ISO 639"
    `LANGUAGE` приймає будь-який валідний ISO 639 код:

    - 2-літерні: `en`, `uk`, `de`, `es`, `it`
    - 3-літерні: `ukr`, `deu`, `spa`
    - Назви: `English`, `Ukrainian`, `German`

### LLM

| Змінна | Опис | Default |
|--------|------|---------|
| `GEMINI_MODEL` | Модель Gemini | `gemini-2.5-flash` |

**Доступні моделі:**

| Модель | Опис | Вартість |
|--------|------|----------|
| `gemini-2.5-flash` | Швидка, дешева | $0.075 / 1M input |
| `gemini-2.0-flash` | Попередня версія | $0.075 / 1M input |
| `gemini-1.5-pro` | Потужніша | $1.25 / 1M input |

!!! note "Актуальність цін"
    Вартості вказані на день релізу і можуть змінюватись.

    Актуальна інформація: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Звертайте увагу на **Free Tier** у використанні певних моделей.

    У переважній більшості випадків безкоштовного ліміту достатньо для code review команди **4-8 розробників**.

### Review

| Змінна | Опис | Default | Діапазон |
|--------|------|---------|----------|
| `REVIEW_MAX_FILES` | Макс. файлів у контексті | `20` | 1-100 |
| `REVIEW_MAX_DIFF_LINES` | Макс. рядків diff на файл | `500` | 1-5000 |

### GitLab

| Змінна | Опис | Default |
|--------|------|---------|
| `GITLAB_URL` | URL GitLab сервера | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    Для self-hosted GitLab встановіть `GITLAB_URL`:
    ```bash
    export GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## Файл .env

Зручно зберігати конфігурацію в `.env`:

```bash
# .env
GOOGLE_API_KEY=AIza...
GITHUB_TOKEN=ghp_...

# Optional
LANGUAGE=uk
LANGUAGE_MODE=adaptive
GEMINI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
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
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GITHUB_TOKEN: ${{ github.token }}  # Автоматичний
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  GOOGLE_API_KEY: $GOOGLE_API_KEY  # З CI/CD Variables
  # GITLAB_TOKEN: $CI_JOB_TOKEN   # Автоматичний (обмежений)
  GITLAB_TOKEN: $GITLAB_TOKEN      # Або PAT для повних прав
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

---

## Валідація

AI Code Reviewer валідує конфігурацію при старті:

### Помилки валідації

```
ValidationError: GOOGLE_API_KEY is too short (minimum 10 characters)
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
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
```

### Мінімальна (GitLab)

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
```

### Українська мова, фіксована

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

### Self-hosted GitLab

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
export GITLAB_URL=https://gitlab.mycompany.com
```

### Debug режим

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LOG_LEVEL=DEBUG
```

---

## Пріоритет конфігурації

1. **Environment variables** (найвищий)
2. **Файл `.env`** в поточній директорії

---

## Наступний крок

- [GitHub інтеграція →](github.md)
- [GitLab інтеграція →](gitlab.md)
