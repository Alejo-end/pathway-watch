"""National five-year survival and case counts from NORDCAN, for Finland, Sweden and Norway.

Goal 3 defines the Nordic level as the average of Sweden and Norway. The app compares Finland
with that level only inside NORDCAN, so that all three countries use the same method.
County values from Sotkanet use another method and are never put on the same scale.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / "data" / "nordcan.json"
COUNTRIES = {"finland": "finland-246", "sweden": "sweden-752", "norway": "norway-578"}


@lru_cache(maxsize=None)
def load(path: Path = FILE) -> dict:
    """The NORDCAN file, read once per path."""
    return json.loads(path.read_text()) if path.exists() else {"sites": {}}


def combined(nc: dict, site: str, country: str) -> dict | None:
    """Both sexes together. Survival is the case-weighted average of the sexes, an approximation."""
    entry = (nc["sites"].get(site) or {}).get(COUNTRIES[country])
    if not entry:
        return None
    cases = sum(v["cases"] for v in entry.values())
    with_surv = [v for v in entry.values() if v.get("surv5") is not None]
    if not with_surv:
        return {"cases": cases, "surv5": None}
    weight = sum(v["cases"] for v in with_surv)
    return {"cases": cases, "surv5": round(sum(v["surv5"] * v["cases"] for v in with_surv) / weight, 1)}


def benchmark(nc: dict, site: str) -> dict:
    """Finland against the Nordic level. `nordic` is None unless both Sweden and Norway are known."""
    out = {c: combined(nc, site, c) for c in COUNTRIES}
    se, no = out["sweden"], out["norway"]
    nordic = round((se["surv5"] + no["surv5"]) / 2, 1) if se and no and se["surv5"] is not None and no["surv5"] is not None else None
    fi = out["finland"]["surv5"] if out["finland"] else None
    return {
        "site": site,
        "period": nc.get("period"),
        "finland": fi,
        "sweden": se["surv5"] if se else None,
        "norway": no["surv5"] if no else None,
        "nordic": nordic,
        "gap": round(fi - nordic, 1) if fi is not None and nordic is not None else None,
        "target": nc.get("goal3_targets", {}).get(site),
        "source": "nordcan",
    }
