#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://live.alpha.kickertool.de"

STATE_PATH = {
    "finished": "overview",
    "running": "live",
    "pre-registration": "pre-registration",
    "check-in": "check-in",
    "planned": "standings",
}

SECTION_ORDER = ("running", "planned", "finished")
SECTION_LABELS = {
    "running": "laufende Turniere",
    "planned": "geplante Turniere",
    "finished": "Turniere der letzten 30 Tage",
}
PLANNED_STATES = {"planned", "pre-registration", "check-in"}


def state_to_section(state):
    if state == "running":
        return "running"
    if state in PLANNED_STATES:
        return "planned"
    if state == "finished":
        return "finished"
    return None


def fmt_date(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%d.%m.%Y")


def render_section(label, tournaments):
    if not tournaments:
        rows = '<tr><td colspan="3">Keine Turniere.</td></tr>'
    else:
        rows = ""
        for t in tournaments:
            slug = t.get("resultPage", {}).get("slug", "")
            name = t.get("name", "")
            ort = t.get("resultPage", {}).get("name", "")
            date = fmt_date(t["date"])
            tid = t.get("_id", "")
            did = t.get("disciplines", [{}])[0].get("_id", "") if t.get("disciplines") else ""
            state = t.get("state", "")
            path = STATE_PATH.get(state, "overview")
            href = f"{BASE_URL}/{slug}/tournaments/{tid}/disciplines/{did}/{path}" if slug and tid and did else "#"
            rows += (
                f'      <tr>'
                f'<td class="col-date">{date}</td>'
                f'<td><a href="{href}" target="_blank" rel="noopener">{name}</a></td>'
                f'<td>{ort}</td>'
                f'</tr>\n'
            )

    return f"""\
  <section>
    <h2>{label}</h2>
    <table>
      <thead>
        <tr><th class="col-date">Datum</th><th>Turnier</th><th>Ort</th></tr>
      </thead>
      <tbody>
{rows}      </tbody>
    </table>
  </section>
"""


def generate():
    data = json.loads(Path("data/tournaments.json").read_text())

    grouped = {k: [] for k in SECTION_ORDER}
    for t in data:
        section = state_to_section(t.get("state"))
        if section:
            grouped[section].append(t)

    grouped["running"].sort(key=lambda t: t["date"])
    grouped["planned"].sort(key=lambda t: t["date"])
    grouped["finished"].sort(key=lambda t: t["date"], reverse=True)

    sections_html = "".join(
        render_section(SECTION_LABELS[k], grouped[k]) for k in SECTION_ORDER
    )

    updated = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    html = f"""\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DTFB Turniere</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
      max-width: 960px;
      margin: 2rem auto;
      padding: 0 1rem;
      color: #dee2e6;
      background: #212529;
    }}
    h2 {{
      font-size: 1rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 2px solid #dee2e6;
      padding-bottom: 0.3rem;
      margin: 2rem 0 0.5rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      text-align: left;
      padding: 0.35rem 0.5rem;
      border-bottom: 1px solid #495057;
    }}
    th {{
      background: #2c3034;
      font-weight: bold;
      white-space: nowrap;
    }}
    .col-date {{
      white-space: nowrap;
      width: 90px;
    }}
    a {{ color: #fff; text-decoration: underline; }}
    a:hover {{ text-decoration: underline; }}
    tbody tr:nth-child(odd) td {{ background: #2c3034; }}
    tbody tr:hover td {{ background: #373b3f; }}
    .updated {{
      font-size: 0.75rem;
      color: #999;
      margin-top: 2rem;
      text-align: right;
    }}
  </style>
</head>
<body>
{sections_html}
  <p class="updated">Zuletzt aktualisiert: {updated}</p>
</body>
</html>
"""

    Path("docs").mkdir(exist_ok=True)
    Path("docs/index.html").write_text(html)
    print("Generated docs/index.html")


if __name__ == "__main__":
    generate()
