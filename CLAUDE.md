# dtifu — DTFB Turnierliste

Statische GitHub Pages Seite, die täglich DTFB-Turniere von der tournament.io API scraped und als HTML rendert.

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
- **Cron (Raspberry Pi):** `0 6 * * * /path/to/dtifu/run.sh >> /var/log/dtifu.log 2>&1`

## run.sh Verhalten

- Bricht bei Fehler ab (`set -e`)
- Committed nur wenn es Änderungen gibt (`git diff` Check)
- Committed `data/tournaments.json` und `docs/index.html`

## Design

- Dark Theme: `background: #212529`
- Links: `color: #fff; text-decoration: underline`
- Row-Striping: `tbody tr:nth-child(odd)`
- Kein Nav, kein Footer, keine Sponsoren — nur die 3 Sektions-Tabellen
