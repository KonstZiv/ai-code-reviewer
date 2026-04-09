# GitHub

Guía detallada para integración con GitHub Actions.

---

## Permisos

### Permisos Mínimos

```yaml
permissions:
  contents: read        # Leer código
  pull-requests: write  # Publicar comentarios
```

### GITHUB_TOKEN en Actions

En GitHub Actions, `GITHUB_TOKEN` está disponible automáticamente:

```yaml
env:
  GITHUB_TOKEN: ${{ github.token }}
```

**Permisos automáticos del token:**

| Permiso | Estado | Nota |
|------------|--------|------|
| `contents: read` | :white_check_mark: | Por defecto |
| `pull-requests: write` | :white_check_mark: | Debe especificarse en `permissions` |

!!! warning "PRs de Forks"
    Para PRs de repositorios fork, `GITHUB_TOKEN` tiene permisos de **solo lectura**.

    AI Review no puede publicar comentarios para PRs de forks.

### Cómo Obtener un Personal Access Token {#get-token}

Para **ejecuciones locales**, necesitas un Personal Access Token (PAT):

1. Ve a `Settings → Developer settings → Personal access tokens`
2. Elige **Fine-grained tokens** (recomendado) o Classic
3. Haz clic en **Generate new token**

**Fine-grained token (recomendado):**

| Configuración | Valor |
|---------|-------|
| Repository access | Only select repositories → tu repositorio |
| Permissions | `Pull requests: Read and write` |

**Classic token:**

| Scope | Descripción |
|-------|-------------|
| `repo` | Acceso completo al repositorio |

4. Haz clic en **Generate token**
5. Copia el token y guárdalo como `GITHUB_TOKEN`

!!! warning "Guarda el token"
    GitHub muestra el token **solo una vez**. Guárdalo inmediatamente.

---

## Triggers

### Trigger Recomendado

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

| Tipo | Cuándo se dispara |
|------|-----------------|
| `opened` | PR creado |
| `synchronize` | Nuevos commits en el PR |
| `reopened` | PR reabierto |

### Filtrado de Archivos

Ejecutar revisión solo para archivos específicos:

```yaml
on:
  pull_request:
    paths:
      - '**.py'
      - '**.js'
      - '**.ts'
```

### Filtrado de Ramas

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

---

## Secretos

### Añadir Secretos

`Settings → Secrets and variables → Actions → New repository secret`

| Secreto | Requerido | Descripción |
|--------|----------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | :white_check_mark: | Clave API de Gemini |

### Uso

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
```

!!! danger "Nunca hardcodees secretos"
    ```yaml
    # ❌ INCORRECTO
    env:
      AI_REVIEWER_GOOGLE_API_KEY: AIza...

    # ✅ CORRECTO
    env:
      AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    ```

---

## Ejemplos de Workflow

### Mínimo

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

!!! info "Sobre `GITHUB_TOKEN`"
    `secrets.GITHUB_TOKEN` es un **token automático** que GitHub crea para cada ejecución del workflow. **No necesitas** añadirlo manualmente a los secretos — ya está disponible.

    Los permisos del token se definen en la sección `permissions` del archivo workflow.

    :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

### Con Concurrencia (recomendado)

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

**Qué hace la concurrencia:**

- Si se hace push de un nuevo commit mientras la revisión aún está en ejecución — la revisión anterior se cancela
- Ahorra recursos y llamadas a la API

### Con Filtrado de PRs de Forks

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    # No ejecutar para PRs de forks (sin acceso a secretos)
    if: github.event.pull_request.head.repo.full_name == github.repository
```

---

## Inputs de GitHub Action

| Input | Descripción | Por defecto |
|-------|-------------|---------|
| `google_api_key` | Clave API de Gemini | **requerido** |
| `github_token` | Token de GitHub | `${{ github.token }}` |
| `language` | Idioma de respuesta | `en` |
| `language_mode` | Modo de idioma | `adaptive` |
| `gemini_model` | Modelo Gemini | `gemini-2.5-flash` |
| `log_level` | Nivel de log | `INFO` |
| `review_max_comment_chars` | Máx. caracteres de comentario MR en el prompt | `3000` |
| `review_include_bot_comments` | Incluir comentarios de bots en el prompt | `true` |
| `review_post_inline_comments` | Publicar comentarios inline en líneas | `true` |
| `gemini_model_fallback` | Cadena de modelos de respaldo (separados por comas) | `gemini-3.1-flash-preview` |
| `review_enable_dialogue` | Agrupar comentarios en diálogos | `true` |
| `discovery_enabled` | Activar project discovery | `true` |
| `discovery_verbose` | Publicar siempre comentario de discovery | `false` |
| `discovery_timeout` | Tiempo de espera de discovery en segundos | `30` |

!!! tip "Variables de entorno"
    La Action mapea los inputs a variables de entorno `AI_REVIEWER_*` internamente. Al ejecutar fuera de la Action, usa las variables `AI_REVIEWER_*` directamente (los nombres antiguos como `GOOGLE_API_KEY` siguen funcionando como fallback).

---

## Resultado de la Revisión

### Comentarios en Línea

AI Review publica comentarios directamente en las líneas de código:

- :red_circle: **CRITICAL** — problemas críticos (seguridad, bugs)
- :yellow_circle: **WARNING** — recomendaciones
- :blue_circle: **INFO** — notas educativas

### Apply Suggestion

Cada comentario con sugerencia de código tiene un botón **"Apply suggestion"**:

```suggestion
fixed_code_here
```

GitHub renderiza esto automáticamente como un botón interactivo.

### Resumen

Al final de la revisión, se publica un Resumen con:

- Estadísticas generales de problemas
- Métricas (tiempo, tokens, costo)
- Buenas prácticas (feedback positivo)

---

## Solución de Problemas

### La Revisión No Publica Comentarios

**Verifica:**

1. `permissions: pull-requests: write` está en el workflow
2. El secreto `AI_REVIEWER_GOOGLE_API_KEY` está configurado
3. El PR no es de un repositorio fork

### "Resource not accessible by integration"

**Causa:** Permisos insuficientes.

**Solución:** Añade permisos:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### Rate Limit de Gemini

**Causa:** Se excedió el límite del nivel gratuito (15 RPM).

**Solución:**

- Espera un minuto
- Añade `concurrency` para cancelar ejecuciones anteriores
- Considera el nivel de pago

---

## Mejores Prácticas

### 1. Siempre usa concurrencia

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### 2. Filtra PRs de forks

```yaml
if: github.event.pull_request.head.repo.full_name == github.repository
```

### 3. Establece timeout

```yaml
jobs:
  review:
    timeout-minutes: 10
```

### 4. Haz el job no bloqueante

```yaml
jobs:
  review:
    continue-on-error: true
```

---

## Siguiente Paso

- [Integración con GitLab →](gitlab.md)
- [Referencia CLI →](api.md)
