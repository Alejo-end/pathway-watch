"""Pathway Watch endpoints.

    uv run uvicorn backend.app:app --port 8010
"""

from __future__ import annotations

import json
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import analysis as A
from . import facts as F
from . import nordcan
from . import sotkanet
from .analyst import summarize
from .channel import channel_table
from .indicators import CANCERS, NATIONAL, has_county_survival
from .priorities import ranking
from .mortality import GOAL3, LABELS, all_years, shared as shared_mortality
from .recommend import MEASURES, recommend

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
SCREENING_TARGET = 80  # % attendance in every county, national cancer strategy, page 5
GOAL3_SURVIVAL = ["lung", "pancreas", "liver"]  # the poor-prognosis cancers of Goal 3, indicator 1

data = sotkanet.load()
mort = shared_mortality()
nc = nordcan.load()
svf = json.loads((ROOT / "data" / "svf_sweden.json").read_text())
app = FastAPI(title="Pathway Watch")


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/counties.geojson")
def geojson():
    return FileResponse(WEB / "counties.geojson", media_type="application/geo+json")


@app.get("/api/meta")
def meta():
    return {
        "counties": [{"code": c, "name": data.names[c]} for c in data.counties],
        "cancers": CANCERS,
        "sources": data.sources(),
    }


# The three map layers share one shape per county: name, latest, year, gap, direction.
# `direction` is below (worse than Finland), above or near. A Sotkanet layer adds `persistence`,
# a survival layer also adds our rough `interval`, and the mortality layer adds `confidence`
# from its 95% interval.
SURVIVAL_OF = {spec["survival"]: key for key, spec in CANCERS.items() if spec["survival"]}

@app.get("/api/map/{indicator}")
def map_layer(indicator: int):
    if indicator not in data.values:
        raise HTTPException(404, "unknown indicator")
    out = {}
    for c in data.counties:
        g = A.gap(data, indicator, c)
        out[c] = {
            "name": data.names[c],
            "latest": g.county_value,
            "year": g.year,
            "gap": g.gap,
            "direction": g.direction,
            "persistence": g.persistence,
            "years_same_side": g.years_same_side,
            "n_years": len(g.years),
        }
        iv = A.survival_interval(data, SURVIVAL_OF[indicator], c) if indicator in SURVIVAL_OF else None
        if iv:
            out[c]["interval"] = asdict(iv)
    return {"indicator": indicator, "source": f"sotkanet:{indicator}", "counties": out}


@app.get("/api/mortality-map/{cause}")
def mortality_layer(cause: str):
    """`gap` is 100 minus the SMR, so a negative gap is worse, as for survival."""
    if not mort.ok or cause not in LABELS:
        raise HTTPException(404, "unknown cause")
    out = {}
    for c in data.counties:
        m = mort.smr(cause, c)
        out[c] = {
            "name": data.names[c], "latest": m.smr, "year": f"{m.years[0]} to {m.years[-1]}",
            "gap": round(100 - m.smr, 1),
            "direction": {"worse": "below", "better": "above", "near": "near"}[m.direction],
            "confidence": m.confidence, "low": m.low, "high": m.high,
        }
    return {"indicator": f"mortality:{cause}", "label": LABELS[cause], "source": "statfin_mortality", "counties": out}


@app.get("/api/channel-map")
def channel_layer():
    """`gap` is Finland's public share minus the county's, so more reliance on the public channel is negative."""
    t = channel_table(data)
    nat = t["national"]["public_share"]
    out = {}
    for c, v in t["counties"].items():
        gap = round(nat - v["public_share"], 1)
        out[c] = {"name": data.names[c], "latest": v["public_share"], "year": v["year"], "gap": gap,
                  "direction": "near" if abs(gap) < 2 else ("below" if gap < 0 else "above"),
                  "public": v["public_visits"], "occupational": v["occupational_visits"]}
    return {"indicator": "channel", "label": "Public channel share", "source": "sotkanet:293", "national": nat, "counties": out}


@app.get("/api/headlines")
def headlines():
    """Four national findings for the top of the page, each with the ID of its source."""
    t = channel_table(data)
    most = min(t["counties"], key=lambda c: t["counties"][c]["rank"])
    screening = []
    for cancer in ("bowel", "breast"):
        ind = CANCERS[cancer]["screening"]
        by_county = {c: data.series(ind, c) for c in data.counties}
        years = sorted({y for v in by_county.values() for y in v})
        year = years[-1]
        vals = {c: v[year] for c, v in by_county.items() if year in v}
        low = min(vals, key=vals.get)
        # In how many of the published years the same county had the lowest value, ties included.
        lowest_years = sum(1 for y in years if by_county[low].get(y) is not None
                           and by_county[low][y] == min(v[y] for v in by_county.values() if y in v))
        screening.append({"cancer": CANCERS[cancer]["label"], "year": year, "lowest": data.names[low],
                          "value": vals[low], "target": SCREENING_TARGET,
                          "below_target": sum(1 for v in vals.values() if v < SCREENING_TARGET),
                          "n": len(vals), "lowest_years": lowest_years, "n_years": len(years),
                          "first_year": years[0], "source": f"sotkanet:{ind}"})
    gaps = [nordcan.benchmark(nc, s) | {"label": LABELS[s]} for s in nc["sites"]]
    return {
        "channel": {"national": t["national"]["public_share"], "year": t["national"]["year"],
                    "most": data.names[most], "most_share": t["counties"][most]["public_share"]},
        "screening": screening,
        "nordic": sorted((b for b in gaps if b["gap"] is not None), key=lambda b: b["gap"])[:4],
        "mirror": {"sweden": svf["national"]["2025"]["share"], "target": svf["target"],
                   "regions": len(svf["regions"]), "finland_counties": len(data.counties)},
    }


@app.get("/api/national/{cancer}")
def national(cancer: str):
    """Where to start in Finland for this cancer: counties ranked by the number of registers that show them behind."""
    if cancer not in CANCERS:
        raise HTTPException(404, "unknown cancer")
    return ranking(data, mort, cancer)


@app.get("/api/county/{county}")
def county_briefing(county: str, cancer: str = "bowel"):
    if county not in data.counties:
        raise HTTPException(404, "unknown county")
    if cancer not in CANCERS:
        raise HTTPException(404, "unknown cancer")
    return _briefing(cancer, county)


@lru_cache(maxsize=256)
def _briefing(cancer: str, county: str) -> dict:
    benchmark = nordcan.benchmark(nc, cancer)
    cases = A.county_cases(data, cancer, county)
    pathway = A.locate(data, cancer, county)
    recs = recommend(data, pathway, county)
    if pathway.step == "national":
        recs[0] = recs[0] | _counties_to_invite_first(cancer)
    facts = (F.survival_and_screening_facts(data, cancer, county) + F.mortality_facts(data, mort, cancer, county)
             + F.nordic_facts(cancer, benchmark) + F.channel_facts(data, county) + F.pathway_and_action_facts(pathway, recs))
    view = _county_survival_view(cancer, county, cases) if has_county_survival(cancer) else _mortality_view(cancer, county, cases, benchmark)
    return {
        "county": {"code": county, "name": data.names[county]},
        "cancer": {"key": cancer, "label": CANCERS[cancer]["label"]},
        "summary": summarize(data, cancer, county, pathway, recs, facts),
        "facts": {f.id: asdict(f) for f in facts},
        "pathway": asdict(pathway),
        "recommendations": recs,
        "nordic": benchmark,
        **view,
        "goal3": _goal3(cancer, county),
        "channel": _channel(county),
        "mirror": _mirror(cancer),
        "missing": _missing(cancer, cases),
    }


def _county_survival_view(cancer: str, county: str, cases: dict) -> dict:
    """Chart and simulation for a cancer with county survival: the county against Finland."""
    ind = CANCERS[cancer]["survival"]
    g = A.gap(data, ind, county)
    own, nat = g.county_value, g.national_value
    iv = A.survival_interval(data, cancer, county)
    return {
        "chart": {"kind": "survival", "source": f"sotkanet:{ind}", "year": g.year, "gap": g.gap,
                  "interval": asdict(iv) if iv else None, "years_same_side": g.years_same_side, "n_years": len(g.years),
                  "county": data.series(ind, county), "national": data.series(ind, NATIONAL)},
        "simulation": {"mode": "county", "cases": cases, "start": own, "goal": nat,
                       "period": g.year, "source": f"sotkanet:{ind}", "target": None,
                       "steps": A.simulation_steps(cases["value"], own, nat)},
    }


def _mortality_view(cancer: str, county: str, cases: dict, benchmark: dict) -> dict:
    """Chart and simulation for a cancer without county survival: county deaths against expected,
    and what the Nordic survival level would mean for the county's yearly patients."""
    return {
        "chart": {"kind": "smr", "source": "statfin_mortality", "county": all_years(mort, cancer, county)} if mort.ok else None,
        "simulation": {"mode": "nordic", "cases": cases, "start": benchmark["finland"], "goal": benchmark["nordic"],
                       "period": benchmark["period"], "source": "nordcan", "target": benchmark["target"],
                       "steps": A.simulation_steps(cases["value"], benchmark["finland"], benchmark["nordic"])},
    }


def _counties_to_invite_first(cancer: str) -> dict:
    """Up to five counties with significantly more deaths than their age structure predicts, worst first."""
    if not mort.ok:
        return {}
    worse = [m for m in (mort.smr(cancer, c) for c in data.counties) if m.direction == "worse" and m.confidence == "high"]
    worse.sort(key=lambda m: -m.smr)
    if not worse:
        return {}
    return {"priority": [{"county": data.names[m.county], "smr": m.smr, "low": m.low, "high": m.high} for m in worse[:5]],
            "priority_source": "statfin_mortality"}


def _channel(county: str) -> dict | None:
    t = channel_table(data)
    c = t["counties"].get(county)
    return {**c, "n": t["n"], "national": t["national"]} if c else None


def _mirror(cancer: str) -> dict:
    """Nordic Mirror: the waiting-time picture Sweden publishes per region, and the roadmap measures
    that would give Finland the same."""
    regions = sorted(({"region": r, **v} for r, v in svf["regions"].items()), key=lambda r: r["2025"])
    return {
        "target": svf["target"], "national": svf["national"],
        "regions": regions, "cancer": svf["by_cancer_2025"].get(cancer), "source": svf["source"],
        "finland_counties": len(data.counties),
        "proposal": [{"measure": m, **{k: MEASURES[m][k] for k in ("action", "page", "actor")}} for m in ("3.1.2", "3.1.4")],
    }


def _goal3(cancer: str, county: str) -> dict | None:
    if not mort.ok:
        return None
    rows = [{**asdict(mort.smr(c, county)), "label": LABELS[c]} for c in dict.fromkeys(GOAL3 + [cancer])]
    survival = [{**nordcan.benchmark(nc, s), "label": LABELS[s]} for s in dict.fromkeys(GOAL3_SURVIVAL + [cancer])]
    return {"rows": rows, "target_fact": "mort.target", "source": "statfin_mortality", "survival": survival}


def _missing(cancer: str, cases: dict) -> list[dict]:
    """What no public source gives, and the roadmap measure that would produce it."""
    out = [
        {"what": "Waiting times from referral to diagnosis and to treatment, per county",
         "why": "Goal 3 indicator 3 asks for treatment within target times. No public source gives them per county.",
         "measure": "3.1.4", "source": "thl_21_2016"},
        {"what": "Stage at diagnosis per county",
         "why": "Stage would tell the steps apart: many late stages point to detection, and low survival within a stage points to treatment.",
         "measure": "3.2.1", "source": "cancer_registry"},
        {"what": "Five-year survival for lung, pancreatic and liver cancer per county",
         "why": "Goal 3 indicator 1 measures survival for these cancers. The app shows their age-adjusted mortality instead.",
         "measure": "3.1.4", "source": "strategy"},
    ]
    no_level = [LABELS[s].lower() for s in dict.fromkeys(GOAL3_SURVIVAL + [cancer]) if nordcan.benchmark(nc, s)["gap"] is None]
    if no_level:
        out.append({"what": "Nordic survival level for " + ", ".join(no_level),
                    "why": "data/nordcan.json lacks a value for Finland, Sweden or Norway. The NORDCAN fact sheets have them.",
                    "measure": None, "source": "nordcan"})
    if cases["status"] == "estimate":
        out.append({"what": "New cases per year per county",
                    "why": "The simulation splits the national count by population share.",
                    "measure": None, "source": "cancer_registry"})
    return out
