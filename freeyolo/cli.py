"""Command-line entry point.

  freeyolo collect      run all sources, upsert into the DB, report new finds
  freeyolo export       (re)generate RESOURCES.md and site/index.html
  freeyolo list         print the catalog (optionally filtered)
  freeyolo add          manually add one resource
  freeyolo ingest       read a JSON array of resources from stdin (web-search feed)
  freeyolo stats        quick counts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import export_markdown, export_site
from .classify import enrich
from .db import Store, DEFAULT_DB
from .models import Resource
from .sources import all_sources

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "RESOURCES.md"
SITE_PATH = ROOT / "site" / "index.html"
ARCHIVE_PATH = ROOT / "site" / "archive.html"


def _store(args) -> Store:
    return Store(args.db)


def cmd_collect(args) -> None:
    store = _store(args)
    total_new = 0
    for src in all_sources():
        before = total_new
        new = store.upsert_many(src.safe_collect())
        total_new += new
        print(f"  [{src.name}] +{new} new")
    print(f"Done. {total_new} new, {store.count()} total in catalog.")
    if not args.no_export:
        _export(store)


def cmd_export(args) -> None:
    _export(_store(args))


def _export(store: Store) -> None:
    newly_expired = store.expire()          # past deadlines move into the archive
    active = store.all(status="active")
    archived = store.all(status="expired")
    export_markdown.write(active, MD_PATH)
    export_site.write(active, SITE_PATH, mode="live",
                      xhref="archive.html", xtext=f"✈ Departed archive ({len(archived)})")
    export_site.write(archived, ARCHIVE_PATH, mode="archive",
                      xhref="index.html", xtext="← Back to live board")
    print(f"Wrote site/index.html ({len(active)} live) + archive.html "
          f"({len(archived)} archived, +{newly_expired} newly expired).")


def cmd_list(args) -> None:
    store = _store(args)
    for r in store.all():
        if args.type and r.type != args.type:
            continue
        if args.dated and not r.is_time_sensitive:
            continue
        date = f" 📅{r.event_date}" if r.event_date else ""
        prov = f" ({r.provider})" if r.provider else ""
        print(f"[{r.type}]{date} {r.title}{prov}\n   {r.url}")


def cmd_add(args) -> None:
    store = _store(args)
    r = enrich(Resource(
        title=args.title, url=args.url, description=args.description or "",
        type=args.type, provider=args.provider or "", source="manual",
        event_date=args.date,
    ))
    new = store.upsert(r)
    print(f"{'Added' if new else 'Updated'}: {r.title}")
    if not args.no_export:
        _export(store)


def cmd_ingest(args) -> None:
    """Ingest a JSON array of resource dicts from stdin.

    This is how a scheduled Claude agent feeds WebSearch discoveries in:
        echo '[{"title": "...", "url": "...", "type": "event", ...}]' \\
            | freeyolo ingest
    """
    store = _store(args)
    payload = json.load(sys.stdin)
    if isinstance(payload, dict):
        payload = [payload]
    resources = []
    for item in payload:
        item.setdefault("source", "websearch")
        resources.append(enrich(Resource(**item)))
    new = store.upsert_many(resources)
    print(f"Ingested {len(resources)} ({new} new).")
    if not args.no_export:
        _export(store)


def cmd_digest(args) -> None:
    """Print upcoming time-sensitive resources — the reminder payload.

    A scheduled job pipes this into an email/notification so deadlines (like the
    Google 5-Day Intensive) surface while you can still act on them.
    """
    from datetime import date, datetime, timedelta

    store = _store(args)
    cutoff = date.today() + timedelta(days=args.within)
    upcoming = []
    for r in store.all(status="active"):
        if not r.event_date:
            continue
        try:
            d = datetime.fromisoformat(r.event_date).date()
        except ValueError:
            continue
        if date.today() <= d <= cutoff:
            upcoming.append((d, r))
    upcoming.sort(key=lambda x: x[0])

    if not upcoming:
        print(f"No free AI opportunities with a deadline in the next {args.within} days.")
        return
    print(f"⏰ {len(upcoming)} free AI opportunity(ies) closing within {args.within} days:\n")
    for d, r in upcoming:
        days = (d - date.today()).days
        when = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
        print(f"📅 {r.event_date} ({when}) — {r.title}")
        print(f"   {r.url}")
        if r.notes:
            print(f"   {r.notes}")
        print()


def cmd_stats(args) -> None:
    store = _store(args)
    resources = store.all()
    by_type: dict[str, int] = {}
    for r in resources:
        by_type[r.type] = by_type.get(r.type, 0) + 1
    dated = sum(1 for r in resources if r.is_time_sensitive and r.status == "active")
    print(f"{len(resources)} total · {dated} active time-sensitive")
    for t, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>4}  {t}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="freeyolo", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=str(DEFAULT_DB), help="path to SQLite db")
    p.add_argument("--no-export", action="store_true",
                   help="skip regenerating md/site after a mutation")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("collect", help="run all sources").set_defaults(func=cmd_collect)
    sub.add_parser("export", help="regenerate md + site").set_defaults(func=cmd_export)
    sub.add_parser("stats", help="counts by type").set_defaults(func=cmd_stats)
    sub.add_parser("ingest", help="ingest JSON from stdin").set_defaults(func=cmd_ingest)

    pd = sub.add_parser("digest", help="upcoming time-sensitive opportunities")
    pd.add_argument("--within", type=int, default=30, help="days ahead (default 30)")
    pd.set_defaults(func=cmd_digest)

    pl = sub.add_parser("list", help="print catalog")
    pl.add_argument("--type")
    pl.add_argument("--dated", action="store_true", help="only time-sensitive")
    pl.set_defaults(func=cmd_list)

    pa = sub.add_parser("add", help="add one resource")
    pa.add_argument("title")
    pa.add_argument("url")
    pa.add_argument("--type", default="other")
    pa.add_argument("--provider")
    pa.add_argument("--description")
    pa.add_argument("--date", help="event date / deadline (YYYY-MM-DD)")
    pa.set_defaults(func=cmd_add)

    args = p.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
