# Schnellstart

Starten Sie AI Code Reviewer in 5 Minuten auf GitHub oder GitLab.

---

## Schritt 1: LLM-Provider wählen und API-Schlüssel erhalten

AI Reviewer unterstützt mehrere LLM-Provider. Wählen Sie einen (oder verwenden Sie beide für Fallback):

=== "Google Gemini (Standard)"

    1. Gehen Sie zu [Google AI Studio](https://aistudio.google.com/)
    2. Melden Sie sich mit Ihrem Google-Konto an
    3. Klicken Sie auf **"Get API key"** → **"Create API key"**
    4. Kopieren Sie den Schlüssel (beginnt mit `AIza...`)

    !!! tip "Kostenlose Stufe"
        Gemini API hat eine kostenlose Stufe: 15 Anfragen pro Minute, ausreichend für die meisten Teams von 4-8 Entwicklern.

=== "Mistral AI"

    1. Gehen Sie zu [Mistral Console](https://console.mistral.ai/)
    2. Registrieren Sie sich oder melden Sie sich an
    3. Navigieren Sie zu **API Keys** → **Create new key**
    4. Kopieren Sie den Schlüssel (beginnt mit `sk-...`)

    !!! tip "Kostenlose Stufe"
        Mistral bietet eine kostenlose Stufe zum Experimentieren. Nach der Registrierung erhalten Sie kostenlose API-Credits, um alle Modelle auszuprobieren. Aktuelle Limits: [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing).

    !!! tip "Kostenloses Codestral"
        Codestral (ein code-spezialisiertes Modell) hat ein eigenes kostenloses Kontingent mit **separatem Endpoint und Schlüssel**:

        1. Gehen Sie zu [codestral.mistral.ai](https://codestral.mistral.ai/)
        2. Generieren Sie einen Codestral API-Schlüssel
        3. Setzen Sie `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai`
        4. Setzen Sie `AI_REVIEWER_MISTRAL_MODEL=codestral-latest`

        Dieser Schlüssel funktioniert **nur** mit `codestral-latest` am Codestral-Endpoint.

=== "Beide (Mistral primär + Google Fallback)"

    Holen Sie sich **beide Schlüssel** mit den Anleitungen oben. Das bietet Ihnen:

    - Mistral als primäres Modell (z.B. `mistral-large-latest`)
    - Google Gemini als automatisches Fallback, wenn Mistral nicht verfügbar ist

    Dies ist die zuverlässigste Konfiguration für den Produktionseinsatz.

!!! warning "Schlüssel speichern"
    API-Schlüssel werden nur einmal angezeigt. Speichern Sie sie an einem sicheren Ort.

---

## Schritt 2: Secrets zum Repository hinzufügen

=== "GitHub"

    **Pfad:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    === "Google only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ihr Gemini-Schlüssel (`AIza...`) |

    === "Mistral only"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ihr Mistral-Schlüssel (`sk-...`) |

    === "Beide Provider"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ihr Mistral-Schlüssel (`sk-...`) |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ihr Gemini-Schlüssel (`AIza...`) |

    Klicken Sie für jeden auf **"Add secret"**.

    ??? info "Detaillierte Anleitung mit Screenshots"
        1. Öffnen Sie Ihr Repository auf GitHub
        2. Klicken Sie auf **Settings** (Zahnrad im oberen Menü)
        3. Finden Sie im linken Menü **Secrets and variables** → **Actions**
        4. Klicken Sie auf die grüne Schaltfläche **New repository secret**
        5. Geben Sie den Namen ein und fügen Sie Ihren Schlüssel ein
        6. Klicken Sie auf **Add secret**
        7. Wiederholen Sie für jedes Secret

    :material-book-open-variant: [Offizielle GitHub-Dokumentation: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Für GitLab benötigen Sie zusätzlich einen **GitLab Token** zum Posten von Kommentaren.

    ### Schritt 2a: GitLab Token erstellen

    === "Personal Access Token (Alle Pläne, einschließlich Free)"

        **Pfad:** Benutzer-Avatar → `Edit profile` → `Access Tokens`

        | Feld | Wert |
        |------|------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Wählen Sie ein Datum (max. 1 Jahr) |
        | **Scopes** | :white_check_mark: `api` |

        Klicken Sie auf **"Create personal access token"** → **Kopieren Sie den Token** (wird nur einmal angezeigt!)

        !!! warning "Kommentare erscheinen unter Ihrem Benutzernamen"
            Ein Personal Access Token ist an Ihr Konto gebunden. Alle Review-Kommentare werden in Ihrem Namen gepostet.

        :material-book-open-variant: [GitLab Docs: Personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

    === "Project Access Token (Premium/Ultimate)"

        !!! note "Maintainer-Rechte erforderlich"
            Zum Erstellen eines Project Access Token benötigen Sie die Rolle **Maintainer** oder **Owner** im Projekt.

            :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

        **Pfad:** Project → `Settings` → `Access Tokens`

        | Feld | Wert |
        |------|------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Wählen Sie ein Datum (max. 1 Jahr) |
        | **Role** | `Developer` |
        | **Scopes** | :white_check_mark: `api` |

        Klicken Sie auf **"Create project access token"** → **Kopieren Sie den Token** (wird nur einmal angezeigt!)

        :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Schritt 2b: Variablen zu CI/CD hinzufügen

    **Pfad:** Project → `Settings` → `CI/CD` → `Variables`

    === "Google only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ihr Gemini-Schlüssel | :white_check_mark: Mask, :x: Protected deaktivieren |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token aus Schritt 2a | :white_check_mark: Mask, :x: Protected deaktivieren |

    === "Mistral only"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ihr Mistral-Schlüssel | :white_check_mark: Mask, :x: Protected deaktivieren |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token aus Schritt 2a | :white_check_mark: Mask, :x: Protected deaktivieren |

    === "Beide Provider"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Ihr Mistral-Schlüssel | :white_check_mark: Mask, :x: Protected deaktivieren |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Ihr Gemini-Schlüssel | :white_check_mark: Mask, :x: Protected deaktivieren |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token aus Schritt 2a | :white_check_mark: Mask, :x: Protected deaktivieren |

    !!! warning "«Protected» deaktivieren!"
        Standardmäßig markiert GitLab neue Variablen als **Protected**. Protected-Variablen sind **nur in geschützten Branches** verfügbar (z.B. `main`), aber MR-Pipelines laufen auf **ungeschützten** Source-Branches — die Variable ist dann leer und Sie erhalten **401 Unauthorized**.

    !!! danger "`CI_JOB_TOKEN` funktioniert nicht"
        Verwenden Sie **nicht** GitLabs automatischen `CI_JOB_TOKEN` — er kann keine Kommentare zu Merge Requests posten.
        Sie **müssen** einen Personal Access Token (oder Project Access Token bei Premium+) erstellen.

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Schritt 3: AI Review zu CI hinzufügen {#ci-setup}

=== "GitHub"

    Erstellen Sie die Datei `.github/workflows/ai-review.yml`:

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

    === "Beide (Mistral primär)"

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

    === "Codestral Free Tier"

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

        !!! note "Codestral-Schlüssel"
            Verwenden Sie den Schlüssel von [codestral.mistral.ai](https://codestral.mistral.ai/), nicht den regulären Mistral API-Schlüssel.

    !!! info "Über `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` ist ein **automatischer Token**, den GitHub für jeden Workflow-Run erstellt. Sie müssen ihn **nicht** manuell zu den Secrets hinzufügen — er ist bereits verfügbar.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

=== "GitLab"

    Erstellen oder aktualisieren Sie `.gitlab-ci.yml`:

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

        CI/CD-Variablen `AI_REVIEWER_GOOGLE_API_KEY` und `AI_REVIEWER_GITLAB_TOKEN` aus Schritt 2b werden automatisch vererbt.

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

        CI/CD-Variablen `AI_REVIEWER_MISTRAL_API_KEY` und `AI_REVIEWER_GITLAB_TOKEN` aus Schritt 2b werden automatisch vererbt.

    === "Beide (Mistral primär)"

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

        Alle drei CI/CD-Variablen (`AI_REVIEWER_MISTRAL_API_KEY`, `AI_REVIEWER_GOOGLE_API_KEY`, `AI_REVIEWER_GITLAB_TOKEN`) aus Schritt 2b werden automatisch vererbt.

    === "Codestral Free Tier"

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

        CI/CD-Variablen `AI_REVIEWER_MISTRAL_API_KEY` (Codestral-Schlüssel verwenden) und `AI_REVIEWER_GITLAB_TOKEN` aus Schritt 2b sind automatisch verfügbar.

---

## Schritt 4: Ergebnis überprüfen

Jetzt wird AI Review automatisch ausgeführt bei:

| Plattform | Ereignis |
|-----------|----------|
| **GitHub** | PR erstellen, neue Commits im PR, PR wiedereröffnen |
| **GitLab** | MR erstellen, neue Commits im MR |

### Was Sie sehen werden

Nach Abschluss des CI-Jobs erscheinen im PR/MR:

- **Inline-Kommentare** — an bestimmte Codezeilen gebunden
- **"Apply suggestion"-Button** — zum schnellen Anwenden von Korrekturen (GitHub)
- **Summary-Kommentar** — allgemeine Übersicht mit Metriken

Jeder Kommentar enthält:

- :red_circle: / :yellow_circle: / :blue_circle: Schweregrad-Badge
- Problembeschreibung
- Korrekturvorschlag
- Aufklappbaren Abschnitt "Warum ist das wichtig?"

In der Fußzeile wird angezeigt, welches Modell und welcher Provider verwendet wurde:

> _Model: Google / gemini-2.5-flash | Tokens: 1,234 | Latency: 2.3s | Est. cost: $0.0012_

---

## Fehlerbehebung

### Review erscheint nicht?

Checkliste überprüfen:

- [ ] API-Schlüssel als Secret hinzugefügt? (`AI_REVIEWER_GOOGLE_API_KEY` oder `AI_REVIEWER_MISTRAL_API_KEY`)
- [ ] `llm_provider` korrekt gesetzt, wenn Mistral verwendet wird? (Standard ist `google`)
- [ ] `github_token` explizit übergeben? (für GitHub)
- [ ] Für GitLab: `AI_REVIEWER_GITLAB_TOKEN` mit Personal Access Token gesetzt?
- [ ] CI-Job erfolgreich abgeschlossen? (Logs überprüfen)
- [ ] Für GitHub: hat `permissions: pull-requests: write`?
- [ ] Für Fork-PRs: Secrets sind nicht verfügbar — das ist erwartetes Verhalten

### Rate Limit?

- **Gemini** Free Tier: 15 Anfragen pro Minute
- **Mistral** Free Tier: aktuelle Limits unter [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing)

Warten Sie eine Minute und versuchen Sie es erneut, oder konfigurieren Sie einen [Fallback-Provider](configuration.md#llm).

:point_right: [Alle Probleme und Lösungen →](troubleshooting.md)

---

## Was kommt als Nächstes?

| Aufgabe | Dokument |
|---------|----------|
| Antwortsprache konfigurieren | [Konfiguration](configuration.md) |
| Erweiterte LLM-Provider-Einstellungen | [Konfiguration → LLM](configuration.md#llm) |
| Modelle ohne Codeänderung wechseln | [GitHub → Variable-gesteuerte Konfiguration](github.md#variable-driven) |
| Erweiterte GitHub-Einstellungen | [GitHub-Leitfaden](github.md) |
| Erweiterte GitLab-Einstellungen | [GitLab-Leitfaden](gitlab.md) |
| Workflow-Beispiele | [Beispiele](examples/index.md) |
