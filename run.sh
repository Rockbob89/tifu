#!/bin/bash
set -e
cd "$(dirname "$0")"

TS() { date +"%Y-%m-%d %H:%M:%S"; }

python3 scraper.py > /dev/null
python3 generate.py > /dev/null

if git diff --quiet && git diff --cached --quiet; then
    echo "$(TS) - no changes"
    exit 0
fi

git add data/tournaments.json docs/index.html
git commit -m "chore: update $(date +%Y-%m-%d %H:%M)" > /dev/null
git push > /dev/null
echo "$(TS) - updated"
