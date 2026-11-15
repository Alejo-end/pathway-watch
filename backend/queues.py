"""The county's general queues at two steps of the pathway, from Sotkanet.

Neither indicator is about cancer. A patient with alarm symptoms should not wait in the non-urgent
queue. A long queue still shows pressure at that step in the county, and it is the only public,
per-county figure for the steps that the lymphoma study shows to be slow on the public route.
"""

from __future__ import annotations

from . import analysis as A
from .indicators import NATIONAL
from .sotkanet import CountyData

# Indicator -> the step of the lymphoma study timeline it stands beside, and how to read it.
QUEUES = {
    6411: {"step": "First contact to physician appointment",
           "what": "non-urgent primary care physician visits that took place more than 7 days after the need was assessed",
           "unit": "%"},
    3336: {"step": "Referral to specialist appointment",
           "what": "patients who waited more than 6 months for specialised care during the year, per 10 000 inhabitants",
           "unit": "per 10 000"},
}


def county_queues(data: CountyData, county: str) -> list[dict]:
    """Each queue in the latest year: the county, Finland, the difference and the rank (1 = longest queue)."""
    out = []
    for ind, spec in QUEUES.items():
        g = A.gap(data, ind, county)
        if g.year is None:
            continue
        latest = {c: data.series(ind, c).get(g.year) for c in data.counties}
        ranked = sorted((v for v in latest.values() if v is not None), reverse=True)
        out.append({
            "indicator": ind, "source": f"sotkanet:{ind}", **spec, "year": g.year,
            "county": g.county_value, "national": data.series(ind, NATIONAL).get(g.year),
            "difference": g.gap, "side": {"above": "longer", "below": "shorter"}.get(g.direction, "near"),
            "rank": ranked.index(g.county_value) + 1, "of": len(ranked),
            "years_same_side": g.years_same_side, "n_years": len(g.years),
        })
    return out


# ---------- specialised care queues by specialty, from THL ----------

import json  # noqa: E402
from functools import lru_cache  # noqa: E402
from pathlib import Path  # noqa: E402

THL_FILE = Path(__file__).resolve().parent.parent / "data" / "raw" / "thl_eshjono.json"
MIN_WAITING = 30  # pooled patient-months below this give no share: a few patients swing it by tens of points

# The specialties on each cancer's pathway, with the step each one stands for.
PATHWAY_SPECIALTIES = {
    "bowel": [("10G", "Diagnosis: gastroenterology, where colonoscopy is booked"),
              ("20G", "Treatment: gastrointestinal surgery"),
              ("65", "Treatment: oncology and radiotherapy")],
    "breast": [("65", "Treatment: oncology and radiotherapy")],
    "cervical": [("30", "Diagnosis and treatment: gynaecology"),
                 ("65", "Treatment: oncology and radiotherapy")],
    "lung": [("80", "Diagnosis: respiratory medicine"),
             ("65", "Treatment: oncology and radiotherapy")],
}
# THL reports specialised care by provider. HUS provides it for the four Uusimaa counties and Helsinki.
HUS = {"01", "02", "03", "04", "90"}


@lru_cache(maxsize=None)
def _thl() -> dict:
    return json.loads(THL_FILE.read_text()) if THL_FILE.exists() else {"rows": [], "months": []}


@lru_cache(maxsize=None)
def _finnish_names() -> dict[str, str]:
    """THL names a provider by the county's Finnish name, as Sotkanet's region list does."""
    regions = json.loads((THL_FILE.parent / "regions.json").read_text())
    return {r["code"]: r["title"]["fi"] for r in regions}


def _provider(county: str) -> str:
    return "HUS" if county in HUS else _finnish_names().get(county, "")


def _pooled(rows: list[dict]) -> tuple[float, float, int]:
    """Patients waiting and those over 90 days, summed over the month-ends that report both."""
    ok = [r for r in rows if r["waiting"] is not None and r["waiting_over_90_days"] is not None]
    return sum(r["waiting"] for r in ok), sum(r["waiting_over_90_days"] for r in ok), len(ok)


def specialist_queues(cancer: str, county: str) -> list[dict]:
    """For each specialty on the pathway: the share of waiting patients who had waited more than 90 days,
    pooled over the last six month-ends, for the county's provider and for Finland."""
    d = _thl()
    by = {}
    for r in d["rows"]:
        by.setdefault((r["specialty"], r["provider"]), []).append(r)
    provider = _provider(county)
    out = []
    for code, step in PATHWAY_SPECIALTIES.get(cancer, []):
        waiting, over, months = _pooled(by.get((code, provider), []))
        n_w, n_o, _ = _pooled(by.get((code, "Finland"), []))
        share = round(100 * over / waiting, 1) if waiting >= MIN_WAITING else None
        others = []
        for (c, p), rows in by.items():
            if c == code and p != "Finland":
                w, o, _ = _pooled(rows)
                if w >= MIN_WAITING:
                    others.append(100 * o / w)
        out.append({
            "specialty": code, "label": d.get("specialties", {}).get(code, code), "step": step,
            "provider": provider, "shared": county in HUS,
            "share_over_90": share, "national_over_90": round(100 * n_o / n_w, 1) if n_w else None,
            "waiting_months": int(waiting), "months": months,
            "rank": None if share is None else 1 + sum(1 for x in others if x > 100 * over / waiting),
            "of": len(others),
            "period": f"{d['months'][0]} to {d['months'][-1]}" if d["months"] else None,
            "source": "thl_eshjono",
        })
    return out
