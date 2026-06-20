"""Source interface. Every collector yields Resource objects and never raises;
a failing source logs and yields nothing so one bad feed can't sink a run."""

from __future__ import annotations

import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class Source:
    name = "base"

    def collect(self):  # -> Iterable[Resource]
        raise NotImplementedError

    def safe_collect(self):
        try:
            yield from self.collect()
        except Exception as exc:  # noqa: BLE001 — resilience is the point
            print(f"  [{self.name}] skipped: {exc}", file=sys.stderr)
