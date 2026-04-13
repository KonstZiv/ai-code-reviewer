# Konfiguration

Alle Einstellungen werden über Umgebungsvariablen konfiguriert.

!!! tip "Migration: `AI_REVIEWER_`-Präfix"
    Ab v1.0.0a7 unterstützen alle Umgebungsvariablen das Präfix `AI_REVIEWER_` (z.B. `AI_REVIEWER_GOOGLE_API_KEY`). Alte Namen (z.B. `GOOGLE_API_KEY`) funktionieren weiterhin als Fallback. Wir empfehlen die Migration zu den neuen Namen, um Konflikte mit anderen Tools in CI/CD-Konfigurationen auf Organisationsebene zu vermeiden.

---

## Erforderliche Variablen

| Variable | Beschreibung | Beispiel | Wie erhalten |
|----------|--------------|----------|--------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Google Gemini API-Schlüssel (kommagetrennt für Multi-Key-Rotation) | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_MISTRAL_API_KEY` | Mistral API-Schlüssel (kommagetrennt für Multi-Key-Rotation) | `sk-...` | [Mistral Console](https://console.mistral.ai/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub-Token (für GitHub) | `ghp_...` | [Anleitung](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab-Token (für GitLab) | `glpat-...` | [Anleitung](gitlab.md#get-token) |

!!! warning "Mindestens ein LLM-API-Schlüssel erforderlich"
    Sie benötigen mindestens einen LLM-API-Schlüssel: `AI_REVIEWER_GOOGLE_API_KEY` **oder** `AI_REVIEWER_MISTRAL_API_KEY` (oder beide).
    Der Schlüssel für den primären Provider (gesetzt über `AI_REVIEWER_LLM_PROVIDER`) ist erforderlich.

!!! warning "Mindestens ein Plattform-Token erforderlich"
    Sie benötigen `AI_REVIEWER_GITHUB_TOKEN` **oder** `AI_REVIEWER_GITLAB_TOKEN` je nach Plattform.

!!! info "GitLab-Token-Typen"
    Für GitLab können Sie einen **Personal Access Token** (funktioniert auf allen Plänen, einschließlich Free)
    oder einen **Project Access Token** (erfordert GitLab Premium/Ultimate) verwenden.

---

## Optionale Variablen {#optional}

### Allgemein

| Variable | Beschreibung | Standard | Bereich |
|----------|--------------|----------|---------|
| `AI_REVIEWER_LOG_LEVEL` | Logging-Level | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_REVIEWER_API_TIMEOUT` | Request-Timeout (Sek.) | `60` | 1-300 |

### Sprache

| Variable | Beschreibung | Standard | Beispiele |
|----------|--------------|----------|-----------|
| `AI_REVIEWER_LANGUAGE` | Antwortsprache | `en` | `uk`, `de`, `es`, `it`, `me` |
| `AI_REVIEWER_LANGUAGE_MODE` | Erkennungsmodus | `adaptive` | `adaptive`, `fixed` |

**Sprachmodi:**

- **`adaptive`** (Standard) — erkennt automatisch die Sprache aus dem PR/MR-Kontext (Beschreibung, Kommentare, verknüpfte Aufgabe)
- **`fixed`** — verwendet immer die Sprache aus `AI_REVIEWER_LANGUAGE`

!!! tip "ISO 639"
    `AI_REVIEWER_LANGUAGE` akzeptiert jeden gültigen ISO 639-Code:

    - 2-Buchstaben: `en`, `uk`, `de`, `es`, `it`
    - 3-Buchstaben: `ukr`, `deu`, `spa`
    - Namen: `English`, `Ukrainian`, `German`

### LLM {#llm}

#### Provider-Auswahl

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `AI_REVIEWER_LLM_PROVIDER` | Primärer LLM-Provider | `google` |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Fallback-Provider (wird verwendet, wenn der primäre erschöpft ist) | _(keiner)_ |

Unterstützte Provider: `google`, `mistral`.

Wenn sowohl primärer als auch Fallback-Provider konfiguriert sind, probiert das System zuerst alle Modelle des primären Providers, dann alle Modelle des Fallback-Providers. Beispiel mit `LLM_PROVIDER=mistral` und `LLM_FALLBACK_PROVIDER=google`:

```
mistral-large → mistral-small → gemini-2.5-flash → gemini-2.5-flash-lite
```

#### Google Gemini Models

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `AI_REVIEWER_GEMINI_MODEL` | Primäres Gemini-Modell | `gemini-2.5-flash` |
| `AI_REVIEWER_GEMINI_MODEL_FALLBACK` | Fallback-Modellkette (kommagetrennt) | `gemini-3-flash-preview,...` |

| Modell | Beschreibung | Kosten |
|--------|--------------|--------|
| `gemini-2.5-flash` | Schnell, stabil, mit Reasoning (Standard) | $0.075 / 1M Input |
| `gemini-3-flash-preview` | Frontier-Klasse Flash (Vorschau) | $0.075 / 1M Input |
| `gemini-2.5-flash-lite` | Schnellste und günstigste in 2.5 | $0.01875 / 1M Input |
| `gemini-2.5-pro` | Leistungsstärkste, tiefes Reasoning | $1.25 / 1M Input |

:material-link: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

#### Mistral Models

| Variable | Beschreibung | Default |
|----------|-------------|---------|
| `AI_REVIEWER_MISTRAL_MODEL` | Primäres Mistral-Modell | `mistral-large-latest` |
| `AI_REVIEWER_MISTRAL_MODEL_FALLBACK` | Fallback-Modellkette (kommagetrennt) | _(keine)_ |
| `AI_REVIEWER_MISTRAL_API_URL` | Benutzerdefinierte API-Basis-URL | _(keine)_ |

| Modell | Beschreibung | Kontext | Preis (Input / Output) |
|--------|-------------|---------|----------------------|
| `mistral-large-latest` | Leistungsstärkstes, MoE 41B/675B (Standard) | 256k | $0.50 / $1.50 |
| `mistral-medium-latest` | Ausgewogenes Leistungs-/Kostenverhältnis | 128k | $0.40 / $2.00 |
| `mistral-small-latest` | Schnell und günstig, Hybrid 6.5B/119B | 256k | $0.15 / $0.60 |
| `codestral-latest` | Für Code optimiert, FIM-Unterstützung | 128k | $0.30 / $0.90 |
| `devstral-latest` | Coding-Agent, günstigstes Mistral-Modell | 256k | $0.10 / $0.30 |

!!! tip "Kostenloses Codestral"
    Codestral hat ein separates kostenloses Kontingent unter `https://codestral.mistral.ai` mit eigenem API-Schlüssel.
    Setzen Sie `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai` und verwenden Sie einen Schlüssel von [codestral.mistral.ai](https://codestral.mistral.ai/).
    Das kostenpflichtige Codestral über `api.mistral.ai` benötigt **keine** benutzerdefinierte URL.

:material-link: [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing)

#### Weitere Einstellungen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `AI_REVIEWER_REVIEW_SPLIT_THRESHOLD` | Zeichenlimit für Code+Test-Split-Review | `30000` |

!!! note "Preisgenauigkeit"
    Die Preise sind zum Release-Datum angegeben und können sich ändern. Aktuelle Informationen finden Sie auf der Preisseite des Providers.

!!! tip "Free Tier"
    Sowohl Google Gemini als auch Mistral bieten kostenlose Stufen, die für Code-Reviews eines Teams von **4-8 Entwicklern** ausreichen. Kombinieren Sie zwei Provider für maximale Zuverlässigkeit.

### Review

| Variable | Beschreibung | Standard | Bereich |
|----------|--------------|----------|---------|
| `AI_REVIEWER_REVIEW_MAX_FILES` | Max. Dateien im Kontext | `20` | 1-100 |
| `AI_REVIEWER_REVIEW_MAX_DIFF_LINES` | Max. Diff-Zeilen pro Datei | `500` | 1-5000 |
| `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS` | Max. Zeichen der MR-Kommentare im Prompt | `3000` | 0-20000 |
| `AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS` | Bot-Kommentare im Prompt einschließen | `true` | true/false |
| `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS` | Inline-Kommentare an Codezeilen posten | `true` | true/false |
| `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE` | Kommentare in Dialog-Threads gruppieren | `true` | true/false |

!!! info "Diskussionskontext"
    Der AI-Reviewer liest bestehende MR/PR-Kommentare, um bereits besprochene
    Vorschläge nicht zu wiederholen. Setzen Sie `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS=0` zum Deaktivieren.

!!! info "Inline-Kommentare"
    Wenn `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS=true` (Standard), werden Issues mit Datei-/Zeileninformationen als Inline-Kommentare am Code gepostet, mit einer kurzen Zusammenfassung als Review-Body. Setzen Sie auf `false` für einen einzelnen Zusammenfassungskommentar.

!!! info "Dialog-Threads"
    Wenn `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE=true` (Standard), werden Kommentare in
    Konversations-Threads gruppiert, damit die KI Antwort-Ketten versteht. Setzen Sie auf `false` für flache Darstellung.

### Discovery

| Variable | Beschreibung | Standard | Bereich |
|----------|--------------|----------|---------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | Projektanalyse vor dem Review aktivieren | `true` | true/false |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | Discovery-Kommentar immer posten (Standard: nur bei Lücken) | `false` | true/false |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | Discovery-Pipeline-Timeout in Sekunden | `30` | 1-300 |

!!! info "Projektanalyse"
    Wenn aktiviert, analysiert AI ReviewBot automatisch Ihr Repository (Sprachen, CI-Pipeline, Config-Dateien) vor jedem Review für intelligenteres Feedback. Setzen Sie auf `false` zum Deaktivieren. Details: [Discovery →](discovery.md).

!!! info "Verbose-Modus"
    Wenn `AI_REVIEWER_DISCOVERY_VERBOSE=true`, wird der Discovery-Kommentar immer gepostet und enthält alle Attention Zones (Well Covered, Weakly Covered, Not Covered). Im Standardmodus wird nur bei Lücken oder nicht abgedeckten Zones gepostet.

### GitLab

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `AI_REVIEWER_GITLAB_URL` | GitLab-Server-URL | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    Für self-hosted GitLab setzen Sie `AI_REVIEWER_GITLAB_URL`:
    ```bash
    export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## .env-Datei

Es ist praktisch, die Konfiguration in `.env` zu speichern:

```bash
# .env

# LLM-Provider (einen oder beide wählen)
AI_REVIEWER_GOOGLE_API_KEY=AIza...
# AI_REVIEWER_MISTRAL_API_KEY=sk-...
# AI_REVIEWER_LLM_PROVIDER=google
# AI_REVIEWER_LLM_FALLBACK_PROVIDER=mistral

# Plattform-Token
AI_REVIEWER_GITHUB_TOKEN=ghp_...

# Optional
AI_REVIEWER_LANGUAGE=uk
AI_REVIEWER_LANGUAGE_MODE=adaptive
AI_REVIEWER_GEMINI_MODEL=gemini-2.5-flash
AI_REVIEWER_LOG_LEVEL=INFO
```

!!! danger "Sicherheit"
    **Committen Sie `.env` niemals in Git!**

    Fügen Sie zu `.gitignore` hinzu:
    ```
    .env
    .env.*
    ```

---

## CI/CD-Konfiguration

### GitHub Actions

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
  AI_REVIEWER_GITHUB_TOKEN: ${{ github.token }}  # Automatisch
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  # AI_REVIEWER_GOOGLE_API_KEY und AI_REVIEWER_GITLAB_TOKEN
  # werden aus CI/CD Variables automatisch vererbt
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

---

## Validierung

AI Code Reviewer validiert die Konfiguration beim Start:

### Validierungsfehler

```
ValidationError: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Lösung:** Überprüfen Sie, ob die Variable korrekt gesetzt ist.

```
ValidationError: Invalid language code 'xyz'
```

**Lösung:** Verwenden Sie einen gültigen ISO 639-Code.

```
ValidationError: LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Lösung:** Verwenden Sie eines der erlaubten Level.

---

## Konfigurationsbeispiele

### Minimal (GitHub)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
```

### Minimal (GitLab)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
```

### Ukrainische Sprache, fest

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LANGUAGE=uk
export AI_REVIEWER_LANGUAGE_MODE=fixed
```

### Self-hosted GitLab

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
```

### Debug-Modus

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LOG_LEVEL=DEBUG
```

---

## Konfigurationspriorität

1. **Umgebungsvariablen** (höchste)
2. **`.env`-Datei** im aktuellen Verzeichnis

---

## Nächster Schritt

- [GitHub-Integration →](github.md)
- [GitLab-Integration →](gitlab.md)
