"""Curated seed resources loaded from data/seeds.yaml.

This is the backbone of the catalog: hand-picked, known-good free AI resources
so the tool is useful on day one without waiting for crawls.
"""

from __future__ import annotations

import yaml

from ..classify import enrich
from ..models import Resource
from .base import Source, DATA_DIR


class SeedSource(Source):
    name = "seed"

    def __init__(self, path=None):
        self.path = path or (DATA_DIR / "seeds.yaml")

    def collect(self):
        if not self.path.exists():
            return
        items = yaml.safe_load(self.path.read_text()) or []
        for item in items:
            r = Resource(source=self.name, **item)
            yield enrich(r)
