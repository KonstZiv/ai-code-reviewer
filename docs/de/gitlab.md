# GitLab

Detaillierter Leitfaden für die Integration mit GitLab CI.

---

## Tokens {#tokens}

### CI_JOB_TOKEN (automatisch)

In GitLab CI ist `CI_JOB_TOKEN` automatisch verfügbar:

```yaml
variables:
  GITLAB_TOKEN: $CI_JOB_TOKEN
```

**`CI_JOB_TOKEN`-Einschränkungen:**

| Funktion | Status |
|----------|--------|
| MR lesen | :white_check_mark: |
| Diff lesen | :white_check_mark: |
| Notes posten | :white_check_mark: |
| Discussions erstellen | :x: |

!!! warning "Eingeschränkte Berechtigungen"
    `CI_JOB_TOKEN` kann keine Inline-Discussions erstellen.

    Für volle Funktionalität verwenden Sie einen Personal Access Token.

### Personal Access Token (empfohlen) {#get-token}

Für **lokale Ausführungen** oder **volle Funktionalität in CI** benötigen Sie einen Personal Access Token:

1. Gehen Sie zu `User Settings → Access Tokens → Add new token`
2. Geben Sie den Token-Namen ein (z.B. `ai-code-reviewer`)
3. Wählen Sie Scope: **`api`**
4. Klicken Sie auf **Create personal access token**
5. Kopieren Sie den Token und speichern Sie ihn als `GITLAB_TOKEN`

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Aus CI/CD Variables
```

!!! warning "Token speichern"
    GitLab zeigt den Token **nur einmal** an. Speichern Sie ihn sofort.

!!! info "Personal Access Token vs Project Access Token"
    **Personal Access Token** (PAT) funktioniert mit **allen GitLab-Plänen**, einschließlich Free.

    **Project Access Token** ist nur mit **GitLab Premium/Ultimate** verfügbar.
    Wenn Sie den Free-Plan verwenden, nutzen Sie einen Personal Access Token.

---

## CI/CD-Variablen

### Variablen hinzufügen

`Settings → CI/CD → Variables → Add variable`

| Variable | Wert | Optionen |
|----------|------|----------|
| `GOOGLE_API_KEY` | Gemini API-Schlüssel | Masked |
| `GITLAB_TOKEN` | PAT (falls benötigt) | Masked |

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
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

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
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
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
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
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
| `CI_JOB_TOKEN` | Automatischer Token |

Sie müssen `--project` und `--mr-iid` nicht übergeben — sie werden automatisch aus CI übernommen.

---

## Review-Ergebnis

### Notes (Kommentare)

AI Review postet Kommentare zum MR als Notes.

### Discussions (Inline)

Für Inline-Kommentare benötigen Sie einen vollständigen PAT-Token (nicht `CI_JOB_TOKEN`).

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

1. `GOOGLE_API_KEY`-Variable ist gesetzt
2. `GITLAB_TOKEN` hat ausreichende Berechtigungen (Scope: `api`)
3. Pipeline läuft für MR (nicht für einen Branch)

### "401 Unauthorized"

**Ursache:** Ungültiger Token.

**Lösung:**

- Überprüfen Sie, ob der Token nicht abgelaufen ist
- Überprüfen Sie den Scope (benötigt `api`)

### "403 Forbidden"

**Ursache:** Unzureichende Berechtigungen.

**Lösung:**

- Verwenden Sie PAT anstelle von `CI_JOB_TOKEN`
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

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # PAT, nicht CI_JOB_TOKEN
```

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
