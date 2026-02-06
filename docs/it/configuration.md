# Configurazione

Tutte le impostazioni vengono configurate tramite variabili d'ambiente.

---

## Variabili Necessarie

| Variabile | Descrizione | Esempio | Come ottenerla |
|-----------|-------------|---------|----------------|
| `GOOGLE_API_KEY` | Chiave API Google Gemini | `AIza...` | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub PAT (per GitHub) | `ghp_...` | [Istruzioni](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab PAT (per GitLab) | `glpat-...` | [Istruzioni](gitlab.md#get-token) |

!!! warning "Almeno un provider necessario"
    Hai bisogno di `GITHUB_TOKEN` **o** `GITLAB_TOKEN` a seconda della piattaforma.
    I token sono specifici per il provider: `GITHUB_TOKEN` serve solo per GitHub, `GITLAB_TOKEN` solo per GitLab.

---

## Variabili Opzionali {#optional}

### Generali

| Variabile | Descrizione | Default | Range |
|-----------|-------------|---------|-------|
| `LOG_LEVEL` | Livello di logging | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `API_TIMEOUT` | Timeout richieste (sec) | `60` | 1-300 |

### Lingua

| Variabile | Descrizione | Default | Esempi |
|-----------|-------------|---------|--------|
| `LANGUAGE` | Lingua delle risposte | `en` | `uk`, `de`, `es`, `it`, `me` |
| `LANGUAGE_MODE` | Modalita di rilevamento | `adaptive` | `adaptive`, `fixed` |

**Modalita lingua:**

- **`adaptive`** (default) — rileva automaticamente la lingua dal contesto PR/MR (descrizione, commenti, task collegato)
- **`fixed`** — usa sempre la lingua da `LANGUAGE`

!!! tip "ISO 639"
    `LANGUAGE` accetta qualsiasi codice ISO 639 valido:

    - 2 lettere: `en`, `uk`, `de`, `es`, `it`
    - 3 lettere: `ukr`, `deu`, `spa`
    - Nomi: `English`, `Ukrainian`, `German`

### LLM

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `GEMINI_MODEL` | Modello Gemini | `gemini-2.5-flash` |

**Modelli disponibili:**

| Modello | Descrizione | Costo |
|---------|-------------|-------|
| `gemini-2.5-flash` | Veloce, economico | $0.075 / 1M input |
| `gemini-2.0-flash` | Versione precedente | $0.075 / 1M input |
| `gemini-1.5-pro` | Piu potente | $1.25 / 1M input |

!!! note "Precisione prezzi"
    I prezzi sono indicati alla data di release e possono cambiare.

    Informazioni aggiornate: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

!!! tip "Free Tier"
    Presta attenzione al **Free Tier** quando usi determinati modelli.

    Nella grande maggioranza dei casi, il limite gratuito e sufficiente per la code review di un team di **4-8 sviluppatori**.

### Review

| Variabile | Descrizione | Default | Range |
|-----------|-------------|---------|-------|
| `REVIEW_MAX_FILES` | Max file nel contesto | `20` | 1-100 |
| `REVIEW_MAX_DIFF_LINES` | Max righe diff per file | `500` | 1-5000 |

### GitLab

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `GITLAB_URL` | URL server GitLab | `https://gitlab.com` |

!!! info "GitLab self-hosted"
    Per GitLab self-hosted, imposta `GITLAB_URL`:
    ```bash
    export GITLAB_URL=https://gitlab.mycompany.com
    ```

---

## File .env

E comodo salvare la configurazione in `.env`:

```bash
# .env
GOOGLE_API_KEY=AIza...
GITHUB_TOKEN=ghp_...

# Opzionali
LANGUAGE=uk
LANGUAGE_MODE=adaptive
GEMINI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
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
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GITHUB_TOKEN: ${{ github.token }}  # Automatico
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

### GitLab CI

```yaml
variables:
  GOOGLE_API_KEY: $GOOGLE_API_KEY  # Da CI/CD Variables
  # GITLAB_TOKEN: $CI_JOB_TOKEN   # Automatico (limitato)
  GITLAB_TOKEN: $GITLAB_TOKEN      # O PAT per permessi completi
  LANGUAGE: uk
  LANGUAGE_MODE: adaptive
```

---

## Validazione

AI Code Reviewer valida la configurazione all'avvio:

### Errori di Validazione

```
ValidationError: GOOGLE_API_KEY is too short (minimum 10 characters)
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
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
```

### Minima (GitLab)

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
```

### Lingua italiana, fissa

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LANGUAGE=it
export LANGUAGE_MODE=fixed
```

### GitLab self-hosted

```bash
export GOOGLE_API_KEY=AIza...
export GITLAB_TOKEN=glpat-...
export GITLAB_URL=https://gitlab.mycompany.com
```

### Modalita debug

```bash
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
export LOG_LEVEL=DEBUG
```

---

## Priorita Configurazione

1. **Variabili d'ambiente** (piu alta)
2. **File `.env`** nella directory corrente

---

## Prossimo Passo

- [Integrazione GitHub →](github.md)
- [Integrazione GitLab →](gitlab.md)
