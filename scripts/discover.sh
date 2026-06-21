#!/bin/bash
# Weekly LLM-powered discovery: run headless Claude with WebSearch to find NEW
# free AI opportunities (esp. time-sensitive ones with deadlines), then ingest
# the structured results into the local catalog. This is the ONLY part that uses
# an LLM and therefore consumes usage/credits — kept weekly to bound cost.
set -euo pipefail

REPO="/Users/zzzhu/workspace/free-yolo"
PY="$REPO/.venv/bin/python"
cd "$REPO"

read -r -d '' PROMPT <<'EOF' || true
You are a scout for FREE resources to learn, use, and understand AI. Use WebSearch
(run ~5-8 focused searches) to find resources that are NEW or TIME-SENSITIVE as of
mid-2026 — especially free live cohorts, hackathons, workshops, and courses that have
an upcoming registration deadline or start date. Prioritize the kind of thing someone
would regret missing: Google/Kaggle intensives, Hugging Face / DeepLearning.AI events,
free MOOC cohorts, AI hackathons (lablab.ai, Devpost), conference free livestreams.

Only include things that are genuinely FREE (free, free-account, or freemium).

Output ONLY a JSON array (no prose, no markdown fences). Each element:
{
  "title": string,
  "url": string,                 // the most specific deep link, not a generic landing page
  "type": "event|course|tutorial|video|book|paper|tool|dataset|community|newsletter|article",
  "provider": string,
  "cost": "free|free-account|freemium",
  "description": string,         // one sentence
  "topics": [string],            // lowercase: llm, rag, agents, prompting, fundamentals, etc.
  "event_date": "YYYY-MM-DD"     // ONLY if it has a real start date / deadline; omit otherwise
}
If you find nothing new, output [].
EOF

echo "[$(date '+%Y-%m-%d %H:%M')] discover: querying Claude…"
RAW="$(claude -p "$PROMPT" --allowedTools WebSearch --model claude-sonnet-4-6 --output-format text || true)"

# Robustly extract the JSON array even if wrapped in stray text/fences.
JSON="$(printf '%s' "$RAW" | "$PY" -c 'import sys; s=sys.stdin.read(); i=s.find("["); j=s.rfind("]"); sys.stdout.write(s[i:j+1] if 0<=i<j else "[]")')"

printf '%s' "$JSON" | "$PY" -m freeyolo.cli ingest

# Refresh the digest and notify if anything is closing soon.
DIGEST="$("$PY" -m freeyolo.cli digest --within 30)"
echo "$DIGEST" > "$REPO/data/digest-latest.txt"
if printf '%s' "$DIGEST" | grep -q '⏰'; then
    COUNT="$(printf '%s' "$DIGEST" | grep -c '📅' || true)"
    osascript -e "display notification \"$COUNT free AI opportunity(ies) closing within 30 days (after weekly discovery).\" with title \"free-yolo\" sound name \"Glass\"" 2>/dev/null || true
fi

# Push the LLM-discovered finds to the public site (Pages redeploys on push).
# Guarded: only if a remote/upstream is configured, and never fails the script.
if git -C "$REPO" remote get-url origin >/dev/null 2>&1; then
    git -C "$REPO" add -A docs RESOURCES.md data/resources.db data/metrics.json data/metrics-history.csv data/seeds.yaml 2>/dev/null || true
    if ! git -C "$REPO" diff --cached --quiet; then
        git -C "$REPO" commit -m "discover: weekly LLM-found resources" >/dev/null 2>&1 || true
        git -C "$REPO" pull --rebase --autostash >/dev/null 2>&1 || true
        git -C "$REPO" push >/dev/null 2>&1 || echo "  (push skipped — set an upstream to publish)"
    fi
fi
echo "[$(date '+%Y-%m-%d %H:%M')] discover done"
