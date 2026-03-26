#!/bin/bash
# AI Feed 자동 수집 + push
cd /tmp/ai-feed-clean
python3 scripts/fetch_feed.py
git add data/feed.json
git diff --staged --quiet || git commit -m "chore: auto feed update $(date -u +%Y-%m-%dT%H:%M)"
git push origin main --force 2>/dev/null || true
