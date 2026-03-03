#!/bin/bash
set -e
cd "$(dirname "$0")"

TS() { date +"%Y-%m-%d %H:%M:%S"; }

trap 'echo "$(TS) - error - $BASH_COMMAND"' ERR

git pull --rebase > /dev/null 2>&1
python3 scraper.py > /dev/null 2>&1

if git diff --quiet data/tournaments.json && git diff --cached --quiet data/tournaments.json; then
    echo "$(TS) - skip - no new results"
    exit 0
fi

COUNT=$(python3 -c "import json; print(len(json.load(open('data/tournaments.json'))))")
python3 generate.py > /dev/null 2>&1
git add data/tournaments.json docs/index.html > /dev/null 2>&1
git commit -m "chore: update $(date +%Y-%m-%d@%H:%M)" > /dev/null 2>&1
git push > /dev/null 2>&1
echo "$(TS) - updated - ${COUNT} tournaments"
