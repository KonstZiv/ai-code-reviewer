# Configurazione

Tutte le impostazioni vengono configurate tramite variabili d'ambiente.

!!! tip "Migrazione: prefisso `AI_REVIEWER_`"
    A partire dalla v1.0.0a7, tutte le variabili d'ambiente supportano il prefisso `AI_REVIEWER_` (es., `AI_REVIEWER_GOOGLE_API_KEY`). I vecchi nomi (es., `GOOGLE_API_KEY`) funzionano ancora come fallback. Si consiglia di migrare ai nuovi nomi per evitare conflitti con altri strumenti nelle configurazioni CI/CD a livello di organizzazione.

---

## Variabili Necessarie

| Variabile | Descrizione | Esempio | Come ottenerla |
|-----------|-------------|---------|----------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Chiave API Google Gemini (separate da virgola per la rotazione delle chiavi) | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_MISTRAL_API_KEY` | Chiave API Mistral (separate da virgola per la rotazione delle chiavi) | `sk-...` | [Mistral Console](https://console.mistral.ai/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub token (per GitHub) | `ghp_...` | [Istruzioni](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab token (per GitLab) | `glpat-...` | [Istruzioni](gitlab.md#get-token) |

!!! warning "Almeno una chiave API LLM necessaria"
    Hai bisogno di almeno una chiave API LLM: `AI_REVIEWER_GOOGLE_API_KEY` **o** `AI_REVIEWER_MISTRAL_API_KEY` (o entrambe).
    La chiave per il provider primario (impostato da `AI_REVIEWER_LLM_PROVIDER`) e obbligatoria.

!!! warning "Almeno un token piattaforma necessario"
    Hai bisogno di `AI_REVIEWER_GITHUB_TOKEN` **o** `AI_REVIEWER_GITLAB_TOKEN` a seconda della piattaforma.

!!! info "Tipi di token GitLab"
    Per GitLab, puoi usare un **Personal Access Token** (funziona su tutti i piani, incluso Free)
    o un **Project Access Token** (richiede GitLab Premium/Ultimate).

---

## Variabili Opzionali {#optional}

### Generali

| Variabile | Descrizione | Default | Range |
|-----------|-------------|---------|-------|
| `AI_REVIEWER_LOG_LEVEL` | Livello di logging | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `AI_REVIEWER_API_TIMEOUT` | Timeout richieste (sec) | `60` | 1-300 |

### Lingua

| Variabile | Descrizione | Default | Esempi |
|-----------|-------------|---------|--------|
| `AI_REVIEWER_LANGUAGE` | Lingua delle risposte | `en` | `uk`, `de`, `es`, `it`, `me` |
| `AI_REVIEWER_LANGUAGE_MODE` | Modalita di rilevamento | `adaptive` | `adaptive`, `fixed` |

**Modalita lingua:**

- **`adaptive`** (default) — rileva automaticamente la lingua dal contesto PR/MR (descrizione, commenti, task collegato)
- **`fixed`** — usa sempre la lingua da `AI_REVIEWER_LANGUAGE`

!!! tip "ISO 639"
    `AI_REVIEWER_LANGUAGE` accetta qualsiasi codice ISO 639 valido:

    - 2 lettere: `en`, `uk`, `de`, `es`, `it`
    - 3 lettere: `ukr`, `deu`, `spa`
    - Nomi: `English`, `Ukrainian`, `German`

### LLM {#llm}

#### Selezione Provider

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `AI_REVIEWER_LLM_PROVIDER` | Provider LLM primario | `google` |
| `AI_REVIEWER_LLM_FALLBACK_PROVIDER` | Provider di fallback (usato quando il primario e esaurito) | _(nessuno)_ |

Provider supportati: `google`, `mistral`.

Quando sia il provider primario che quello di fallback sono configurati, il sistema prova prima tutti i modelli del provider primario, poi tutti i modelli del provider di fallback. Esempio con `LLM_PROVIDER=mistral` e `LLM_FALLBACK_PROVIDER=google`:

```
mistral-large → mistral-small → gemini-2.5-flash → gemini-2.5-flash-lite
```

#### Google Gemini Models

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `AI_REVIEWER_GEMINI_MODEL` | Modello Gemini primario | `gemini-2.5-flash` |
| `AI_REVIEWER_GEMINI_MODEL_FALLBACK` | Catena di modelli di fallback (separati da virgola) | `gemini-3-flash-preview,...` |

| Modello | Descrizione | Costo |
|---------|-------------|-------|
| `gemini-2.5-flash` | Veloce, stabile, con ragionamento (predefinito) | $0.075 / 1M input |
| `gemini-3-flash-preview` | Flash di classe frontier (anteprima) | $0.075 / 1M input |
| `gemini-2.5-flash-lite` | Il piu veloce e economico in 2.5 | $0.01875 / 1M input |
| `gemini-2.5-pro` | Piu potente, con ragionamento profondo | $1.25 / 1M input |

:material-link: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

#### Mistral Models

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `AI_REVIEWER_MISTRAL_MODEL` | Modello Mistral primario | `mistral-large-latest` |
| `AI_REVIEWER_MISTRAL_MODEL_FALLBACK` | Catena di modelli di fallback (separati da virgola) | _(nessuno)_ |
| `AI_REVIEWER_MISTRAL_API_URL` | URL endpoint API Mistral (per Codestral o self-hosted) | _(API Mistral standard)_ |

| Modello | Descrizione | Contesto | Prezzo (input / output) |
|---------|-------------|----------|------------------------|
| `mistral-large-latest` | Più potente, MoE 41B/675B (predefinito) | 256k | $0.50 / $1.50 |
| `mistral-medium-latest` | Equilibrio prestazioni/costo | 128k | $0.40 / $2.00 |
| `mistral-small-latest` | Veloce ed economico, hybrid 6.5B/119B | 256k | $0.15 / $0.60 |
| `codestral-latest` | Ottimizzato per il codice, supporto FIM | 128k | $0.30 / $0.90 |
| `devstral-latest` | Coding agent, Mistral più economico | 256k | $0.10 / $0.30 |

!!! tip "Codestral gratuito"
    Codestral ha un proprio livello gratuito con **endpoint e chiave separati**:

    1. Vai su [codestral.mistral.ai](https://codestral.mistral.ai/)
    2. Genera una chiave API Codestral
    3. Imposta `AI_REVIEWER_MISTRAL_API_URL=https://codestral.mistral.ai`
    4. Imposta `AI_REVIEWER_MISTRAL_MODEL=codestral-latest`

    Questa chiave funziona **solo** con `codestral-latest` sull'endpoint Codestral.

:material-link: [Mistral Pricing](https://mistral.ai/products/la-plateforme#pricing)

#### Altre Impostazioni

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `AI_REVIEWER_REVIEW_SPLIT_THRESHOLD` | Soglia caratteri per review split codice+test | `30000` |

!!! note "Precisione prezzi"
    I prezzi sono indicati alla data di release e possono cambiare. Controlla la pagina dei prezzi del provider per informazioni aggiornate.

!!! tip "Free Tier"
    Sia Google Gemini che Mistral offrono tier gratuiti sufficienti per la code review di un team di **4-8 sviluppatori**. Combina due provider per la massima affidabilita.

### Review

| Variabile | Descrizione | Default | Range |
|-----------|-------------|---------|-------|
| `AI_REVIEWER_REVIEW_MAX_FILES` | Max file nel contesto | `20` | 1-100 |
| `AI_REVIEWER_REVIEW_MAX_DIFF_LINES` | Max righe diff per file | `500` | 1-5000 |
| `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS` | Max caratteri commenti MR nel prompt | `3000` | 0-20000 |
| `AI_REVIEWER_REVIEW_INCLUDE_BOT_COMMENTS` | Includi commenti bot nel prompt | `true` | true/false |
| `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS` | Pubblica commenti inline sulle righe | `true` | true/false |
| `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE` | Raggruppa commenti in thread di dialogo | `true` | true/false |

!!! info "Contesto della discussione"
    Il revisore AI legge i commenti esistenti della MR/PR per evitare di ripetere suggerimenti
    gia discussi. Imposta `AI_REVIEWER_REVIEW_MAX_COMMENT_CHARS=0` per disabilitare.

!!! info "Commenti inline"
    Quando `AI_REVIEWER_REVIEW_POST_INLINE_COMMENTS=true` (default), gli issue con informazioni su file/riga vengono pubblicati come commenti inline sul codice, con un breve riepilogo come corpo della review. Imposta `false` per un singolo commento di riepilogo.

!!! info "Thread di dialogo"
    Quando `AI_REVIEWER_REVIEW_ENABLE_DIALOGUE=true` (default), i commenti vengono raggruppati in
    thread di conversazione in modo che l'AI comprenda le catene di risposte. Imposta `false` per il rendering piatto.

### Discovery

| Variabile | Descrizione | Default | Range |
|-----------|-------------|---------|-------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | Attivare l'analisi del progetto prima della review | `true` | true/false |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | Pubblica sempre il commento discovery (default: solo in caso di lacune) | `false` | true/false |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | Timeout della pipeline discovery in secondi | `30` | 1-300 |

!!! info "Analisi del progetto"
    Quando attivato, AI ReviewBot analizza automaticamente il tuo repository (linguaggi, pipeline CI, file di config) prima di ogni review per un feedback piu intelligente. Imposta `false` per disabilitare. Dettagli: [Discovery →](discovery.md).

!!! info "Modalita verbose"
    Quando `AI_REVIEWER_DISCOVERY_VERBOSE=true`, il commento discovery viene sempre pubblicato e include tutte le Attention Zones (Well Covered, Weakly Covered, Not Covered). La modalita predefinita pubblica solo in caso di lacune o zone non coperte.

### GitLab

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `AI_REVIEWER_GITLAB_URL` | URL server GitLab | `https://gitlab.com` |

!!! info "GitLab self-hosted"
    Per GitLab self-hosted, imposta `AI_REVIEWER_GITLAB_URL`:
    ```bash
    export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## File .env

E comodo salvare la configurazione in `.env`:

```bash
# .env

# Provider LLM (scegline uno o entrambi)
AI_REVIEWER_GOOGLE_API_KEY=AIza...
# AI_REVIEWER_MISTRAL_API_KEY=sk-...
# AI_REVIEWER_LLM_PROVIDER=google
# AI_REVIEWER_LLM_FALLBACK_PROVIDER=mistral

# Token piattaforma
AI_REVIEWER_GITHUB_TOKEN=ghp_...

# Opzionali
AI_REVIEWER_LANGUAGE=uk
AI_REVIEWER_LANGUAGE_MODE=adaptive
AI_REVIEWER_GEMINI_MODEL=gemini-2.5-flash
AI_REVIEWER_LOG_LEVEL=INFO
```

!!! danger "Sicurezza"
    **Non committare mai `.env` su git!**

    Aggiungi a `.gitignore`:
    ```
    .env
    .env.*
    ```

---

## Configurazione CI/CD

### GitHub Actions

```yaml
env:
  AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
  AI_REVIEWER_GITHUB_TOKEN: ${{ github.token }}  # Automatico
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  # AI_REVIEWER_GOOGLE_API_KEY e AI_REVIEWER_GITLAB_TOKEN
  # vengono ereditati automaticamente dalle CI/CD Variables
  AI_REVIEWER_LANGUAGE: uk
  AI_REVIEWER_LANGUAGE_MODE: adaptive
```

---

## Validazione

AI Code Reviewer valida la configurazione all'avvio:

### Errori di Validazione

```
ValidationError: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Soluzione:** Controlla che la variabile sia impostata correttamente.

```
ValidationError: Invalid language code 'xyz'
```

**Soluzione:** Usa un codice ISO 639 valido.

```
ValidationError: LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Soluzione:** Usa uno dei livelli consentiti.

---

## Esempi di Configurazione

### Minima (GitHub)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
```

### Minima (GitLab)

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
```

### Lingua italiana, fissa

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LANGUAGE=it
export AI_REVIEWER_LANGUAGE_MODE=fixed
```

### GitLab self-hosted

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITLAB_TOKEN=glpat-...
export AI_REVIEWER_GITLAB_URL=https://gitlab.mycompany.com
```

### Modalita debug

```bash
export AI_REVIEWER_GOOGLE_API_KEY=AIza...
export AI_REVIEWER_GITHUB_TOKEN=ghp_...
export AI_REVIEWER_LOG_LEVEL=DEBUG
```

---

## Priorita Configurazione

1. **Variabili d'ambiente** (piu alta)
2. **File `.env`** nella directory corrente

---

## Prossimo Passo

- [Integrazione GitHub →](github.md)
- [Integrazione GitLab →](gitlab.md)
