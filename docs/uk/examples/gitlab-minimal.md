# GitLab: Мінімальний приклад

Найпростіша конфігурація для GitLab CI.

---

## Крок 1: Додайте змінну

`Settings → CI/CD → Variables → Add variable`

| Назва | Значення | Опції |
|-------|----------|-------|
| `GOOGLE_API_KEY` | Ваш Gemini API ключ | Masked |

---

## Крок 2: Додайте job

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

---

## Крок 3: Створіть MR

Готово! AI review з'явиться як коментарі до MR.

---

## Що включено

| Функція | Статус |
|---------|--------|
| Notes до MR | :white_check_mark: |
| Мовна адаптивність | :white_check_mark: (adaptive) |
| Метрики | :white_check_mark: |
| Auto-retry | :white_check_mark: |

---

## Обмеження

| Обмеження | Рішення |
|-----------|---------|
| `CI_JOB_TOKEN` обмежений | Використовуйте PAT |
| Немає inline discussions | Потрібен PAT з scope `api` |
| MR блокується при помилці | Додайте `allow_failure: true` |

!!! info "PAT vs Project Access Token"
    **Personal Access Token** (PAT) працює на **всіх планах GitLab**, включаючи Free.

    **Project Access Token** потребує **GitLab Premium/Ultimate**.
    На Free плані завжди використовуйте Personal Access Token.

---

## Наступний крок

:point_right: [Розширений приклад →](gitlab-advanced.md)
