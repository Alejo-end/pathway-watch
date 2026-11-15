"""A safe, implementable radiotherapy equity pilot.

The public sources used by Cancer Care Atlas do not contain patient-level radiotherapy
data.  This module therefore deliberately contains a measurement specification, not a
claim about a county's radiotherapy performance.  A hospital may implement it only after
its data controller, radiation oncology lead and quality team approve the protocol.
"""

from __future__ import annotations


PILOT = {
    "title": "Radiotherapy equity baseline: measure before attributing a treatment gap",
    "status": "protocol, not county performance data",
    "purpose": (
        "Find whether access to radiotherapy differs after a multidisciplinary team has decided that it is indicated. "
        "It does not decide whether radiotherapy is right for an individual patient."
    ),
    "unit": "One completed course of external-beam radiotherapy; report only aggregate results.",
    "cohort": {
        "include": "Adults whose multidisciplinary team records radiotherapy as indicated, grouped by tumour site and treatment intent.",
        "exclude": "Courses cancelled because the clinical indication changed, and records without an indication date; report each exclusion count.",
    },
    "timestamps": [
        {"name": "Decision", "field": "MDT decision date, treatment intent (radical, adjuvant or palliative) and urgency category", "owner": "MDT / oncology"},
        {"name": "Clinical clock", "field": "For adjuvant courses, the date of surgery or of the last chemotherapy cycle, because the MDT date does not start the clinical clock", "owner": "MDT / oncology"},
        {"name": "Referral", "field": "Radiotherapy referral accepted date", "owner": "radiotherapy service"},
        {"name": "Ready to start", "field": "CT simulation and approved-plan dates", "owner": "physics / planning"},
        {"name": "Treatment", "field": "First and final fraction dates, including brachytherapy fractions", "owner": "treatment unit"},
    ],
    "measures": [
        "Median and 90th-percentile days from MDT decision to first fraction, by tumour site, intent and urgency category. Report palliative and radical courses apart: a short palliative wait hides a long radical one in a pooled median.",
        "For adjuvant courses, days from surgery or the last chemotherapy cycle to first fraction.",
        "For definitive chemoradiotherapy of cervical cancer, overall treatment time from the first external fraction to the last brachytherapy fraction. In a multicentre series, each extra day lowered local control (hazard ratio 1.023 per day), so a county without local brachytherapy can lose control through travel and scheduling alone.",
        "Share starting within the locally agreed target; publish the target beside the result rather than importing one from another pathway.",
        "Share with an interruption, cancellation or material change after planning, with the reason category and missingness shown.",
        "Travel burden: travel-time band to the treatment unit, reported as an aggregate distribution only.",
    ],
    "stratifiers": "County of residence, tumour site, treatment intent, age band and travel-time band. Do not rank named clinicians or infer individual appropriateness.",
    "quality": "Freeze a data dictionary, reconcile referral and first-fraction dates with the oncology information system, report missing values, and review outliers before release.",
    "privacy": "Suppress every cell below five courses; no patient-level export, free text, identifiers or clinician-level comparison in this tool.",
    "governance": "Named data controller, radiation oncology clinical lead, medical physics lead and quality-register contact approve the cohort, legal basis and release before the first extract.",
    "decision_rule": "After the baseline and the first quarterly report, investigate a persistent difference only if data completeness is at least 95%, the comparison is case-mix reviewed and the governance group agrees the signal is actionable.",
    "limits": "Capacity, travel, delay and completion do not measure benefit or appropriateness. Any comparison needs case-mix review and cannot establish that a delay caused an outcome.",
    "sources": ["borras_2015", "hanna_2020", "tanderup_2016", "local_step"],
}


# ---------- where each county's patients get radiotherapy ----------

import json  # noqa: E402
import math  # noqa: E402
from functools import lru_cache  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UNITS_FILE = ROOT / "data" / "radiotherapy_units.json"
MAP_FILE = ROOT / "web" / "counties.geojson"


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres. A straight line, so always shorter than the road."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


@lru_cache(maxsize=None)
def _outlines() -> dict[str, list[tuple[float, float]]]:
    """Every outline point of every county on the app's map, as (lat, lon)."""
    geo = json.loads(MAP_FILE.read_text())
    out: dict[str, list[tuple[float, float]]] = {}
    for f in geo["features"]:
        polys = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
        out[f["properties"]["hyvinvointialue"]] = [(lat, lon) for poly in polys for ring in poly for lon, lat in ring]
    return out


@lru_cache(maxsize=None)
def units() -> dict:
    return json.loads(UNITS_FILE.read_text())


def access(county: str) -> dict:
    """The radiotherapy unit that serves a county, and how far its farthest edge lies from that unit.

    `farthest_km` is the straight line from the unit to the farthest point of the county outline,
    rounded to 10 km. It is a lower bound for the longest trip, not a travel time. A county whose
    unit no public source names gets no unit and no distance.
    """
    d = units()
    served = d["served_by"].get(county) or {"unit": None, "basis": "not_verified"}
    if not served["unit"]:
        return {"county": county, "unit": None, "verified": False, "in_county": False, "farthest_km": None,
                "basis": "No public source that we found names the unit that treats this county's patients."}
    keys = served["unit"] if isinstance(served["unit"], list) else [served["unit"]]
    us = [d["units"][k] for k in keys]
    points = _outlines().get(county, [])
    # The farthest point of the county, measured to the nearest of its units.
    far = max((min(km(u["lat"], u["lon"], lat, lon) for u in us) for lat, lon in points), default=None)
    return {
        "county": county,
        "unit": " or ".join(u["name"] for u in us),
        "city": " or ".join(u["city"] for u in us),
        "verified": True,
        "in_county": any(u["county"] == county for u in us),
        "farthest_km": None if far is None else int(round(far, -1)),
        "basis": us[0]["says"] if served["basis"] == "own" else served["basis"] + ".",
        "url": served.get("url") or us[0]["url"],
    }


def access_all(counties: list[str]) -> list[dict]:
    """Every county, the farthest first. Counties without a verified unit come last."""
    rows = [access(c) for c in counties]
    return sorted(rows, key=lambda r: (r["farthest_km"] is None, -(r["farthest_km"] or 0)))
