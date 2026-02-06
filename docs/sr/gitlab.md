# GitLab

Detaljan vodič za integraciju sa GitLab CI.

---

## Tokeni {#tokens}

### CI_JOB_TOKEN (automatski)

U GitLab CI, `CI_JOB_TOKEN` je automatski dostupan:

```yaml
variables:
  GITLAB_TOKEN: $CI_JOB_TOKEN
```

**Ograničenja `CI_JOB_TOKEN`:**

| Funkcionalnost | Status |
|---------|--------|
| Čitanje MR | :white_check_mark: |
| Čitanje diff-a | :white_check_mark: |
| Objavljivanje bilješki | :white_check_mark: |
| Kreiranje diskusija | :x: |

!!! warning "Ograničene dozvole"
    `CI_JOB_TOKEN` ne može kreirati inline diskusije.

    Za punu funkcionalnost, koristite Personal Access Token.

### Personal Access Token (preporučeno) {#get-token}

Za **lokalno pokretanje** ili **punu funkcionalnost u CI-ju**, trebate Personal Access Token:

1. Idite na `User Settings → Access Tokens → Add new token`
2. Unesite ime tokena (npr. `ai-code-reviewer`)
3. Izaberite scope: **`api`**
4. Kliknite **Create personal access token**
5. Kopirajte token i sačuvajte ga kao `GITLAB_TOKEN`

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Iz CI/CD Variables
```

!!! warning "Sačuvajte token"
    GitLab prikazuje token **samo jednom**. Sačuvajte ga odmah.

!!! info "Personal Access Token vs Project Access Token"
    **Personal Access Token** (PAT) radi na **svim GitLab planovima**, uključujući Free.

    **Project Access Token** je dostupan samo na **GitLab Premium/Ultimate**.
    Ako ste na Free planu, koristite Personal Access Token.

---

## CI/CD varijable

### Dodavanje varijabli

`Settings → CI/CD → Variables → Add variable`

| Varijabla | Vrijednost | Opcije |
|----------|-------|---------|
| `GOOGLE_API_KEY` | Gemini API ključ | Masked |
| `GITLAB_TOKEN` | PAT (ako je potreban) | Masked |

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
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

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
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
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
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
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
| `CI_JOB_TOKEN` | Automatski token |

Ne morate proslijeđivati `--project` i `--mr-iid` — uzimaju se iz CI-ja automatski.

---

## Rezultat revizije

### Bilješke (komentari)

AI Review objavljuje komentare na MR kao bilješke.

### Diskusije (inline)

Za inline komentare, trebate pun PAT token (ne `CI_JOB_TOKEN`).

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

1. `GOOGLE_API_KEY` varijabla je podešena
2. `GITLAB_TOKEN` ima dovoljne dozvole (scope: `api`)
3. Pipeline se pokreće za MR (ne za granu)

### "401 Unauthorized"

**Uzrok:** Nevažeći token.

**Rješenje:**

- Provjerite da token nije istekao
- Provjerite scope (potreban `api`)

### "403 Forbidden"

**Uzrok:** Nedovoljne dozvole.

**Rješenje:**

- Koristite PAT umjesto `CI_JOB_TOKEN`
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

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # PAT, ne CI_JOB_TOKEN
```

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
