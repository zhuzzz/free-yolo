"""Core data model: a single free AI resource."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

# Controlled vocabularies — kept small on purpose so filtering stays useful.
TYPES = [
    "course",      # structured multi-lesson learning
    "tutorial",    # single how-to / guide
    "video",       # talk, lecture, youtube
    "book",        # free book / ebook
    "paper",       # research paper
    "tool",        # something you can use (playground, library, app)
    "dataset",     # data to practice on
    "community",   # forum, discord, subreddit
    "event",       # time-bound: live cohort, workshop, hackathon
    "newsletter",  # recurring article feed
    "article",     # blog post
    "other",
]

COST = ["free", "free-account", "freemium"]

# Tracking params we strip when computing a resource's stable identity.
_TRACKING = re.compile(r"^(utm_|fbclid|gclid|ref|ref_src|mc_|igsh|si)$", re.I)


def _normalize_url(url: str) -> str:
    """Canonicalize a URL so the same resource hashes to one id."""
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parts.path.rstrip("/") or "/"
    query = urlencode(
        [(k, v) for k, v in parse_qsl(parts.query) if not _TRACKING.match(k)]
    )
    return urlunsplit((scheme, netloc, path, query, ""))


def _today() -> str:
    return date.today().isoformat()


@dataclass
class Resource:
    title: str
    url: str
    description: str = ""
    type: str = "other"
    topics: list[str] = field(default_factory=list)
    cost: str = "free"
    source: str = "manual"          # which collector found it
    provider: str = ""              # Google / Hugging Face / fast.ai ...
    found_at: str = field(default_factory=_today)
    event_date: str | None = None   # start date or registration deadline (ISO)
    status: str = "active"          # active | expired
    notes: str = ""
    id: str = ""                    # derived from normalized url

    def __post_init__(self) -> None:
        # YAML may parse a bare date (2026-07-06) into a date/datetime object.
        if isinstance(self.event_date, (date, datetime)):
            self.event_date = self.event_date.isoformat()
        self.url = _normalize_url(self.url)
        if not self.id:
            # Identity is url + title: dedupes the same resource across re-runs
            # and sources, without silently merging two distinct events that
            # happen to share one generic landing-page URL.
            key = f"{self.url}\n{self.title.strip().lower()}"
            self.id = hashlib.sha1(key.encode()).hexdigest()[:16]
        if self.type not in TYPES:
            self.type = "other"
        if self.cost not in COST:
            self.cost = "free"
        # A past event_date means the chance is gone.
        if self.event_date and self.status == "active" and _is_past(self.event_date):
            self.status = "expired"

    @property
    def is_time_sensitive(self) -> bool:
        return self.event_date is not None

    def to_row(self) -> dict:
        d = asdict(self)
        d["topics"] = ",".join(self.topics)
        return d

    @classmethod
    def from_row(cls, row: dict) -> "Resource":
        data = dict(row)
        topics = data.get("topics") or ""
        data["topics"] = [t for t in topics.split(",") if t]
        return cls(**data)


def _is_past(iso: str) -> bool:
    try:
        return datetime.fromisoformat(iso).date() < date.today()
    except ValueError:
        return False
