# Konfiguracija

Sva podešavanja se konfigurišu putem varijabli okruženja.

!!! tip "Migracija: prefiks `AI_REVIEWER_`"
    Od v1.0.0a7, sve varijable okruženja podržavaju prefiks `AI_REVIEWER_` (npr., `AI_REVIEWER_GOOGLE_API_KEY`). Stara imena (npr., `GOOGLE_API_KEY`) i dalje rade kao fallback. Preporučujemo migraciju na nova imena kako bi se izbjegli konflikti sa drugim alatima u CI/CD konfiguracijama na nivou organizacije.

---

## Obavezne varijable

| Varijabla | Opis | Primjer | Kako dobiti |
|----------|-------------|---------|------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Google Gemini API ključ (раздвојене зарезом за ротацију кључева) | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub PAT (za GitHub) | `ghp_...` | [Instrukcije](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab PAT (za GitLab) | `glpat-...` | [Instrukcije](gitlab.md#get-token) |

!!! warning "Potreban je barem jedan provajder"
    Trebate `AI_REVIEWER_GITHUB_TOKEN` **ili** `AI_REVIEWER_GITLAB_TOKEN` zavisno od platforme.
    Tokeni su specifični za provajdera: `AI_REVIEWER_GITHUB_TOKEN` je potreban samo za GitHub, `AI_REVIEWER_GITLAB_TOKEN` samo za GitLab.

---

## Opcione varijable {#optional}

### Opšte

| Varijabla | Opis | Podrazumijevano | Opseg |
|----------|-------------|---------|-------|
| `AI_REVIEWER_LOG_LEVEL` | Nivo logovanja | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_REVIEWER_API_TIMEOUT` | Timeout zahtjeva (sek) | `60` | 1-300 |

### Jezik

| Varijabla | Opis | Podrazumijevano | Primjeri |
|----------|-------------|---------|----------|
| `AI_REVIEWER_LANGUAGE` | Jezik odgovora | `en` | `uk`, `de`, `es`, `it`, `me` |
| `AI_REVIEWER_LANGUAGE_MODE` | Režim detekcije | `adaptive` | `adaptive`, `fixed` |

**Jezički režimi:**

- **`adaptive`** (podrazumijevano) — automatski prepoznaje jezik iz konteksta PR/MR (opis, komentari, povezani zadatak)
- **`fixed`** — uvijek koristi jezik iz `AI_REVIEWER_LANGUAGE`

!!! tip "ISO 639"
    `AI_REVIEWER_LANGUAGE` prihvata bilo koji validan ISO 639 kod:

    - 2-slovna: `en`, `uk`, `de`, `es`, `it`
    - 3-slovna: `ukr`, `deu`, `spa`
    - Imena: `English`, `Ukrainian`, `German`

### LLM

| Varijabla | Opis | Podrazumijevano |
|----------|-------------|---------|
| `AI_REVIEWER_GEMINI_MODEL` | Gemini model | `gemini-2.5-flash` |
| `AI_REVIEWER_GEMINI_MODEL_FALLBACK` | Lanac rezervnih modela (odvojenih zarezima) | `gemini-3.1-flash-preview` |
| `AI_REVIEWER_REVIEW_SPLIT_THRESHOLD` | Prag karaktera za podijeljen pregled kod+testovi | `30000` |

**Dostupni modeli:**

| Model | Opis | Cena |
|-------|------|------|
| `gemini-2.5-flash` | Brz, stabilan, sa sposobnošću rasuđivanja (podrazumevano) | $0.075 / 1M ulaz |
| `gemini-3.1-flash-preview` | Frontier-klasa flash (pregled) | $0.075 / 1M ulaz |
| `gemini-2.5-flash-lite` | Najbrži i najjeftiniji u 2.5 | $0.01875 / 1M ulaz |
| `gemini-2.5-pro` | Najmoćniji, sa dubokim rasuđivanjem | $1.25 / 1M ulaz |

!!! note "Tačnost cijena"
    Cijene su navedene na datum izdanja i mogu se promijeniti.

    Aktuelne informacije: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Besplatni nivo"
    Obratite pažnju na **Free Tier** kada koristite određene modele.

    U ogromnoj većini slučajeva, besplatno ograničenje je dovoljno za reviziju koda tima od **4-8 programera**.

### Revizija

| Varijabla | Opis | Podrazumijevano | Opseg |
|----------|-------------|---------|-------|
| `AI_REVIEWER_REVIEW_MAX_FILES` | Maksimalno fajlova u kontekstu | `20` | 1-100 |
| `AI_REVIEWER_REVIEW_MAX_DIFF_LINES` | Maksimalno linija diff-a po fajlu | `500` | 1-5000 |
| `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS` | Maks. karaktera komentara MR u promptu | `3000` | 0-20000 |
| `AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS` | Uključi bot komentare u prompt | `true` | true/false |
| `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS` | Postavljanje inline komentara na linije | `true` | true/false |
| `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE` | Grupisanje komentara u dijalog niti | `true` | true/false |

!!! info "Kontekst diskusije"
    AI revizor čita postojeće komentare MR/PR kako ne bi ponavljao prijedloge
    koji su već razmatrani. Postavite `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS=0` za deaktivaciju.

!!! info "Inline komentari"
    Kada je `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS=true` (podrazumijevano), issue-i sa informacijama o fajlu/liniji se postavljaju kao inline komentari na kodu, sa kratkim sažetkom kao tijelom revizije. Postavite na `false` za jedan sažetak komentar.

!!! info "Dijalog niti"
    Kada je `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE=true` (podrazumijevano), komentari se grupišu u
    konverzacijske niti kako bi AI razumio lance odgovora. Postavite na `false` za ravno prikazivanje.

### Discovery

| Varijabla | Opis | Podrazumijevano | Opseg |
|----------|-------------|---------|-------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | Aktiviranje analize projekta prije pregleda | `true` | true/false |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | Uvijek objaviti discovery komentar (podrazumijevano: samo pri prazninama) | `false` | true/false |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | Timeout discovery pipeline-a u sekundama | `30` | 1-300 |

!!! info "Analiza projekta"
    Kada je aktivirano, AI ReviewBot automatski analizira vaš repozitorijum (jezici, CI pipeline, config fajlovi) prije svakog pregleda za pametniji feedback. Postavite na `false` za deaktivaciju. Detalji: [Discovery →](discovery.md).

!!! info "Verbose režim"
    Kada je `AI_REVIEWER_DISCOVERY_VERBOSE=true`, discovery komentar se uvijek objavljuje i uključuje sve Attention Zones (Well Covered, Weakly Covered, Not Covered). Podrazumijevani režim objavljuje samo kada postoje praznine ili nepokrivene zone.

### GitLab

| Varijabla | Opis | Podrazumijevano |
|----------|-------------|---------|
| `AI_REVIEWER_GITLAB_URL` | URL GitLab servera | `https://gitlab.com` |

!!! info "Self-hosted GitLab"
    Za self-hosted GitLab, podesite `AI_REVIEWER_GITLAB_URL`:
    ```bash
    export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## .env fajl

Praktično je čuvati konfiguraciju u `.env`:

```bash
# .env
AI_REVIEWER_GOOGLE_API_KEY=AIza...
AI_REVIEWER_GITHUB_TOKEN=ghp_...

# Opciono
AI_REVIEWER_LANGUAGE=uk
AI_REVIEWER_LANGUAGE_MODE=adaptive
AI_REVIEWER_GEMINI_MODEL=gemini-2.5-flash
AI_REVIEWER_LOG_LEVEL=INFO
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
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
  AI_REVIEWER_GITHUB_TOKEN: ${{ github.token }}  # Automatski
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  AI_REVIEWER_GOOGLE_API_KEY: $AI_REVIEWER_GOOGLE_API_KEY  # Iz CI/CD Variables
  AI_REVIEWER_GITLAB_TOKEN: $AI_REVIEWER_GITLAB_TOKEN      # Project Access Token
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

---

## Validacija

AI Code Reviewer validira konfiguraciju pri pokretanju:

### Greške validacije

```
ValidationError: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Rješenje:** Provjerite da je varijabla ispravno podešena.

```
ValidationError: Invalid language code 'xyz'
```

**Rješenje:** Koristite validan ISO 639 kod.

```
ValidationError: AI_REVIEWER_LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Rješenje:** Koristite jedan od dozvoljenih nivoa.

---

## Primjeri konfiguracije

### Minimalna (GitHub)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
```

### Minimalna (GitLab)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
```

### Ukrajinski jezik, fiksiran

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LANGUAGE=uk
export AI_REVIEWER_LANGUAGE_MODE=fixed
```

### Self-hosted GitLab

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
```

### Debug režim

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LOG_LEVEL=DEBUG
```

---

## Prioritet konfiguracije

1. **Varijable okruženja** (najviši)
2. **`.env` fajl** u tekućem direktorijumu

---

## Sljedeći korak

- [GitHub integracija →](github.md)
- [GitLab integracija →](gitlab.md)
