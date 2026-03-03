# dtifu — DTFB Turnierliste

Statische GitHub Pages Seite, die DTFB-Turniere von der tournament.io API scraped und als HTML rendert.

## Workflow (PFLICHT — bei jedem Task)

1. `git fetch origin`
2. Feature Branch von `origin/main` erstellen: `git checkout -b feat/xyz origin/main`
3. Arbeit auf Feature Branch
4. PR auf `main` erstellen, mergen
5. Branch lokal und remote löschen

**Nie direkt auf `main` committen.**

## Branching

- **`main`** — Produktiv. Nur Merges via PR. Der Pi-Cron läuft auf `main` und zieht Code-Änderungen automatisch via `git pull --rebase`.
- **Feature Branches** — Format: `feat/`, `fix/`, `chore/`. Immer von `origin/main` branchen (nicht lokalem `main` — könnte stale sein). Kein permanenter `dev`-Branch.

## Architektur

```
scraper.py   → GET API → data/tournaments.json
generate.py  → tournaments.json → docs/index.html
run.sh       → orchestriert beide + git commit/push (Cron)
```

## API

```
GET https://api.tournament.io/v1/table_soccer/result/tournaments
    ?from={unix_ms}&to={unix_ms}&filter=dtfb
```

- Kein Pagination-Limit — liefert alle Einträge im Zeitraum
- `scraper.py` nutzt dynamischen Range: 30 Tage zurück bis 365 Tage voraus
- Relevante Felder: `_id`, `name`, `date`, `state`, `disciplines[0]._id`, `resultPage.slug`, `resultPage.name`

## State → Sektion-Mapping

| API `state`        | Sektion                      | URL-Suffix        |
|--------------------|------------------------------|-------------------|
| `running`          | laufende Turniere            | `live`            |
| `planned`          | geplante Turniere            | `standings`       |
| `pre-registration` | geplante Turniere            | `pre-registration`|
| `check-in`         | geplante Turniere            | `check-in`        |
| `finished`         | Turniere der letzten 30 Tage | `overview`        |

## Turnier-URL Schema

```
https://live.alpha.kickertool.de/{resultPage.slug}/tournaments/{_id}/disciplines/{disciplines[0]._id}/{status}
```

Beispiel:
```
https://live.alpha.kickertool.de/kixx/tournaments/tio:g36jgIf7L04cQ/disciplines/tio:s3tlOA9vz0hf9/pre-registration
```

## Deployment

- **GitHub Repo:** `git@github.com:Rockbob89/tifu.git`
- **GitHub Pages:** Branch `main`, Folder `/docs`
- **Custom Domain:** `tifu.mario-christ.de` (CNAME `tifu` → `rockbob89.github.io`)
- **Cron (Raspberry Pi):** `*/5 * * * * /path/to/dtifu/run.sh >> /var/log/dtifu.log 2>&1`

## run.sh Verhalten

- Bricht bei Fehler ab (`set -e`)
- Committed nur wenn es Änderungen gibt (`git diff` Check)
- Committed `data/tournaments.json` und `docs/index.html`

## Design

- Dark Theme: `background: #212529`, Text: `#dee2e6`, Borders: `#32383e`
- Links: `color: #fff; text-decoration: underline`
- Row-Striping: `tbody tr:nth-child(odd) td { background: #2c3034; }`
- Font: System-Stack, 14.4px, max-width 899px
- Kein Nav, kein Footer, keine Sponsoren — nur die 3 Sektions-Tabellen
- Viewport: `width=device-width, initial-scale=0.5, shrink-to-fit=yes` (wie tifu.info — zeigt Desktop-Layout auf Mobile)

## Spalten & Disziplinen

- 4 Spalten: Datum | Turnier | Disziplinen | Ort
- Disziplinen-Labels aus `shortName`: bekannte Namen (OD, OE, DD, DE, MX, DYP) direkt; generische `D1`/`D2` → aus `entryType` (single→OE, byp→OD, monster_dyp→DYP)
- Youth-Disziplinen (Regex `^\d{2}[ED]`, `^G[V]?[ED]`, `^J\d+`) → kollabiert zu einem "Junioren"-Link (`/live`)
- Einzelne Disziplin → direkter Link `/disciplines/{did}/{status}`
- Mehrere Disziplinen → `/tournaments/{tid}/live`
