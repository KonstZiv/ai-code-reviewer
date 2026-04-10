# GitLab

Detaillierter Leitfaden für die Integration mit GitLab CI.

---

## Tokens {#tokens}

### Personal Access Token (PAT) {#get-token}

**Empfohlen für alle GitLab-Pläne** (einschließlich Free).

!!! danger "`CI_JOB_TOKEN` funktioniert nicht"
    GitLabs automatischer `CI_JOB_TOKEN` **kann keine Kommentare** zu Merge Requests posten
    (die Notes API erfordert den `api`-Scope, den `CI_JOB_TOKEN` nicht hat).
    Sie **müssen** einen Personal Access Token oder Project Access Token verwenden.

**So erstellen Sie einen PAT:**

1. Gehen Sie zu **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Füllen Sie die Felder aus:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** nach Bedarf festlegen (z.B. 1 Jahr)
    - **Scopes:** aktivieren Sie **`api`**
3. Klicken Sie auf **Create personal access token**
4. **Kopieren Sie den Token sofort** — GitLab zeigt ihn nur einmal!

**Verwendung in CI:**

1. Gehen Sie zu **Settings → CI/CD → Variables → Add variable**
2. Variable hinzufügen:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN`
    - **Value:** fügen Sie Ihren Token ein
    - **Flags:** aktivieren Sie **Masked**, :x: **deaktivieren** Sie Protected

    Die Variable wird automatisch an alle Jobs vererbt — kein YAML `variables:` Mapping nötig.

!!! warning "«Protected» deaktivieren!"
    Standardmäßig markiert GitLab neue Variablen als **Protected**. Protected-Variablen sind **nur in geschützten Branches** verfügbar (z.B. `main`).

    MR-Pipelines laufen auf **ungeschützten** Source-Branches — die Variable ist dann leer und Sie erhalten **401 Unauthorized**.

    **Deaktivieren Sie immer «Protected»** für `AI_REVIEWER_GITLAB_TOKEN` und `AI_REVIEWER_GOOGLE_API_KEY`.

!!! warning "Token speichern"
    GitLab zeigt den Token **nur einmal** an. Speichern Sie ihn sofort an einem sicheren Ort.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Nur verfügbar mit **GitLab Premium** und **Ultimate** Plänen. Eine gute Wahl, wenn Sie einen projektbezogenen Token anstelle eines persönlichen bevorzugen.

**Vorteile gegenüber PAT:**

- Auf ein einzelnes Projekt beschränkt (kein Zugriff auf andere Projekte)
- Kann von Projekt-Maintainern widerrufen werden (keine Abhängigkeit von einem bestimmten Benutzer)
- Besser für Teams — nicht an ein persönliches Konto gebunden

**So erstellen Sie einen Project Access Token:**

1. Gehen Sie zu **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Füllen Sie die Felder aus:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (Minimum erforderlich)
    - **Scopes:** aktivieren Sie **`api`**
3. Klicken Sie auf **Create project access token**
4. **Kopieren Sie den Token sofort**

**Verwendung in CI:**

Gleich wie PAT — als `AI_REVIEWER_GITLAB_TOKEN` in CI/CD Variables hinzufügen:

1. **Key:** `AI_REVIEWER_GITLAB_TOKEN`
2. **Value:** fügen Sie Ihren Project Access Token ein

!!! info "Welchen Token wählen?"
    | | Personal Access Token | Project Access Token |
    |---|---|---|
    | **Plan** | Alle (einschließlich Free) | Nur Premium/Ultimate |
    | **Einrichtung** | Manuell | Manuell |
    | **Geltungsbereich** | Alle Projekte des Benutzers | Einzelnes Projekt |
    | **Inline-Kommentare** | :white_check_mark: | :white_check_mark: |
    | **Am besten für** | Free-Plan + volle Funktionen | Teams mit Premium/Ultimate |

---

## CI/CD-Variablen

### Variablen hinzufügen

`Settings → CI/CD → Variables → Add variable`

| Variable | Wert | Optionen |
|----------|------|----------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API-Schlüssel | :white_check_mark: Masked, :x: **Uncheck** Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | Personal / Project Access Token | :white_check_mark: Masked, :x: **Uncheck** Protected |

!!! tip "Masked"
    Aktivieren Sie immer **Masked** für Secrets — sie werden nicht in Logs angezeigt.

---

## Trigger

### Empfohlener Trigger

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Dies führt den Job nur für Merge-Request-Pipelines aus.

### Alternativer Trigger (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — neuere Syntax, von GitLab empfohlen.

---

## Job-Beispiele

### Minimal

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

CI/CD-Variablen `AI_REVIEWER_GOOGLE_API_KEY` und `AI_REVIEWER_GITLAB_TOKEN` werden automatisch vererbt.

### Vollständig (empfohlen)

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

**Was es bewirkt:**

- `allow_failure: true` — MR wird nicht blockiert, wenn Review fehlschlägt
- `timeout: 10m` — maximal 10 Minuten
- `interruptible: true` — kann bei neuem Commit abgebrochen werden

### Mit benutzerdefinierter Stage

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
  needs: []  # Nicht auf vorherige Stages warten
```

---

## Self-hosted GitLab

### Konfiguration

```yaml
variables:
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
```

### Docker Registry

Wenn Ihr GitLab keinen Zugriff auf `ghcr.io` hat, erstellen Sie einen Mirror:

```bash
# Auf einer Maschine mit Zugriff
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

## GitLab CI-Variablen

AI Code Reviewer verwendet automatisch:

| Variable | Beschreibung |
|----------|--------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | MR-Nummer |
| `CI_SERVER_URL` | GitLab-URL |

Sie müssen `--repo` und `--pr` nicht übergeben — sie werden automatisch aus CI übernommen.

---

## Variable-gesteuerte Konfiguration {#variable-driven}

Verwenden Sie **CI/CD Variables**, um zwischen LLM-Anbietern und Modellen zu wechseln, ohne `.gitlab-ci.yml` zu ändern. Dies ist nützlich, um die Review-Qualität verschiedener Modelle am selben MR zu vergleichen.

### Einrichtung

**CI/CD Variables** (`Settings → CI/CD → Variables`):

| Variable | Beschreibung | Optionen |
|----------|-------------|----------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API-Schlüssel | :white_check_mark: Masked, :x: Protected deaktivieren |
| `AI_REVIEWER_MISTRAL_API_KEY` | Mistral API-Schlüssel | :white_check_mark: Masked, :x: Protected deaktivieren |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab-Token | :white_check_mark: Masked, :x: Protected deaktivieren |
| `AI_REVIEWER_LLM_PROVIDER` | Primärer Anbieter (`google`, `mistral`) | :x: Protected deaktivieren |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Fallback-Anbieter | :x: Protected deaktivieren |
| `AI_REVIEWER_MISTRAL_MODEL` | Mistral-Modell | :x: Protected deaktivieren |
| `AI_REVIEWER_MISTRAL_API_URL` | Benutzerdefinierte API-URL (für Codestral Free Tier) | :x: Protected deaktivieren |

### Job-Konfiguration

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

Kein `variables:`-Abschnitt nötig — alle `AI_REVIEWER_*` CI/CD-Variablen werden automatisch vererbt.

### Presets umschalten

Ändern Sie die CI/CD Variables in der GitLab-Oberfläche und klicken Sie auf **Retry** für die Pipeline desselben MR:

| Preset | `AI_REVIEWER_LLM_PROVIDER` | `AI_REVIEWER_MISTRAL_MODEL` | `AI_REVIEWER_MISTRAL_API_URL` | `AI_REVIEWER_LLM_FALLBACK_PROVIDER` |
|--------|---------------------------|---------------------------|-------------------------------|-------------------------------------|
| Gemini (Standard) | `google` | _(leer)_ | _(leer)_ | _(leer)_ |
| Mistral Large | `mistral` | `mistral-large-latest` | _(leer)_ | `google` |
| Codestral Free | `mistral` | `codestral-latest` | `https://codestral.mistral.ai` | `google` |
| Devstral | `mistral` | `devstral-latest` | _(leer)_ | `google` |

!!! tip "Codestral Free Tier Schlüssel"
    Für das Preset „Codestral Free" muss `AI_REVIEWER_MISTRAL_API_KEY` einen Schlüssel von [codestral.mistral.ai](https://codestral.mistral.ai/) enthalten, nicht von `console.mistral.ai`.

!!! info "Kein Hardcoding im YAML nötig"
    Anders als bei GitHub Actions (wo Inputs explizit zugeordnet werden müssen) übergibt GitLab CI automatisch alle CI/CD-Variablen als Umgebungsvariablen. Setzen Sie sie einfach in der Oberfläche — die Anwendung erkennt sie über das Präfix `AI_REVIEWER_*`.

---

## Review-Ergebnis

### Notes (Kommentare)

AI Review postet Kommentare zum MR als Notes.

### Discussions (Inline)

Für Inline-Kommentare benötigen Sie einen Personal Access Token oder Project Access Token mit `api`-Scope.

Inline-Kommentare erscheinen direkt neben Code-Zeilen in der Diff-Ansicht.

### Zusammenfassung

Am Ende des Reviews wird eine Zusammenfassungs-Note gepostet mit:

- Gesamtstatistik
- Metriken
- Gute Praktiken

---

## Fehlerbehebung

### Review postet keine Kommentare

**Überprüfen:**

1. `AI_REVIEWER_GOOGLE_API_KEY`-Variable ist gesetzt
2. `AI_REVIEWER_GITLAB_TOKEN` hat ausreichende Berechtigungen (Scope: `api`)
3. Pipeline läuft für MR (nicht für einen Branch)

### "401 Unauthorized"

**Ursache:** Ungültiger Token.

**Lösung:**

- Überprüfen Sie, ob der Token nicht abgelaufen ist
- Überprüfen Sie den Scope (benötigt `api`)

### "403 Forbidden"

**Ursache:** Unzureichende Berechtigungen.

**Lösung:**

- Überprüfen Sie, ob der Token den `api`-Scope hat
- Überprüfen Sie, ob der Token Zugriff auf das Projekt hat

### "404 Not Found"

**Ursache:** MR nicht gefunden.

**Lösung:**

- Überprüfen Sie, ob die Pipeline für MR läuft
- Überprüfen Sie `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Ursache:** API-Limit überschritten.

**Lösung:**

- AI Code Reviewer wiederholt automatisch mit Backoff
- Bei anhaltendem Problem — warten oder Limits erhöhen

---

## Best Practices

### 1. PAT für volle Funktionalität verwenden

### 2. allow_failure hinzufügen

```yaml
allow_failure: true
```

MR wird nicht blockiert, wenn Review fehlschlägt.

### 3. Timeout setzen

```yaml
timeout: 10m
```

### 4. Job unterbrechbar machen

```yaml
interruptible: true
```

Altes Review wird bei neuem Commit abgebrochen.

### 5. Nicht auf andere Stages warten

```yaml
needs: []
```

Review startet sofort, ohne auf Build/Test zu warten.

---

## Nächster Schritt

- [GitHub-Integration →](github.md)
- [CLI-Referenz →](api.md)
