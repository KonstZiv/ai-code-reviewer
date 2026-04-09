# Troubleshooting

FAQ e risoluzione dei problemi comuni.

---

## Problemi Comuni

### Action mostra --help invece di eseguire

**Sintomo:** Nei log del CI job si vede:

```
Usage: ai-review [OPTIONS]
...
╭─ Options ─────────────────────────────────────────────────────────╮
│ --provider  -p      [github|gitlab]  CI provider...              │
```

**Causa:** Si sta usando una vecchia versione del Docker image (prima di v1.0.0a2).

**Soluzione:**

Aggiorna all'ultima versione:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1  # Usa sempre l'ultima v1.x
```

Se il problema persiste, specifica esplicitamente la versione:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1.0.0a2  # O piu recente
```

---

### La Revisione Non Appare

**Sintomo:** Il job CI e passato con successo, ma non ci sono commenti.

**Controlla:**

1. **Log del job CI** — ci sono errori?
2. **Chiave API** — `AI_REVIEWER_GOOGLE_API_KEY` e valida?
3. **Token** — ci sono permessi di scrittura?
4. **github_token** — e stato passato esplicitamente?

=== "GitHub"

    ```yaml
    permissions:
      contents: read
      pull-requests: write  # ← Necessario!
    ```

=== "GitLab"

    Assicurati che `GITLAB_TOKEN` abbia scope `api`.

---

### "Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short"

**Causa:** La chiave non e impostata o e incorretta.

**Soluzione:**

1. Controlla che il secret sia aggiunto nelle impostazioni del repo
2. Controlla il nome (case-sensitive)
3. Controlla che la chiave sia valida su [Google AI Studio](https://aistudio.google.com/)

---

### "401 Unauthorized" / "403 Forbidden"

**Causa:** Token non valido o insufficiente.

=== "GitHub"

    ```yaml
    # Controlla i permessi
    permissions:
      contents: read
      pull-requests: write
    ```

=== "GitLab"

    - Controlla che il token non sia scaduto
    - Controlla lo scope: serve `api`
    - Assicurati di usare un Project Access Token

---

### "404 Not Found"

**Causa:** PR/MR o repository non trovato.

**Soluzione:**

1. Controlla che il PR/MR esista
2. Controlla il nome del repository
3. Controlla che il token abbia accesso al repository

---

### "429 Too Many Requests" (Rate Limit)

**Causa:** Limite API superato.

**Limiti Free Tier Gemini:**

| Limite | Valore |
|--------|--------|
| Richieste per minuto | 15 |
| Token al giorno | 1,000,000 |
| Richieste al giorno | 1,500 |

**Soluzione:**

1. AI Code Reviewer riprova automaticamente con backoff esponenziale
2. Se il problema persiste — aspetta o passa al tier a pagamento
3. Aggiungi `concurrency` per cancellare i duplicati:

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

---

### "500 Internal Server Error"

**Causa:** Problema lato API (Google, GitHub, GitLab).

**Soluzione:**

1. AI Code Reviewer riprova automaticamente (fino a 5 tentativi)
2. Controlla lo stato dei servizi:
   - [Google Cloud Status](https://status.cloud.google.com/)
   - [GitHub Status](https://www.githubstatus.com/)
   - [GitLab Status](https://status.gitlab.com/)

---

### Revisione Troppo Lenta

**Causa:** PR grande o rete lenta.

**Soluzione:**

1. Riduci la dimensione del PR
2. Configura i limiti:

```bash
export REVIEW_MAX_FILES=10
export REVIEW_MAX_DIFF_LINES=300
```

3. Imposta timeout:

```yaml
# GitHub
timeout-minutes: 10

# GitLab
timeout: 10m
```

---

### PR da Fork Non Ricevono Revisione

**Causa:** I secret non sono disponibili per PR da fork (sicurezza).

**Soluzione:**

Questo e il comportamento previsto. Per PR da fork:

1. Il maintainer puo eseguire la revisione manualmente
2. Oppure usare `pull_request_target` (attenzione alla sicurezza!)

---

### Lingua Risposta Sbagliata

**Causa:** Configurazione lingua incorretta.

**Soluzione:**

1. Per lingua fissa:
```bash
export LANGUAGE=it
export LANGUAGE_MODE=fixed
```

2. Per lingua adattiva — assicurati che la descrizione del PR sia scritta nella lingua desiderata

---

## FAQ

### Posso usarlo senza chiave API?

**No.** Una chiave API Google Gemini e necessaria. Il free tier e sufficiente per la maggior parte dei progetti.

### Bitbucket e supportato?

**No** (non ancora). Solo GitHub e GitLab.

### Posso usare altri LLM (ChatGPT, Claude)?

**No** (nel MVP). Il supporto per altri LLM e pianificato per versioni future.

### E sicuro inviare codice a Google API?

**Importante sapere:**

- Il codice viene inviato a Google Gemini API per l'analisi
- Leggi i [Google AI Terms](https://ai.google.dev/terms)
- Per progetti sensibili, considera soluzioni self-hosted (nelle versioni future)

### Quanto costa?

**Prezzi Gemini Flash:**

| Metrica | Costo |
|---------|-------|
| Token in input | $0.075 / 1M |
| Token in output | $0.30 / 1M |

**Approssimativamente:** ~1000 revisioni = ~$1

Free tier: ~100 revisioni/giorno gratis.

### Come disabilitare la revisione per certi file?

Non esiste ancora `.ai-reviewerignore`. Pianificato per versioni future.

Workaround: filtra nel workflow:

```yaml
on:
  pull_request:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Posso eseguirlo localmente?

**Si:**

```bash
pip install ai-reviewbot
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token
ai-review --provider github --repo owner/repo --pr 123
```

---

## Debugging

### Abilita Log Verbosi

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Controlla Configurazione

```bash
# Controlla che le variabili siano impostate
echo $AI_REVIEWER_GOOGLE_API_KEY | head -c 10
echo $GITHUB_TOKEN | head -c 10
```

### Testa Chiamata API

```bash
# Testa Gemini API
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$AI_REVIEWER_GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Ottieni Aiuto

Se il problema non e risolto:

1. :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — per bug
2. :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — per domande

**Quando crei un issue, includi:**

- Versione AI Code Reviewer (`ai-review --version`)
- Provider CI (GitHub/GitLab)
- Log (con secret nascosti!)
- Passi per riprodurre

---

## Prossimo Passo

- [Esempi →](examples/index.md)
- [Configurazione →](configuration.md)
