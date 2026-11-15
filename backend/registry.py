"""How much the Finnish Cancer Registry knows about stage in each county.

The registry publishes stage at diagnosis for the whole country only. It records stage from the
clinical notification, the treating unit's summary of a new cancer. Its quality application gives,
per county and year, the share of new cancers for which that summary arrived. A low share means
that even the registry cannot tell early from late diagnoses in the county.
"""

from __future__ import annotations

import json
from functools import lru_cache

from .indicators import NATIONAL
from .sotkanet import RAW

FILE = RAW / "fcr_clinical_notifications.json"


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(FILE.read_text())


def notification_shares(cancer: str, county: str) -> dict | None:
    """Yearly shares for the county and for Finland, or None for a cancer the application does not cover."""
    doc = _load()
    site = doc["sites"].get(cancer)
    if not site or county not in site:
        return None
    return {"years": doc["years"], "county": site[county], "national": site[NATIONAL]}


def _span(values: list[int]) -> str:
    lo, hi = min(values), max(values)
    return f"{lo}%" if lo == hi else f"{lo}% to {hi}%"


def stage_sentence(cancer: str, county: str, name: str) -> str | None:
    """One sentence for the pathway notes: how much stage the registry can know in this county."""
    s = notification_shares(cancer, county)
    if s is None:
        return None
    y = s["years"]
    return (f"The Cancer Registry records stage from the clinical notification of the treating unit. For {name}, it "
            f"received one for {_span(s['county'])} of new cases each year from {y[0]} to {y[-1]} (Finland: "
            f"{_span(s['national'])}). Stage per county is not published, and where this share is low the registry "
            "cannot tell early from late diagnoses either. The county's own records can.")
