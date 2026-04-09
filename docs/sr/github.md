# GitHub

Detaljan vodič za integraciju sa GitHub Actions.

---

## Dozvole

### Minimalne dozvole

```yaml
permissions:
  contents: read        # Čitanje koda
  pull-requests: write  # Objavljivanje komentara
```

### GITHUB_TOKEN u Actions

U GitHub Actions, `GITHUB_TOKEN` je automatski dostupan:

```yaml
env:
  GITHUB_TOKEN: ${{ github.token }}
```

**Automatske dozvole tokena:**

| Dozvola | Status | Napomena |
|------------|--------|------|
| `contents: read` | :white_check_mark: | Podrazumijevano |
| `pull-requests: write` | :white_check_mark: | Mora se navesti u `permissions` |

!!! warning "Fork PR-ovi"
    Za PR-ove iz fork repozitorijuma, `GITHUB_TOKEN` ima **samo-čitanje** dozvole.

    AI Review ne može objavljivati komentare za fork PR-ove.

### Kako dobiti Personal Access Token {#get-token}

Za **lokalno pokretanje**, trebate Personal Access Token (PAT):

1. Idite na `Settings → Developer settings → Personal access tokens`
2. Izaberite **Fine-grained tokens** (preporučeno) ili Classic
3. Kliknite **Generate new token**

**Fine-grained token (preporučeno):**

| Podešavanje | Vrijednost |
|---------|-------|
| Repository access | Only select repositories → vaš repozitorijum |
| Permissions | `Pull requests: Read and write` |

**Classic token:**

| Scope | Opis |
|-------|-------------|
| `repo` | Pun pristup repozitorijumu |

4. Kliknite **Generate token**
5. Kopirajte token i sačuvajte ga kao `GITHUB_TOKEN`

!!! warning "Sačuvajte token"
    GitHub prikazuje token **samo jednom**. Sačuvajte ga odmah.

---

## Triggeri

### Preporučeni trigger

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

| Tip | Kada se aktivira |
|------|-----------------|
| `opened` | PR kreiran |
| `synchronize` | Novi commitovi u PR-u |
| `reopened` | PR ponovo otvoren |

### Filtriranje fajlova

Pokrenite reviziju samo za određene fajlove:

```yaml
on:
  pull_request:
    paths:
      - '**.py'
      - '**.js'
      - '**.ts'
```

### Filtriranje grana

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

---

## Tajne

### Dodavanje tajni

`Settings → Secrets and variables → Actions → New repository secret`

| Tajna | Obavezna | Opis |
|--------|----------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | :white_check_mark: | Gemini API ključ |

### Upotreba

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
```

!!! danger "Nikada ne hardkodujte tajne"
    ```yaml
    # ❌ POGREŠNO
    env:
      AI_REVIEWER_GOOGLE_API_KEY: AIza...

    # ✅ ISPRAVNO
    env:
      AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    ```

---

## Primjeri workflow-a

### Minimalni

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
```

!!! info "O `GITHUB_TOKEN`"
    `secrets.GITHUB_TOKEN` je **automatski token** koji GitHub kreira za svako pokretanje workflow-a. **Ne trebate** ga ručno dodavati u tajne — već je dostupan.

    Dozvole tokena se definišu sekcijom `permissions` u workflow fajlu.

    :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

### Sa konkurentnošću (preporučeno)

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
          language: uk
          language_mode: adaptive
```

**Šta radi konkurentnost:**

- Ako se novi commit push-uje dok revizija još traje — stara revizija se otkazuje
- Štedi resurse i API pozive

### Sa filterom fork PR-ova

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    # Ne pokreći za fork PR-ove (nema pristupa tajnama)
    if: github.event.pull_request.head.repo.full_name == github.repository
```

---

## GitHub Action inputi

| Input | Opis | Podrazumijevano |
|-------|-------------|---------|
| `google_api_key` | Gemini API ključ | **obavezno** |
| `github_token` | GitHub token | `${{ github.token }}` |
| `language` | Jezik odgovora | `en` |
| `language_mode` | Jezički režim | `adaptive` |
| `gemini_model` | Gemini model | `gemini-2.5-flash` |
| `log_level` | Nivo logova | `INFO` |
| `review_max_comment_chars` | Maks. znakova komentara MR-a u promptu | `3000` |
| `review_include_bot_comments` | Uključi komentare botova u prompt | `true` |
| `review_post_inline_comments` | Objavi inline komentare na linijama | `true` |
| `gemini_model_fallback` | Fallback model chain (comma-separated) | `gemini-3.1-flash-preview` |
| `review_enable_dialogue` | Grupisati komentare u dijaloge | `true` |
| `discovery_enabled` | Aktivirati project discovery | `true` |
| `discovery_verbose` | Uvijek objaviti discovery komentar | `false` |
| `discovery_timeout` | Tajmaut discovery-ja u sekundama | `30` |

!!! tip "Varijable okruženja"
    Action interno mapira inpute na `AI_REVIEWER_*` varijable okruženja. Kada pokrećete van Action-a, koristite `AI_REVIEWER_*` varijable direktno (stara imena poput `GOOGLE_API_KEY` i dalje rade kao fallback).

---

## Rezultat revizije

### Inline komentari

AI Review objavljuje komentare direktno na linijama koda:

- :red_circle: **CRITICAL** — kritični problemi (bezbjednost, bagovi)
- :yellow_circle: **WARNING** — preporuke
- :blue_circle: **INFO** — edukativne napomene

### Apply Suggestion

Svaki komentar sa prijedlogom koda ima dugme **"Apply suggestion"**:

```suggestion
fixed_code_here
```

GitHub automatski renderuje ovo kao interaktivno dugme.

### Rezime

Na kraju revizije, objavljuje se Rezime sa:

- Ukupnom statistikom problema
- Metrikama (vrijeme, tokeni, cijena)
- Dobrim praksama (pozitivne povratne informacije)

---

## Rješavanje problema

### Revizija ne objavljuje komentare

**Provjerite:**

1. `permissions: pull-requests: write` je u workflow-u
2. `AI_REVIEWER_GOOGLE_API_KEY` tajna je podešena
3. PR nije iz fork repozitorijuma

### "Resource not accessible by integration"

**Uzrok:** Nedovoljne dozvole.

**Rješenje:** Dodajte dozvole:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### Rate Limit od Gemini

**Uzrok:** Prekoračeno ograničenje besplatnog nivoa (15 RPM).

**Rješenje:**

- Sačekajte minut
- Dodajte `concurrency` da otkažete stare pokretanja
- Razmislite o plaćenom nivou

---

## Najbolje prakse

### 1. Uvijek koristite konkurentnost

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### 2. Filtrirajte fork PR-ove

```yaml
if: github.event.pull_request.head.repo.full_name == github.repository
```

### 3. Podesite timeout

```yaml
jobs:
  review:
    timeout-minutes: 10
```

### 4. Učinite job neblokirajućim

```yaml
jobs:
  review:
    continue-on-error: true
```

---

## Sljedeći korak

- [GitLab integracija →](gitlab.md)
- [CLI referenca →](api.md)
