# GitLab

Guía detallada para integración con GitLab CI.

---

## Tokens {#tokens}

### Personal Access Token (PAT) {#get-token}

**Recomendado para todos los planes de GitLab** (incluido Free).

!!! danger "`CI_JOB_TOKEN` no funciona"
    El `CI_JOB_TOKEN` automático de GitLab **no puede publicar comentarios** en Merge Requests
    (la API de Notes requiere el scope `api`, que `CI_JOB_TOKEN` no tiene).
    **Debes** usar un Personal Access Token o un Project Access Token.

**Cómo crear:**

1. Ve a **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Completa los campos:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** configura según necesidad (ej. 1 año)
    - **Scopes:** marca **`api`**
3. Haz clic en **Create personal access token**
4. **Copia el token inmediatamente** — GitLab lo muestra solo una vez!

**Cómo usar en CI:**

1. Ve a **Settings → CI/CD → Variables → Add variable**
2. Añade la variable:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN`
    - **Value:** pega tu token
    - **Flags:** marca **Masked**, :x: **desmarca** Protected

    La variable estará disponible automáticamente para todos los jobs — no se necesita mapeo YAML `variables:`.

!!! warning "¡Desmarca «Protected»!"
    Por defecto, GitLab marca las nuevas variables como **Protected**. Las variables Protected **solo están disponibles en ramas protegidas** (ej. `main`).

    Los pipelines de MR se ejecutan en ramas de origen **no protegidas** — la variable estará vacía y obtendrás **401 Unauthorized**.

    **Siempre desmarca «Protected»** para `AI_REVIEWER_GITLAB_TOKEN` y `AI_REVIEWER_GOOGLE_API_KEY`.

!!! warning "Guarda el token"
    GitLab muestra el token **solo una vez**. Guárdalo en un lugar seguro inmediatamente.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Disponible solo en planes **GitLab Premium** y **Ultimate**. Una buena opción si prefieres un token con alcance de proyecto en lugar de uno personal.

**Ventajas sobre PAT:**

- Limitado a un solo proyecto (sin acceso a otros proyectos)
- Puede ser revocado por los maintainers del proyecto (sin dependencia de un usuario específico)
- Mejor para equipos — no está vinculado a una cuenta personal

**Cómo crear:**

1. Ve a **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Completa los campos:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (mínimo requerido)
    - **Scopes:** marca **`api`**
3. Haz clic en **Create project access token**
4. **Copia el token inmediatamente**

**Cómo usar en CI:**

Igual que PAT — añade como `AI_REVIEWER_GITLAB_TOKEN` en CI/CD Variables:

1. **Key:** `AI_REVIEWER_GITLAB_TOKEN`
2. **Value:** pega tu Project Access Token

!!! info "¿Qué token elegir?"
    | | Personal Access Token | Project Access Token |
    |---|---|---|
    | **Plan** | Todos (incluido Free) | Solo Premium/Ultimate |
    | **Configuración** | Manual | Manual |
    | **Alcance** | Todos los proyectos del usuario | Un solo proyecto |
    | **Comentarios inline** | :white_check_mark: | :white_check_mark: |
    | **Mejor para** | Plan Free + funciones completas | Equipos en Premium/Ultimate |

---

## Variables CI/CD

### Añadir Variables

`Settings → CI/CD → Variables → Add variable`

| Variable | Valor | Opciones |
|----------|-------|---------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Clave API de Gemini | :white_check_mark: Masked, :x: **Uncheck** Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | PAT (si es necesario) | :white_check_mark: Masked, :x: **Uncheck** Protected |

!!! tip "Masked"
    Siempre activa **Masked** para secretos — no se mostrarán en los logs.

---

## Triggers

### Trigger Recomendado

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Esto ejecuta el job solo para pipelines de Merge Request.

### Trigger Alternativo (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — sintaxis más nueva, recomendada por GitLab.

---

## Ejemplos de Jobs

### Mínimo

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Las variables CI/CD `AI_REVIEWER_GOOGLE_API_KEY` y `AI_REVIEWER_GITLAB_TOKEN` se heredan automáticamente.

### Completo (recomendado)

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

**Qué hace:**

- `allow_failure: true` — el MR no se bloquea si la revisión falla
- `timeout: 10m` — máximo 10 minutos
- `interruptible: true` — puede cancelarse con nuevo commit

### Con Stage Personalizado

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
  needs: []  # No esperar por stages anteriores
```

---

## GitLab Self-hosted

### Configuración

```yaml
variables:
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
```

### Docker Registry

Si tu GitLab no tiene acceso a `ghcr.io`, crea un mirror:

```bash
# En una máquina con acceso
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

## Variables de GitLab CI

AI Code Reviewer usa automáticamente:

| Variable | Descripción |
|----------|-------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | Número del MR |
| `CI_SERVER_URL` | URL de GitLab |

No necesitas pasar `--repo` y `--pr` — se toman del CI automáticamente.

---

## Configuración mediante Variables CI/CD {#variable-driven}

Use **CI/CD Variables** para cambiar entre proveedores LLM y modelos sin modificar `.gitlab-ci.yml`. Esto es útil para comparar la calidad de revisión de diferentes modelos en el mismo MR.

### Configuración

**CI/CD Variables** (`Settings → CI/CD → Variables`):

| Variable | Descripción | Opciones |
|----------|-------------|----------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Clave API de Gemini | :white_check_mark: Masked, :x: Desmarcar Protected |
| `AI_REVIEWER_MISTRAL_API_KEY` | Clave API de Mistral | :white_check_mark: Masked, :x: Desmarcar Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | Token de GitLab | :white_check_mark: Masked, :x: Desmarcar Protected |
| `AI_REVIEWER_LLM_PROVIDER` | Proveedor principal (`google`, `mistral`) | :x: Desmarcar Protected |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Proveedor de respaldo | :x: Desmarcar Protected |
| `AI_REVIEWER_MISTRAL_MODEL` | Modelo Mistral | :x: Desmarcar Protected |
| `AI_REVIEWER_MISTRAL_API_URL` | URL API personalizada (para Codestral free tier) | :x: Desmarcar Protected |

### Configuración del job

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

No se necesita sección `variables:` — todas las variables CI/CD `AI_REVIEWER_*` se heredan automáticamente.

### Cambiar presets

Cambie las CI/CD Variables en la interfaz de GitLab y haga clic en **Retry** en el pipeline del mismo MR:

| Preset | `AI_REVIEWER_LLM_PROVIDER` | `AI_REVIEWER_MISTRAL_MODEL` | `AI_REVIEWER_MISTRAL_API_URL` | `AI_REVIEWER_LLM_FALLBACK_PROVIDER` |
|--------|---------------------------|---------------------------|-------------------------------|-------------------------------------|
| Gemini (predeterminado) | `google` | _(vacío)_ | _(vacío)_ | _(vacío)_ |
| Mistral Large | `mistral` | `mistral-large-latest` | _(vacío)_ | `google` |
| Codestral free | `mistral` | `codestral-latest` | `https://codestral.mistral.ai` | `google` |
| Devstral | `mistral` | `devstral-latest` | _(vacío)_ | `google` |

!!! tip "Clave de Codestral free tier"
    Para el preset "Codestral free", `AI_REVIEWER_MISTRAL_API_KEY` debe contener una clave de [codestral.mistral.ai](https://codestral.mistral.ai/), no de `console.mistral.ai`.

!!! info "No es necesario codificar en YAML"
    A diferencia de GitHub Actions (donde los inputs deben mapearse explícitamente), GitLab CI pasa automáticamente todas las variables CI/CD como variables de entorno. Simplemente configúrelas en la interfaz — la aplicación las detecta mediante el prefijo `AI_REVIEWER_*`.

---

## Resultado de la Revisión

### Notas (comentarios)

AI Review publica comentarios en el MR como notas.

### Discusiones (en línea)

Para comentarios en línea, necesitas un Personal Access Token o Project Access Token con scope `api`.

Los comentarios en línea aparecen directamente junto a las líneas de código en la vista de diff.

### Resumen

Al final de la revisión, se publica una nota de Resumen con:

- Estadísticas generales
- Métricas
- Buenas prácticas

---

## Solución de Problemas

### La Revisión No Publica Comentarios

**Verifica:**

1. La variable `AI_REVIEWER_GOOGLE_API_KEY` está configurada
2. `AI_REVIEWER_GITLAB_TOKEN` tiene permisos suficientes (scope: `api`)
3. El pipeline está ejecutándose para un MR (no para una rama)

### "401 Unauthorized"

**Causa:** Token inválido.

**Solución:**

- Verifica que el token no haya expirado
- Verifica el scope (necesita `api`)

### "403 Forbidden"

**Causa:** Permisos insuficientes.

**Solución:**

- Verifica que estás usando un Personal Access Token (no `CI_JOB_TOKEN`)
- Verifica que el token tenga acceso al proyecto

### "404 Not Found"

**Causa:** MR no encontrado.

**Solución:**

- Verifica que el pipeline esté ejecutándose para un MR
- Verifica `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Causa:** Límite de API excedido.

**Solución:**

- AI Code Reviewer reintenta automáticamente con backoff
- Si persiste — espera o aumenta los límites

---

## Mejores Prácticas

### 1. Usa PAT para funcionalidad completa

### 2. Añade allow_failure

```yaml
allow_failure: true
```

El MR no se bloqueará si la revisión falla.

### 3. Establece timeout

```yaml
timeout: 10m
```

### 4. Haz el job interruptible

```yaml
interruptible: true
```

La revisión anterior se cancelará con un nuevo commit.

### 5. No esperes por otros stages

```yaml
needs: []
```

La revisión comenzará inmediatamente, sin esperar por build/test.

---

## Siguiente Paso

- [Integración con GitHub →](github.md)
- [Referencia CLI →](api.md)
