# Konfiguracija

Sva podešavanja se konfigurišu putem varijabli okruženja.

---

## Obavezne varijable

| Varijabla | Opis | Primjer | Kako dobiti |
|----------|-------------|---------|------------|
| `GOOGLE_API_KEY` | Google Gemini API ključ | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub PAT (za GitHub) | `ghp_...` | [Instrukcije](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab PAT (za GitLab) | `glpat-...` | [Instrukcije](gitlab.md#get-token) |

!!! warning "Potreban je barem jedan provajder"
    Trebate `GITHUB_TOKEN` **ili** `GITLAB_TOKEN` zavisno od platforme.
    Tokeni su specifični za provajdera: `GITHUB_TOKEN` je potreban samo za GitHub, `GITLAB_TOKEN` samo za GitLab.

---

## Opcione varijable {#optional}

### Opšte

| Varijabla | Opis | Podrazumijevano | Opseg |
|----------|-------------|---------|-------|
| `LOG_LEVEL` | Nivo logovanja | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `API_TIMEOUT` | Timeout zahtjeva (sek) | `60` | 1-300 |

### Jezik

| Varijabla | Opis | Podrazumijevano | Primjeri |
|----------|-------------|---------|----------|
| `LANGUAGE` | Jezik odgovora | `en` | `uk`, `de`, `es`, `it`, `me` |
| `LANGUAGE_MODE` | Režim detekcije | `adaptive` | `adaptive`, `fixed` |

**Jezički režimi:**

- **`adaptive`** (podrazumijevano) — automatski prepoznaje jezik iz konteksta PR/MR (opis, komentari, povezani zadatak)
- **`fixed`** — uvijek koristi jezik iz `LANGUAGE`

!!! tip "ISO 639"
    `LANGUAGE` prihvata bilo koji validan ISO 639 kod:

    - 2-slovna: `en`, `uk`, `de`, `es`, `it`
    - 3-slovna: `ukr`, `deu`, `spa`
    - Imena: `English`, `Ukrainian`, `German`

### LLM

| Varijabla | Opis | Podrazumijevano |
|----------|-------------|---------|
| `GEMINI_MODEL` | Gemini model | `gemini-2.5-flash` |

**Dostupni modeli:**

| Model | Opis | Cijena |
|-------|-------------|------|
| `gemini-2.5-flash` | Brz, jeftin | $0.075 / 1M ulaz |
| `gemini-2.0-flash` | Prethodna verzija | $0.075 / 1M ulaz |
| `gemini-1.5-pro` | Moćniji | $1.25 / 1M ulaz |

!!! note "Tačnost cijena"
    Cijene su navedene na datum izdanja i mogu se promijeniti.

    Aktuelne informacije: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Besplatni nivo"
    Obratite pažnju na **Free Tier** kada koristite određene modele.

    U ogromnoj većini slučajeva, besplatno ograničenje je dovoljno za reviziju koda tima od **4-8 programera**.

### Revizija

| Varijabla | Opis | Podrazumijevano | Opseg |
|----------|-------------|---------|-------|
| `REVIEW_MAX_FILES` | Maksimalno fajlova u kontekstu | `20` | 1-100 |
| `REVIEW_MAX_DIFF_LINES` | Maksimalno linija diff-a po fajlu | `500` | 1-5000 |

### GitLab

| Varijabla | Opis | Podrazumijevano |
|----------|-------------|---------|
| `GITLAB_URL` | URL GitLab servera | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    Za self-hosted GitLab, podesite `GITLAB_URL`:
    ```bash
    export GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## .env fajl

Praktično je čuvati konfiguraciju u `.env`:

```bash
# .env
GOOGLE_API_KEY=AIza...
GITHUB_TOKEN=ghp_...

# Opciono
LANGUAGE=uk
LANGUAGE_MODE=adaptive
GEMINI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
```

!!! danger "Bezbjednost"
    **Nikada ne komitujte `.env` u git!**

    Dodajte u `.gitignore`:
    ```
    .env
    .env.*
    ```

---

## CI/CD konfiguracija

### GitHub Actions

```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GITHUB_TOKEN: ${{ github.token }}  # Automatski
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  GOOGLE_API_KEY: $GOOGLE_API_KEY  # Iz CI/CD Variables
  # GITLAB_TOKEN: $CI_JOB_TOKEN   # Automatski (ograničen)
  GITLAB_TOKEN: $GITLAB_TOKEN      # Ili PAT za pune dozvole
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

---

## Validacija

AI Code Reviewer validira konfiguraciju pri pokretanju:

### Greške validacije

```
ValidationError: GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Rješenje:** Provjerite da je varijabla ispravno podešena.

```
ValidationError: Invalid language code 'xyz'
```

**Rješenje:** Koristite validan ISO 639 kod.

```
ValidationError: LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Rješenje:** Koristite jedan od dozvoljenih nivoa.

---

## Primjeri konfiguracije

### Minimalna (GitHub)

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
```

### Minimalna (GitLab)

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
```

### Ukrajinski jezik, fiksiran

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

### Debug režim

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LOG_LEVEL=DEBUG
```

---

## Prioritet konfiguracije

1. **Varijable okruženja** (najviši)
2. **`.env` fajl** u tekućem direktorijumu

---

## Sljedeći korak

- [GitHub integracija →](github.md)
- [GitLab integracija →](gitlab.md)
