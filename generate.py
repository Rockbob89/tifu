#!/usr/bin/env python3
import html as html_mod
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

TZ = ZoneInfo("Europe/Berlin")

BASE_URL = "https://live.kickertool3.de"

STALE_THRESHOLD = timedelta(hours=48)

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
RUNNING_STATES = {"running", "check-in"}
PLANNED_STATES = {"planned", "pre-registration"}

ALWAYS_INCLUDE_ORTE = {"Kixx Hamburg"}

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

            ort_attr = html_mod.escape(ort, quote=True)
            name_attr = html_mod.escape(name, quote=True)
            rows += (
                f'      <tr data-ort="{ort_attr}" data-name="{name_attr}">'
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

    now = datetime.now(timezone.utc)
    grouped = {k: [] for k in SECTION_ORDER}
    for t in data:
        section = state_to_section(t.get("state"))
        if not section:
            continue
        if section == "running":
            t_date = datetime.fromisoformat(t["date"].replace("Z", "+00:00"))
            if now - t_date > STALE_THRESHOLD:
                grouped["finished"].append(t)
                continue
        grouped[section].append(t)

    grouped["running"].sort(key=lambda t: t["date"])
    grouped["planned"].sort(key=lambda t: t["date"])
    grouped["finished"].sort(key=lambda t: t["date"], reverse=True)

    # Top-Orte für Tags berechnen
    ort_counts = Counter(
        t.get("resultPage", {}).get("name", "")
        for t in data if t.get("resultPage", {}).get("name", "")
    )
    top_orte = [ort for ort, _ in ort_counts.most_common(10)]
    for ort in ALWAYS_INCLUDE_ORTE:
        if ort not in top_orte:
            top_orte.append(ort)
    top_orte = sorted(top_orte, key=lambda o: (o not in ALWAYS_INCLUDE_ORTE, top_orte.index(o)))

    all_orte_extra = sorted(
        [ort for ort in ort_counts if ort not in top_orte],
        key=lambda o: o.lower()
    )
    all_orte = top_orte + all_orte_extra

    tag_buttons = ""
    for i, ort in enumerate(all_orte):
        extra = ' tag-extra' if i >= len(top_orte) else ''
        tag_buttons += (
            f'<button class="tag{extra}" data-filter-ort="{html_mod.escape(ort, quote=True)}">{html_mod.escape(ort)}</button>'
        )
    tag_buttons += '<button class="tag tag-toggle" id="toggle-tags">alle Orte &raquo;</button>'

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
    .filter-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
      margin-bottom: 1.5rem;
    }}
    .filter-bar {{
      flex-direction: column;
    }}
    .search-wrap {{
      position: relative;
      width: 100%;
    }}
    .search-clear {{
      position: absolute;
      right: 6px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: #999;
      font-size: 18px;
      cursor: pointer;
      padding: 0 8px;
      border-left: 1px solid #999;
      line-height: 1;
    }}
    .search-clear:hover {{
      color: #dee2e6;
    }}
    .filter-bar input {{
      width: 100%;
      padding: 0.4rem 0.6rem;
      font-size: 14.4px;
      background: #2c3034;
      border: 1px solid #32383e;
      color: #dee2e6;
      border-radius: 4px;
      outline: none;
    }}
    .filter-bar input:focus {{
      border-color: #dee2e6;
    }}
    .tag-extra {{
      display: none;
    }}
    .tag-row.expanded .tag-extra {{
      display: inline-block;
    }}
    .tag-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}
    .tag {{
      padding: 0.25rem 0.6rem;
      font-size: 12px;
      background: #2c3034;
      border: 1px solid #32383e;
      color: #999;
      border-radius: 12px;
      cursor: pointer;
      white-space: nowrap;
    }}
    @media (hover: hover) {{
      .tag:hover {{
        color: #dee2e6;
        border-color: #dee2e6;
      }}
    }}
    .tag.tag-toggle {{
      border-color: #999;
    }}
    .tag.active {{
      background: #dee2e6;
      color: #212529;
      border-color: #dee2e6;
    }}
  </style>
</head>
<body>
  <p class="updated"><span>Zuletzt aktualisiert: {updated}</span><a href="mailto:tifu@mario-christ.de">tifu@mario-christ.de</a></p>
  <div class="filter-bar">
    <div class="search-wrap">
      <input type="text" id="search" placeholder="Suche nach Turnier, Ort, Disziplin...">
      <button type="button" id="search-clear" class="search-clear">&times;</button>
    </div>
    <div class="tag-row">{tag_buttons}</div>
  </div>
{sections_html}
  <script>
  (function() {{
    var search = document.getElementById('search');
    var tags = document.querySelectorAll('.tag[data-filter-ort]');
    var activeOrt = null;

    function applyFilter() {{
      var q = search.value.toLowerCase();
      var rows = document.querySelectorAll('tbody tr');
      rows.forEach(function(row) {{
        if (!row.dataset.ort && !row.dataset.name) return;
        var text = row.textContent.toLowerCase();
        var matchText = !q || text.indexOf(q) !== -1;
        var matchOrt = !activeOrt || row.dataset.ort === activeOrt;
        row.style.display = (matchText && matchOrt) ? '' : 'none';
      }});
    }}

    var clearBtn = document.getElementById('search-clear');
    clearBtn.addEventListener('click', function() {{
      search.value = '';
      tags.forEach(function(t) {{ t.classList.remove('active'); }});
      activeOrt = null;
      applyFilter();
    }});

    var toggle = document.getElementById('toggle-tags');
    var tagRow = document.querySelector('.tag-row');
    toggle.addEventListener('click', function() {{
      tagRow.classList.toggle('expanded');
      toggle.innerHTML = tagRow.classList.contains('expanded') ? '&laquo; weniger' : 'alle Orte &raquo;';
    }});

    search.addEventListener('input', function() {{
      if (activeOrt) {{
        tags.forEach(function(t) {{ t.classList.remove('active'); }});
        activeOrt = null;
      }}
      applyFilter();
    }});

    tags.forEach(function(tag) {{
      tag.addEventListener('click', function() {{
        if (tag.classList.contains('active')) {{
          tag.classList.remove('active');
          activeOrt = null;
        }} else {{
          tags.forEach(function(t) {{ t.classList.remove('active'); }});
          tag.classList.add('active');
          activeOrt = tag.dataset.filterOrt;
          search.value = '';
        }}
        applyFilter();
      }});
    }});
  }})();
  </script>
  <script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "0b4643989a2944059cf1bcb5df4dd73b"}}'></script>
</body>
</html>
"""

    Path("docs").mkdir(exist_ok=True)
    Path("docs/index.html").write_text(html)
    print("Generated docs/index.html")


if __name__ == "__main__":
    generate()
