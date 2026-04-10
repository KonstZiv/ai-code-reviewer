# Inicio Rápido

Pon en marcha AI Code Reviewer en 5 minutos en GitHub o GitLab.

---

## Paso 1: Elige tu proveedor LLM y obtén una clave API

AI Reviewer soporta múltiples proveedores LLM. Elige uno (o usa ambos para fallback):

=== "Google Gemini (predeterminado)"

    1. Ve a [Google AI Studio](https://aistudio.google.com/)
    2. Inicia sesión con tu cuenta de Google
    3. Haz clic en **"Get API key"** → **"Create API key"**
    4. Copia la clave (comienza con `AIza...`)

    !!! tip "Nivel gratuito"
        Gemini API tiene un nivel gratuito: 15 solicitudes por minuto, suficiente para la mayoría de los equipos de 4-8 desarrolladores.

=== "Mistral AI"

    1. Ve a [Mistral Console](https://console.mistral.ai/)
    2. Regístrate o inicia sesión
    3. Navega a **API Keys** → **Create new key**
    4. Copia la clave (comienza con `sk-...`)

    !!! tip "Nivel gratuito"
        Mistral ofrece un nivel gratuito para experimentación. Después de registrarte, obtienes créditos API gratuitos para probar todos los modelos. Límites actuales: [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing).

    !!! tip "Codestral gratuito"
        Codestral (un modelo especializado en código) tiene su propio nivel gratuito con **endpoint y clave separados**:

        1. Vaya a [codestral.mistral.ai](https://codestral.mistral.ai/)
        2. Genere una clave API de Codestral
        3. Configure `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai`
        4. Configure `AI_REVIEWER_MISTRAL_MODEL=codestral-latest`

        Esta clave funciona **solo** con `codestral-latest` en el endpoint de Codestral.

=== "Ambos (Mistral primario + Google fallback)"

    Obtén **ambas claves** usando las instrucciones anteriores. Esto te da:

    - Mistral como modelo primario (ej. `mistral-large-latest`)
    - Google Gemini como fallback automático si Mistral no está disponible

    Esta es la configuración más confiable para uso en producción.

!!! warning "Guarda la clave"
    Las claves API solo se muestran una vez. Guárdalas en un lugar seguro.

---

## Paso 2: Añadir secretos al repositorio

=== "GitHub"

    **Ruta:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    === "Google only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Tu clave Gemini (`AIza...`) |

    === "Mistral only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Tu clave Mistral (`sk-...`) |

    === "Ambos proveedores"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Tu clave Mistral (`sk-...`) |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Tu clave Gemini (`AIza...`) |

    Haz clic en **"Add secret"** para cada uno.

    ??? info "Instrucciones detalladas con capturas de pantalla"
        1. Abre tu repositorio en GitHub
        2. Haz clic en **Settings** (engranaje en el menú superior)
        3. En el menú izquierdo, busca **Secrets and variables** → **Actions**
        4. Haz clic en el botón verde **New repository secret**
        5. Ingresa el nombre y pega tu clave
        6. Haz clic en **Add secret**
        7. Repite para cada secreto

    :material-book-open-variant: [Documentación oficial de GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Para GitLab también necesitas un **token de GitLab** para publicar comentarios.

    ### Paso 2a: Crear un token de GitLab

    === "Personal Access Token (Todos los planes, incluido Free)"

        **Ruta:** Avatar de usuario → `Edit profile` → `Access Tokens`

        | Campo | Valor |
        |-------|-------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Elige una fecha (máx. 1 año) |
        | **Scopes** | :white_check_mark: `api` |

        Haz clic en **"Create personal access token"** → **Copia el token** (¡solo se muestra una vez!)

        !!! warning "Los comentarios aparecerán bajo tu nombre de usuario"
            Un Personal Access Token está vinculado a tu cuenta. Todos los comentarios de revisión se publicarán en tu nombre.

        :material-book-open-variant: [GitLab Docs: Personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

    === "Project Access Token (Premium/Ultimate)"

        !!! note "Se requieren permisos de Maintainer"
            Para crear un Project Access Token necesitas el rol **Maintainer** u **Owner** en el proyecto.

            :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

        **Ruta:** Project → `Settings` → `Access Tokens`

        | Campo | Valor |
        |-------|-------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Elige una fecha (máx. 1 año) |
        | **Role** | `Developer` |
        | **Scopes** | :white_check_mark: `api` |

        Haz clic en **"Create project access token"** → **Copia el token** (¡solo se muestra una vez!)

        :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Paso 2b: Añadir variables en CI/CD

    **Ruta:** Project → `Settings` → `CI/CD` → `Variables`

    === "Google only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Tu clave Gemini | :white_check_mark: Mask, :x: Desmarca Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token del paso 2a | :white_check_mark: Mask, :x: Desmarca Protected |

    === "Mistral only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Tu clave Mistral | :white_check_mark: Mask, :x: Desmarca Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token del paso 2a | :white_check_mark: Mask, :x: Desmarca Protected |

    === "Ambos proveedores"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Tu clave Mistral | :white_check_mark: Mask, :x: Desmarca Protected |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Tu clave Gemini | :white_check_mark: Mask, :x: Desmarca Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token del paso 2a | :white_check_mark: Mask, :x: Desmarca Protected |

    !!! warning "¡Desmarca «Protected»!"
        Por defecto, GitLab marca las nuevas variables como **Protected**. Las variables Protected **solo están disponibles en ramas protegidas** (ej. `main`), pero los pipelines de MR se ejecutan en ramas de origen **no protegidas** — la variable estará vacía y obtendrás **401 Unauthorized**.

    !!! danger "`CI_JOB_TOKEN` no funciona"
        El `CI_JOB_TOKEN` automático de GitLab **no puede publicar comentarios** en Merge Requests.
        **Debes** crear un Personal Access Token (o Project Access Token en Premium+).

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Paso 3: Añadir AI Review al CI {#ci-setup}

=== "GitHub"

    Crea el archivo `.github/workflows/ai-review.yml`:

    === "Google only"

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
        ```

    === "Mistral only"

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
                  mistral_api_key: ${{ secrets.AI_REVIEWER_MISTRAL_API_KEY }}
                  llm_provider: mistral
        ```

    === "Ambos (Mistral primario)"

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
                  mistral_api_key: ${{ secrets.AI_REVIEWER_MISTRAL_API_KEY }}
                  google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
                  llm_provider: mistral
                  llm_fallback_provider: google
        ```

    === "Codestral free tier"

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
                  mistral_api_key: ${{ secrets.AI_REVIEWER_MISTRAL_API_KEY }}
                  llm_provider: mistral
                  mistral_model: codestral-latest
                  mistral_api_url: https://codestral.mistral.ai
        ```

        !!! note "Clave de Codestral"
            Use la clave de [codestral.mistral.ai](https://codestral.mistral.ai/), no la clave API regular de Mistral.

    !!! info "Sobre `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` es un **token automático** que GitHub crea para cada workflow run. **No necesitas** añadirlo manualmente a los secretos — ya está disponible.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

=== "GitLab"

    Crea o actualiza `.gitlab-ci.yml`:

    === "Google only"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        Las variables CI/CD `AI_REVIEWER_GOOGLE_API_KEY` y `AI_REVIEWER_GITLAB_TOKEN` del paso 2b están disponibles automáticamente.

    === "Mistral only"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          variables:
            AI_REVIEWER_LLM_PROVIDER: mistral
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        Las variables CI/CD `AI_REVIEWER_MISTRAL_API_KEY` y `AI_REVIEWER_GITLAB_TOKEN` del paso 2b están disponibles automáticamente.

    === "Ambos (Mistral primario)"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          variables:
            AI_REVIEWER_LLM_PROVIDER: mistral
            AI_REVIEWER_LLM_FALLBACK_PROVIDER: google
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        Las tres variables CI/CD (`AI_REVIEWER_MISTRAL_API_KEY`, `AI_REVIEWER_GOOGLE_API_KEY`, `AI_REVIEWER_GITLAB_TOKEN`) del paso 2b están disponibles automáticamente.

    === "Codestral free tier"

        ```yaml
        stages:
          - review

        ai-review:
          image: ghcr.io/konstziv/ai-code-reviewer:1
          stage: review
          variables:
            AI_REVIEWER_LLM_PROVIDER: mistral
            AI_REVIEWER_MISTRAL_MODEL: codestral-latest
            AI_REVIEWER_MISTRAL_API_URL: https://codestral.mistral.ai
          script:
            - ai-review
          rules:
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
          allow_failure: true
        ```

        Las variables CI/CD `AI_REVIEWER_MISTRAL_API_KEY` (use la clave de Codestral) y `AI_REVIEWER_GITLAB_TOKEN` del Paso 2b están disponibles automáticamente.

---

## Paso 4: Verificar resultado

Ahora AI Review se ejecutará automáticamente cuando:

| Plataforma | Evento |
|------------|--------|
| **GitHub** | Crear PR, nuevos commits en PR, reopening PR |
| **GitLab** | Crear MR, nuevos commits en MR |

### Qué verás

Después de que el job de CI termine, en el PR/MR aparecerán:

- **Comentarios inline** — vinculados a líneas de código específicas
- **Botón "Apply suggestion"** — para aplicar correcciones rápidamente (GitHub)
- **Comentario Summary** — resumen general con métricas

Cada comentario contiene:

- :red_circle: / :yellow_circle: / :blue_circle: Badge de severidad
- Descripción del problema
- Sugerencia de corrección
- Sección colapsable "¿Por qué importa esto?"

En el pie del comentario se muestra qué modelo y proveedor se utilizó:

> _Model: Google / gemini-2.5-flash | Tokens: 1,234 | Latency: 2.3s | Est. cost: $0.0012_

---

## Solución de Problemas

### ¿No aparece la revisión?

Verifica la lista:

- [ ] ¿Clave API añadida como secreto? (`AI_REVIEWER_GOOGLE_API_KEY` o `AI_REVIEWER_MISTRAL_API_KEY`)
- [ ] ¿`llm_provider` configurado correctamente si usas Mistral? (predeterminado es `google`)
- [ ] ¿`github_token` pasado explícitamente? (para GitHub)
- [ ] Para GitLab: ¿`AI_REVIEWER_GITLAB_TOKEN` configurado con un Personal Access Token?
- [ ] ¿El job de CI terminó exitosamente? (revisa logs)
- [ ] Para GitHub: ¿tiene `permissions: pull-requests: write`?
- [ ] Para PRs de forks: los secretos no están disponibles — comportamiento esperado

### ¿Rate limit?

- **Gemini** free tier: 15 solicitudes por minuto
- **Mistral** free tier: límites actuales en [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing)

Espera un minuto e intenta de nuevo, o configura un [proveedor de fallback](configuration.md#llm).

:point_right: [Todos los problemas y soluciones →](troubleshooting.md)

---

## ¿Qué sigue?

| Tarea | Documento |
|-------|-----------|
| Configurar idioma de respuestas | [Configuración](configuration.md) |
| Configuración avanzada de proveedores LLM | [Configuración → LLM](configuration.md#llm) |
| Configuración avanzada de GitHub | [Guía de GitHub](github.md) |
| Configuración avanzada de GitLab | [Guía de GitLab](gitlab.md) |
| Ejemplos de workflows | [Ejemplos](examples/index.md) |
