#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_URL = "https://api.tournament.io/v1/table_soccer/result/tournaments?from={from_ms}&to={to_ms}&filter=dtfb"


def fetch_tournaments():
    now = datetime.now(timezone.utc)
    from_ms = int((now - timedelta(days=30)).timestamp() * 1000)
    to_ms = int((now + timedelta(days=365)).timestamp() * 1000)

    url = API_URL.format(from_ms=from_ms, to_ms=to_ms)
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())

    Path("data").mkdir(exist_ok=True)
    Path("data/tournaments.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )
    print(f"Fetched {len(data)} tournaments")


if __name__ == "__main__":
    fetch_tournaments()
