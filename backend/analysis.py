"""Compares a county with the country: the gap, how sure it is, the likely pathway step and the simulation.

Plain code, no language model.
"""

from __future__ import annotations

from dataclasses import dataclass

from .indicators import CANCERS, NATIONAL, STEPS, WINDOW, has_county_survival
from .sotkanet import CountyData

NEAR = 1.0  # a difference smaller than this many points counts as "near the national value"


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
    years_agreeing: int  # years that, taken alone, give the same direction


def gap(data: CountyData, indicator: int, county: str, window: int = WINDOW) -> Gap:
    """County against the national value over the last `window` years with data for both.

    Confidence says how many single years agree with the direction of the average: all of
    them is high, all but one is medium, fewer is low. For "near", a year agrees if it is
    itself within NEAR points of the national value. Fewer than `window` years is always low.
    """
    own = data.series(indicator, county)
    nat = data.series(indicator, NATIONAL)
    years = sorted(set(own) & set(nat))[-window:]
    cv = [own[y] for y in years]
    nv = [nat[y] for y in years]
    diffs = [c - n for c, n in zip(cv, nv)]
    if not diffs:
        return Gap(indicator, county, [], [], [], None, "unknown", "low", 0)
    avg = round(sum(diffs) / len(diffs), 1)
    direction = "near" if abs(avg) < NEAR else ("below" if avg < 0 else "above")
    if direction == "near":
        agreeing = sum(1 for d in diffs if abs(d) < NEAR)
    else:
        sign = -1 if direction == "below" else 1
        agreeing = sum(1 for d in diffs if d * sign >= NEAR)
    if len(years) < window:
        confidence = "low"
    elif agreeing == window:
        confidence = "high"
    elif agreeing == window - 1:
        confidence = "medium"
    else:
        confidence = "low"
    return Gap(indicator, county, years, cv, nv, avg, direction, confidence, agreeing)


def rank(data: CountyData, indicator: int, county: str) -> tuple[int, int]:
    """Rank of the county by its latest value, 1 = lowest. Returns (rank, number of counties)."""
    latest = {}
    for c in data.counties:
        s = data.series(indicator, c)
        if s:
            latest[c] = s[max(s)]
    order = sorted(latest, key=lambda c: latest[c])
    return (order.index(county) + 1 if county in order else 0, len(order))


@dataclass
class Pathway:
    cancer: str
    step: str  # detection, later, watch, none, unknown, national
    label: str
    confidence: str
    reason: str
    caveats: list[str]


def locate(data: CountyData, cancer: str, county: str) -> Pathway:
    """The most likely pathway step. It is an inference from public data, never a proven cause.

    With county data: low survival with low screening points to detection. Low survival with
    normal screening points to referral, diagnosis or treatment. Normal survival with low
    screening is an early warning ("watch"). Without county survival data, the step comes
    from national evidence.
    """
    if not has_county_survival(cancer):
        return _locate_from_national_evidence(cancer)
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
        return Pathway(
            cancer, "detection", STEPS["detection"], _weaker(surv.confidence, scr.confidence),
            "Survival and screening attendance are both below the national value.", caveats,
        )
    return Pathway(
        cancer, "later",
        f"{STEPS['referral']}, {STEPS['diagnosis'].lower()} or {STEPS['treatment'].lower()}",
        surv.confidence if scr.direction != "unknown" else "low",
        "Survival is below the national value, but screening attendance is not. "
        "The difference most likely starts after detection.",
        caveats + ["No public source gives referral or waiting times per county, so the app cannot tell these three steps apart."],
    )


def _locate_from_national_evidence(cancer: str) -> Pathway:
    """Lung cancer: survival far below the Nordic level (NORDCAN), and the roadmap's statement
    that poor-prognosis cancers are often diagnosed at an advanced stage (page 22)."""
    return Pathway(
        cancer, "national", "Detection and diagnosis", "medium",
        "Five-year survival in Finland is far below the Nordic level, and the roadmap reports that poor-prognosis "
        "cancers are often diagnosed at an advanced stage, with vague symptoms and smoking stigma delaying care (roadmap, page 22).",
        ["No public source gives lung cancer survival, stage or screening per county. The county view uses age-adjusted mortality.",
         "A lung cancer screening pilot started in 2026 in Helsinki and eight counties (roadmap, page 46)."],
    )


def _weaker(a: str, b: str) -> str:
    order = ["low", "medium", "high"]
    return order[min(order.index(a), order.index(b))]


def estimated_cases(data: CountyData, county: str, national_cases: int | None, basis: str, source: str) -> dict:
    """New cases per year in the county: the national count times the county's population share.

    It ignores the age structure of the county, so the result is labelled as an estimate.
    `basis` says where the national count comes from, for display.
    """
    pop = data.population.get(county)
    nat = data.population.get(NATIONAL)
    if not pop or not nat or national_cases is None:
        return {"value": None, "status": "missing", "source": source}
    return {
        "value": round(national_cases * pop / nat),
        "status": "estimate",
        "source": source,
        "method": f"{national_cases} new cases per year in Finland ({basis}) x county population share {pop / nat:.1%}",
    }


def simulate(cases: float | None, survival: float | None, target: float | None, share: float = 1.0) -> int | None:
    """Extra five-year survivors per yearly cohort if survival closes `share` of its gap to the target."""
    if cases is None or survival is None or target is None:
        return None
    gain = max(0.0, target - survival) / 100
    return round(cases * gain * share)


def simulation_steps(cases: float | None, survival: float | None, target: float | None) -> dict | None:
    """The simulation for every whole percent of the gap closed, 0 to 100, for the slider."""
    if cases is None or survival is None or target is None:
        return None
    lift = max(0.0, target - survival)
    return {
        "survivors": [simulate(cases, survival, target, s / 100) for s in range(101)],
        "reached": [round(survival + lift * s / 100, 1) for s in range(101)],
    }
