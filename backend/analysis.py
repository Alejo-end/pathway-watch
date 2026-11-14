"""Compares a county with the country: the gap, how persistent it is, the pathway question and the simulation.

Plain code, no language model.
"""

from __future__ import annotations

from dataclasses import dataclass

from .indicators import CANCERS, NATIONAL, STEPS, has_county_survival
from .sotkanet import CountyData

# A difference of up to this many points counts as "near the national value". Sotkanet rounds survival
# to whole percent, so a gap of exactly one point can be rounding alone and must not count as a gap.
NEAR = 1.0
MIN_YEARS = 3  # fewer shared years than this say nothing about persistence


@dataclass
class Gap:
    indicator: int
    county: str
    year: int | None  # the latest year with a value for both the county and Finland
    county_value: float | None
    national_value: float | None
    gap: float | None  # county minus national in that year
    direction: str  # below, above, near, unknown
    years: list[int]  # every year with a value for both, oldest first
    county_values: list[float]
    national_values: list[float]
    years_same_side: int  # years in which the county is on the same side as in the latest year
    persistence: str  # persistent, mixed, short


def _side(diff: float) -> str:
    if abs(diff) <= NEAR:
        return "near"
    return "below" if diff < 0 else "above"


def gap(data: CountyData, indicator: int, county: str) -> Gap:
    """County against the national value in the latest year that has both. No averaging.

    Each Sotkanet survival value covers ten years of diagnoses, so neighbouring years share
    most of their patients. An average of such years removes no noise, and agreement between
    them is not a test. Sotkanet publishes no confidence interval.

    `persistence` describes, it does not test. "persistent": at least three shared years, and
    the county is on the same side as in the latest year in more than half of them. "mixed":
    at least three shared years, but not most. "short": fewer than three shared years.
    """
    own = data.series(indicator, county)
    nat = data.series(indicator, NATIONAL)
    years = sorted(set(own) & set(nat))
    if not years:
        return Gap(indicator, county, None, None, None, None, "unknown", [], [], [], 0, "short")
    cv = [own[y] for y in years]
    nv = [nat[y] for y in years]
    diffs = [c - n for c, n in zip(cv, nv)]
    latest = round(diffs[-1], 1)
    direction = _side(latest)
    same = sum(1 for d in diffs if _side(round(d, 1)) == direction)
    if len(years) < MIN_YEARS:
        persistence = "short"
    else:
        persistence = "persistent" if same * 2 > len(years) else "mixed"
    return Gap(indicator, county, years[-1], cv[-1], nv[-1], latest, direction, years, cv, nv, same, persistence)


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
    evidence: str  # persistent, mixed, short, or national
    reason: str
    caveats: list[str]


def locate(data: CountyData, cancer: str, county: str) -> Pathway:
    """The pathway step to ask about first. A question to investigate, never a located cause.

    The rule compares whole counties, not patients. Low survival with low screening raises a
    question about detection. Low survival with normal screening raises a question about
    referral, diagnosis or treatment. Normal survival with low screening is an early warning
    ("watch"). Without county survival data, the question comes from national evidence.
    """
    if not has_county_survival(cancer):
        return _locate_from_national_evidence(cancer)
    spec = CANCERS[cancer]
    surv = gap(data, spec["survival"], county)
    scr = gap(data, spec["screening"], county)
    caveats = ["The rule compares counties, not patients. Survival describes patients diagnosed up to ten years ago."]
    if cancer == "bowel":
        caveats.append(
            "Bowel screening started nationally in 2022. Five-year survival describes patients "
            "diagnosed years earlier, so screening in the same year cannot explain it."
        )
    if surv.direction == "unknown":
        return Pathway(cancer, "unknown", "Not enough data", "short", "No survival data for this county.", caveats)
    if surv.direction != "below" and scr.direction == "below":
        return Pathway(
            cancer, "watch", STEPS["detection"], scr.persistence,
            "Survival is not below the national value, but screening attendance is. "
            "Late detection can show in survival only years later. This raises a question about detection.", caveats,
        )
    if surv.direction != "below":
        return Pathway(
            cancer, "none", "No survival gap found", surv.persistence,
            "Five-year survival is at or above the national value.", caveats,
        )
    if scr.direction == "below":
        return Pathway(
            cancer, "detection", STEPS["detection"], _weaker(surv.persistence, scr.persistence),
            "Survival and screening attendance are both below the national value. "
            "This raises a question about detection.", caveats,
        )
    return Pathway(
        cancer, "later",
        f"{STEPS['referral']}, {STEPS['diagnosis'].lower()} or {STEPS['treatment'].lower()}",
        surv.persistence if scr.direction != "unknown" else "short",
        "Survival is below the national value, but screening attendance is not. "
        "This raises a question about the steps after detection.",
        caveats + ["No public source gives referral or waiting times per county, so the app cannot tell these three steps apart."],
    )


def _locate_from_national_evidence(cancer: str) -> Pathway:
    """Lung cancer: survival far below the Nordic level (NORDCAN), and the roadmap's statement
    that poor-prognosis cancers are often diagnosed at an advanced stage (page 22)."""
    return Pathway(
        cancer, "national", "Detection and diagnosis", "national",
        "Five-year survival in Finland is far below the Nordic level, and the roadmap reports that poor-prognosis "
        "cancers are often diagnosed at an advanced stage, with vague symptoms and smoking stigma delaying care "
        "(roadmap, page 22). This raises a question about detection and diagnosis in every county.",
        ["No public source gives lung cancer survival, stage or screening per county. The county view uses age-adjusted mortality.",
         "A lung cancer screening pilot started in 2026 in Helsinki and eight counties (roadmap, page 46)."],
    )


def _weaker(a: str, b: str) -> str:
    order = ["short", "mixed", "persistent"]
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
