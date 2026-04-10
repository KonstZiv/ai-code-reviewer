# Quick Start

Configura AI Code Reviewer in 5 minuti su GitHub o GitLab.

---

## Passo 1: Scegli il Provider LLM e Ottieni una Chiave API

AI Reviewer supporta diversi provider LLM. Scegline uno (o usa entrambi per il fallback):

=== "Google Gemini (predefinito)"

    1. Vai su [Google AI Studio](https://aistudio.google.com/)
    2. Accedi con il tuo account Google
    3. Clicca **"Get API key"** → **"Create API key"**
    4. Copia la chiave (inizia con `AIza...`)

    !!! tip "Tier gratuito"
        L'API Gemini ha un tier gratuito: 15 richieste al minuto, sufficiente per la maggior parte dei team di 4-8 sviluppatori.

=== "Mistral AI"

    1. Vai su [Mistral Console](https://console.mistral.ai/)
    2. Registrati o accedi
    3. Vai su **API Keys** → **Create new key**
    4. Copia la chiave (inizia con `sk-...`)

    !!! tip "Tier gratuito"
        Mistral offre un tier gratuito per la sperimentazione. Dopo la registrazione, ricevi crediti API gratuiti per provare tutti i modelli. Controlla [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing) per i limiti attuali.

    !!! tip "Codestral gratuito"
        Codestral (un modello specializzato per il codice) ha un proprio livello gratuito con **endpoint e chiave separati**:

        1. Vai su [codestral.mistral.ai](https://codestral.mistral.ai/)
        2. Genera una chiave API Codestral
        3. Imposta `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai`
        4. Imposta `AI_REVIEWER_MISTRAL_MODEL=codestral-latest`

        Questa chiave funziona **solo** con `codestral-latest` sull'endpoint Codestral.

=== "Entrambi (Mistral primario + Google fallback)"

    Ottieni **entrambe le chiavi** seguendo le istruzioni qui sopra. Questo ti offre:

    - Mistral come modello primario (es. `mistral-large-latest`)
    - Google Gemini come fallback automatico se Mistral non e disponibile

    Questa e la configurazione piu affidabile per l'uso in produzione.

!!! warning "Salva la chiave"
    Le chiavi API vengono mostrate una sola volta. Salvale in un posto sicuro.

---

## Passo 2: Aggiungi i Secret nel Repository

=== "GitHub"

    **Percorso:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    === "Solo Google"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | La tua chiave Gemini (`AIza...`) |

    === "Solo Mistral"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | La tua chiave Mistral (`sk-...`) |

    === "Entrambi i provider"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | La tua chiave Mistral (`sk-...`) |
        | `AI_REVIEWER_GOOGLE_API_KEY` | La tua chiave Gemini (`AIza...`) |

    Clicca **"Add secret"** per ciascuno.

    ??? info "Istruzioni dettagliate con screenshot"
        1. Apri il tuo repository su GitHub
        2. Clicca **Settings** (ingranaggio nel menu superiore)
        3. Nel menu a sinistra trova **Secrets and variables** → **Actions**
        4. Clicca il pulsante verde **New repository secret**
        5. Inserisci il nome e incolla la chiave
        6. Clicca **Add secret**
        7. Ripeti per ogni secret

    :material-book-open-variant: [Documentazione ufficiale GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Per GitLab devi creare un **token GitLab** per pubblicare commenti.

    ### Passo 2a: Crea un token GitLab

    === "Personal Access Token (Tutti i piani, incluso Free)"

        **Percorso:** Avatar utente → `Edit profile` → `Access Tokens`

        | Campo | Valore |
        |-------|--------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Scegli una data (max 1 anno) |
        | **Scopes** | :white_check_mark: `api` |

        Clicca **"Create personal access token"** → **Copia il token** (viene mostrato una sola volta!)

        !!! warning "I commenti appariranno sotto il tuo nome utente"
            Un Personal Access Token e legato al tuo account. Tutti i commenti della revisione saranno pubblicati a tuo nome.

        :material-book-open-variant: [GitLab Docs: Personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

    === "Project Access Token (Premium/Ultimate)"

        !!! note "Servono i permessi Maintainer"
            Per creare un Project Access Token serve il ruolo **Maintainer** o **Owner** nel progetto.

            :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

        **Percorso:** Project → `Settings` → `Access Tokens`

        | Campo | Valore |
        |-------|--------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Scegli una data (max 1 anno) |
        | **Role** | `Developer` |
        | **Scopes** | :white_check_mark: `api` |

        Clicca **"Create project access token"** → **Copia il token** (viene mostrato una sola volta!)

        :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Passo 2b: Aggiungi le Variabili in CI/CD

    **Percorso:** Project → `Settings` → `CI/CD` → `Variables`

    === "Solo Google"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | La tua chiave Gemini | :white_check_mark: Mask, :x: Deseleziona Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token dal passo 2a | :white_check_mark: Mask, :x: Deseleziona Protected |

    === "Solo Mistral"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | La tua chiave Mistral | :white_check_mark: Mask, :x: Deseleziona Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token dal passo 2a | :white_check_mark: Mask, :x: Deseleziona Protected |

    === "Entrambi i provider"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | La tua chiave Mistral | :white_check_mark: Mask, :x: Deseleziona Protected |
        | `AI_REVIEWER_GOOGLE_API_KEY` | La tua chiave Gemini | :white_check_mark: Mask, :x: Deseleziona Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token dal passo 2a | :white_check_mark: Mask, :x: Deseleziona Protected |

    !!! warning "Deseleziona «Protected»!"
        Per impostazione predefinita, GitLab contrassegna le nuove variabili come **Protected**. Le variabili Protected sono **disponibili solo nei branch protetti** (es. `main`), ma le pipeline MR vengono eseguite su branch sorgente **non protetti** — la variabile sara vuota e otterrai **401 Unauthorized**.

    !!! danger "`CI_JOB_TOKEN` non funziona"
        Il `CI_JOB_TOKEN` automatico di GitLab **non puo pubblicare commenti** sulle Merge Request.
        **Devi** creare un Personal Access Token (o un Project Access Token su Premium+).

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Passo 3: Aggiungi AI Review nel CI {#ci-setup}

=== "GitHub"

    Crea il file `.github/workflows/ai-review.yml`:

    === "Solo Google"

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

    === "Solo Mistral"

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

    === "Entrambi (Mistral primario)"

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

        !!! note "Chiave Codestral"
            Usa la chiave da [codestral.mistral.ai](https://codestral.mistral.ai/), non la chiave API Mistral normale.

    !!! info "Info su `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` e un **token automatico** che GitHub crea per ogni workflow run. **Non serve** aggiungerlo manualmente ai secret — e gia disponibile.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

=== "GitLab"

    Crea o aggiorna `.gitlab-ci.yml`:

    === "Solo Google"

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

        Le variabili CI/CD `AI_REVIEWER_GOOGLE_API_KEY` e `AI_REVIEWER_GITLAB_TOKEN` dal Passo 2b vengono ereditate automaticamente.

    === "Solo Mistral"

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

        Le variabili CI/CD `AI_REVIEWER_MISTRAL_API_KEY` e `AI_REVIEWER_GITLAB_TOKEN` dal Passo 2b vengono ereditate automaticamente.

    === "Entrambi (Mistral primario)"

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

        Tutte e tre le variabili CI/CD (`AI_REVIEWER_MISTRAL_API_KEY`, `AI_REVIEWER_GOOGLE_API_KEY`, `AI_REVIEWER_GITLAB_TOKEN`) dal Passo 2b vengono ereditate automaticamente.

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

        Le variabili CI/CD `AI_REVIEWER_MISTRAL_API_KEY` (usa la chiave Codestral) e `AI_REVIEWER_GITLAB_TOKEN` dal Passo 2b sono disponibili automaticamente.

---

## Passo 4: Verifica il Risultato

Ora AI Review partira automaticamente quando:

| Piattaforma | Evento |
|-------------|--------|
| **GitHub** | Creazione PR, nuovi commit in PR, riapertura PR |
| **GitLab** | Creazione MR, nuovi commit in MR |

### Cosa Vedrai

Dopo il completamento del job CI, appariranno nel PR/MR:

- **Commenti inline** — collegati a righe specifiche di codice
- **Pulsante "Apply suggestion"** — per applicare rapidamente le correzioni (GitHub)
- **Commento summary** — panoramica generale con metriche

Ogni commento contiene:

- :red_circle: / :yellow_circle: / :blue_circle: Badge di gravita
- Descrizione del problema
- Suggerimento di correzione
- Sezione espandibile "Perche e importante?"

Il footer mostra quale modello e provider e stato utilizzato:

> _Model: Google / gemini-2.5-flash | Tokens: 1,234 | Latency: 2.3s | Est. cost: $0.0012_

---

## Troubleshooting

### La revisione non appare?

Controlla questa checklist:

- [ ] La chiave API e stata aggiunta come secret? (`AI_REVIEWER_GOOGLE_API_KEY` o `AI_REVIEWER_MISTRAL_API_KEY`)
- [ ] `llm_provider` e impostato correttamente se usi Mistral? (il predefinito e `google`)
- [ ] `github_token` passato esplicitamente? (per GitHub)
- [ ] Per GitLab: `AI_REVIEWER_GITLAB_TOKEN` e impostato su un Personal Access Token?
- [ ] Il job CI e terminato con successo? (controlla i log)
- [ ] Per GitHub: hai `permissions: pull-requests: write`?
- [ ] Per PR da fork: i secret non sono disponibili — comportamento previsto

### Rate limit?

- **Gemini** tier gratuito: 15 richieste al minuto
- **Mistral** tier gratuito: controlla [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing) per i limiti attuali

Aspetta un minuto e riprova, oppure configura un [provider di fallback](configuration.md#llm).

:point_right: [Tutti i problemi e soluzioni →](troubleshooting.md)

---

## Cosa Fare Dopo?

| Compito | Documento |
|---------|-----------|
| Configurare la lingua delle risposte | [Configurazione](configuration.md) |
| Impostazioni avanzate provider LLM | [Configurazione → LLM](configuration.md#llm) |
| Cambiare modelli senza modificare il codice | [GitHub → Configurazione tramite Variables](github.md#variable-driven) |
| Impostazioni avanzate GitHub | [Guida GitHub](github.md) |
| Impostazioni avanzate GitLab | [Guida GitLab](gitlab.md) |
| Esempi di workflow | [Esempi](examples/index.md) |
