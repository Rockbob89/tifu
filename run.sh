#!/bin/bash
set -e
cd "$(dirname "$0")"

python3 scraper.py
python3 generate.py

if git diff --quiet && git diff --cached --quiet; then
    echo "No changes, skipping commit."
    exit 0
fi

git add data/tournaments.json docs/index.html
git commit -m "chore: daily update $(date +%Y-%m-%d)"
git push
