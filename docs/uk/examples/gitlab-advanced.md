# GitLab: Розширений приклад

Production-ready конфігурація з усіма best practices.

---

## Крок 1: Створіть Personal Access Token (PAT)

`User Settings → Access Tokens → Add new token`

| Поле | Значення |
|------|----------|
| Name | `ai-code-reviewer` |
| Scopes | `api` |
| Expiration | За потреби |

!!! info "Free план"
    **Personal Access Token** працює на **всіх планах GitLab**, включаючи Free.

    **Project Access Token** доступний лише на **GitLab Premium/Ultimate**.

---

## Крок 2: Додайте змінні

`Settings → CI/CD → Variables`

| Назва | Значення | Опції |
|-------|----------|-------|
| `GOOGLE_API_KEY` | Gemini API ключ | Masked |
| `GITLAB_TOKEN` | PAT з Кроку 1 | Masked |

---

## Крок 3: Додайте job

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - review

# ... інші jobs ...

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1

  script:
    - ai-review

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

  # Не блокувати MR якщо review failed
  allow_failure: true

  # Timeout захист
  timeout: 10m

  # Можна скасувати при новому коміті
  interruptible: true

  # Не чекати на інші stages
  needs: []

  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
```

---

## Що включено

| Функція | Статус | Опис |
|---------|--------|------|
| Inline discussions | :white_check_mark: | З PAT токеном |
| Non-blocking | :white_check_mark: | `allow_failure: true` |
| Timeout | :white_check_mark: | 10 хвилин |
| Interruptible | :white_check_mark: | Скасовується при новому коміті |
| Паралельний запуск | :white_check_mark: | `needs: []` |
| Українська мова | :white_check_mark: | `LANGUAGE: uk` |

---

## Варіації

### Self-hosted GitLab

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    GITLAB_URL: https://gitlab.mycompany.com
```

### З кастомним Docker registry

```yaml
ai-review:
  # Якщо ghcr.io недоступний
  image: registry.mycompany.com/devops/ai-code-reviewer:latest
```

### З DEBUG логами

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LOG_LEVEL: DEBUG
```

### Тільки для певних гілок

```yaml
ai-review:
  # ...
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: always
    - if: $CI_MERGE_REQUEST_TARGET_BRANCH_NAME == "main"
      when: always
```

---

## CI_JOB_TOKEN vs PAT

| Функція | CI_JOB_TOKEN | PAT |
|---------|--------------|-----|
| Читати MR | :white_check_mark: | :white_check_mark: |
| Постити notes | :white_check_mark: | :white_check_mark: |
| Inline discussions | :x: | :white_check_mark: |
| Потребує налаштування | :x: | :white_check_mark: |

**Рекомендація:** Використовуйте Personal Access Token для повної функціональності. Він працює на всіх планах GitLab, включаючи Free.

---

## Troubleshooting

### Review не постить коментарі

1. Перевірте логи job
2. Перевірте що `GITLAB_TOKEN` має scope `api`
3. Перевірте що pipeline запущено для MR

### "401 Unauthorized"

Токен невалідний або expired. Створіть новий PAT.

### "403 Forbidden"

Токен не має доступу до проєкту. Перевірте права.

---

## Повний приклад .gitlab-ci.yml

```yaml
stages:
  - lint
  - test
  - review
  - deploy

lint:
  stage: lint
  image: python:3.13
  script:
    - pip install ruff
    - ruff check .

test:
  stage: test
  image: python:3.13
  script:
    - pip install pytest
    - pytest

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  interruptible: true
  needs: []
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Наступний крок

:point_right: [Конфігурація →](../configuration.md)
