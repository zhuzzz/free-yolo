# 🦾 free-yolo

Collect, dedupe and surface **free resources for learning, using and understanding AI** —
and catch the *time-sensitive* ones (live cohorts, hackathons, course deadlines) **before they expire**.

> Born from missing Google's *5-Day Gen AI Intensive* because we found it after it ended.
> The point isn't another static "awesome list" — it's not missing the next one.

## How it works

```
sources ─┐
  seed   │   curated YAML backbone (known-good resources)
  rss    ├─▶ collect ─▶ dedupe ─▶ classify ─▶ SQLite ─▶ export ─┬▶ RESOURCES.md
  github │                                                       └▶ site/index.html
websearch┘   (fed in via `ingest`)                                  (static, free hosting)
```

Two layers of value:
- **Catalog** — a searchable, deduped database of free AI resources, exported as a Markdown
  list and a self-contained static web page (host on GitHub Pages for free).
- **Don't-miss radar** — resources with a start date / deadline are flagged and sorted first,
  so time-sensitive opportunities surface while you can still act on them.

## Quick start

```bash
pip install -e .            # or: pip install pyyaml feedparser requests

freeyolo collect            # run all sources, store, regenerate md + site
freeyolo stats              # counts by type
freeyolo list --dated       # just the time-sensitive ones
open site/index.html        # browse/filter in the browser
```

Outputs: [`RESOURCES.md`](RESOURCES.md), `site/index.html` (live board), and
`site/archive.html` (departed/expired opportunities). Each export moves any resource
whose deadline has passed into the archive automatically.

## Commands

| command | what it does |
|---|---|
| `freeyolo collect` | run seed + RSS + GitHub sources, upsert, re-export |
| `freeyolo export` | regenerate `RESOURCES.md` and `site/index.html` from the DB |
| `freeyolo list [--type T] [--dated]` | print the catalog |
| `freeyolo add "Title" URL --type course --date 2026-09-01` | add one by hand |
| `freeyolo ingest` | read a JSON array of resources from stdin |
| `freeyolo digest [--within 30]` | print upcoming time-sensitive opportunities (reminder payload) |
| `freeyolo stats` | quick counts |

## Sources

- **seed** (`data/seeds.yaml`) — hand-picked, verified free resources. The backbone.
- **rss** (`data/feeds.yaml`) — polls AI-education feeds for new posts & announcements.
- **github** — searches the public GitHub API for free-course / awesome-list repos.
- **websearch** — not a crawler: feed live web-search results in via `ingest` (below).

### Feeding in web-search discoveries

The highest-signal time-sensitive finds (new cohorts, hackathons) come from web search.
A scheduled Claude Code agent can search, then pipe structured results in:

```bash
echo '[{"title":"Some New Free AI Cohort","url":"https://...","type":"event",
        "provider":"X","event_date":"2026-09-01","description":"..."}]' \
  | freeyolo ingest
```

## Keeping it fresh (scheduling)

Two local launchd jobs (macOS, in `scripts/`) keep the catalog current — no cloud, no email:

| job | schedule | what it does | cost |
|---|---|---|---|
| `com.freeyolo.daily` | daily 09:00 | `daily.sh`: `collect` + re-export, write `data/digest-latest.txt`, macOS notification if anything closes within 30 days | free (pure Python) |
| `com.freeyolo.discover` | Mon 09:30 | `discover.sh`: headless Claude (`claude -p`) runs WebSearch for new/time-sensitive free AI opportunities → `ingest` into the catalog | uses LLM credits (kept weekly) |

Install / reload:

```bash
cp scripts/com.freeyolo.*.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.freeyolo.daily.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.freeyolo.discover.plist
# run one now without waiting for the schedule:
launchctl kickstart -k gui/$(id -u)/com.freeyolo.daily
```

The daily job is free and surfaces deadlines from the existing catalog; the weekly discover
job is the only LLM-powered (paid) piece, so it runs infrequently. Logs: `data/daily.log`,
`data/discover.log`.

## Data model

Each resource: `title, url, description, type, topics[], cost, source, provider, found_at,
event_date, status`. Identity is a hash of the normalized URL (tracking params stripped), so
the same resource from multiple sources collapses to one entry. A past `event_date` auto-marks
the resource `expired` and drops it from the active list.
