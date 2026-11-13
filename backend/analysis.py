"""Gaps, confidence and the likely pathway step. Plain code, no language model.

Every number the app shows is computed here and carries the ID of its source.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .indicators import CANCERS, EXCLUDED, INDICATORS, NATIONAL, STEPS
from .sources import STATIC_SOURCES, sotkanet_source

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

WINDOW = 3  # years in the rolling average
NEAR = 1.0  # a gap smaller than this many points counts as "near the national value"


@dataclass
class Fact:
    id: str
    text: str
    value: float | None
    unit: str
    source: str


@dataclass
class Gap:
    indicator: int
    county: str
    years: list[int]
    county_values: list[float]
    national_values: list[float]
    avg_gap: float | None  # county minus national, average over the window
    direction: str  # below, above, near, unknown
    confidence: str  # high, medium, low
    years_outside: int


@dataclass
class Data:
    """All indicator values, keyed as values[indicator][region_code][year]."""

    values: dict[int, dict[str, dict[int, float]]]
    names: dict[str, str]
    population: dict[str, float]
    fetched: dict[int, str]
    titles: dict[int, str]
    reference: dict = field(default_factory=dict)

    @property
    def counties(self) -> list[str]:
        return sorted(c for c in self.names if c != NATIONAL and c not in EXCLUDED)

    def sources(self) -> dict[str, dict]:
        out = dict(STATIC_SOURCES)
        for ind, title in self.titles.items():
            out[f"sotkanet:{ind}"] = sotkanet_source(ind, title, self.fetched.get(ind))
        return out


def load(raw: Path = RAW) -> Data:
    regions = json.loads((raw / "regions.json").read_text())
    code_of = {r["id"]: r["code"] for r in regions}
    names = {r["code"]: short_name(r["title"]["fi"]) for r in regions}
    values: dict[int, dict[str, dict[int, float]]] = {}
    fetched: dict[int, str] = {}
    titles: dict[int, str] = {}
    population: dict[str, float] = {}
    for path in sorted(raw.glob("sotkanet_*.json")):
        doc = json.loads(path.read_text())
        ind = doc["indicator"]
        table: dict[str, dict[int, float]] = {}
        for row in doc["rows"]:
            code = code_of.get(row["region"])
            if code is not None:
                table.setdefault(code, {})[row["year"]] = float(row["value"])
        if ind == 127:
            population = {c: max(v.items())[1] for c, v in table.items()}
            continue
        values[ind] = table
        fetched[ind] = doc.get("fetched", "")
        titles[ind] = doc.get("title") or INDICATORS[ind].short
    reference = json.loads((raw.parent / "reference.json").read_text())
    _apply_nordcan(reference)
    return Data(values, names, population, fetched, titles, reference)


def _apply_nordcan(reference: dict) -> None:
    """Replace the approximate values in reference.json with NORDCAN values where they exist."""
    from . import nordcan

    nc = nordcan.load()
    for site in ("bowel", "breast", "cervical"):
        fi = nordcan.combined(nc, site, "finland")
        if fi:
            reference["national_new_cases_per_year"][site] = {
                "value": fi["cases"], "source": "nordcan", "status": "checked",
                "note": f"NORDCAN, average {nc.get('period')}",
            }
        bench = nordcan.benchmark(nc, site)
        reference["nordic_five_year_survival"][site] = {
            "value": bench["nordic"], "source": "nordcan",
            "status": "checked" if bench["nordic"] is not None else "missing", "benchmark": bench,
        }


def short_name(fi: str) -> str:
    """'Päijät-Hämeen hyvinvointialue' -> 'Päijät-Häme'. Names are Finnish genitives."""
    special = {
        "Helsingin kaupunki": "Helsinki",
        "Koko maa": "Finland",
        "Ahvenanmaa": "Åland",
        "Vantaan ja Keravan hyvinvointialue": "Vantaa-Kerava",
        "Itä-Uudenmaan hyvinvointialue": "East Uusimaa",
        "Keski-Uudenmaan hyvinvointialue": "Central Uusimaa",
        "Länsi-Uudenmaan hyvinvointialue": "West Uusimaa",
        "Varsinais-Suomen hyvinvointialue": "Southwest Finland",
        "Satakunnan hyvinvointialue": "Satakunta",
        "Kanta-Hämeen hyvinvointialue": "Kanta-Häme",
        "Pirkanmaan hyvinvointialue": "Pirkanmaa",
        "Päijät-Hämeen hyvinvointialue": "Päijät-Häme",
        "Kymenlaakson hyvinvointialue": "Kymenlaakso",
        "Etelä-Karjalan hyvinvointialue": "South Karelia",
        "Etelä-Savon hyvinvointialue": "South Savo",
        "Pohjois-Savon hyvinvointialue": "North Savo",
        "Pohjois-Karjalan hyvinvointialue": "North Karelia",
        "Keski-Suomen hyvinvointialue": "Central Finland",
        "Etelä-Pohjanmaan hyvinvointialue": "South Ostrobothnia",
        "Pohjanmaan hyvinvointialue": "Ostrobothnia",
        "Keski-Pohjanmaan hyvinvointialue": "Central Ostrobothnia",
        "Pohjois-Pohjanmaan hyvinvointialue": "North Ostrobothnia",
        "Kainuun hyvinvointialue": "Kainuu",
        "Lapin hyvinvointialue": "Lapland",
    }
    return special.get(fi, fi)


def series(data: Data, indicator: int, region: str) -> dict[int, float]:
    return dict(sorted(data.values.get(indicator, {}).get(region, {}).items()))


def gap(data: Data, indicator: int, county: str, window: int = WINDOW) -> Gap:
    """County against the national value over the last `window` years with data for both."""
    own = series(data, indicator, county)
    nat = series(data, indicator, NATIONAL)
    years = sorted(set(own) & set(nat))[-window:]
    cv = [own[y] for y in years]
    nv = [nat[y] for y in years]
    diffs = [c - n for c, n in zip(cv, nv)]
    if not diffs:
        return Gap(indicator, county, [], [], [], None, "unknown", "low", 0)
    avg = round(sum(diffs) / len(diffs), 1)
    direction = "near" if abs(avg) < NEAR else ("below" if avg < 0 else "above")
    if direction == "near":
        outside = 0
    else:
        sign = -1 if direction == "below" else 1
        outside = sum(1 for d in diffs if d * sign >= NEAR)
    if len(years) < window:
        confidence = "low"
    elif outside == window:
        confidence = "high"
    elif outside == window - 1:
        confidence = "medium"
    else:
        confidence = "low"
    return Gap(indicator, county, years, cv, nv, avg, direction, confidence, outside)


def rank(data: Data, indicator: int, county: str) -> tuple[int, int]:
    """Rank of the county by its latest value, 1 = lowest. Returns (rank, number of counties)."""
    latest = {}
    for c in data.counties:
        s = series(data, indicator, c)
        if s:
            latest[c] = s[max(s)]
    order = sorted(latest, key=lambda c: latest[c])
    return (order.index(county) + 1 if county in order else 0, len(order))


@dataclass
class Pathway:
    cancer: str
    step: str  # detection, later, watch, none, unknown
    label: str
    confidence: str
    reason: str
    caveats: list[str]


def locate(data: Data, cancer: str, county: str) -> Pathway:
    """The demo rule. Low survival with low screening points to detection.
    Low survival with normal screening points to referral, diagnosis or treatment.
    The result is a 'most likely' step, never a cause."""
    spec = CANCERS[cancer]
    surv = gap(data, spec["survival"], county)
    scr = gap(data, spec["screening"], county)
    caveats = []
    if cancer == "bowel":
        caveats.append(
            "Bowel screening started nationally in 2022. Five-year survival describes patients "
            "diagnosed years earlier, so screening in the same year cannot explain it."
        )
    if surv.direction == "unknown":
        return Pathway(cancer, "unknown", "Not enough data", "low", "No survival data for this county.", caveats)
    if surv.direction != "below" and scr.direction == "below":
        return Pathway(
            cancer, "watch", STEPS["detection"], scr.confidence,
            "Survival is not below the national value, but screening attendance is. "
            "Late detection can show in survival only years later.", caveats,
        )
    if surv.direction != "below":
        return Pathway(
            cancer, "none", "No survival gap found", surv.confidence,
            "Five-year survival is at or above the national value.", caveats,
        )
    if scr.direction == "below":
        conf = _weaker(surv.confidence, scr.confidence)
        return Pathway(
            cancer, "detection", STEPS["detection"], conf,
            "Survival and screening attendance are both below the national value.", caveats,
        )
    conf = surv.confidence if scr.direction != "unknown" else "low"
    return Pathway(
        cancer, "later",
        f"{STEPS['referral']}, {STEPS['diagnosis'].lower()} or {STEPS['treatment'].lower()}",
        conf,
        "Survival is below the national value, but screening attendance is not. "
        "The difference most likely starts after detection.",
        caveats + ["No public source gives referral or waiting times per county, so the app cannot tell these three steps apart."],
    )


def _weaker(a: str, b: str) -> str:
    order = ["low", "medium", "high"]
    return order[min(order.index(a), order.index(b))]


def estimated_cases(data: Data, cancer: str, county: str) -> dict:
    """New cases per year in the county, estimated from the national count and the population share.
    This ignores the age structure of the county and is labelled as an estimate."""
    ref = data.reference["national_new_cases_per_year"][cancer]
    pop = data.population.get(county)
    nat = data.population.get(NATIONAL)
    if not pop or not nat or ref["value"] is None:
        return {"value": None, "status": "missing", "source": ref["source"]}
    return {
        "value": round(ref["value"] * pop / nat),
        "status": "estimate",
        "source": ref["source"],
        "method": f"{ref['value']} new cases per year in Finland ({ref.get('note') or ref['status']}) x county population share {pop / nat:.1%}",
    }


def simulate(cases: float | None, county_survival: float | None, target_survival: float | None, share: float = 1.0) -> int | None:
    """Extra five-year survivors per yearly cohort if the county closes `share` of its gap to the target."""
    if cases is None or county_survival is None or target_survival is None:
        return None
    gain = max(0.0, target_survival - county_survival) / 100
    return round(cases * gain * share)


def facts_for(data: Data, cancer: str, county: str) -> list[Fact]:
    """The computed facts a sentence about this county may cite."""
    spec = CANCERS[cancer]
    name = data.names[county]
    out: list[Fact] = []
    for key in ("survival", "screening"):
        ind = spec[key]
        g = gap(data, ind, county)
        label = INDICATORS[ind].short.lower()
        src = f"sotkanet:{ind}"
        if not g.years:
            continue
        y = g.years[-1]
        out.append(Fact(f"{ind}.county.{y}", f"{name}, {label}, {y}: {g.county_values[-1]:g}%", g.county_values[-1], "%", src))
        out.append(Fact(f"{ind}.national.{y}", f"Finland, {label}, {y}: {g.national_values[-1]:g}%", g.national_values[-1], "%", src))
        if g.avg_gap is not None:
            out.append(Fact(
                f"{ind}.gap",
                f"{name}, {label}: {g.avg_gap:+g} points against the national value, average {g.years[0]}–{g.years[-1]}, "
                f"outside the national value in {g.years_outside} of {len(g.years)} years ({g.confidence} confidence)",
                g.avg_gap, "points", src,
            ))
        r, n = rank(data, ind, county)
        if r:
            out.append(Fact(f"{ind}.rank", f"{name} ranks {r} of {n} counties on {label} in {y} (1 = lowest)", r, "rank", src))
    return out


def mortality_facts(data: Data, mort, cancer: str, county: str) -> list[Fact]:
    """Facts on age-adjusted cancer mortality (Goal 3, indicators 1 and 2)."""
    from .mortality import GOAL3, LABELS

    if not mort or not mort.ok:
        return []
    name = data.names[county]
    out = []
    for cause in dict.fromkeys(GOAL3 + [cancer]):
        m = mort.smr(cause, county)
        span = f"{m.years[0]}–{m.years[-1]}"
        out.append(Fact(
            f"mort.{cause}",
            f"{name}, {LABELS[cause].lower()} deaths {span}: {m.observed} against {m.expected:g} expected from the age structure, "
            f"SMR {m.smr} (95% interval {m.low}–{m.high}, {m.confidence} confidence)",
            m.smr, "SMR", "statfin_mortality",
        ))
    m = mort.smr("all", county)
    out.append(Fact(
        "mort.target",
        f"{name} has {round(m.deaths_per_year)} cancer deaths per year on average in {m.years[0]}–{m.years[-1]}. "
        f"The Goal 3 target of 10% fewer deaths means {round(m.deaths_per_year * 0.1)} fewer per year",
        round(m.deaths_per_year * 0.1), "deaths", "statfin_mortality",
    ))
    return out


def as_dict(obj) -> dict:
    return asdict(obj)
