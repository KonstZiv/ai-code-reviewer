# Brzi početak

Pokrenite AI Code Reviewer za 5 minuta na GitHub-u ili GitLab-u.

---

## Korak 1: Izaberite LLM provajdera i preuzmite API ključ

AI Reviewer podržava više LLM provajdera. Izaberite jednog (ili koristite oba za fallback):

=== "Google Gemini (podrazumijevano)"

    1. Idite na [Google AI Studio](https://aistudio.google.com/)
    2. Prijavite se sa Google nalogom
    3. Kliknite **"Get API key"** → **"Create API key"**
    4. Kopirajte ključ (počinje sa `AIza...`)

    !!! tip "Besplatni nivo"
        Gemini API ima besplatni nivo: 15 zahtjeva po minuti, dovoljno za većinu timova od 4-8 programera.

=== "Mistral AI"

    1. Idite na [Mistral Console](https://console.mistral.ai/)
    2. Registrujte se ili se prijavite
    3. Idite na **API Keys** → **Create new key**
    4. Kopirajte ključ (počinje sa `sk-...`)

    !!! tip "Besplatni nivo"
        Mistral nudi besplatni nivo za eksperimentisanje. Nakon registracije, dobijate besplatne API kredite za isprobavanje svih modela. Provjerite [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing) za aktuelna ograničenja.

    !!! tip "Besplatni Codestral"
        Codestral (model specijalizovan za kod) ima vlastiti besplatni nivo sa **odvojenim endpoint-om i ključem**:

        1. Idite na [codestral.mistral.ai](https://codestral.mistral.ai/)
        2. Generišite Codestral API ključ
        3. Postavite `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai`
        4. Postavite `AI_REVIEWER_MISTRAL_MODEL=codestral-latest`

        Ovaj ključ radi **samo** sa `codestral-latest` na Codestral endpoint-u.

=== "Oba (Mistral primarni + Google fallback)"

    Preuzmite **oba ključa** koristeći gornja uputstva. Ovo vam daje:

    - Mistral kao primarni model (npr. `mistral-large-latest`)
    - Google Gemini kao automatski fallback ako Mistral nije dostupan

    Ovo je najpouzdanija konfiguracija za produkcijsku upotrebu.

!!! warning "Sačuvajte ključ"
    API ključevi se prikazuju samo jednom. Sačuvajte ih na bezbjednom mjestu.

---

## Korak 2: Dodajte tajne u repozitorijum

=== "GitHub"

    **Putanja:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    === "Samo Google"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Vaš Gemini ključ (`AIza...`) |

    === "Samo Mistral"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Vaš Mistral ključ (`sk-...`) |

    === "Oba provajdera"

        | Name | Value |
        |------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Vaš Mistral ključ (`sk-...`) |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Vaš Gemini ključ (`AIza...`) |

    Kliknite **"Add secret"** za svaki.

    ??? info "Detaljna uputstva sa snimcima ekrana"
        1. Otvorite vaš repozitorijum na GitHub-u
        2. Kliknite **Settings** (zupčanik u gornjem meniju)
        3. U lijevom meniju pronađite **Secrets and variables** → **Actions**
        4. Kliknite zeleno dugme **New repository secret**
        5. Unesite ime i zalijepite ključ
        6. Kliknite **Add secret**
        7. Ponovite za svaku tajnu

    :material-book-open-variant: [Zvanična dokumentacija GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Za GitLab trebate kreirati **GitLab token** za postavljanje komentara.

    ### Korak 2a: Kreirajte GitLab token

    === "Personal Access Token (Svi planovi, uključujući Free)"

        **Putanja:** Korisnički avatar → `Edit profile` → `Access Tokens`

        | Polje | Vrijednost |
        |------|----------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Izaberite datum (maks. 1 godina) |
        | **Scopes** | :white_check_mark: `api` |

        Kliknite **"Create personal access token"** → **Kopirajte token** (prikazuje se samo jednom!)

        !!! warning "Komentari će se pojavljivati pod vašim korisničkim imenom"
            Personal Access Token je vezan za vaš nalog. Svi komentari revizije biće objavljeni u vaše ime.

        :material-book-open-variant: [GitLab Docs: Personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

    === "Project Access Token (Premium/Ultimate)"

        !!! note "Potrebna Maintainer prava"
            Za kreiranje Project Access Token-a potrebna je uloga **Maintainer** ili **Owner** u projektu.

            :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

        **Putanja:** Project → `Settings` → `Access Tokens`

        | Polje | Vrijednost |
        |------|----------|
        | **Token name** | `ai-reviewer` |
        | **Expiration date** | Izaberite datum (maks. 1 godina) |
        | **Role** | `Developer` |
        | **Scopes** | :white_check_mark: `api` |

        Kliknite **"Create project access token"** → **Kopirajte token** (prikazuje se samo jednom!)

        :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Korak 2b: Dodajte varijable u CI/CD

    **Putanja:** Project → `Settings` → `CI/CD` → `Variables`

    === "Samo Google"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_GOOGLE_API_KEY` | Vaš Gemini ključ | :white_check_mark: Mask, :x: Odznačite Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token iz koraka 2a | :white_check_mark: Mask, :x: Odznačite Protected |

    === "Samo Mistral"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Vaš Mistral ključ | :white_check_mark: Mask, :x: Odznačite Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token iz koraka 2a | :white_check_mark: Mask, :x: Odznačite Protected |

    === "Oba provajdera"

        | Key | Value | Flags |
        |-----|-------|-------|
        | `AI_REVIEWER_MISTRAL_API_KEY` | Vaš Mistral ključ | :white_check_mark: Mask, :x: Odznačite Protected |
        | `AI_REVIEWER_GOOGLE_API_KEY` | Vaš Gemini ključ | :white_check_mark: Mask, :x: Odznačite Protected |
        | `AI_REVIEWER_GITLAB_TOKEN` | Token iz koraka 2a | :white_check_mark: Mask, :x: Odznačite Protected |

    !!! warning "Odznačite «Protected»!"
        Podrazumijevano, GitLab označava nove varijable kao **Protected**. Protected varijable su **dostupne samo u zaštićenim granama** (npr. `main`), ali MR pipeline-i se pokreću na **nezaštićenim** izvornim granama — varijabla će biti prazna i dobićete **401 Unauthorized**.

    !!! danger "`CI_JOB_TOKEN` ne radi"
        GitLab-ov automatski `CI_JOB_TOKEN` **ne može postavljati komentare** na Merge Request-e.
        **Morate** kreirati Personal Access Token (ili Project Access Token na Premium+).

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Korak 3: Dodajte AI Review u CI {#ci-setup}

=== "GitHub"

    Kreirajte fajl `.github/workflows/ai-review.yml`:

    === "Samo Google"

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

    === "Samo Mistral"

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

    === "Oba (Mistral primarni)"

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

        !!! note "Codestral ključ"
            Koristite ključ sa [codestral.mistral.ai](https://codestral.mistral.ai/), ne obični Mistral API ključ.

    !!! info "O `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` je **automatski token** koji GitHub kreira za svako pokretanje workflow-a. **Ne treba** ga dodavati u tajne ručno — već je dostupan.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

=== "GitLab"

    Kreirajte ili ažurirajte `.gitlab-ci.yml`:

    === "Samo Google"

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

        CI/CD varijable `AI_REVIEWER_GOOGLE_API_KEY` i `AI_REVIEWER_GITLAB_TOKEN` iz Koraka 2b se nasljeđuju automatski.

    === "Samo Mistral"

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

        CI/CD varijable `AI_REVIEWER_MISTRAL_API_KEY` i `AI_REVIEWER_GITLAB_TOKEN` iz Koraka 2b se nasljeđuju automatski.

    === "Oba (Mistral primarni)"

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

        Sve tri CI/CD varijable (`AI_REVIEWER_MISTRAL_API_KEY`, `AI_REVIEWER_GOOGLE_API_KEY`, `AI_REVIEWER_GITLAB_TOKEN`) iz Koraka 2b se nasljeđuju automatski.

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

        CI/CD varijable `AI_REVIEWER_MISTRAL_API_KEY` (koristite Codestral ključ) i `AI_REVIEWER_GITLAB_TOKEN` iz Koraka 2b su automatski dostupne.

---

## Korak 4: Provjerite rezultat

Sada će se AI Review pokretati automatski pri:

| Platforma | Događaj |
|-----------|---------|
| **GitHub** | Kreiranje PR-a, novi komiti u PR-u, ponovno otvaranje PR-a |
| **GitLab** | Kreiranje MR-a, novi komiti u MR-u |

### Šta ćete vidjeti

Nakon završetka CI job-a, u PR/MR će se pojaviti:

- **Inline komentari** — povezani sa specifičnim linijama koda
- **Dugme "Apply suggestion"** — za brzu primjenu ispravki (GitHub)
- **Summary komentar** — opšti pregled sa metrikama

Svaki komentar sadrži:

- :red_circle: / :yellow_circle: / :blue_circle: Oznaku ozbiljnosti
- Opis problema
- Prijedlog ispravke
- Sklopivi odjeljak "Zašto je ovo važno?"

Footer prikazuje koji model i provajder je korišćen:

> _Model: Google / gemini-2.5-flash | Tokens: 1,234 | Latency: 2.3s | Est. cost: $0.0012_

---

## Rješavanje problema

### Revizija se ne pojavljuje?

Provjerite listu:

- [ ] Da li je API ključ dodat kao tajna? (`AI_REVIEWER_GOOGLE_API_KEY` ili `AI_REVIEWER_MISTRAL_API_KEY`)
- [ ] Da li je `llm_provider` ispravno podešen ako koristite Mistral? (podrazumijevano je `google`)
- [ ] `github_token` eksplicitno proslijeđen? (za GitHub)
- [ ] Za GitLab: da li je `AI_REVIEWER_GITLAB_TOKEN` podešen na Personal Access Token?
- [ ] CI job završen uspješno? (provjerite logove)
- [ ] Za GitHub: ima li `permissions: pull-requests: write`?
- [ ] Za fork PR-ove: tajne nijesu dostupne — ovo je očekivano ponašanje

### Rate limit?

- **Gemini** besplatni nivo: 15 zahtjeva po minuti
- **Mistral** besplatni nivo: provjerite [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing) za aktuelna ograničenja

Sačekajte minut i pokušajte ponovo, ili konfigurišite [fallback provajder](configuration.md#llm).

:point_right: [Svi problemi i rješenja →](troubleshooting.md)

---

## Šta dalje?

| Zadatak | Dokument |
|--------|----------|
| Konfigurišite jezik odgovora | [Konfiguracija](configuration.md) |
| Napredna podešavanja LLM provajdera | [Konfiguracija → LLM](configuration.md#llm) |
| Napredna podešavanja GitHub | [GitHub vodič](github.md) |
| Napredna podešavanja GitLab | [GitLab vodič](gitlab.md) |
| Primjeri workflow-a | [Primjeri](examples/index.md) |
