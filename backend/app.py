"""Pathway Watch endpoints.

    uv run uvicorn backend.app:app --port 8010
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import analysis as A
from .analyst import extra_facts, summarize
from .indicators import CANCERS, INDICATORS, NATIONAL
from .mortality import GOAL3, LABELS, Mortality
from .recommend import recommend

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
data = A.load()
mort = Mortality()
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


@lru_cache(maxsize=256)
def _briefing(cancer: str, county: str) -> dict:
    spec = CANCERS[cancer]
    pathway = A.locate(data, cancer, county)
    recs = recommend(data, pathway, county)
    facts = A.facts_for(data, cancer, county) + A.mortality_facts(data, mort, cancer, county) + extra_facts(pathway, recs)
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
        "missing": missing(cancer, nordic, cases),
    }


def goal3(cancer: str, county: str) -> dict | None:
    if not mort.ok:
        return None
    rows = [{**A.as_dict(mort.smr(c, county)), "label": LABELS[c], "fact": f"mort.{c}"} for c in dict.fromkeys(GOAL3 + [cancer])]
    return {"rows": rows, "target_fact": "mort.target", "source": "statfin_mortality"}


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
    if nordic["value"] is None:
        out.append({"what": f"Nordic five-year survival for {CANCERS[cancer]['label'].lower()}",
                    "why": "Goal 3 sets the Nordic level as the target. The NORDCAN value is not loaded yet.",
                    "measure": None, "source": "nordcan"})
    if cases["status"] != "checked":
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
