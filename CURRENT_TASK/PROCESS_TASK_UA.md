# Канвас прогресу Спрінту 1 (Розширений) — MVP Code Reviewer

**Початок спрінту:** 2026-01-20
**Мета спрінту:** MVP з GitHub + GitLab, Inline Comments, WOW-ефект
**Статус:** 🚧 В роботі

---

## 📊 Огляд спрінту

| Метрика | Ціль | Поточне | Статус |
|---------|------|---------|--------|
| **Завдань виконано** | 10/10 | 9/10 | 🏗️ |
| **Покриття тестами** | ≥80% | 92% | ✅ |
| **GitHub інтеграція** | ✅ Працює | ✅ GitProvider ABC | ✅ |
| **GitLab інтеграція** | ✅ Працює | ✅ GitLabClient готовий | ✅ |
| **Inline Comments** | ✅ Apply button | ✅ WOW-форматування готове | ✅ |
| **Мовна адаптивність** | ✅ Працює | ✅ ISO 639 + Proximity Rule | ✅ |
| **Метрики** | ✅ В footer | ✅ Tokens, latency, cost | ✅ |
| **Docker image** | ✅ Опубліковано | ✅ DockerHub + GHCR | ✅ |
| **GitHub Action** | ✅ Marketplace | ✅ Опубліковано | ✅ |
| **PyPI package** | ✅ v1.0.0a1 | ✅ Опубліковано | ✅ |

---

## 🎯 Беклог спрінту

### ✅ Раніше виконані завдання (з попередньої версії спрінту)

Наступні компоненти були створені раніше і потребують **рефакторингу/розширення**:

| Компонент | Статус | Потрібні зміни |
|-----------|--------|----------------|
| `core/models.py` | ✅ Базовий | Додати CodeIssue, GoodPractice, ReviewMetrics |
| `core/config.py` | ✅ Базовий | Додати LanguageMode, GitLab settings |
| `core/formatter.py` | ✅ Базовий | Переписати з WOW-форматуванням |
| `integrations/github.py` | ✅ Базовий | Рефакторинг на GitProvider, Inline Comments |
| `integrations/gemini.py` | ✅ Базовий | Додати метрики |
| `integrations/prompts.py` | ✅ Базовий | Оновити для менторського ревʼю |
| `reviewer.py` | ✅ Базовий | Оновити для нової архітектури |
| `cli.py` | ✅ Базовий | Виправити entry point, GitLab support |

---

### 🔧 Завдання 1: Фундамент та виправлення
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-23)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 2 години

**Чеклист:**
- [x] Виправлено entry point в `pyproject.toml`
- [x] Створено `ensure_timezone()` в `utils/time.py`
- [x] Додано `LanguageMode` enum в Settings
- [x] Додано `api_timeout` в Settings
- [x] Додано `@lru_cache` для `get_settings()`
- [x] Додано `tenacity` в залежності
- [x] `ai-review --help` працює

**Нотатки:**
```
- Entry point: змінено main → app (Typer вимагає app object)
- Додано clear_settings_cache() для тестів
- api_timeout: 5-300 сек, default 30
- LanguageMode: ADAPTIVE (default), FIXED
- 173 тестів пройшли після Task 1
```

---

### 🔌 Завдання 2: Архітектура провайдерів (Adapter)
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-23)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 3 години

**Чеклист:**
- [x] Створено `GitProvider` ABC в `base.py`
- [x] Створено `LineComment` dataclass
- [x] `GitHubClient` наслідує `GitProvider`
- [x] Реалізовано `submit_review()` з batch posting
- [x] `reviewer.py` використовує інтерфейс
- [x] Inline comments через GitHub Review API
- [x] Тести оновлено

**Нотатки:**
```
- Створено base.py: GitProvider ABC, LineComment, ReviewSubmission
- GitHubClient тепер наслідує GitProvider
- reviewer.py абстраговано від провайдера (dependency injection)
- CLI створює GitHubClient і передає в review_pull_request()
- Два методи для коментарів: post_comment() і submit_review()
- submit_review() використовує GitHub PR Review API для inline comments
- LineComment підтримує suggestions (→ кнопка "Apply suggestion")
- 196 тестів, 93% coverage
```

---

### 🦊 Завдання 3: Інтеграція GitLab
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [x] Створено `GitLabClient(GitProvider)` в `gitlab.py`
- [x] Реалізовано `get_merge_request()`
- [x] Реалізовано `get_linked_task()`
- [x] Реалізовано `submit_review()` через Discussions
- [x] Додано `GITLAB_TOKEN`, `GITLAB_URL` в Settings
- [x] Оновлено CLI для GitLab context
- [x] Написано інтеграційні тести

**Нотатки:**
```
- GitLabClient: повна імплементація GitProvider інтерфейсу
- get_merge_request(): отримання MR з notes та diffs
- get_linked_task(): пошук linked issues (Closes #123, Fixes #456)
- post_comment(): публікація notes до MR
- submit_review(): inline коментарі через Discussions API
- handle_gitlab_errors decorator для rate limiting (HTTP 429)
- CLI: extract_gitlab_context() для CI_PROJECT_PATH, CI_MERGE_REQUEST_IID
- Тести: 19 тестів для GitLabClient, 6 для config, 3 для CLI
- 222 тести, 92% coverage
```

---

### 🌍 Завдання 4a: Мовна адаптивність
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 3 години

**Чеклист:**
- [x] Додано залежність `python-iso639` для валідації ISO 639
- [x] Створено валідатор `_validate_language_code()` в config.py
- [x] Створено `utils/language.py` з алгоритмом "Proximity Rule"
- [x] Реалізовано `collect_text_samples()`, `build_language_instruction()`
- [x] Оновлено system prompt для адаптивності
- [x] Додано `detected_language` в `ReviewResult`
- [x] `LANGUAGE_MODE=fixed` працює
- [x] `LANGUAGE_MODE=adaptive` з fallback на англійську працює
- [x] Footer для російської мови ("Слава Украине!") в formatter.py
- [x] Тести написано (15 тестів для language.py + 8 для валідації + 10 для formatter)

**Нотатки:**
```
ISO 639 валідація:
- python-iso639 бібліотека для валідації всіх частин стандарту
- Нормалізація до ISO 639-1 (en, uk, de) де можливо
- Підтримка назв мов (Ukrainian → uk)

Алгоритм "Proximity Rule":
- Збирає тексти з коментарів (найновіші першими), MR description, task
- Фільтрує короткі тексти (<8 слів)
- Включає контекст в prompt для LLM визначення мови

Спеціальне повідомлення для ru:
- При LANGUAGE=ru до кожного review додається footer
- "каждый россиянин... Слава Украине!"

255 тестів, 93% coverage
```

---

### 🎨 Завдання 4b: Розширена структура ревʼю та WOW-форматування
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [x] Оновлено `models.py` з CodeIssue, GoodPractice
- [x] Оновлено system prompt для менторського ревʼю
- [x] Переписано `formatter.py` з WOW-форматуванням
- [x] GitHub suggestion syntax працює
- [x] Collapsible sections працюють
- [x] Good practices відображаються
- [x] Before/After diff preview працює

**Нотатки:**
```
Нові моделі:
- CodeIssue: unified модель з category, severity, why_matters, learn_more_url
- GoodPractice: позитивний фідбек
- IssueSeverity: CRITICAL, WARNING, INFO
- IssueCategory: SECURITY, CODE_QUALITY, ARCHITECTURE, PERFORMANCE, TESTING

Оновлений ReviewResult:
- issues: tuple[CodeIssue, ...] замість vulnerabilities
- good_practices: tuple[GoodPractice, ...]
- Нові properties: critical_count, warning_count, info_count, good_practice_count

Форматування:
- Summary card з підрахунком issues
- Секції по категоріям (🔒 Security, 📝 Code Quality, etc.)
- Collapsible learning sections (<details>)
- Before/After diff preview
- ```suggestion syntax для Apply button
- format_inline_comment() - компактний формат для line comments

272 тести, 93% coverage
```

---

### 📈 Завдання 4c: Метрики виконання
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 2 години

**Чеклист:**
- [x] Створено `ReviewMetrics` модель
- [x] `GeminiClient` збирає метрики
- [x] Обчислюється estimated cost
- [x] Footer з метриками в output
- [x] Тести написано

**Нотатки:**
```
ReviewMetrics модель:
- model_name, prompt_tokens, completion_tokens, total_tokens
- api_latency_ms, estimated_cost_usd
- cost_formatted (4 десяткові при <$0.01, інакше 2)
- latency_formatted (ms при <1000, інакше секунди)

Gemini pricing (per 1M tokens):
- gemini-2.5-flash: $0.075 input, $0.30 output
- gemini-1.5-pro: $1.25 input, $5.00 output
- Fallback для невідомих моделей: $1.00/$3.00

GeminiClient оновлено:
- time.perf_counter() для вимірювання latency
- response.usage_metadata для token counts
- calculate_cost() для обчислення вартості
- ReviewResult тепер включає metrics

Footer з метриками:
_Model: gemini-2.5-flash | Tokens: 1,500 | Latency: 1.2s | Est. cost: $0.0002_

Рефакторинг за ревʼю:
- DEFAULT_MODEL константа замість hardcoded string
- model_copy(update=...) замість model_dump() + model_validate()
- Тести оновлено для використання DEFAULT_MODEL

300 тестів, 93% coverage
```

---

### 🐳 Завдання 5: Контейнеризація та локальна підготовка
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Верифіковано:** ✅ (2026-01-25)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 3 години

**Чеклист:**
- [x] Створено multi-stage `Dockerfile`
- [x] Створено `.dockerignore`
- [x] Створено `action.yml`
- [x] Створено `examples/github-workflow.yml`
- [x] Створено `examples/gitlab-ci.yml`
- [x] Створено `examples/README.md`
- [x] Docker image збирається локально
- [x] `action.yml` валідний

> **Примітка:** Публікація на GHCR, DockerHub та GitHub Marketplace перенесена в Завдання 8

**Верифікація (2026-01-25):**
| Перевірка | Результат |
|-----------|-----------|
| Docker build | ✅ Success, 325MB |
| `ai-review --help` | ✅ CLI працює |
| Non-root user | ✅ `appuser` |
| git CLI | ✅ `git version 2.39.5` |
| Health check | ✅ 30s interval |
| Файли examples/ | ✅ 3 файли |

**Нотатки:**
```
Dockerfile:
- Multi-stage build: builder + runtime
- Builder: ghcr.io/astral-sh/uv:python3.13-bookworm-slim (uv для швидкого встановлення)
- Runtime: python:3.13-slim-bookworm (мінімальний образ)
- Розмір образу: 325MB
- Non-root user (appuser) для безпеки
- Health check: ai-review --help
- git CLI включено (потрібен для GitPython)
- Editable install: .venv + src копіюються в runtime

.dockerignore:
- Виключає tests/, docs/, .git, IDE файли, __pycache__, тощо
- Мінімізує context для швидкої збірки

action.yml (GitHub Action):
- Inputs: github_token, google_api_key, language, language_mode, gemini_model, log_level
- Docker runner з Dockerfile
- Environment variables автоматично передаються

examples/:
- github-workflow.yml: повний приклад workflow для GitHub Actions
  - Concurrency group для prevent duplicate reviews
  - Skip if PR is from fork (no secrets)
  - Permissions: contents read, pull-requests write
- gitlab-ci.yml: шаблон для GitLab CI
  - Rules: only merge_request_event
  - CI_JOB_TOKEN автоматично доступний
  - allow_failure: true
- README.md: документація з Quick Start та Troubleshooting

Проблема вирішена:
- uv sync створює editable install (.pth файл → /app/src)
- Потрібно копіювати src в runtime stage
- COPY --from=builder /app/src /app/src
```

---

### 🧪 Завдання 6: Тестування та стійкість
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-25)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [x] Створено `utils/retry.py`
- [x] Retry decorators додано до API clients
- [x] Error handling wrapper створено
- [x] Retry tests написано (33 тести)
- [x] Оновлено тести GitHub/GitLab/Gemini для нових exceptions
- [x] Логи структуровані (attempt, error_type, retry_in_ms)

**Exception Hierarchy:**
| Тип | Base | Retry? | HTTP Code |
|-----|------|--------|-----------|
| `RateLimitError` | `RetryableError` | ✅ | 429 |
| `ServerError` | `RetryableError` | ✅ | 5xx |
| `AuthenticationError` | `APIClientError` | ❌ Fail Fast | 401 |
| `ForbiddenError` | `APIClientError` | ❌ Fail Fast | 403 |
| `NotFoundError` | `APIClientError` | ❌ Fail Fast | 404 |

**Retry Configuration:**
- Max attempts: 5
- Backoff: exponential (2s → 30s)
- Logging: attempt, error_type, retry_in_ms

**Нотатки:**
```
Створено utils/retry.py:
- Ієрархія exceptions: RetryableError → RateLimitError, ServerError
- APIClientError → AuthenticationError, ForbiddenError, NotFoundError
- APIError з контекстом (provider, operation, original_error)
- @with_retry decorator з tenacity
- _log_retry_attempt() callback для логування
- raise_for_status(), is_retryable_status() helpers
- Новий синтаксис Python 3.12+ type parameters [**P, R]

Оновлено API clients:
- github.py: _convert_github_exception(), @with_retry на методах
- gitlab.py: _convert_gitlab_exception() з mapping dict, @with_retry
- gemini.py: _convert_google_exception(), @with_retry на generate_review()

Тести:
- tests/unit/test_retry.py: 33 нових тести
- tests/integration/test_github.py: оновлено для exceptions
- tests/integration/test_gitlab.py: оновлено для exceptions
- tests/integration/test_gemini.py: додано error handling тести

Виправлення ruff/mypy:
- Додано `-> None` до всіх __init__ методів
- Винесено f-string в змінні для exceptions
- Рефакторинг _convert_gitlab_exception з mapping dict
- Додано google.api_core.* до mypy overrides

343 тести, 92% coverage
```

---

### 📚 Завдання 7: Багатомовна документація
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-27)
**Призначено:** Claude Code (AI) + Human (review)
**Оцінка часу:** 6 годин

---

**Фаза 0: Узгодження структури** (Claude + Human) ✅
- [x] Обговорити фінальну структуру docs/
- [x] Визначити список файлів для MVP (10 файлів UK + README)
- [x] Узгодити i18n підхід (uk → en → інші)
- [x] Затвердити структуру (2026-01-25)

**Фаза 1: Створення** (Claude) ✅ **ЗАВЕРШЕНО** (2026-01-26)
- [x] Налаштувати MkDocs + mkdocs-material
- [x] Налаштувати i18n плагін (mkdocs-static-i18n)
- [x] Створити структуру директорій
- [x] Написати документацію **українською** (uk/):
  - [x] index.md (landing)
  - [x] installation.md (Docker / PyPI / Source)
  - [x] quick-start.md (GitHub + GitLab)
  - [x] configuration.md (всі опції)
  - [x] github.md (platform-specific)
  - [x] gitlab.md (platform-specific)
  - [x] api.md (CLI reference)
  - [x] troubleshooting.md (FAQ + errors)
  - [x] examples/*.md (5 файлів)
- [ ] Створити README.md (останній, після Фази 2)

**Фаза 2: Вичитка** (Human) ✅ **ЗАВЕРШЕНО** (2026-01-27)
- [x] index.md — відревʼювовано, правки внесені (2026-01-26)
- [x] installation.md — відревʼювовано, переписано за новою структурою (2026-01-27)
- [x] quick-start.md — відревʼювовано (2026-01-27)
- [x] configuration.md — відревʼювовано (2026-01-27)
- [x] github.md — відревʼювовано (2026-01-27)
- [x] gitlab.md — відревʼювовано (2026-01-27)
- [x] api.md — відревʼювовано (2026-01-27)
- [x] troubleshooting.md — відревʼювовано (2026-01-27)
- [x] examples/*.md (5 файлів) — відревʼювовано (2026-01-27)
- [x] Затвердити фінальний текст — ✅ Фаза 2 завершена (2026-01-27)

**Фаза 3: Переклад** (Claude) ✅ **ЗАВЕРШЕНО** (2026-01-27)
- [x] Перекласти на English (en/) — primary
- [x] Перекласти на Deutsch (de/)
- [x] Перекласти на Español (es/)
- [x] Перекласти на Crnogorski (sr/) — *примітка: locale sr через обмеження Material theme*
- [x] Перекласти на Italiano (it/)

**Фаза 4: Деплой** (Claude)
- [x] Перемикач мов працює (налаштовано в mkdocs.yml)
- [ ] GitHub Pages / GitLab Pages налаштовано
- [ ] Автодеплой працює

---

**Статус мов:**
| Мова | Код | Фаза 1 | Фаза 2 | Фаза 3 |
|------|-----|--------|--------|--------|
| 🇺🇦 Українська | uk | ✅ | ✅ | — (source) |
| 🇬🇧 English | en | ✅ | — | ✅ |
| 🇩🇪 Deutsch | de | — | — | ✅ |
| 🇪🇸 Español | es | — | — | ✅ |
| 🇲🇪 Crnogorski | sr | — | — | ✅ |
| 🇮🇹 Italiano | it | — | — | ✅ |

**Затверджена структура docs/ (MVP):**
```
docs/
├── uk/                          # Source of truth
│   ├── index.md                 # Landing (що це, features, how it works)
│   ├── installation.md          # Docker / PyPI / Source install
│   ├── quick-start.md           # Copy-paste GitHub + GitLab
│   ├── configuration.md         # Всі env vars, опції, defaults
│   ├── github.md                # GitHub-specific
│   ├── gitlab.md                # GitLab-specific
│   ├── api.md                   # CLI commands reference
│   ├── troubleshooting.md       # FAQ + errors
│   └── examples/                # Приклади workflows
│       ├── index.md             # Огляд прикладів
│       ├── github-minimal.md
│       ├── github-advanced.md
│       ├── gitlab-minimal.md
│       └── gitlab-advanced.md
├── en/                          # Primary for international
├── de/
├── es/
├── me/
└── it/
mkdocs.yml
README.md                        # Короткий landing → посилання на docs
                                 # Створюється ОСТАННІМ
```

**Порядок створення файлів:**
| # | Файл | Опис |
|---|------|------|
| 1 | `index.md` | Landing page |
| 2 | `installation.md` | Docker / PyPI / Source |
| 3 | `quick-start.md` | Copy-paste workflows |
| 4 | `configuration.md` | Env vars, опції |
| 5 | `github.md` | GitHub-specific |
| 6 | `gitlab.md` | GitLab-specific |
| 7 | `api.md` | CLI reference |
| 8 | `troubleshooting.md` | FAQ + errors |
| 9 | `examples/*.md` | Приклади workflows |
| 10 | **README.md** | Останній (всі посилання готові) |

**Навігація (mkdocs.yml):**
```yaml
nav:
  - Головна: index.md
  - Встановлення: installation.md
  - Швидкий старт: quick-start.md
  - Конфігурація: configuration.md
  - GitHub: github.md
  - GitLab: gitlab.md
  - CLI Reference: api.md
  - Приклади:
    - examples/index.md
    - examples/github-minimal.md
    - examples/github-advanced.md
    - examples/gitlab-minimal.md
    - examples/gitlab-advanced.md
  - Troubleshooting: troubleshooting.md
```

**Нотатки:**
```
Workflow:
1. UK пишеться першою — Human вичитує рідною мовою
2. Після затвердження — переклад на всі мови
3. EN стає "primary" для міжнародної аудиторії
4. Виправлення робляться один раз до перекладу
5. README.md створюється останнім з робочими посиланнями

Фаза 0 затверджена: 2026-01-25
Ref: CURRENT_TASK/ai_reviewer_documentation_structure.md

Фаза 1 завершена: 2026-01-26
- mkdocs.yml оновлено з i18n плагіном
- 13 файлів uk/ створено (8 основних + 5 examples)
- en/ = копія uk/ (тимчасово, для fallback)
- Зміна: me → sr (MkDocs Material не підтримує Montenegrin)
- navigation.instant вимкнено (конфлікт з i18n switcher)
- `uv run mkdocs build` успішно збирає site/ (7.1MB)
- `uv run mkdocs serve` для локального перегляду

Фаза 2 розпочата: 2026-01-26
- index.md — Human внів значні правки (розширено опис, уточнено вартість)
- При sync en/index.md = uk/index.md (fallback до перекладу)

Фаза 3 завершена: 2026-01-27
- 52 файли перекладено (13 × 4 мови: en, de, es, sr, it)
- Переклад виконано паралельно 4 агентами
- UI покращення:
  - Прапорці країн перед назвами мов
  - Іконка 🌐 для перемикача мов (CSS override)
  - docs/stylesheets/extra.css створено
- Виправлено 404 при зміні мови:
  - Видалено extra.alternate (конфліктувало з i18n плагіном)
  - site_url: !ENV [SITE_URL, ""] для локальної розробки
- `uv run mkdocs build` успішно збирає всі 6 мов (~2 сек)

=== ІНФО ДЛЯ ВІДНОВЛЕННЯ СЕСІЇ ===
Поточний стан:
- Завдання 7 ЗАВЕРШЕНО ✅
- Всі 6 мов документації готові
- Перемикач мов працює

Команди для роботи:
- Перегляд: `uv run mkdocs serve` → http://127.0.0.1:8000/
- Build: `uv run mkdocs build`

Далі:
- Завдання 8: CI/CD Pipeline та публікація
- Фаза 4: GitHub Pages deploy
- README.md створюється останнім
```

---

### 🔄 Завдання 8: CI/CD Pipeline та публікація
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-28)
**Призначено:** Claude Code (AI) + Human (secrets)
**Оцінка часу:** 4 години
**Версія релізу:** `1.0.0a1`

---

**Фаза 1: Підготовка файлів (Claude)** ✅

| # | Файл | Дія | Статус |
|---|------|-----|--------|
| 1.1 | `pyproject.toml` | Версія `0.1.0` → `1.0.0a1` | ✅ |
| 1.2 | `release.yml` | Видалити `deploy-docs`, додати виклик docker-publish | ✅ |
| 1.3 | `docker-publish.yml` | Створити (GHCR + DockerHub, multi-arch) | ✅ |
| 1.4 | `action.yml` | Pre-built image замість Dockerfile | ✅ |
| 1.5 | `DOCKERHUB_README.md` | Створити | ✅ |
| 1.6 | `README.md` | Створити (фінальний крок документації) | ✅ |

**Фаза 2: Налаштування (Human)** ✅

| # | Платформа | Дія | Статус |
|---|-----------|-----|--------|
| 2.1 | PyPI | Trusted Publisher (ai-reviewbot) | ✅ |
| 2.2 | GitHub | Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | ✅ |
| 2.3 | GitHub | Settings → Pages → gh-pages branch | ✅ |

**Фаза 3: Реліз (Human)** ✅

| # | Дія | Статус |
|---|-----|--------|
| 3.1 | Merge dev to main | ✅ |
| 3.2 | GitHub Release v1.0.0a1 + "Publish to Marketplace" | ✅ |
| 3.3 | Верифікація всіх артефактів | ✅ |

---

**Опубліковані артефакти:**

| Артефакт | Платформа | URL | Статус |
|----------|-----------|-----|--------|
| README.md | GitHub | repo root | ✅ |
| PyPI package | pypi.org | https://pypi.org/project/ai-reviewbot/1.0.0a1/ | ✅ |
| Docker image | DockerHub | https://hub.docker.com/r/konstziv/ai-reviewbot | ✅ |
| Docker image | GHCR | https://github.com/KonstZiv/ai-code-reviewer/pkgs/container/ai-code-reviewer | ✅ |
| GitHub Action | Marketplace | https://github.com/marketplace/actions/ai-reviewbot | ✅ |
| Documentation | GitHub Pages | https://konstziv.github.io/ai-code-reviewer/ | ✅ |

---

**Workflows (фінальна конфігурація):**

| Workflow | Файл | Тригер | Статус |
|----------|------|--------|--------|
| Tests | `tests.yml` | PR to main, push to main | ✅ |
| Docs | `docs.yml` | push to main | ✅ |
| AI Review | `ai-review.yml` | PR | ✅ |
| Release | `release.yml` | tag v*.*.* | ✅ |
| Docker | `docker-publish.yml` | workflow_call від release | ✅ |

**Послідовність при релізі:**
```
tag v1.0.0a1 → release.yml (test → build → PyPI → GitHub Release)
                    ↓ on success
              docker-publish.yml (GHCR + DockerHub)
```

---

**Виправлення під час релізу:**
- `tests.yml`: видалено dev з push triggers (уникнення дублювання тестів)
- `docs.yml`: `--group docs` замість `--group dev` (i18n plugin)
- `release.yml`: explicit secrets замість `secrets: inherit`
- DockerHub token: оновлено з Read/Write/Delete правами

**Нотатки:**
```
2026-01-28: План узгоджено, починаємо виконання Фази 1
2026-01-28: Фаза 1 ЗАВЕРШЕНА ✅
2026-01-28: Фаза 2 ЗАВЕРШЕНА ✅
2026-01-28: Фаза 3 ЗАВЕРШЕНА ✅
  - Реліз v1.0.0a1 опубліковано
  - Всі артефакти доступні (PyPI, DockerHub, GHCR, Marketplace, Pages)
  - DockerHub description workflow виправлено (token permissions)

Далі: Завдання 9 — Ручне тестування та QA
```

---

### 🔍 Завдання 9: Ручне тестування та QA
**Статус:** 🚧 В роботі
**Призначено:** Human (5 студентів) + AI (підготовка плану)
**Оцінка часу:** 8 годин (паралельно 5 груп)

---

**Концепція тестування:**
Кожна група тестує конкретний сценарій використання + паралельно верифікує відповідну українську документацію.

**5 груп тестування:**

| # | Група | Сценарій | Документація |
|---|-------|----------|--------------|
| 1 | **GitHub: Швидкий старт** | Новий користувач додає AI ReviewBot через Marketplace Action | docs/uk/github.md, quick-start.md |
| 2 | **GitLab: Швидкий старт** | Новий користувач налаштовує в GitLab CI через Docker | docs/uk/gitlab.md, quick-start.md |
| 3 | **Конфігурація** | Налаштування мови, language_mode, вибір моделі | docs/uk/configuration.md |
| 4 | **Docker: Локальний запуск** | Pull образу, запуск з env vars напряму | docs/uk/installation.md (Docker) |
| 5 | **PyPI: Python пакет** | pip install, використання як бібліотеки | docs/uk/installation.md (PyPI) |

---

**Формат звіту тестувальника (для кожного кроку):**
```
Крок #: [назва]
✅/❌ Функціональність: [працює / не працює / частково]
✅/❌ Документація: [точна / неточна / відсутня]
📝 Коментар: [що не так, що покращити]
🔗 Скріншот: [якщо потрібно]
```

---

**Детальний план Групи 1: GitHub — Швидкий старт**

| # | Крок | Що перевіряємо | Документація |
|---|------|----------------|--------------|
| 1 | Передумови | GitHub repo, Google API key. Як отримати Gemini API key? | docs/uk — "Вимоги" |
| 2 | Знайти Action | GitHub Marketplace → "AI ReviewBot". Посилання актуальне? | docs/uk — посилання |
| 3 | Створити workflow | `.github/workflows/ai-review.yml` за прикладом. Copy-paste працює? | docs/uk — YAML приклад |
| 4 | Додати секрети | Settings → Secrets → `GOOGLE_API_KEY`. Процес описано? | docs/uk — секрети |
| 5 | Створити PR | PR з кодом (Python/JS). Рекомендації є? | docs/uk — тестування |
| 6 | Перевірити результат | Workflow завершився, коментарі з'явились. Що очікувати? | docs/uk — результат |
| 7 | Оцінити якість | Коментарі релевантні? Мова правильна? | Загальна оцінка |

**Очікуваний результат:**
- PR з AI-коментарями
- Звіт з 7 пунктів

---

**Статус груп:**
| Група | План | Виконання | Звіт |
|-------|------|-----------|------|
| 1. GitHub Quick Start | ✅ | ⏳ | ⏳ |
| 2. GitLab Quick Start | ⏳ | ⏳ | ⏳ |
| 3. Configuration | ⏳ | ⏳ | ⏳ |
| 4. Docker | ⏳ | ⏳ | ⏳ |
| 5. PyPI | ⏳ | ⏳ | ⏳ |

**Нотатки:**
```
2026-01-30: QA виявило критичну помилку — виправлено ✅
- Проблема: Action показував --help замість виконання
- Причина: github_token не передавався явно в прикладах
- Виправлено: оновлено всі приклади (6 мов) + troubleshooting
- Реліз v1.0.0a2 опубліковано

2026-01-28: План тестування розпочато
- Визначено 5 груп з різними сценаріями
- Концепція: функціональність + документація паралельно
- Детальний план Групи 1 готовий
- Плани груп 2-5 потрібно деталізувати

Далі: Продовжити QA, деталізувати плани груп 2-5
```

---

### 🚀 Завдання 10: Стабільний реліз v1.0.0
**Статус:** ⏳ Очікує Завдання 9 (QA)
**Призначено:** Human
**Оцінка часу:** 1 година

> **Примітка:** Alpha реліз v1.0.0a2 вже опубліковано (виправлено помилку з --help).
> Це завдання — фінальний стабільний реліз після QA.

**Чеклист:**
- [ ] Всі баги з ручного тестування виправлено
- [ ] Документація оновлена за результатами тестування
- [ ] Версія оновлена в `pyproject.toml` (1.0.0a2 → 1.0.0)
- [ ] CHANGELOG.md написано
- [ ] Тег `v1.0.0` створено
- [ ] GitHub Release (стабільний, не pre-release)
- [ ] Анонс опубліковано

**Нотатки:**
```
2026-01-28: Alpha реліз v1.0.0a1 опубліковано в Task 8
- Всі артефакти доступні
- Потрібно пройти QA перед стабільним релізом
```

---

## 🧪 Прогрес тестування

### Покриття тестами по модулях

| Модуль | Ціль | Поточне | Статус |
|--------|------|---------|--------|
| core/models.py | ≥90% | 100% | ✅ |
| core/config.py | ≥90% | 100% | ✅ |
| core/formatter.py | ≥80% | 96% | ✅ |
| integrations/base.py | ≥80% | 100% | ✅ |
| integrations/github.py | ≥80% | 88% | ✅ |
| integrations/gitlab.py | ≥80% | 88% | ✅ |
| integrations/gemini.py | ≥80% | 100% | ✅ |
| integrations/prompts.py | ≥80% | 100% | ✅ |
| utils/time.py | ≥80% | 91% | ✅ |
| utils/language.py | ≥80% | 100% | ✅ |
| utils/retry.py | ≥90% | 87% | ✅ |
| cli.py | ≥80% | 88% | ✅ |
| reviewer.py | ≥80% | 94% | ✅ |
| **Загалом** | **≥80%** | **92%** | ✅ |

---

## 📅 Графік виконання

```
Завдання 1 (Foundation)     ██████████  ✅ Завершено
    ↓
Завдання 2 (Adapter)        ██████████  ✅ Завершено
    ↓
Завдання 3 (GitLab)         ██████████  ✅ Завершено
    ↓
Завдання 4a (Language)      ██████████  ✅ Завершено
    ↓
Завдання 4b (WOW)           ██████████  ✅ Завершено
    ↓
Завдання 4c (Metrics)       ██████████  ✅ Завершено
    ↓
Завдання 5 (Docker)         ██████████  ✅ Завершено
    ↓
Завдання 6 (Testing)        ██████████  ✅ Завершено
    ↓
Завдання 7 (Docs)           ██████████  ✅ Завершено
    ↓
Завдання 8 (CI/CD)          ██████████  ✅ Завершено
    ↓
Завдання 9 (QA)             ██░░░░░░░░  🚧 Ручне тестування
    ↓
Завдання 10 (Release)       ░░░░░░░░░░
```

---

## 🎯 Щоденний стендап

### Фокус на сьогодні
```
Завдання 9: Ручне тестування та QA
- [x] План тестування створено (5 груп)
- [x] Детальний план Групи 1 готовий
- [ ] Деталізувати плани груп 2-5
- [ ] Роздати завдання студентам
- [ ] Зібрати звіти та виправити баги
```

### Прогрес з останнього оновлення
```
2026-01-30: Критичне виправлення — Action показував --help ✅
  🐛 Issue від студентів: "В логах CI видно --help замість ревʼю"

  Причина:
    - github_token / GITLAB_TOKEN не передавались явно в прикладах
    - CLI виводить help коли не може визначити контекст (PR/MR)

  ✅ Виправлено (коміти be35c67, 8ed614e):
    - Додано github_token до всіх прикладів quick-start (6 мов)
    - Додано GITLAB_TOKEN до прикладів GitLab CI
    - Нова секція в troubleshooting
    - Реліз v1.0.0a2 опубліковано

2026-01-29: Критичні виправлення GitHub Action та Docker ✅
  🐛 Issue від студентів: "Unable to resolve action @v1"

  Виявлені проблеми:
    1. Git тег v1 не існував (тільки v1.0.0a1)
    2. Docker images не мали тегів :1, :1.0, :1.0.0a1 (тільки :latest)
    3. docker-publish.yml: workflow_dispatch не передавав версію
    4. docker-publish.yml: github.repository uppercase → Docker fail
    5. examples/*.yml: застарілі посилання @v0.1.0

  ✅ Виправлено:
    - Створено тег v1 → d2918a9
    - Оновлено docker-publish.yml з input для версії
    - Додано lowercase конвертацію для Docker tags
    - Перезапущено docker-publish з версією 1.0.0a1
    - Оновлено examples/ на @v1
    - Вся документація консистентна

  📦 Docker images тепер доступні:
    - ghcr.io/konstziv/ai-code-reviewer:1 ✅
    - ghcr.io/konstziv/ai-code-reviewer:1.0 ✅
    - ghcr.io/konstziv/ai-code-reviewer:1.0.0a1 ✅
    - koszivdocker/ai-reviewbot:1 ✅

2026-01-28: Завдання 8 ЗАВЕРШЕНО ✅
  ✅ Реліз v1.0.0a1 опубліковано

2026-01-28: Завдання 9 розпочато
  📋 План ручного тестування: 5 груп студентів
```

### Блокери
```
Немає
```

### Питання
```
Немає — готові до ручного тестування
```

---

## 📝 Журнал рішень

### Рішення 1: 2026-01-23 — Inline Comments як пріоритет
**Питання:** Чи є inline comments критичними для MVP?
**Рішення:** Так, це пріоритет для WOW-ефекту
**Обґрунтування:** Apply Suggestion кнопка — killer feature для UX
**Вплив:** Потребує GitHub Review API замість Issue Comments

### Рішення 2: 2026-01-23 — Без накопичувальної статистики
**Питання:** Чи потрібна stats persistence в MVP?
**Рішення:** Ні, тільки поточні метрики
**Обґрунтування:** CI не має persistence, реалізуємо в Спрінті 2
**Вплив:** Спрощує MVP, фокус на core functionality

### Рішення 3: 2026-01-23 — Без Rating системи
**Питання:** Чи потрібен Rating (A-F) в MVP?
**Рішення:** Ні, додамо пізніше
**Обґрунтування:** Потребує визначення критеріїв, не блокує цінність
**Вплив:** Спрощує ReviewResult модель

### Рішення 4: 2026-01-23 — LanguageMode.FIXED замість STRICT
**Питання:** Як назвати режим фіксованої мови?
**Рішення:** `FIXED` замість `STRICT`
**Обґрунтування:** Семантично точніше, "strict" може сприйматися як суворий режим
**Вплив:** Зміна в config.py

### Рішення 5: 2026-01-23 — Два методи для коментарів
**Питання:** Чи замінити Issue Comments на PR Review API?
**Рішення:** Зберегти обидва як окремі інструменти
**Обґрунтування:** Різні use cases — post_comment() для summary/errors, submit_review() для inline з suggestions
**Вплив:** GitProvider має два методи: post_comment() і submit_review()

### Рішення 6: 2026-01-23 — Dependency Injection в reviewer.py
**Питання:** Як абстрагувати reviewer від конкретного провайдера?
**Рішення:** Provider передається як параметр (DI), CLI створює конкретний client
**Обґрунтування:** Чиста архітектура, легко тестувати, легко додати GitLab
**Вплив:** review_pull_request(provider, repo_name, mr_id, settings)

### Рішення 7: 2026-01-24 — Міграція з Vulnerability на CodeIssue
**Питання:** Чи залишати старий Vulnerability model для backward compatibility?
**Рішення:** Повна міграція на CodeIssue, видалення Vulnerability
**Обґрунтування:** Internal API, немає зовнішніх споживачів, спрощує код
**Вплив:** ReviewResult.vulnerabilities → ReviewResult.issues

### Рішення 8: 2026-01-24 — Compact формат для inline comments
**Питання:** Чи потрібен окремий формат для inline comments?
**Рішення:** Так, format_inline_comment() — максимально стиснутий формат
**Обґрунтування:** Inline comments мають обмежений простір, не потрібен Before/After та collapsible
**Вплив:** Додано окрему функцію format_inline_comment()

### Рішення 9: 2026-01-24 — DEFAULT_MODEL константа
**Питання:** Як уникнути hardcoded model name в GeminiClient?
**Рішення:** Винести default model name в константу DEFAULT_MODEL
**Обґрунтування:** Краща читабельність, легше змінювати, тести використовують константу
**Вплив:** GeminiClient.__init__(model_name=DEFAULT_MODEL), тести оновлено

### Рішення 10: 2026-01-24 — Base image для Docker
**Питання:** Який базовий образ використовувати для Docker?
**Рішення:** ghcr.io/astral-sh/uv:python3.13-bookworm-slim (builder) + python:3.13-slim-bookworm (runtime)
**Обґрунтування:**
- Alpine не підходить (pydantic-core має Rust extension, потрібен manylinux)
- uv образ = швидке встановлення залежностей
- Slim bookworm = мінімальний розмір + glibc для wheels
**Вплив:** Образ 325MB, multi-stage build

### Рішення 11: 2026-01-25 — Перенесення публікації з Завдання 5 в Завдання 8
**Питання:** Чи має Завдання 5 включати публікацію на GHCR/DockerHub/Marketplace?
**Рішення:** Ні, публікацію перенесено в Завдання 8 (CI/CD Pipeline)
**Обґрунтування:**
- Завдання 5 фокусується на локальній підготовці (Dockerfile, action.yml, examples)
- Публікація логічно належить до CI/CD pipeline
- Потребує налаштування secrets (Human task)
- Завдання 8 вже включало docker-publish.yml
**Вплив:**
- Завдання 5: тільки локальна збірка та підготовка файлів
- Завдання 8: розширено з публікацією на GHCR, DockerHub, GitHub Marketplace, PyPI
- Оцінка часу Завдання 8: 2→4 години

### Рішення 12: 2026-01-25 — Ієрархія exceptions для retry
**Питання:** Яку структуру exceptions використовувати для retry logic?
**Рішення:** Дві гілки: RetryableError (retry) та APIClientError (fail fast)
**Обґрунтування:**
- RetryableError → RateLimitError (429), ServerError (5xx) — тимчасові помилки
- APIClientError → AuthenticationError (401), ForbiddenError (403), NotFoundError (404) — fail fast
- Чітке розділення: retry vs immediate failure
- tenacity retry_if_exception_type(RetryableError) для автоматичного retry
**Вплив:**
- Уніфікована обробка помилок у всіх API clients
- Максимум 5 спроб з exponential backoff (2s → 30s)
- Структуроване логування: attempt, error_type, retry_in_ms

### Рішення 13: 2026-01-26 — Locale для Crnogorski
**Питання:** MkDocs Material не підтримує locale `me` (Montenegrin)
**Рішення:** Використовувати `sr` (Serbian) як locale для чорногорської мови
**Обґрунтування:**
- MkDocs Material має обмежений набір мовних шаблонів
- Сербська і чорногорська дуже близькі (латиниця)
- Альтернативи: `hr` (Croatian) або custom template
- `sr` найближчий з доступних
**Вплив:**
- mkdocs.yml: locale `sr` з name `Crnogorski`
- URL буде /sr/ замість /me/
- Функціональність повністю збережена

### Рішення 14: 2026-01-27 — Видалення extra.alternate
**Питання:** Перемикач мов дає 404 при переході на /uk/
**Рішення:** Видалити manual `extra.alternate` секцію з mkdocs.yml
**Обґрунтування:**
- mkdocs-static-i18n з `reconfigure_material: true` автоматично налаштовує switcher
- Manual alternate конфліктував з автоматичним налаштуванням
- Default language (en) знаходився в корені (/), а не в /en/
**Вплив:**
- mkdocs.yml: видалено extra.alternate секцію
- site_url: !ENV [SITE_URL, ""] для гнучкості локальної розробки
- Перемикач мов працює коректно

### Рішення 15: 2026-01-28 — CI/CD архітектура
**Питання:** Як організувати workflows для релізу?
**Рішення:**
- Docs deploy: тільки на push to main (`docs.yml`)
- Docker publish: послідовно після PyPI (`workflow_call`)
- action.yml: pre-built image замість Dockerfile
**Обґрунтування:**
- Docs на main: документація завжди актуальна, не залежить від релізу
- Послідовний Docker: консистентність артефактів (якщо PyPI fail — Docker не публікується)
- Pre-built image: швидший запуск для користувачів Action
**Вплив:**
- release.yml: видалено deploy-docs, додано виклик docker-publish
- docker-publish.yml: новий workflow з workflow_call trigger
- action.yml: image змінено на `docker://ghcr.io/konstziv/ai-reviewbot:1`

### Рішення 16: 2026-01-28 — Версія релізу
**Питання:** Яку версію використовувати для першого релізу?
**Рішення:** `1.0.0a1` замість `0.1.0`
**Обґрунтування:**
- Alpha версія чітко показує стадію розробки
- Семантична версія 1.x готує до production release
- Дозволяє ітерації (a2, a3, beta, rc) перед стабільним релізом
**Вплив:**
- pyproject.toml: version = "1.0.0a1"
- Docker tags: 1.0.0a1, 1.0, 1 (без latest для alpha)

---

## 🐛 Проблеми та рішення

### Проблема 1: Entry Point — 2026-01-23
**Проблема:** `ai-review = "ai_reviewer.cli:main"` не працює з Typer
**Рішення:** Змінено на `ai-review = "ai_reviewer.cli:app"`
**Статус:** ✅ Виправлено в Завданні 1

### Проблема 2: CLI тести — 0% coverage
**Проблема:** CLI модуль не має тестів
**Рішення:** Додано unit tests для CLI
**Статус:** ✅ Виправлено (88% coverage)

### Проблема 3: Docker editable install — 2026-01-24
**Проблема:** `ModuleNotFoundError: No module named 'ai_reviewer'` при запуску контейнера
**Причина:** uv sync створює editable install (.pth файл вказує на /app/src), але src не копіюється в runtime stage
**Рішення:** Додано `COPY --from=builder /app/src /app/src` в runtime stage
**Статус:** ✅ Виправлено

### Проблема 4: GitHub Action v1 not found — 2026-01-29
**Проблема:** `Unable to resolve action konstziv/ai-code-reviewer@v1, unable to find version v1`
**Причина:** Тег `v1` не був створений (тільки `v1.0.0a1`)
**Рішення:** Створено тег `v1` що вказує на HEAD main
**Статус:** ✅ Виправлено

### Проблема 5: Docker images без semver тегів — 2026-01-29
**Проблема:** Docker images мали тільки `:latest`, не було `:1`, `:1.0`, `:1.0.0a1`
**Причина:** `workflow_dispatch` запускався без git tag ref, тому `docker/metadata-action` semver patterns не працювали
**Рішення:** Додано `version` input в docker-publish.yml для ручних запусків
**Статус:** ✅ Виправлено

### Проблема 6: Docker tag uppercase error — 2026-01-29
**Проблема:** `invalid tag: repository name must be lowercase`
**Причина:** `github.repository` повертає `KonstZiv/ai-code-reviewer` з uppercase
**Рішення:** Додано `${GITHUB_REPOSITORY,,}` bash lowercase конвертацію
**Статус:** ✅ Виправлено

### Проблема 7: Action показує --help замість виконання — 2026-01-30
**Проблема:** В логах CI job видно `--help` output замість виконання ревʼю
**Причина:** `github_token` / `GITLAB_TOKEN` не передавались явно в прикладах workflow. CLI виводить help коли не може визначити контекст (PR/MR).
**Рішення:**
1. Додано `github_token: ${{ secrets.GITHUB_TOKEN }}` до всіх прикладів quick-start (6 мов)
2. Додано `GITLAB_TOKEN: $CI_JOB_TOKEN` до прикладів GitLab CI
3. Нова секція в troubleshooting — "Action показує --help замість виконання"
4. Оновлено чеклист діагностики — "чи передано github_token явно?"
**Статус:** ✅ Виправлено, реліз v1.0.0a2

---

## 💡 Висновки та інсайти

### Технічні висновки
```
- GitHub Review API потрібен для Apply Suggestion (не Issue Comments)
- GitLab використовує Discussions API для inline comments
- Мовна адаптивність краще через LLM prompt, ніж бібліотеку
```

### Процесні висновки
```
- WOW-ефект важливіший за кількість фіч
- Inline comments = головний диференціатор від конкурентів
```

### Інсайти про інструменти
```
- tenacity — стандарт для retry logic в Python
- GitHub suggestion syntax автоматично рендерить Apply кнопку
- Pydantic model_copy(update=...) ефективніший за model_dump() + model_validate()
- Google GenAI SDK повертає usage_metadata з token counts
- uv sync створює editable install — потрібно копіювати src в runtime
- Multi-stage Docker: uv image для build, slim python для runtime
- GitPython потребує git CLI в контейнері
- mkdocs-static-i18n: reconfigure_material=true автоматично налаштовує switcher
- MkDocs: site_url через ENV змінну (!ENV [VAR, "default"]) для локальної розробки
- Emoji в YAML: безпечно використовувати у name полях без лапок
```

---

## ✅ Чеклист завершення спрінту

### Функціональність
- [x] GitHub інтеграція з Inline Comments
- [x] GitLab інтеграція з Discussions
- [x] Мовна адаптивність працює
- [x] WOW-форматування виглядає добре
- [x] Метрики відображаються
- [x] Retry logic працює
- [x] Error messages зрозумілі

### Якість коду
- [x] Всі тести проходять
- [x] Покриття ≥80% (92%)
- [x] Ruff check проходить
- [x] Mypy проходить
- [x] Pre-commit хуки працюють

### Дистрибуція
- [x] Docker image опубліковано (DockerHub + GHCR)
- [x] GitHub Action опубліковано (Marketplace)
- [x] GitLab template працює
- [x] PyPI package опубліковано (ai-reviewbot 1.0.0a2)

### Документація
- [x] 6 мов документації
- [x] Перемикач мов працює
- [x] Автодеплой працює (GitHub Pages)

### Реліз (Alpha)
- [x] Тег v1.0.0a1 створено
- [x] Тег v1.0.0a2 створено (виправлення --help)
- [x] GitHub Release опубліковано (pre-release)
- [ ] CHANGELOG.md написано

### Ручне тестування (QA)
- [ ] GitHub Quick Start протестовано
- [ ] GitLab Quick Start протестовано
- [ ] Configuration протестовано
- [ ] Docker протестовано
- [ ] PyPI протестовано
- [ ] Документація верифікована

---

## 🎊 Ретроспектива спрінту

**Що пішло добре:**
```
[Заповнити в кінці спрінту]
```

**Що можна покращити:**
```
[Заповнити в кінці спрінту]
```

**Дії для наступного спрінту:**
```
[Заповнити в кінці спрінту]
```

---

## 📊 Фінальні метрики спрінту

**Заповнити при завершенні:**

- Дата початку: 2026-01-20
- Дата завершення: [Дата]
- Тривалість: [Днів]
- Завдань виконано: 9/10
- Покриття тестами: 92%
- Рядків коду: ~1200
- Нових файлів: 11+ (base.py, time.py, gitlab.py, language.py, retry.py, Dockerfile, action.yml, .dockerignore, examples/*.yml, docs/stylesheets/extra.css, docs/{uk,en,de,es,sr,it}/*.md)
- Тестів: 343
- Коммітів: [X]

---

## 🚀 Попередній перегляд Спрінту 2

**Спрінт 2: Intelligence & Learning**
- Контекст репозиторію (conventions, patterns)
- Multi-LLM router (Claude, GPT, Gemini)
- Кешування результатів
- Накопичувальна статистика
- Auto-fix PR creation
- Rating система (A-F)
- Interactive commands (@ai-reviewer explain)

---

**Памʼятай:** Оновлюй цей документ під час роботи! 📝

**WOW-ефект понад усе! 🎆**

---

## 🔄 Відновлення сесії (Session Recovery)

**Останнє оновлення:** 2026-01-30

### Поточний стан
- **Sprint 1:** майже завершено (9/10 завдань done, QA в роботі)
- **Реліз:** v1.0.0a2 опубліковано (alpha) — виправлено помилку з `--help`
- **Гілка:** main (всі виправлення змержені)
- **Тег v1:** 8ed614e (актуальний, вказує на v1.0.0a2)

### Опубліковані артефакти (всі працюють ✅)
| Артефакт | URL/Image |
|----------|-----------|
| PyPI | https://pypi.org/project/ai-reviewbot/1.0.0a2/ |
| DockerHub | `koszivdocker/ai-reviewbot:1` |
| GHCR | `ghcr.io/konstziv/ai-code-reviewer:1` |
| Marketplace | https://github.com/marketplace/actions/ai-reviewbot |
| Documentation | https://konstziv.github.io/ai-code-reviewer/ |
| Codecov | https://codecov.io/gh/KonstZiv/ai-code-reviewer |

### ⚠️ Важливо: Правильні Docker URL
```bash
# GHCR (по імені репозиторію)
ghcr.io/konstziv/ai-code-reviewer:1

# DockerHub (DOCKERHUB_USERNAME = koszivdocker)
koszivdocker/ai-reviewbot:1

# GitHub Action
uses: KonstZiv/ai-code-reviewer@v1
```

### Консистентність документації ✅
| Елемент | Значення | Кількість посилань |
|---------|----------|-------------------|
| GitHub Action | `@v1` | 58 |
| GHCR Docker | `:1` | 126 |
| DockerHub | `:1` | 8 |

### Наступні кроки
1. **Деталізувати плани груп 2-5** для ручного тестування
2. **Роздати завдання студентам** (5 груп)
3. **Зібрати звіти** та виправити знайдені баги
4. **Завдання 10:** Стабільний реліз v1.0.0 після QA

### План ручного тестування (Завдання 9)
5 груп, кожна тестує сценарій + верифікує документацію:

| # | Група | Сценарій | Статус плану |
|---|-------|----------|--------------|
| 1 | GitHub Quick Start | Marketplace Action → PR → коментарі | ✅ Готовий |
| 2 | GitLab Quick Start | Docker в CI → MR → коментарі | ⏳ Потрібно |
| 3 | Конфігурація | Мова, model, language_mode | ⏳ Потрібно |
| 4 | Docker | Pull + run локально | ⏳ Потрібно |
| 5 | PyPI | pip install + використання | ⏳ Потрібно |

**Детальний план Групи 1** — див. секцію "Завдання 9" вище.

### Команди для початку роботи
```bash
cd /Users/kostyantynzivenko/Desktop/documents/REVIEW-AI/ai-code-reviewer
git status
git log --oneline -5
uv run pytest  # перевірити що тести проходять
uv run mkdocs serve  # локальний перегляд документації
```

### Важливі файли
- `CURRENT_TASK/PROCESS_TASK_UA.md` — цей файл (прогрес спрінту)
- `action.yml` — GitHub Action definition (image: ghcr.io/konstziv/ai-code-reviewer:1)
- `.github/workflows/docker-publish.yml` — публікація Docker images
- `mkdocs.yml` — конфігурація документації
- `docs/uk/` — українська документація (source of truth)
