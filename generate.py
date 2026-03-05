#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

TZ = ZoneInfo("Europe/Berlin")

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
RUNNING_STATES = {"running", "pre-registration"}
PLANNED_STATES = {"planned", "check-in"}

MAIN_SHORT_NAMES = {"OD", "OE", "DD", "DE", "MX", "DYP"}

ENTRY_TYPE_LABEL = {
    "single": "OE",
    "byp": "OD",
    "monster_dyp": "DYP",
}

GENERIC_SHORT_NAMES = re.compile(r"^D\d+$", re.IGNORECASE)
YOUTH_SHORT_NAMES = re.compile(r"^(U?\d{2}[ED]|G[V]?[ED]|J\d+)$", re.IGNORECASE)


def is_youth(d):
    return bool(YOUTH_SHORT_NAMES.match(d.get("shortName", "")))


def discipline_label(d):
    sn = d.get("shortName", "")
    if sn.upper() in MAIN_SHORT_NAMES:
        return sn.upper()
    if GENERIC_SHORT_NAMES.match(sn):
        return ENTRY_TYPE_LABEL.get(d.get("entryType", ""), "")
    return sn or ""


def state_to_section(state):
    if state in RUNNING_STATES:
        return "running"
    if state in PLANNED_STATES:
        return "planned"
    if state == "finished":
        return "finished"
    return None


def fmt_date(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(TZ)
    return dt.strftime("%d.%m.%Y")


def render_section(label, tournaments):
    if not tournaments:
        rows = '      <tr><td colspan="4">Keine Turniere.</td></tr>\n'
    else:
        rows = ""
        for t in tournaments:
            slug = t.get("resultPage", {}).get("slug", "")
            name = t.get("name", "").strip()
            ort = t.get("resultPage", {}).get("name", "")
            date = fmt_date(t["date"])
            tid = t.get("_id", "")
            disciplines = t.get("disciplines", [])
            state = t.get("state", "")
            path = STATE_PATH.get(state, "overview")

            # Tournament link
            if len(disciplines) == 1:
                did = disciplines[0].get("_id", "")
                t_href = f"{BASE_URL}/{slug}/tournaments/{tid}/disciplines/{did}/{path}" if slug and tid and did else f"{BASE_URL}/{slug}/tournaments/{tid}/live"
            else:
                t_href = f"{BASE_URL}/{slug}/tournaments/{tid}/live" if slug and tid else "#"

            # Discipline links
            disc_links = []
            has_youth = False
            for d in disciplines:
                if is_youth(d):
                    has_youth = True
                    continue
                lbl = discipline_label(d)
                if not lbl:
                    continue
                did = d.get("_id", "")
                d_href = f"{BASE_URL}/{slug}/tournaments/{tid}/disciplines/{did}/{path}" if slug and tid and did else "#"
                disc_links.append(f'<a href="{d_href}" target="_blank" rel="noopener">{lbl}</a>')
            if has_youth:
                j_href = f"{BASE_URL}/{slug}/tournaments/{tid}/live" if slug and tid else "#"
                disc_links.append(f'<a href="{j_href}" target="_blank" rel="noopener">Junioren</a>')
            disc_cell = " &middot; ".join(disc_links) if disc_links else ""

            rows += (
                f'      <tr>'
                f'<td class="col-date">{date}</td>'
                f'<td class="col-name"><a href="{t_href}" target="_blank" rel="noopener">{name}</a></td>'
                f'<td class="col-disc">{disc_cell}</td>'
                f'<td class="col-ort">{ort}</td>'
                f'</tr>\n'
            )

    return f"""\
  <section>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th colspan="4" class="col-section">{label}</th></tr>
          <tr><th class="col-date">Datum</th><th class="col-name">Turnier</th><th class="col-disc">Disziplinen</th><th class="col-ort">Ort</th></tr>
        </thead>
        <tbody>
{rows}        </tbody>
      </table>
    </div>
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

    updated = datetime.now(TZ).strftime("%d.%m.%Y %H:%M")

    html = f"""\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=0.5, shrink-to-fit=yes">
  <title>DTFB Turniere</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 14.4px;
      font-weight: 400;
      max-width: 899px;
      margin: 2rem auto;
      padding: 0 1rem;
      color: #dee2e6;
      background: #212529;
    }}
    section {{ width: 100%; }}
    section + section {{ margin-top: 3.5rem; }}
    .col-section {{
      font-size: inherit;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      text-align: center;
      padding: 0.3rem 0.4rem;
      margin-top: 1.5rem;
    }}
    .table-wrap {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}
    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      white-space: nowrap;
      table-layout: auto;
    }}
    tr {{ border: 1px solid #32383e; }}
    th, td {{
      text-align: left;
      padding: 0.3rem 0.6rem;
      border: 1px solid #32383e;
    }}
    th {{ font-weight: bold; text-align: center; }}
    .col-date {{ text-align: center; width: 85px; }}
    .col-disc {{ text-align: left; }}
    a {{ color: #fff; text-decoration: underline; }}
    a:hover {{ opacity: 0.75; }}
    tbody tr:nth-child(odd) td {{ background: #2c3034; }}
    tbody tr:hover td {{ background: #373b3f; }}
    .updated {{
      font-size: 0.75rem;
      color: #999;
      margin-bottom: 0.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .updated a {{ color: #999; text-decoration: none; }}
    .updated a:hover {{ color: #dee2e6; opacity: 1; }}
  </style>
</head>
<body>
  <p class="updated"><span>Zuletzt aktualisiert: {updated}</span><a href="mailto:tifu@mario-christ.de">tifu@mario-christ.de</a></p>
{sections_html}
</body>
</html>
"""

    Path("docs").mkdir(exist_ok=True)
    Path("docs/index.html").write_text(html)
    print("Generated docs/index.html")


if __name__ == "__main__":
    generate()
