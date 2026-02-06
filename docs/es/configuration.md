# Configuración

Todas las configuraciones se hacen mediante variables de entorno.

---

## Variables Requeridas

| Variable | Descripción | Ejemplo | Cómo obtener |
|----------|-------------|---------|------------|
| `GOOGLE_API_KEY` | Clave API de Google Gemini | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub PAT (para GitHub) | `ghp_...` | [Instrucciones](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab PAT (para GitLab) | `glpat-...` | [Instrucciones](gitlab.md#get-token) |

!!! warning "Se requiere al menos un proveedor"
    Necesitas `GITHUB_TOKEN` **o** `GITLAB_TOKEN` dependiendo de la plataforma.
    Los tokens son específicos del proveedor: `GITHUB_TOKEN` solo se necesita para GitHub, `GITLAB_TOKEN` solo para GitLab.

---

## Variables Opcionales {#optional}

### General

| Variable | Descripción | Por defecto | Rango |
|----------|-------------|---------|-------|
| `LOG_LEVEL` | Nivel de logging | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `API_TIMEOUT` | Timeout de solicitud (seg) | `60` | 1-300 |

### Idioma

| Variable | Descripción | Por defecto | Ejemplos |
|----------|-------------|---------|----------|
| `LANGUAGE` | Idioma de respuesta | `en` | `uk`, `de`, `es`, `it`, `me` |
| `LANGUAGE_MODE` | Modo de detección | `adaptive` | `adaptive`, `fixed` |

**Modos de idioma:**

- **`adaptive`** (por defecto) — detecta automáticamente el idioma del contexto del PR/MR (descripción, comentarios, tarea vinculada)
- **`fixed`** — siempre usa el idioma de `LANGUAGE`

!!! tip "ISO 639"
    `LANGUAGE` acepta cualquier código ISO 639 válido:

    - 2 letras: `en`, `uk`, `de`, `es`, `it`
    - 3 letras: `ukr`, `deu`, `spa`
    - Nombres: `English`, `Ukrainian`, `German`

### LLM

| Variable | Descripción | Por defecto |
|----------|-------------|---------|
| `GEMINI_MODEL` | Modelo Gemini | `gemini-2.5-flash` |

**Modelos disponibles:**

| Modelo | Descripción | Costo |
|-------|-------------|------|
| `gemini-2.5-flash` | Rápido, económico | $0.075 / 1M entrada |
| `gemini-2.0-flash` | Versión anterior | $0.075 / 1M entrada |
| `gemini-1.5-pro` | Más potente | $1.25 / 1M entrada |

!!! note "Precisión de precios"
    Los precios están listados a la fecha de lanzamiento y pueden cambiar.

    Información actual: [Precios de Gemini API](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Presta atención al **Free Tier** al usar ciertos modelos.

    En la gran mayoría de los casos, el límite gratuito es suficiente para la revisión de código de un equipo de **4-8 desarrolladores**.

### Revisión

| Variable | Descripción | Por defecto | Rango |
|----------|-------------|---------|-------|
| `REVIEW_MAX_FILES` | Máximo de archivos en contexto | `20` | 1-100 |
| `REVIEW_MAX_DIFF_LINES` | Máximo de líneas de diff por archivo | `500` | 1-5000 |

### GitLab

| Variable | Descripción | Por defecto |
|----------|-------------|---------|
| `GITLAB_URL` | URL del servidor GitLab | `https://gitlab.com` |

!!! info "GitLab Self-hosted"
    Para GitLab self-hosted, configura `GITLAB_URL`:
    ```bash
    export GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## Archivo .env

Es conveniente almacenar la configuración en `.env`:

```bash
# .env
GOOGLE_API_KEY=AIza...
GITHUB_TOKEN=ghp_...

# Opcional
LANGUAGE=uk
LANGUAGE_MODE=adaptive
GEMINI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
```

!!! danger "Seguridad"
    **¡Nunca hagas commit de `.env` a git!**

    Añade a `.gitignore`:
    ```
    .env
    .env.*
    ```

---

## Configuración CI/CD

### GitHub Actions

```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GITHUB_TOKEN: ${{ github.token }}  # Automático
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  GOOGLE_API_KEY: $GOOGLE_API_KEY  # Desde CI/CD Variables
  # GITLAB_TOKEN: $CI_JOB_TOKEN   # Automático (limitado)
  GITLAB_TOKEN: $GITLAB_TOKEN      # O PAT para permisos completos
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

---

## Validación

AI Code Reviewer valida la configuración al iniciar:

### Errores de Validación

```
ValidationError: GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Solución:** Verifica que la variable esté configurada correctamente.

```
ValidationError: Invalid language code 'xyz'
```

**Solución:** Usa un código ISO 639 válido.

```
ValidationError: LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Solución:** Usa uno de los niveles permitidos.

---

## Ejemplos de Configuración

### Mínima (GitHub)

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
```

### Mínima (GitLab)

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
```

### Idioma ucraniano, fijo

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

### GitLab Self-hosted

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
export GITLAB_URL=https://gitlab.mycompany.com
```

### Modo debug

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LOG_LEVEL=DEBUG
```

---

## Prioridad de Configuración

1. **Variables de entorno** (más alta)
2. **Archivo `.env`** en el directorio actual

---

## Siguiente Paso

- [Integración con GitHub →](github.md)
- [Integración con GitLab →](gitlab.md)
