"""Discover free AI learning repos via the public GitHub search API.

No auth needed (unauthenticated rate limit is ~10 search req/min, plenty for a
periodic run). Surfaces 'awesome' lists and free course repos.
"""

from __future__ import annotations

from ..classify import enrich
from ..models import Resource
from .base import Source

QUERIES = [
    "free AI course in:name,description,readme stars:>500",
    "awesome LLM in:name stars:>1000",
    "machine learning roadmap in:name,description stars:>1000",
]
PER_QUERY = 6


class GitHubSource(Source):
    name = "github"

    def __init__(self, queries=None, per_query: int = PER_QUERY):
        self.queries = queries or QUERIES
        self.per_query = per_query

    def collect(self):
        import requests

        seen = set()
        for q in self.queries:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": q, "sort": "stars", "per_page": self.per_query},
                headers={"Accept": "application/vnd.github+json"},
                timeout=20,
            )
            if resp.status_code != 200:
                continue
            for repo in resp.json().get("items", []):
                full = repo["full_name"]
                if full in seen:
                    continue
                seen.add(full)
                r = Resource(
                    title=full,
                    url=repo["html_url"],
                    description=(repo.get("description") or "")[:400],
                    type="course" if "course" in q else "tutorial",
                    provider="GitHub",
                    source="github",
                    notes=f"★{repo.get('stargazers_count', 0)}",
                )
                yield enrich(r)
