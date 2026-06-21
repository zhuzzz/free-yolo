#!/bin/bash
# Daily free-yolo refresh: collect from all sources, regenerate md + site,
# then surface any free AI opportunity with a deadline in the next 30 days.
# Pure-Python, no LLM cost. Wired to run via launchd (see scripts/com.freeyolo.daily.plist).
set -euo pipefail

REPO="/Users/zzzhu/workspace/free-yolo"
PY="$REPO/.venv/bin/python"
cd "$REPO"

# 1. Refresh the catalog (also re-exports RESOURCES.md + docs/index.html).
"$PY" -m freeyolo.cli collect

# 2. Build the digest of upcoming dated opportunities.
DIGEST="$("$PY" -m freeyolo.cli digest --within 30)"
echo "$DIGEST" > "$REPO/data/digest-latest.txt"

# 3. Notify on macOS only when something is actually closing soon.
if printf '%s' "$DIGEST" | grep -q '⏰'; then
    COUNT="$(printf '%s' "$DIGEST" | grep -c '📅' || true)"
    osascript -e "display notification \"$COUNT free AI opportunity(ies) closing within 30 days. See data/digest-latest.txt\" with title \"free-yolo\" sound name \"Glass\"" 2>/dev/null || true
fi

echo "[$(date '+%Y-%m-%d %H:%M')] daily run done"
