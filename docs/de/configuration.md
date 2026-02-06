# Konfiguration

Alle Einstellungen werden über Umgebungsvariablen konfiguriert.

---

## Erforderliche Variablen

| Variable | Beschreibung | Beispiel | Wie erhalten |
|----------|--------------|----------|--------------|
| `GOOGLE_API_KEY` | Google Gemini API-Schlüssel | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub PAT (für GitHub) | `ghp_...` | [Anleitung](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab PAT (für GitLab) | `glpat-...` | [Anleitung](gitlab.md#get-token) |

!!! warning "Mindestens ein Provider erforderlich"
    Sie benötigen `GITHUB_TOKEN` **oder** `GITLAB_TOKEN` je nach Plattform.
    Tokens sind Provider-spezifisch: `GITHUB_TOKEN` wird nur für GitHub benötigt, `GITLAB_TOKEN` nur für GitLab.

---

## Optionale Variablen {#optional}

### Allgemein

| Variable | Beschreibung | Standard | Bereich |
|----------|--------------|----------|---------|
| `LOG_LEVEL` | Logging-Level | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `API_TIMEOUT` | Request-Timeout (Sek.) | `60` | 1-300 |

### Sprache

| Variable | Beschreibung | Standard | Beispiele |
|----------|--------------|----------|-----------|
| `LANGUAGE` | Antwortsprache | `en` | `uk`, `de`, `es`, `it`, `me` |
| `LANGUAGE_MODE` | Erkennungsmodus | `adaptive` | `adaptive`, `fixed` |

**Sprachmodi:**

- **`adaptive`** (Standard) — erkennt automatisch die Sprache aus dem PR/MR-Kontext (Beschreibung, Kommentare, verknüpfte Aufgabe)
- **`fixed`** — verwendet immer die Sprache aus `LANGUAGE`

!!! tip "ISO 639"
    `LANGUAGE` akzeptiert jeden gültigen ISO 639-Code:

    - 2-Buchstaben: `en`, `uk`, `de`, `es`, `it`
    - 3-Buchstaben: `ukr`, `deu`, `spa`
    - Namen: `English`, `Ukrainian`, `German`

### LLM

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `GEMINI_MODEL` | Gemini-Modell | `gemini-2.5-flash` |

**Verfügbare Modelle:**

| Modell | Beschreibung | Kosten |
|--------|--------------|--------|
| `gemini-2.5-flash` | Schnell, günstig | $0.075 / 1M Input |
| `gemini-2.0-flash` | Vorherige Version | $0.075 / 1M Input |
| `gemini-1.5-pro` | Leistungsstärker | $1.25 / 1M Input |

!!! note "Preisgenauigkeit"
    Die Preise sind zum Release-Datum angegeben und können sich ändern.

    Aktuelle Informationen: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Achten Sie auf den **Free Tier** bei der Verwendung bestimmter Modelle.

    In den allermeisten Fällen ist das kostenlose Limit für Code-Reviews eines Teams von **4-8 Entwicklern** ausreichend.

### Review

| Variable | Beschreibung | Standard | Bereich |
|----------|--------------|----------|---------|
| `REVIEW_MAX_FILES` | Max. Dateien im Kontext | `20` | 1-100 |
| `REVIEW_MAX_DIFF_LINES` | Max. Diff-Zeilen pro Datei | `500` | 1-5000 |

### GitLab

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `GITLAB_URL` | GitLab-Server-URL | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    Für self-hosted GitLab setzen Sie `GITLAB_URL`:
    ```bash
    export GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## .env-Datei

Es ist praktisch, die Konfiguration in `.env` zu speichern:

```bash
# .env
GOOGLE_API_KEY=AIza...
GITHUB_TOKEN=ghp_...

# Optional
LANGUAGE=uk
LANGUAGE_MODE=adaptive
GEMINI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
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
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GITHUB_TOKEN: ${{ github.token }}  # Automatisch
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  GOOGLE_API_KEY: $GOOGLE_API_KEY  # Aus CI/CD Variables
  # GITLAB_TOKEN: $CI_JOB_TOKEN   # Automatisch (eingeschränkt)
  GITLAB_TOKEN: $GITLAB_TOKEN      # Oder PAT für volle Berechtigungen
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

---

## Validierung

AI Code Reviewer validiert die Konfiguration beim Start:

### Validierungsfehler

```
ValidationError: GOOGLE_API_KEY is too short (minimum 10 characters)
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
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
```

### Minimal (GitLab)

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
```

### Ukrainische Sprache, fest

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

### Self-hosted GitLab

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
export GITLAB_URL=https://gitlab.mycompany.com
```

### Debug-Modus

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LOG_LEVEL=DEBUG
```

---

## Konfigurationspriorität

1. **Umgebungsvariablen** (höchste)
2. **`.env`-Datei** im aktuellen Verzeichnis

---

## Nächster Schritt

- [GitHub-Integration →](github.md)
- [GitLab-Integration →](gitlab.md)
