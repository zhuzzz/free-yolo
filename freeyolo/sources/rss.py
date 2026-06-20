"""Pull recent posts from curated AI-education feeds (data/feeds.yaml).

Feeds keep the catalog fresh: new tutorials, course announcements and talks
show up here days after they're published.
"""

from __future__ import annotations

import yaml

from ..classify import enrich
from ..models import Resource
from .base import Source, DATA_DIR

MAX_PER_FEED = 8


class RSSSource(Source):
    name = "rss"

    def __init__(self, path=None, max_per_feed: int = MAX_PER_FEED):
        self.path = path or (DATA_DIR / "feeds.yaml")
        self.max_per_feed = max_per_feed

    def collect(self):
        import feedparser  # imported lazily so `--help` works without deps

        if not self.path.exists():
            return
        feeds = yaml.safe_load(self.path.read_text()) or []
        for feed in feeds:
            url = feed["url"]
            provider = feed.get("provider", "")
            default_type = feed.get("type", "article")
            parsed = feedparser.parse(url)
            for entry in parsed.entries[: self.max_per_feed]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue
                summary = entry.get("summary", "")[:400]
                r = Resource(
                    title=title,
                    url=link,
                    description=_strip_html(summary),
                    type=default_type,
                    provider=provider,
                    source=f"rss:{provider or url}",
                )
                yield enrich(r)


def _strip_html(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text).strip()
