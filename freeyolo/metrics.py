"""Catalog observability: a metrics snapshot + growth history, and the scaling tier.

Lets the user watch the catalog approach the ~10k threshold and confirm the export
auto-switched strategies (Tier A inline → B external json → C indexed/paginated).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

from .db import Store
from .export_site import tier_for, TIER_B_MIN, TIER_C_MIN

_HIST_COLS = ["date", "total", "active", "expired", "dated", "tier"]


def compute(store: Store) -> dict:
    resources = store.all()
    active = [r for r in resources if r.status == "active"]
    n = len(active)
    next_threshold = TIER_B_MIN if n < TIER_B_MIN else (TIER_C_MIN if n < TIER_C_MIN else None)
    return {
        "date": date.today().isoformat(),
        "total": len(resources),
        "active": n,
        "expired": sum(1 for r in resources if r.status == "expired"),
        "dated": sum(1 for r in active if r.event_date),
        "tier": tier_for(n),
        "next_threshold": next_threshold,
        "to_next_threshold": (next_threshold - n) if next_threshold else None,
        "by_source": dict(Counter(r.source.split(":")[0] for r in active).most_common()),
        "by_type": dict(Counter(r.type for r in active).most_common()),
    }


def write(store: Store, data_dir: Path) -> dict:
    """Write data/metrics.json and append a row to data/metrics-history.csv."""
    data_dir = Path(data_dir)
    m = compute(store)
    (data_dir / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=2))

    hist = data_dir / "metrics-history.csv"
    fresh = not hist.exists()
    with hist.open("a") as f:
        if fresh:
            f.write(",".join(_HIST_COLS) + "\n")
        f.write(",".join(str(m[c]) for c in _HIST_COLS) + "\n")
    return m
