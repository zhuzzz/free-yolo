"""Collectors that yield Resource objects from various places."""

from .seed import SeedSource
from .rss import RSSSource
from .github import GitHubSource

__all__ = ["SeedSource", "RSSSource", "GitHubSource", "all_sources"]


def all_sources():
    """The default collection pipeline, cheapest/most-reliable first."""
    return [SeedSource(), RSSSource(), GitHubSource()]
