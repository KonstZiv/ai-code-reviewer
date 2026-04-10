# GitLab

Detaljan vodič za integraciju sa GitLab CI.

---

## Tokeni {#tokens}

### Personal Access Token (PAT) {#get-token}

**Preporučeno za sve GitLab planove** (uključujući Free).

!!! danger "`CI_JOB_TOKEN` ne radi"
    GitLab-ov automatski `CI_JOB_TOKEN` **ne može postavljati komentare** na Merge Request-e
    (Notes API zahtijeva `api` scope, koji `CI_JOB_TOKEN` nema).
    **Morate** koristiti Personal Access Token ili Project Access Token.

**Kako kreirati:**

1. Idite na **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Popunite polja:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** podesite prema potrebi (npr. 1 godina)
    - **Scopes:** označite **`api`**
3. Kliknite **Create personal access token**
4. **Kopirajte token odmah** — GitLab ga prikazuje samo jednom!

**Kako koristiti u CI-ju:**

1. Idite na **Settings → CI/CD → Variables → Add variable**
2. Dodajte varijablu:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN`
    - **Value:** nalijepite vaš token
    - **Flags:** označite **Masked**, :x: **odznačite** Protected

    Varijabla je automatski dostupna svim job-ovima — nije potreban YAML `variables:` mapping.

!!! warning "Odznačite «Protected»!"
    Podrazumijevano, GitLab označava nove varijable kao **Protected**. Protected varijable su **dostupne samo u zaštićenim granama** (npr. `main`).

    MR pipeline-i se pokreću na **nezaštićenim** izvornim granama — varijabla će biti prazna i dobićete **401 Unauthorized**.

    **Uvijek odznačite «Protected»** za `AI_REVIEWER_GITLAB_TOKEN` i `AI_REVIEWER_GOOGLE_API_KEY`.

!!! warning "Sačuvajte token"
    GitLab prikazuje token **samo jednom**. Sačuvajte ga odmah na sigurnom mjestu.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Dostupan samo na **GitLab Premium** i **Ultimate** planovima. Dobar izbor ako preferirate token ograničen na projekat umjesto ličnog.

**Prednosti u odnosu na PAT:**

- Ograničen na jedan projekat (nema pristupa drugim projektima)
- Može ga opozvati maintainer projekta (nema zavisnosti od konkretnog korisnika)
- Bolji za timove — nije vezan za lični nalog

**Kako kreirati:**

1. Idite na **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Popunite polja:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (minimalno potreban)
    - **Scopes:** označite **`api`**
3. Kliknite **Create project access token**
4. **Kopirajte token odmah**

**Kako koristiti u CI-ju:**

Isto kao PAT — dodajte kao `AI_REVIEWER_GITLAB_TOKEN` u CI/CD Variables:

1. **Key:** `AI_REVIEWER_GITLAB_TOKEN`
2. **Value:** nalijepite vaš Project Access Token

!!! info "Koji token odabrati?"
    | | Personal Access Token | Project Access Token |
    |---|---|---|
    | **Plan** | Svi (uključujući Free) | Samo Premium/Ultimate |
    | **Podešavanje** | Ručno | Ručno |
    | **Opseg** | Svi projekti korisnika | Jedan projekat |
    | **Inline komentari** | :white_check_mark: | :white_check_mark: |
    | **Najbolje za** | Free plan + pune funkcije | Timovi na Premium/Ultimate |

---

## CI/CD varijable

### Dodavanje varijabli

`Settings → CI/CD → Variables → Add variable`

| Varijabla | Vrijednost | Opcije |
|----------|-------|---------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API ključ | :white_check_mark: Masked, :x: **Uncheck** Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | Personal Access Token (scope: `api`) | :white_check_mark: Masked, :x: **Uncheck** Protected |

!!! tip "Masked"
    Uvijek omogućite **Masked** za tajne — neće se prikazivati u logovima.

---

## Triggeri

### Preporučeni trigger

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Ovo pokreće job samo za Merge Request pipeline-e.

### Alternativni trigger (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — novija sintaksa, preporučena od strane GitLab-a.

---

## Primjeri job-a

### Minimalni

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

CI/CD varijable `AI_REVIEWER_GOOGLE_API_KEY` i `AI_REVIEWER_GITLAB_TOKEN` se nasljeđuju automatski.

### Puni (preporučeno)

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

**Šta radi:**

- `allow_failure: true` — MR nije blokiran ako revizija ne uspije
- `timeout: 10m` — maksimalno 10 minuta
- `interruptible: true` — može se otkazati na novi commit

### Sa prilagođenom fazom

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
  needs: []  # Ne čeka prethodne faze
```

---

## Self-hosted GitLab

### Konfiguracija

```yaml
variables:
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
```

### Docker registar

Ako vaš GitLab nema pristup `ghcr.io`, kreirajte mirror:

```bash
# Na mašini sa pristupom
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

## GitLab CI varijable

AI Code Reviewer automatski koristi:

| Varijabla | Opis |
|----------|-------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | Broj MR-a |
| `CI_SERVER_URL` | GitLab URL |

Ne morate proslijeđivati `--repo` i `--pr` — uzimaju se iz CI-ja automatski.

---

## Konfiguracija putem CI/CD varijabli {#variable-driven}

Koristite **CI/CD Variables** za prebacivanje između LLM provajdera i modela bez mijenjanja `.gitlab-ci.yml`. Ovo je korisno za poređenje kvaliteta revizije različitih modela na istom MR-u.

### Podešavanje

**CI/CD Variables** (`Settings → CI/CD → Variables`):

| Varijabla | Opis | Opcije |
|-----------|------|--------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API ključ | :white_check_mark: Masked, :x: Isključiti Protected |
| `AI_REVIEWER_MISTRAL_API_KEY` | Mistral API ključ | :white_check_mark: Masked, :x: Isključiti Protected |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab token | :white_check_mark: Masked, :x: Isključiti Protected |
| `AI_REVIEWER_LLM_PROVIDER` | Primarni provajder (`google`, `mistral`) | :x: Isključiti Protected |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Fallback provajder | :x: Isključiti Protected |
| `AI_REVIEWER_MISTRAL_MODEL` | Mistral model | :x: Isključiti Protected |
| `AI_REVIEWER_MISTRAL_API_URL` | Prilagođeni URL API-ja (za Codestral free tier) | :x: Isključiti Protected |

### Konfiguracija job-a

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

Sekcija `variables:` nije potrebna — sve `AI_REVIEWER_*` CI/CD varijable se nasljeđuju automatski.

### Prebacivanje preseta

Promijenite CI/CD Variables u GitLab interfejsu i kliknite **Retry** na pipeline istog MR-a:

| Preset | `AI_REVIEWER_LLM_PROVIDER` | `AI_REVIEWER_MISTRAL_MODEL` | `AI_REVIEWER_MISTRAL_API_URL` | `AI_REVIEWER_LLM_FALLBACK_PROVIDER` |
|--------|---------------------------|---------------------------|-------------------------------|-------------------------------------|
| Gemini (podrazumijevano) | `google` | _(prazno)_ | _(prazno)_ | _(prazno)_ |
| Mistral Large | `mistral` | `mistral-large-latest` | _(prazno)_ | `google` |
| Codestral free | `mistral` | `codestral-latest` | `https://codestral.mistral.ai` | `google` |
| Devstral | `mistral` | `devstral-latest` | _(prazno)_ | `google` |

!!! tip "Codestral free tier ključ"
    Za preset „Codestral free" `AI_REVIEWER_MISTRAL_API_KEY` mora sadržavati ključ sa [codestral.mistral.ai](https://codestral.mistral.ai/), ne sa `console.mistral.ai`.

!!! info "Nije potrebno unositi u YAML"
    Za razliku od GitHub Actions (gdje se inputi moraju eksplicitno mapirati), GitLab CI automatski prosljeđuje sve CI/CD varijable kao varijable okruženja. Samo ih postavite u interfejsu — aplikacija ih prepoznaje preko prefiksa `AI_REVIEWER_*`.

---

## Rezultat revizije

### Bilješke (komentari)

AI Review objavljuje komentare na MR kao bilješke.

### Diskusije (inline)

Za inline komentare, trebate Personal Access Token ili Project Access Token.

Inline komentari se pojavljuju direktno pored linija koda u diff pogledu.

### Rezime

Na kraju revizije, objavljuje se bilješka Rezime sa:

- Ukupnom statistikom
- Metrikama
- Dobrim praksama

---

## Rješavanje problema

### Revizija ne objavljuje komentare

**Provjerite:**

1. `AI_REVIEWER_GOOGLE_API_KEY` varijabla je podešena
2. `AI_REVIEWER_GITLAB_TOKEN` ima dovoljne dozvole (scope: `api`)
3. Pipeline se pokreće za MR (ne za granu)

### "401 Unauthorized"

**Uzrok:** Nevažeći token.

**Rješenje:**

- Provjerite da token nije istekao
- Provjerite scope (potreban `api`)

### "403 Forbidden"

**Uzrok:** Nedovoljne dozvole.

**Rješenje:**

- Provjerite da koristite Personal Access Token (ne `CI_JOB_TOKEN`)
- Provjerite da token ima pristup projektu

### "404 Not Found"

**Uzrok:** MR nije pronađen.

**Rješenje:**

- Provjerite da se pipeline pokreće za MR
- Provjerite `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Uzrok:** Prekoračeno API ograničenje.

**Rješenje:**

- AI Code Reviewer automatski ponavlja sa eksponencijalnim backoff-om
- Ako se nastavi — sačekajte ili povećajte ograničenja

---

## Najbolje prakse

### 1. Koristite PAT za punu funkcionalnost

### 2. Dodajte allow_failure

```yaml
allow_failure: true
```

MR neće biti blokiran ako revizija ne uspije.

### 3. Podesite timeout

```yaml
timeout: 10m
```

### 4. Učinite job prekidivim

```yaml
interruptible: true
```

Stara revizija će se otkazati na novi commit.

### 5. Ne čekajte druge faze

```yaml
needs: []
```

Revizija će početi odmah, bez čekanja na build/test.

---

## Sljedeći korak

- [GitHub integracija →](github.md)
- [CLI referenca →](api.md)
