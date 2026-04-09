# Configuración

Todas las configuraciones se hacen mediante variables de entorno.

!!! tip "Migración: prefijo `AI_REVIEWER_`"
    Desde v1.0.0a7, todas las variables de entorno admiten el prefijo `AI_REVIEWER_` (ej., `AI_REVIEWER_GOOGLE_API_KEY`). Los nombres antiguos (ej., `GOOGLE_API_KEY`) siguen funcionando como fallback. Recomendamos migrar a los nuevos nombres para evitar conflictos con otras herramientas en configuraciones CI/CD a nivel de organización.

---

## Variables Requeridas

| Variable | Descripción | Ejemplo | Cómo obtener |
|----------|-------------|---------|--------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Clave API de Google Gemini (separadas por comas para rotación de claves) | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub PAT (para GitHub) | `ghp_...` | [Instrucciones](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab PAT (para GitLab) | `glpat-...` | [Instrucciones](gitlab.md#get-token) |

!!! warning "Se requiere al menos un proveedor"
    Necesitas `AI_REVIEWER_GITHUB_TOKEN` **o** `AI_REVIEWER_GITLAB_TOKEN` dependiendo de la plataforma.
    Los tokens son específicos del proveedor: `AI_REVIEWER_GITHUB_TOKEN` solo se necesita para GitHub, `AI_REVIEWER_GITLAB_TOKEN` solo para GitLab.

---

## Variables Opcionales {#optional}

### General

| Variable | Descripción | Por defecto | Rango |
|----------|-------------|-------------|-------|
| `AI_REVIEWER_LOG_LEVEL` | Nivel de logging | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_REVIEWER_API_TIMEOUT` | Timeout de solicitud (seg) | `60` | 1-300 |

### Idioma

| Variable | Descripción | Por defecto | Ejemplos |
|----------|-------------|-------------|----------|
| `AI_REVIEWER_LANGUAGE` | Idioma de respuesta | `en` | `uk`, `de`, `es`, `it`, `me` |
| `AI_REVIEWER_LANGUAGE_MODE` | Modo de detección | `adaptive` | `adaptive`, `fixed` |

**Modos de idioma:**

- **`adaptive`** (por defecto) — detecta automáticamente el idioma del contexto del PR/MR (descripción, comentarios, tarea vinculada)
- **`fixed`** — siempre usa el idioma de `AI_REVIEWER_LANGUAGE`

!!! tip "ISO 639"
    `AI_REVIEWER_LANGUAGE` acepta cualquier código ISO 639 válido:

    - 2 letras: `en`, `uk`, `de`, `es`, `it`
    - 3 letras: `ukr`, `deu`, `spa`
    - Nombres: `English`, `Ukrainian`, `German`

### LLM

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `AI_REVIEWER_GEMINI_MODEL` | Modelo Gemini | `gemini-2.5-flash` |
| `AI_REVIEWER_GEMINI_MODEL_FALLBACK` | Cadena de modelos de respaldo (separados por comas) | `gemini-3.1-flash-preview` |
| `AI_REVIEWER_REVIEW_SPLIT_THRESHOLD` | Umbral de caracteres para revisión dividida código+tests | `30000` |

**Modelos disponibles:**

| Modelo | Descripción | Costo |
|--------|-------------|-------|
| `gemini-2.5-flash` | Rápido, estable, con razonamiento (predeterminado) | $0.075 / 1M entrada |
| `gemini-3.1-flash-preview` | Flash de clase frontier (vista previa) | $0.075 / 1M entrada |
| `gemini-2.5-flash-lite` | El más rápido y económico en 2.5 | $0.01875 / 1M entrada |
| `gemini-2.5-pro` | El más potente, razonamiento profundo | $1.25 / 1M entrada |

!!! note "Precisión de precios"
    Los precios están listados a la fecha de lanzamiento y pueden cambiar.

    Información actual: [Precios de Gemini API](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Presta atención al **Free Tier** al usar ciertos modelos.

    En la gran mayoría de los casos, el límite gratuito es suficiente para la revisión de código de un equipo de **4-8 desarrolladores**.

### Revisión

| Variable | Descripción | Por defecto | Rango |
|----------|-------------|-------------|-------|
| `AI_REVIEWER_REVIEW_MAX_FILES` | Máximo de archivos en contexto | `20` | 1-100 |
| `AI_REVIEWER_REVIEW_MAX_DIFF_LINES` | Máximo de líneas de diff por archivo | `500` | 1-5000 |
| `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS` | Máx. caracteres de comentarios MR en prompt | `3000` | 0-20000 |
| `AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS` | Incluir comentarios de bots en prompt | `true` | true/false |
| `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS` | Publicar comentarios inline en líneas | `true` | true/false |
| `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE` | Agrupar comentarios en hilos de diálogo | `true` | true/false |

!!! info "Contexto de discusión"
    El revisor AI lee los comentarios existentes del MR/PR para evitar repetir sugerencias
    que ya fueron discutidas. Configure `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS=0` para desactivar.

!!! info "Comentarios inline"
    Cuando `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS=true` (por defecto), los issues con información de archivo/línea se publican como comentarios inline en el código, con un resumen corto como cuerpo de la revisión. Configura `false` para un único comentario de resumen.

!!! info "Hilos de diálogo"
    Cuando `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE=true` (por defecto), los comentarios se agrupan en
    hilos de conversación para que la IA entienda las cadenas de respuestas. Configura `false` para renderizado plano.

### Discovery

| Variable | Descripción | Por defecto | Rango |
|----------|-------------|-------------|-------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | Activar análisis de proyecto antes de la revisión | `true` | true/false |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | Siempre publicar comentario de discovery (por defecto: solo cuando hay brechas) | `false` | true/false |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | Timeout del pipeline de discovery en segundos | `30` | 1-300 |

!!! info "Análisis de proyecto"
    Cuando está activado, AI ReviewBot analiza automáticamente tu repositorio (lenguajes, pipeline CI, archivos de config) antes de cada revisión para proporcionar feedback más inteligente. Configura `false` para desactivar. Detalles: [Discovery →](discovery.md).

!!! info "Modo verbose"
    Cuando `AI_REVIEWER_DISCOVERY_VERBOSE=true`, el comentario de discovery siempre se publica e incluye todas las Attention Zones (Well Covered, Weakly Covered, Not Covered). El modo por defecto solo publica cuando hay brechas o zonas no cubiertas.

### GitLab

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `AI_REVIEWER_GITLAB_URL` | URL del servidor GitLab | `https://gitlab.com` |

!!! info "GitLab Self-hosted"
    Para GitLab self-hosted, configura `AI_REVIEWER_GITLAB_URL`:
    ```bash
    export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## Archivo .env

Es conveniente almacenar la configuración en `.env`:

```bash
# .env
AI_REVIEWER_GOOGLE_API_KEY=AIza...
AI_REVIEWER_GITHUB_TOKEN=ghp_...

# Opcional
AI_REVIEWER_LANGUAGE=uk
AI_REVIEWER_LANGUAGE_MODE=adaptive
AI_REVIEWER_GEMINI_MODEL=gemini-2.5-flash
AI_REVIEWER_LOG_LEVEL=INFO
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
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
  AI_REVIEWER_GITHUB_TOKEN: ${{ github.token }}  # Automático
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  AI_REVIEWER_GOOGLE_API_KEY: $AI_REVIEWER_GOOGLE_API_KEY  # Desde CI/CD Variables
  AI_REVIEWER_GITLAB_TOKEN: $AI_REVIEWER_GITLAB_TOKEN      # Project Access Token
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

---

## Validación

AI Code Reviewer valida la configuración al iniciar:

### Errores de Validación

```
ValidationError: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
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
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
```

### Mínima (GitLab)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
```

### Idioma ucraniano, fijo

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LANGUAGE=uk
export AI_REVIEWER_LANGUAGE_MODE=fixed
```

### GitLab Self-hosted

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
```

### Modo debug

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LOG_LEVEL=DEBUG
```

---

## Prioridad de Configuración

1. **Variables de entorno** (más alta)
2. **Archivo `.env`** en el directorio actual

---

## Siguiente Paso

- [Integración con GitHub →](github.md)
- [Integración con GitLab →](gitlab.md)
