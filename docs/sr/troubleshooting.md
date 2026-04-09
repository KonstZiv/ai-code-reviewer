# Rješavanje problema

FAQ i rješavanje uobičajenih problema.

---

## Uobičajeni problemi

### Action prikazuje --help umjesto izvršavanja

**Simptom:** U CI job logovima vidite:

```
Usage: ai-review [OPTIONS]
...
╭─ Options ─────────────────────────────────────────────────────────╮
│ --provider  -p      [github|gitlab]  CI provider...              │
```

**Uzrok:** Koristi se stara verzija Docker image-a (prije v1.0.0a2).

**Rješenje:**

Ažurirajte na najnoviju verziju:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1  # Uvijek koristi najnoviju v1.x
```

Ako problem i dalje postoji, eksplicitno navedite verziju:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1.0.0a2  # Ili novija
```

---

### Revizija se ne pojavljuje

**Simptom:** CI job je uspješno prošao, ali nema komentara.

**Provjerite:**

1. **Logove CI job-a** — ima li grešaka?
2. **API ključ** — je li `AI_REVIEWER_GOOGLE_API_KEY` validan?
3. **Token** — ima li dozvole za pisanje?
4. **github_token** — da li je eksplicitno proslijeđen?

=== "GitHub"

    ```yaml
    permissions:
      contents: read
      pull-requests: write  # ← Obavezno!
    ```

=== "GitLab"

    Provjerite da `GITLAB_TOKEN` ima scope `api`.

---

### "Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short"

**Uzrok:** Ključ nije podešen ili je neispravan.

**Rješenje:**

1. Provjerite da je tajna dodana u podešavanjima repozitorijuma
2. Provjerite ime (razlikuje velika i mala slova)
3. Provjerite da je ključ validan na [Google AI Studio](https://aistudio.google.com/)

---

### "401 Unauthorized" / "403 Forbidden"

**Uzrok:** Nevažeći ili nedovoljni token.

=== "GitHub"

    ```yaml
    # Provjerite dozvole
    permissions:
      contents: read
      pull-requests: write
    ```

=== "GitLab"

    - Provjerite da token nije istekao
    - Provjerite scope: potreban `api`
    - Uvjerite se da koristite Project Access Token

---

### "404 Not Found"

**Uzrok:** PR/MR ili repozitorijum nije pronađen.

**Rješenje:**

1. Provjerite da PR/MR postoji
2. Provjerite ime repozitorijuma
3. Provjerite da token ima pristup repozitorijumu

---

### "429 Too Many Requests" (Rate Limit)

**Uzrok:** Prekoračeno API ograničenje.

**Ograničenja Gemini Free Tier:**

| Ograničenje | Vrijednost |
|-------|-------|
| Zahtjevi po minuti | 15 |
| Tokeni po danu | 1,000,000 |
| Zahtjevi po danu | 1,500 |

**Rješenje:**

1. AI Code Reviewer automatski ponavlja sa eksponencijalnim backoff-om
2. Ako problem potraje — sačekajte ili pređite na plaćeni nivo
3. Dodajte `concurrency` da otkažete duplikate:

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

---

### "500 Internal Server Error"

**Uzrok:** Problem na strani API-ja (Google, GitHub, GitLab).

**Rješenje:**

1. AI Code Reviewer automatski ponavlja (do 5 pokušaja)
2. Provjerite status servisa:
   - [Google Cloud Status](https://status.cloud.google.com/)
   - [GitHub Status](https://www.githubstatus.com/)
   - [GitLab Status](https://status.gitlab.com/)

---

### Revizija je prespora

**Uzrok:** Veliki PR ili spora mreža.

**Rješenje:**

1. Smanjite veličinu PR-a
2. Konfigurišite ograničenja:

```bash
export REVIEW_MAX_FILES=10
export REVIEW_MAX_DIFF_LINES=300
```

3. Podesite timeout:

```yaml
# GitHub
timeout-minutes: 10

# GitLab
timeout: 10m
```

---

### Fork PR-ovi ne dobijaju reviziju

**Uzrok:** Tajne nijesu dostupne za fork PR-ove (bezbjednost).

**Rješenje:**

Ovo je očekivano ponašanje. Za fork PR-ove:

1. Maintainer može ručno pokrenuti reviziju
2. Ili koristite `pull_request_target` (budite oprezni sa bezbjednošću!)

---

### Pogrešan jezik odgovora

**Uzrok:** Neispravna konfiguracija jezika.

**Rješenje:**

1. Za fiksirani jezik:
```bash
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

2. Za adaptivni jezik — provjerite da je opis PR-a napisan na željenom jeziku

---

## FAQ

### Mogu li ga koristiti bez API ključa?

**Ne.** Potreban je Google Gemini API ključ. Besplatni nivo je dovoljan za većinu projekata.

### Je li Bitbucket podržan?

**Ne** (još uvijek). Samo GitHub i GitLab.

### Mogu li koristiti druge LLM-ove (ChatGPT, Claude)?

**Ne** (u MVP-u). Podrška za druge LLM-ove je planirana za buduće verzije.

### Je li bezbijedno slati kod na Google API?

**Važno znati:**

- Kod se šalje na Google Gemini API za analizu
- Pregledajte [Google AI Terms](https://ai.google.dev/terms)
- Za osjetljive projekte, razmislite o self-hosted rješenjima (u budućim verzijama)

### Koliko košta?

**Cijene Gemini Flash:**

| Metrika | Cijena |
|--------|------|
| Ulazni tokeni | $0.075 / 1M |
| Izlazni tokeni | $0.30 / 1M |

**Približno:** ~1000 revizija = ~$1

Besplatni nivo: ~100 revizija/dan besplatno.

### Kako onemogućiti reviziju za određene fajlove?

Još nema `.ai-reviewerignore`. Planirano za buduće verzije.

Zaobilaznica: filter u workflow-u:

```yaml
on:
  pull_request:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Mogu li ga pokrenuti lokalno?

**Da:**

```bash
pip install ai-reviewbot
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token
ai-review --provider github --repo owner/repo --pr 123
```

---

## Debagovanje

### Omogućite detaljne logove

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Provjerite konfiguraciju

```bash
# Provjerite da su varijable podešene
echo $AI_REVIEWER_GOOGLE_API_KEY | head -c 10
echo $GITHUB_TOKEN | head -c 10
```

### Testirajte API poziv

```bash
# Test Gemini API
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$AI_REVIEWER_GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Potražite pomoć

Ako problem nije riješen:

1. :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — za bagove
2. :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — za pitanja

**Pri kreiranju issue-a, uključite:**

- Verziju AI Code Reviewer-a (`ai-review --version`)
- CI provajdera (GitHub/GitLab)
- Logove (sa skrivenim tajnama!)
- Korake za reprodukciju

---

## Sljedeći korak

- [Primjeri →](examples/index.md)
- [Konfiguracija →](configuration.md)
