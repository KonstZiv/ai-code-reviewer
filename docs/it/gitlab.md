# GitLab

Guida dettagliata per l'integrazione con GitLab CI.

---

## Token {#tokens}

### CI_JOB_TOKEN (automatico)

In GitLab CI, `CI_JOB_TOKEN` e automaticamente disponibile:

```yaml
variables:
  GITLAB_TOKEN: $CI_JOB_TOKEN
```

**Limitazioni di `CI_JOB_TOKEN`:**

| Funzionalita | Stato |
|--------------|-------|
| Leggi MR | :white_check_mark: |
| Leggi diff | :white_check_mark: |
| Pubblica note | :white_check_mark: |
| Crea discussioni | :x: |

!!! warning "Permessi limitati"
    `CI_JOB_TOKEN` non puo creare discussioni inline.

    Per la funzionalita completa, usa un Personal Access Token.

### Personal Access Token (consigliato) {#get-token}

Per **esecuzioni locali** o **funzionalita completa in CI**, hai bisogno di un Personal Access Token:

1. Vai su `User Settings → Access Tokens → Add new token`
2. Inserisci il nome del token (es. `ai-code-reviewer`)
3. Seleziona scope: **`api`**
4. Clicca **Create personal access token**
5. Copia il token e salvalo come `GITLAB_TOKEN`

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Da CI/CD Variables
```

!!! warning "Salva il token"
    GitLab mostra il token **una sola volta**. Salvalo immediatamente.

!!! info "Personal Access Token vs Project Access Token"
    **Personal Access Token** (PAT) funziona su **tutti i piani GitLab**, incluso Free.

    **Project Access Token** e disponibile solo su **GitLab Premium/Ultimate**.
    Se sei sul piano Free, usa un Personal Access Token.

---

## Variabili CI/CD

### Aggiungere Variabili

`Settings → CI/CD → Variables → Add variable`

| Variabile | Valore | Opzioni |
|-----------|--------|---------|
| `GOOGLE_API_KEY` | Chiave API Gemini | Masked |
| `GITLAB_TOKEN` | PAT (se necessario) | Masked |

!!! tip "Masked"
    Abilita sempre **Masked** per i secret — non verranno mostrati nei log.

---

## Trigger

### Trigger Consigliato

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Questo esegue il job solo per le pipeline di Merge Request.

### Trigger Alternativo (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — sintassi piu recente, consigliata da GitLab.

---

## Esempi Job

### Minimo

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

### Completo (consigliato)

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

**Cosa fa:**

- `allow_failure: true` — la MR non viene bloccata se la revisione fallisce
- `timeout: 10m` — massimo 10 minuti
- `interruptible: true` — puo essere cancellato con un nuovo commit

### Con Stage Personalizzato

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
  needs: []  # Non aspettare gli stage precedenti
```

---

## GitLab Self-hosted

### Configurazione

```yaml
variables:
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
```

### Docker Registry

Se il tuo GitLab non ha accesso a `ghcr.io`, crea un mirror:

```bash
# Su una macchina con accesso
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

## Variabili CI GitLab

AI Code Reviewer usa automaticamente:

| Variabile | Descrizione |
|-----------|-------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | Numero MR |
| `CI_SERVER_URL` | URL GitLab |
| `CI_JOB_TOKEN` | Token automatico |

Non hai bisogno di passare `--project` e `--mr-iid` — vengono presi automaticamente dalla CI.

---

## Risultato della Review

### Note (commenti)

AI Review pubblica commenti sulla MR come note.

### Discussioni (inline)

Per commenti inline, hai bisogno di un token PAT completo (non `CI_JOB_TOKEN`).

I commenti inline appaiono direttamente accanto alle righe di codice nella vista diff.

### Summary

Alla fine della revisione, viene pubblicata una nota Summary con:

- Statistiche generali
- Metriche
- Good practice

---

## Troubleshooting

### La Review Non Pubblica Commenti

**Controlla:**

1. La variabile `GOOGLE_API_KEY` e impostata
2. `GITLAB_TOKEN` ha permessi sufficienti (scope: `api`)
3. La pipeline e in esecuzione per una MR (non per un branch)

### "401 Unauthorized"

**Causa:** Token non valido.

**Soluzione:**

- Controlla che il token non sia scaduto
- Controlla lo scope (serve `api`)

### "403 Forbidden"

**Causa:** Permessi insufficienti.

**Soluzione:**

- Usa PAT invece di `CI_JOB_TOKEN`
- Controlla che il token abbia accesso al progetto

### "404 Not Found"

**Causa:** MR non trovata.

**Soluzione:**

- Controlla che la pipeline sia in esecuzione per una MR
- Controlla `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Causa:** Limite API superato.

**Soluzione:**

- AI Code Reviewer riprova automaticamente con backoff esponenziale
- Se persiste — aspetta o aumenta i limiti

---

## Best Practice

### 1. Usa PAT per funzionalita completa

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # PAT, non CI_JOB_TOKEN
```

### 2. Aggiungi allow_failure

```yaml
allow_failure: true
```

La MR non verra bloccata se la revisione fallisce.

### 3. Imposta timeout

```yaml
timeout: 10m
```

### 4. Rendi il job interrompibile

```yaml
interruptible: true
```

La vecchia revisione verra cancellata con un nuovo commit.

### 5. Non aspettare altri stage

```yaml
needs: []
```

La revisione partira immediatamente, senza aspettare build/test.

---

## Prossimo Passo

- [Integrazione GitHub →](github.md)
- [Riferimento CLI →](api.md)
