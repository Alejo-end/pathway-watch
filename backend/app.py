"""Pathway Watch endpoints.

    uv run uvicorn backend.app:app --port 8010
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import analysis as A
from . import nordcan as NC
from .analyst import extra_facts, summarize
from .channel import channel_facts, channel_table
from .recommend import MEASURES
from .indicators import CANCERS, INDICATORS, NATIONAL
from .mortality import GOAL3, LABELS, Mortality
from .recommend import recommend

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
data = A.load()
mort = Mortality()
nc = NC.load()
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
        "cancers": {k: {"label": v["label"], "survival": v["survival"], "screening": v["screening"]} for k, v in CANCERS.items()},
        "indicators": {i: {"short": x.short, "kind": x.kind, "cancer": x.cancer} for i, x in INDICATORS.items()},
        "sources": data.sources(),
    }


@app.get("/api/map/{indicator}")
def map_layer(indicator: int):
    if indicator not in data.values:
        raise HTTPException(404, "unknown indicator")
    out = {}
    for c in data.counties:
        g = A.gap(data, indicator, c)
        s = A.series(data, indicator, c)
        out[c] = {
            "name": data.names[c],
            "latest": s[max(s)] if s else None,
            "year": max(s) if s else None,
            "gap": g.avg_gap,
            "direction": g.direction,
            "confidence": g.confidence,
        }
    nat = A.series(data, indicator, NATIONAL)
    return {"indicator": indicator, "source": f"sotkanet:{indicator}", "national": nat, "counties": out}


@app.get("/api/mortality-map/{cause}")
def mortality_layer(cause: str):
    """Same shape as /api/map. `gap` is 100 minus the SMR, so a negative gap is worse, as for survival."""
    if not mort.ok or cause not in LABELS:
        raise HTTPException(404, "unknown cause")
    out = {}
    for c in data.counties:
        m = mort.smr(cause, c)
        out[c] = {
            "name": data.names[c], "latest": m.smr, "year": f"{m.years[0]}–{m.years[-1]}",
            "gap": round(100 - m.smr, 1),
            "direction": {"worse": "below", "better": "above", "near": "near"}[m.direction],
            "confidence": m.confidence, "low": m.low, "high": m.high,
        }
    return {"indicator": f"mortality:{cause}", "label": LABELS[cause], "source": "statfin_mortality", "counties": out}


@app.get("/api/headlines")
def headlines():
    """Four national findings for the top of the page. Every number is computed here and cites a source."""
    t = channel_table(data)
    most = min(t["counties"], key=lambda c: t["counties"][c]["rank"])
    screening = []
    for cancer in ("bowel", "breast"):
        ind = CANCERS[cancer]["screening"]
        latest = {c: A.series(data, ind, c) for c in data.counties}
        year = max(max(v) for v in latest.values() if v)
        vals = {c: v[year] for c, v in latest.items() if year in v}
        low = min(vals, key=vals.get)
        screening.append({"cancer": CANCERS[cancer]["label"], "year": year, "lowest": data.names[low],
                          "value": vals[low], "below_target": sum(1 for v in vals.values() if v < 80),
                          "n": len(vals), "source": f"sotkanet:{ind}"})
    nordic = sorted((NC.benchmark(nc, s) | {"label": LABELS[s]} for s in ("lung", "liver", "cervical", "pancreas", "bowel", "breast")),
                    key=lambda b: b["gap"] if b["gap"] is not None else 0)
    return {
        "channel": {"national": t["national"]["public_share"], "year": t["national"]["year"],
                    "most": data.names[most], "most_share": t["counties"][most]["public_share"]},
        "screening": screening,
        "nordic": [b for b in nordic if b["gap"] is not None][:4],
        "mirror": {"sweden": svf["national"]["2025"]["share"], "target": svf["target"],
                   "regions": len(svf["regions"]), "finland_counties": len(data.counties)},
    }


@app.get("/api/channel-map")
def channel_layer():
    """Same shape as /api/map. `gap` is Finland's public share minus the county's, so more public reliance is negative."""
    t = channel_table(data)
    nat = t["national"]["public_share"]
    out = {}
    for c, v in t["counties"].items():
        gap = round(nat - v["public_share"], 1)
        out[c] = {"name": data.names[c], "latest": v["public_share"], "year": v["year"], "gap": gap,
                  "direction": "near" if abs(gap) < 2 else ("below" if gap < 0 else "above"), "confidence": "high",
                  "public": v["public_visits"], "occupational": v["occupational_visits"]}
    return {"indicator": "channel", "label": "Public channel share", "source": "sotkanet:293", "national": nat, "counties": out}


@lru_cache(maxsize=256)
def _briefing(cancer: str, county: str) -> dict:
    spec = CANCERS[cancer]
    pathway = A.locate(data, cancer, county)
    recs = recommend(data, pathway, county)
    facts = (A.facts_for(data, cancer, county) + A.mortality_facts(data, mort, cancer, county)
             + channel_facts(data, county) + extra_facts(pathway, recs))
    summary = summarize(data, cancer, county, pathway, recs, facts)
    surv = A.gap(data, spec["survival"], county)
    scr = A.gap(data, spec["screening"], county)
    cases = A.estimated_cases(data, cancer, county)
    nordic = data.reference["nordic_five_year_survival"][cancer]
    nat_series = A.series(data, spec["survival"], NATIONAL)
    return {
        "county": {"code": county, "name": data.names[county]},
        "cancer": {"key": cancer, "label": spec["label"]},
        "summary": summary,
        "facts": {f.id: A.as_dict(f) for f in facts},
        "gaps": {"survival": A.as_dict(surv), "screening": A.as_dict(scr)},
        "pathway": A.as_dict(pathway),
        "recommendations": recs,
        "chart": {
            "indicator": spec["survival"],
            "source": f"sotkanet:{spec['survival']}",
            "county": A.series(data, spec["survival"], county),
            "national": nat_series,
            "nordic": nordic,
            "screening_indicator": spec["screening"],
            "screening_county": A.series(data, spec["screening"], county),
            "screening_national": A.series(data, spec["screening"], NATIONAL),
        },
        "simulation": {
            "cases": cases,
            "county_survival": surv.county_values[-1] if surv.years else None,
            "national_survival": surv.national_values[-1] if surv.years else None,
            "year": surv.years[-1] if surv.years else None,
            "extra_survivors_full": A.simulate(
                cases["value"], surv.county_values[-1] if surv.years else None,
                surv.national_values[-1] if surv.years else None,
            ),
        },
        "goal3": goal3(cancer, county),
        "channel": channel_block(county),
        "mirror": mirror(cancer),
        "missing": missing(cancer, nordic, cases),
    }


def channel_block(county: str) -> dict | None:
    t = channel_table(data)
    c = t["counties"].get(county)
    if not c:
        return None
    return {**c, "n": t["n"], "national": t["national"], "facts": ["channel.share", "channel.visits", "channel.rank", "channel.roadmap"]}


def mirror(cancer: str) -> dict:
    """Nordic Mirror: the waiting-time picture Sweden publishes per region, and what Finland has instead."""
    regions = sorted(({"region": r, **v} for r, v in svf["regions"].items()), key=lambda r: r["2025"])
    return {
        "measure": svf["measure"], "target": svf["target"], "national": svf["national"],
        "regions": regions, "cancer": svf["by_cancer_2025"].get(cancer), "source": svf["source"],
        "finland_counties": len(data.counties),
        "proposal": [{"measure": m, **{k: MEASURES[m][k] for k in ("action", "page", "actor")}} for m in ("3.1.2", "3.1.4")],
    }


def goal3(cancer: str, county: str) -> dict | None:
    if not mort.ok:
        return None
    rows = [{**A.as_dict(mort.smr(c, county)), "label": LABELS[c], "fact": f"mort.{c}"} for c in dict.fromkeys(GOAL3 + [cancer])]
    survival = [{**NC.benchmark(nc, s), "label": LABELS[s]} for s in dict.fromkeys(["lung", "pancreas", "liver", cancer])]
    return {"rows": rows, "target_fact": "mort.target", "source": "statfin_mortality", "survival": survival}


def missing(cancer: str, nordic: dict, cases: dict) -> list[dict]:
    out = [
        {"what": "Waiting times from referral to diagnosis and to treatment, per county",
         "why": "Goal 3 indicator 3 asks for treatment within target times. No public source gives them per county.",
         "measure": "3.2.1", "source": "thl_21_2016"},
        {"what": "Stage at diagnosis per county",
         "why": "Stage would show whether detection or later steps cause the gap.",
         "measure": "3.2.1", "source": "cancer_registry"},
    ]
    out.append({"what": "Five-year survival for lung, pancreatic and liver cancer per county",
                "why": "Goal 3 indicator 1 measures survival for these cancers. The app shows their age-adjusted mortality instead.",
                "measure": "3.1.4", "source": "strategy"})
    unread = [LABELS[s].lower() for s in dict.fromkeys(["lung", "pancreas", "liver", cancer]) if NC.benchmark(nc, s)["nordic"] is None or NC.benchmark(nc, s)["finland"] is None]
    if unread:
        out.append({"what": "NORDCAN survival values not read yet: " + ", ".join(unread),
                    "why": "The NORDCAN data service went into maintenance during the reading. The values go into data/nordcan.json.",
                    "measure": None, "source": "nordcan"})
    if cases["value"] is not None:  # the national count is checked, the county split is not
        out.append({"what": "New cases per year per county",
                    "why": "The simulation uses an estimate from the national count and the population share.",
                    "measure": None, "source": "cancer_registry"})
    return out


@app.get("/api/county/{county}")
def county_briefing(county: str, cancer: str = "bowel"):
    if county not in data.counties:
        raise HTTPException(404, "unknown county")
    if cancer not in CANCERS:
        raise HTTPException(404, "unknown cancer")
    return _briefing(cancer, county)
