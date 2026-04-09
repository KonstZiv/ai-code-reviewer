# Troubleshooting

FAQ та вирішення типових проблем.

---

## Поширені проблеми

### Action показує --help замість виконання

**Симптом:** В логах CI job видно:

```
Usage: ai-review [OPTIONS]
...
╭─ Options ─────────────────────────────────────────────────────────╮
│ --provider  -p      [github|gitlab]  CI provider...              │
```

**Причина:** Використовується стара версія Docker image (до v1.0.0a2).

**Рішення:**

Оновіть до останньої версії:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1  # Завжди використовує останню v1.x
```

Якщо проблема залишається, явно вкажіть версію:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1.0.0a2  # Або новіше
```

---

### Review не з'являється

**Симптом:** CI job пройшов успішно, але коментарів немає.

**Перевірте:**

1. **Логи CI job** — чи є помилки?
2. **API ключ** — чи валідний `AI_REVIEWER_GOOGLE_API_KEY`?
3. **Токен** — чи є права на write?
4. **github_token** — чи передано явно?

=== "GitHub"

    ```yaml
    permissions:
      contents: read
      pull-requests: write  # ← Обов'язково!
    ```

=== "GitLab"

    Переконайтесь що `GITLAB_TOKEN` має scope `api`.

---

### "Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short"

**Причина:** Ключ не встановлено або він некоректний.

**Рішення:**

1. Перевірте що секрет додано в repo settings
2. Перевірте назву (case-sensitive)
3. Перевірте що ключ валідний на [Google AI Studio](https://aistudio.google.com/)

---

### "401 Unauthorized" / "403 Forbidden"

**Причина:** Невалідний або недостатній токен.

=== "GitHub"

    ```yaml
    # Перевірте permissions
    permissions:
      contents: read
      pull-requests: write
    ```

=== "GitLab"

    - Перевірте що токен не expired
    - Перевірте scope: потрібен `api`
    - Переконайтесь що використовуєте Project Access Token

---

### "404 Not Found"

**Причина:** PR/MR або репозиторій не знайдено.

**Рішення:**

1. Перевірте що PR/MR існує
2. Перевірте назву репозиторію
3. Перевірте що токен має доступ до репозиторію

---

### "429 Too Many Requests" (Rate Limit)

**Причина:** Перевищено ліміт API.

**Gemini Free Tier ліміти:**

| Ліміт | Значення |
|-------|----------|
| Requests per minute | 15 |
| Tokens per day | 1,000,000 |
| Requests per day | 1,500 |

**Рішення:**

1. AI Code Reviewer автоматично робить retry з exponential backoff
2. Якщо проблема постійна — зачекайте або перейдіть на paid tier
3. Додайте `concurrency` для скасування дублікатів:

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

---

### "500 Internal Server Error"

**Причина:** Проблема на стороні API (Google, GitHub, GitLab).

**Рішення:**

1. AI Code Reviewer автоматично робить retry (до 5 спроб)
2. Перевірте статус сервісів:
   - [Google Cloud Status](https://status.cloud.google.com/)
   - [GitHub Status](https://www.githubstatus.com/)
   - [GitLab Status](https://status.gitlab.com/)

---

### Review занадто повільний

**Причина:** Великий PR або повільна мережа.

**Рішення:**

1. Зменшіть розмір PR
2. Налаштуйте ліміти:

```bash
export REVIEW_MAX_FILES=10
export REVIEW_MAX_DIFF_LINES=300
```

3. Встановіть timeout:

```yaml
# GitHub
timeout-minutes: 10

# GitLab
timeout: 10m
```

---

### Fork PRs не отримують review

**Причина:** Секрети недоступні для fork PRs (security).

**Рішення:**

Це очікувана поведінка. Для fork PRs:

1. Maintainer може запустити review вручну
2. Або використати `pull_request_target` (обережно з безпекою!)

---

### Мова відповідей неправильна

**Причина:** Неправильна конфігурація мови.

**Рішення:**

1. Для фіксованої мови:
```bash
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

2. Для адаптивної мови — переконайтесь що PR description написаний потрібною мовою

---

## FAQ

### Чи можна використовувати без API ключа?

**Ні.** Потрібен Google Gemini API ключ. Free tier достатній для більшості проєктів.

### Чи підтримується Bitbucket?

**Ні** (поки що). Тільки GitHub та GitLab.

### Чи можна використовувати інші LLM (ChatGPT, Claude)?

**Ні** (в MVP). Підтримка інших LLM планується в майбутніх версіях.

### Чи безпечно передавати код до Google API?

**Важливо знати:**

- Код передається до Google Gemini API для аналізу
- Ознайомтесь з [Google AI Terms](https://ai.google.dev/terms)
- Для sensitive проєктів розгляньте self-hosted рішення (у майбутніх версіях)

### Скільки коштує?

**Gemini Flash pricing:**

| Метрика | Вартість |
|---------|----------|
| Input tokens | $0.075 / 1M |
| Output tokens | $0.30 / 1M |

**Приблизно:** ~1000 reviews = ~$1

Free tier: ~100 reviews/день безкоштовно.

### Як відключити review для певних файлів?

Поки що немає `.ai-reviewerignore`. Планується в майбутніх версіях.

Workaround: фільтруйте в workflow:

```yaml
on:
  pull_request:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Чи можна запустити локально?

**Так:**

```bash
pip install ai-reviewbot
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token
ai-review --provider github --repo owner/repo --pr 123
```

---

## Debugging

### Увімкнути verbose логи

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Перевірити конфігурацію

```bash
# Перевірте що змінні встановлені
echo $AI_REVIEWER_GOOGLE_API_KEY | head -c 10
echo $GITHUB_TOKEN | head -c 10
```

### Тестовий запуск API

```bash
# Перевірити Gemini API
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$AI_REVIEWER_GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Отримати допомогу

Якщо проблема не вирішена:

1. :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — для багів
2. :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — для питань

**При створенні issue додайте:**

- Версію AI Code Reviewer (`ai-review --version`)
- CI провайдер (GitHub/GitLab)
- Логи (з прихованими секретами!)
- Кроки для відтворення

---

## Наступний крок

- [Приклади →](examples/index.md)
- [Конфігурація →](configuration.md)
