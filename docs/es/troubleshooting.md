# Solución de Problemas

FAQ y resolución de problemas comunes.

---

## Problemas Comunes

### Action muestra --help en lugar de ejecutarse

**Síntoma:** En los logs del CI job se ve:

```
Usage: ai-review [OPTIONS]
...
╭─ Options ─────────────────────────────────────────────────────────╮
│ --provider  -p      [github|gitlab]  CI provider...              │
```

**Causa:** Usando una versión antigua del Docker image (anterior a v1.0.0a2).

**Solución:**

Actualiza a la última versión:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1  # Siempre usa la última v1.x
```

Si el problema persiste, especifica explícitamente la versión:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1.0.0a2  # O más reciente
```

---

### La Revisión No Aparece

**Síntoma:** El job de CI pasó exitosamente, pero no hay comentarios.

**Verifica:**

1. **Logs del job de CI** — ¿hay errores?
2. **Clave API** — ¿es válida `AI_REVIEWER_GOOGLE_API_KEY`?
3. **Token** — ¿hay permisos de escritura?
4. **github_token** — ¿se pasó explícitamente?

=== "GitHub"

    ```yaml
    permissions:
      contents: read
      pull-requests: write  # ← ¡Requerido!
    ```

=== "GitLab"

    Asegúrate de que `GITLAB_TOKEN` tenga scope `api`.

---

### "Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short"

**Causa:** La clave no está configurada o es incorrecta.

**Solución:**

1. Verifica que el secreto esté añadido en la configuración del repo
2. Verifica el nombre (sensible a mayúsculas/minúsculas)
3. Verifica que la clave sea válida en [Google AI Studio](https://aistudio.google.com/)

---

### "401 Unauthorized" / "403 Forbidden"

**Causa:** Token inválido o insuficiente.

=== "GitHub"

    ```yaml
    # Verifica permisos
    permissions:
      contents: read
      pull-requests: write
    ```

=== "GitLab"

    - Verifica que el token no haya expirado
    - Verifica el scope: necesita `api`
    - Asegúrate de usar Project Access Token

---

### "404 Not Found"

**Causa:** PR/MR o repositorio no encontrado.

**Solución:**

1. Verifica que el PR/MR exista
2. Verifica el nombre del repositorio
3. Verifica que el token tenga acceso al repositorio

---

### "429 Too Many Requests" (Rate Limit)

**Causa:** Límite de API excedido.

**Límites del Free Tier de Gemini:**

| Límite | Valor |
|--------|-------|
| Solicitudes por minuto | 15 |
| Tokens por día | 1,000,000 |
| Solicitudes por día | 1,500 |

**Solución:**

1. AI Code Reviewer reintenta automáticamente con backoff exponencial
2. Si el problema persiste — espera o cambia al nivel de pago
3. Añade `concurrency` para cancelar duplicados:

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

---

### "500 Internal Server Error"

**Causa:** Problema en el lado de la API (Google, GitHub, GitLab).

**Solución:**

1. AI Code Reviewer reintenta automáticamente (hasta 5 intentos)
2. Verifica el estado del servicio:
   - [Google Cloud Status](https://status.cloud.google.com/)
   - [GitHub Status](https://www.githubstatus.com/)
   - [GitLab Status](https://status.gitlab.com/)

---

### La Revisión es Muy Lenta

**Causa:** PR grande o red lenta.

**Solución:**

1. Reduce el tamaño del PR
2. Configura límites:

```bash
export REVIEW_MAX_FILES=10
export REVIEW_MAX_DIFF_LINES=300
```

3. Establece timeout:

```yaml
# GitHub
timeout-minutes: 10

# GitLab
timeout: 10m
```

---

### Los PRs de Forks No Reciben Revisión

**Causa:** Los secretos no están disponibles para PRs de forks (seguridad).

**Solución:**

Este es el comportamiento esperado. Para PRs de forks:

1. El mantenedor puede ejecutar la revisión manualmente
2. O usar `pull_request_target` (¡ten cuidado con la seguridad!)

---

### Idioma de Respuesta Incorrecto

**Causa:** Configuración de idioma incorrecta.

**Solución:**

1. Para idioma fijo:
```bash
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

2. Para idioma adaptativo — asegúrate de que la descripción del PR esté escrita en el idioma deseado

---

## FAQ

### ¿Puedo usarlo sin una clave API?

**No.** Se requiere una clave de Google Gemini API. El nivel gratuito es suficiente para la mayoría de los proyectos.

### ¿Se soporta Bitbucket?

**No** (aún no). Solo GitHub y GitLab.

### ¿Puedo usar otros LLMs (ChatGPT, Claude)?

**No** (en MVP). El soporte para otros LLMs está planificado para futuras versiones.

### ¿Es seguro enviar código a la API de Google?

**Importante saber:**

- El código se envía a la API de Google Gemini para análisis
- Revisa los [Términos de Google AI](https://ai.google.dev/terms)
- Para proyectos sensibles, considera soluciones self-hosted (en futuras versiones)

### ¿Cuánto cuesta?

**Precios de Gemini Flash:**

| Métrica | Costo |
|---------|-------|
| Tokens de entrada | $0.075 / 1M |
| Tokens de salida | $0.30 / 1M |

**Aproximadamente:** ~1000 revisiones = ~$1

Nivel gratuito: ~100 revisiones/día gratis.

### ¿Cómo deshabilitar la revisión para ciertos archivos?

Aún no hay `.ai-reviewerignore`. Planificado para futuras versiones.

Solución alternativa: filtrar en el workflow:

```yaml
on:
  pull_request:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### ¿Puedo ejecutarlo localmente?

**Sí:**

```bash
pip install ai-reviewbot
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token
ai-review --provider github --repo owner/repo --pr 123
```

---

## Depuración

### Habilitar Logs Detallados

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Verificar Configuración

```bash
# Verificar que las variables estén configuradas
echo $AI_REVIEWER_GOOGLE_API_KEY | head -c 10
echo $GITHUB_TOKEN | head -c 10
```

### Probar Llamada a la API

```bash
# Probar API de Gemini
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$AI_REVIEWER_GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Obtener Ayuda

Si el problema no se resuelve:

1. :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — para bugs
2. :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — para preguntas

**Al crear un issue, incluye:**

- Versión de AI Code Reviewer (`ai-review --version`)
- Proveedor CI (GitHub/GitLab)
- Logs (¡con secretos ocultos!)
- Pasos para reproducir

---

## Siguiente Paso

- [Ejemplos →](examples/index.md)
- [Configuración →](configuration.md)
