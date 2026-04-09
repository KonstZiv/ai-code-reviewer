# Fehlerbehebung

FAQ und Lösung häufiger Probleme.

---

## Häufige Probleme

### Action zeigt --help anstatt auszuführen

**Symptom:** In CI job Logs sehen Sie:

```
Usage: ai-review [OPTIONS]
...
╭─ Options ─────────────────────────────────────────────────────────╮
│ --provider  -p      [github|gitlab]  CI provider...              │
```

**Ursache:** Verwendung einer alten Docker Image Version (vor v1.0.0a2).

**Lösung:**

Aktualisieren Sie auf die neueste Version:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1  # Verwendet immer neueste v1.x
```

Wenn das Problem weiterhin besteht, geben Sie explizit die Version an:

```yaml
- uses: KonstZiv/ai-code-reviewer@v1.0.0a2  # Oder neuer
```

---

### Review erscheint nicht

**Symptom:** CI-Job erfolgreich abgeschlossen, aber keine Kommentare.

**Überprüfen:**

1. **CI-Job-Logs** — gibt es Fehler?
2. **API-Schlüssel** — ist `AI_REVIEWER_GOOGLE_API_KEY` gültig?
3. **Token** — gibt es Schreibberechtigungen?
4. **github_token** — wurde es explizit übergeben?

=== "GitHub"

    ```yaml
    permissions:
      contents: read
      pull-requests: write  # ← Erforderlich!
    ```

=== "GitLab"

    Stellen Sie sicher, dass `GITLAB_TOKEN` den Scope `api` hat.

---

### "Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short"

**Ursache:** Schlüssel ist nicht gesetzt oder falsch.

**Lösung:**

1. Überprüfen Sie, ob das Secret in den Repo-Einstellungen hinzugefügt ist
2. Überprüfen Sie den Namen (Groß-/Kleinschreibung beachten)
3. Überprüfen Sie, ob der Schlüssel bei [Google AI Studio](https://aistudio.google.com/) gültig ist

---

### "401 Unauthorized" / "403 Forbidden"

**Ursache:** Ungültiger oder unzureichender Token.

=== "GitHub"

    ```yaml
    # Berechtigungen überprüfen
    permissions:
      contents: read
      pull-requests: write
    ```

=== "GitLab"

    - Überprüfen Sie, ob der Token nicht abgelaufen ist
    - Überprüfen Sie den Scope: benötigt `api`
    - Stellen Sie sicher, dass Sie einen Project Access Token verwenden

---

### "404 Not Found"

**Ursache:** PR/MR oder Repository nicht gefunden.

**Lösung:**

1. Überprüfen Sie, ob PR/MR existiert
2. Überprüfen Sie den Repository-Namen
3. Überprüfen Sie, ob der Token Zugriff auf das Repository hat

---

### "429 Too Many Requests" (Rate Limit)

**Ursache:** API-Limit überschritten.

**Gemini Free Tier Limits:**

| Limit | Wert |
|-------|------|
| Anfragen pro Minute | 15 |
| Tokens pro Tag | 1.000.000 |
| Anfragen pro Tag | 1.500 |

**Lösung:**

1. AI Code Reviewer wiederholt automatisch mit exponentiellem Backoff
2. Wenn das Problem anhält — warten oder zum kostenpflichtigen Tier wechseln
3. `concurrency` hinzufügen, um Duplikate abzubrechen:

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

---

### "500 Internal Server Error"

**Ursache:** Problem auf der API-Seite (Google, GitHub, GitLab).

**Lösung:**

1. AI Code Reviewer wiederholt automatisch (bis zu 5 Versuche)
2. Service-Status überprüfen:
   - [Google Cloud Status](https://status.cloud.google.com/)
   - [GitHub Status](https://www.githubstatus.com/)
   - [GitLab Status](https://status.gitlab.com/)

---

### Review zu langsam

**Ursache:** Großer PR oder langsames Netzwerk.

**Lösung:**

1. PR-Größe reduzieren
2. Limits konfigurieren:

```bash
export REVIEW_MAX_FILES=10
export REVIEW_MAX_DIFF_LINES=300
```

3. Timeout setzen:

```yaml
# GitHub
timeout-minutes: 10

# GitLab
timeout: 10m
```

---

### Fork-PRs bekommen kein Review

**Ursache:** Secrets sind für Fork-PRs nicht verfügbar (Sicherheit).

**Lösung:**

Dies ist erwartetes Verhalten. Für Fork-PRs:

1. Maintainer kann Review manuell ausführen
2. Oder `pull_request_target` verwenden (Vorsicht bei Sicherheit!)

---

### Falsche Antwortsprache

**Ursache:** Falsche Sprachkonfiguration.

**Lösung:**

1. Für feste Sprache:
```bash
export LANGUAGE=uk
export LANGUAGE_MODE=fixed
```

2. Für adaptive Sprache — stellen Sie sicher, dass die PR-Beschreibung in der gewünschten Sprache verfasst ist

---

## FAQ

### Kann ich es ohne API-Schlüssel verwenden?

**Nein.** Ein Google Gemini API-Schlüssel ist erforderlich. Der Free Tier reicht für die meisten Projekte aus.

### Wird Bitbucket unterstützt?

**Nein** (noch nicht). Nur GitHub und GitLab.

### Kann ich andere LLMs verwenden (ChatGPT, Claude)?

**Nein** (im MVP). Unterstützung für andere LLMs ist für zukünftige Versionen geplant.

### Ist es sicher, Code an die Google API zu senden?

**Wichtig zu wissen:**

- Code wird zur Analyse an die Google Gemini API gesendet
- Lesen Sie die [Google AI Terms](https://ai.google.dev/terms)
- Für sensible Projekte ziehen Sie Self-hosted-Lösungen in Betracht (in zukünftigen Versionen)

### Wie viel kostet es?

**Gemini Flash Preise:**

| Metrik | Kosten |
|--------|--------|
| Input-Tokens | $0.075 / 1M |
| Output-Tokens | $0.30 / 1M |

**Ungefähr:** ~1000 Reviews = ~$1

Free Tier: ~100 Reviews/Tag kostenlos.

### Wie deaktiviere ich das Review für bestimmte Dateien?

Es gibt noch kein `.ai-reviewerignore`. Geplant für zukünftige Versionen.

Workaround: Im Workflow filtern:

```yaml
on:
  pull_request:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Kann ich es lokal ausführen?

**Ja:**

```bash
pip install ai-reviewbot
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token
ai-review --provider github --repo owner/repo --pr 123
```

---

## Debugging

### Ausführliche Logs aktivieren

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Konfiguration überprüfen

```bash
# Überprüfen, ob Variablen gesetzt sind
echo $AI_REVIEWER_GOOGLE_API_KEY | head -c 10
echo $GITHUB_TOKEN | head -c 10
```

### API-Aufruf testen

```bash
# Gemini API testen
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$AI_REVIEWER_GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Hilfe erhalten

Wenn das Problem nicht gelöst ist:

1. :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — für Bugs
2. :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — für Fragen

**Beim Erstellen eines Issues angeben:**

- AI Code Reviewer Version (`ai-review --version`)
- CI-Provider (GitHub/GitLab)
- Logs (mit versteckten Secrets!)
- Schritte zur Reproduktion

---

## Nächster Schritt

- [Beispiele →](examples/index.md)
- [Konfiguration →](configuration.md)
