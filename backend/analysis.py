"""Compares a county with the country: the gap, a rough interval for it, the pathway question and the simulation.

Plain code, no language model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

from . import nordcan
from .indicators import CANCERS, NATIONAL, STEPS, SURVIVAL_WINDOW_YEARS, has_county_survival
from .mortality import shared as shared_mortality
from .registry import stage_sentence
from .sotkanet import CountyData

# A difference of up to this many points counts as "near the national value". Sotkanet rounds survival
# to whole percent, so a gap of exactly one point can be rounding alone and must not count as a gap.
NEAR = 1.0
MIN_YEARS = 3  # fewer shared years than this say nothing about persistence
DEATHS_TO_CHECK = 30  # below this many deaths in the pooled years, the SMR interval is too wide to confirm anything
ROUNDING_VARIANCE = 2 / 12  # two values rounded to whole percent, each with a uniform error of half a point


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
    them is not a test. For survival, `survival_interval` gives the evidence.

    `persistence` describes, it does not test. "persistent": at least three shared years, and
    the county is on the same side as in the latest year in more than half of them. "mixed":
    at least three shared years, but not most. "short": fewer than three shared years.
    """
    own = data.series(indicator, county)
    nat = data.series(indicator, NATIONAL)
    years = sorted(set(own) & set(nat))
    if not years:
        return Gap(indicator, county, None, None, None, None, "unknown", [], 0, "short")
    diffs = [own[y] - nat[y] for y in years]
    latest = round(diffs[-1], 1)
    direction = _side(latest)
    same = sum(1 for d in diffs if _side(round(d, 1)) == direction)
    if len(years) < MIN_YEARS:
        persistence = "short"
    else:
        persistence = "persistent" if same * 2 > len(years) else "mixed"
    return Gap(indicator, county, years[-1], own[years[-1]], nat[years[-1]], latest, direction, years, same, persistence)


@dataclass
class Interval:
    """A rough 95% interval for a county's survival gap. Our estimate, not a published figure."""

    patients: int  # estimated patients behind the county value: new cases per year x the years one value covers
    cases_per_year: int
    se: float  # standard error of the gap, in points: the patient count and the rounding together
    low: float  # the gap minus 1.96 standard errors
    high: float  # the gap plus 1.96 standard errors
    excludes_zero: bool
    comparisons: int = 1  # how many counties are compared with Finland at once
    strict_low: float | None = None  # the same interval with the limit for that many comparisons
    strict_high: float | None = None
    strict_excludes_zero: bool | None = None


def strict_z(comparisons: int) -> float:
    """The normal limit that keeps the chance of any false signal among `comparisons` intervals at 5%
    (Bonferroni). 1.96 for one comparison, about 3.05 for 22."""
    return NormalDist().inv_cdf(1 - 0.05 / (2 * max(comparisons, 1)))


def rough_interval(county_value: float | None, national_value: float | None, cases_per_year: float | None,
                   comparisons: int = 1) -> Interval | None:
    """A rough 95% interval for county minus national survival, from the number of patients.

    The standard error of the county value is binomial: sqrt(p(1-p)/n), with n = new cases
    per year x the ten diagnosis years behind one Sotkanet value. Sotkanet rounds the county
    and the national value to whole percent, which adds a variance of 1/12 for each.

    The result is still too narrow, for reasons that the page states. Relative survival
    varies more than a plain share. The follow-up uses only part of the ten years. The
    county case count is an estimate from the age structure. The national value counts as
    exact apart from its rounding. Sotkanet publishes no interval.

    The app compares every county with Finland, so about one 95% interval in twenty excludes
    zero by chance. `comparisons` is the number of counties. The strict interval uses the
    limit of `strict_z`, and a gap that excludes zero there is not explained by the number of counties.
    """
    if county_value is None or national_value is None or not cases_per_year:
        return None
    n = round(cases_per_year * SURVIVAL_WINDOW_YEARS)
    p = min(max(county_value / 100, 0.0), 1.0)
    se = math.sqrt(100 ** 2 * p * (1 - p) / n + ROUNDING_VARIANCE)
    diff = county_value - national_value
    low, high = round(diff - 1.96 * se, 1) + 0.0, round(diff + 1.96 * se, 1) + 0.0  # + 0.0 turns -0.0 into 0.0
    z = strict_z(comparisons)
    s_low, s_high = round(diff - z * se, 1) + 0.0, round(diff + z * se, 1) + 0.0
    return Interval(n, round(cases_per_year), round(se, 1), low, high, low > 0 or high < 0,
                    comparisons, s_low, s_high, s_low > 0 or s_high < 0)


def many_counties_caveat(iv: Interval) -> str:
    """What the stricter limit says about a gap whose 95% interval excludes zero."""
    verdict = ("still excludes zero, so the number of counties does not explain the gap" if iv.strict_excludes_zero
               else "includes zero, so the gap can be one of the chance signals")
    return (f"The app compares {iv.comparisons} counties with Finland, so about one 95% interval excludes zero by "
            f"chance. With the stricter limit for {iv.comparisons} comparisons the interval is "
            f"{iv.strict_low:+g} to {iv.strict_high:+g} points. It {verdict}.")


def county_cases(data: CountyData, cancer: str, county: str) -> dict:
    """Estimated new cases per year in the county, from the NORDCAN count for Finland and the county's age structure."""
    nc = nordcan.load()
    finland = nordcan.combined(nc, cancer, "finland")
    mort = shared_mortality()
    return estimated_cases(data, county, finland["cases"] if finland else None,
                           f"NORDCAN, average {nc.get('period')}", "nordcan",
                           age_share=mort.expected_share(cancer, county) if mort.ok else None)


def survival_interval(data: CountyData, cancer: str, county: str) -> Interval | None:
    """The rough interval for the county's latest survival gap. None without survival data or a case count."""
    if not has_county_survival(cancer):
        return None
    g = gap(data, CANCERS[cancer]["survival"], county)
    return rough_interval(g.county_value, g.national_value, county_cases(data, cancer, county)["value"],
                          comparisons=len(data.counties))


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
    step: str  # detection, later, any, watch, none, unknown, national
    label: str
    evidence: str  # interval_excludes_zero, interval_includes_zero, persistent, mixed, short, or national
    reason: str
    caveats: list[str]
    deaths: str | None = None  # agree, not_confirmed or too_few: the survival gap read against deaths


ATTENDANCE = "attendance in the public screening programme"
OUTSIDE_PROGRAMME = ("The attendance figure counts the public programme only. A test in occupational or private "
                     "care is not in it. How many people in this county have no test at all is not known.")


def screening_is_too_new(cancer: str, survival_year: int | None) -> bool:
    """True when the national screening programme started inside the diagnosis years of the survival value.
    Then most of those patients were diagnosed before the programme, and attendance cannot explain survival."""
    started = CANCERS[cancer].get("screening_started")
    return started is not None and survival_year is not None and started > survival_year - SURVIVAL_WINDOW_YEARS + 1


def locate(data: CountyData, cancer: str, county: str) -> Pathway:
    """The pathway step to ask about first. A question to investigate, never a located cause.

    The rule compares whole counties, not patients. Low survival with low programme attendance
    raises a question about detection. Low survival with normal attendance raises a question
    about referral, diagnosis or treatment. Normal survival with low attendance is an early
    warning ("watch"). Without county survival data, the question comes from national evidence.

    Bowel cancer is different. National bowel screening started in 2022, inside the ten
    diagnosis years of every published survival value. So attendance never explains a bowel
    survival gap, and the step is "any": this data cannot tell which step. Low attendance in
    the new programme is still an early warning of its own.

    The evidence for a survival gap is the rough interval of `survival_interval`. The evidence
    for an attendance gap is its `persistence`.
    """
    if not has_county_survival(cancer):
        return _locate_from_national_evidence(cancer)
    spec = CANCERS[cancer]
    surv = gap(data, spec["survival"], county)
    scr = gap(data, spec["screening"], county)
    too_new = screening_is_too_new(cancer, surv.year)
    caveats = ["The rule compares counties, not patients. Survival describes patients diagnosed up to ten years ago."]
    if too_new:
        caveats.append(
            f"National {spec['label'].lower().replace(' cancer', '')} screening started in {spec['screening_started']}. "
            "Most patients behind the survival value were diagnosed before it, so attendance cannot explain survival."
        )
    r, n = rank(data, spec["survival"], county)
    if r == 1:
        caveats.append(
            f"{data.names[county]} has the lowest survival value of {n} counties. The lowest of {n} counties tends to "
            "look less extreme the next time it is measured, so the interval matters more than the rank."
        )
    if surv.direction == "unknown":
        return Pathway(cancer, "unknown", "Not enough data", "short", "No survival data for this county.", caveats)
    if surv.direction != "below" and scr.direction == "below":
        reason = (
            f"Survival is not below the national value, but {ATTENDANCE} is. "
            + ("The programme is new, so this is an early sign of how it works, not an explanation of survival. "
               if too_new else "Late detection can show in survival only years later. ")
            + "This raises a question about detection."
        )
        return Pathway(cancer, "watch", STEPS["detection"], scr.persistence, reason, caveats + [OUTSIDE_PROGRAMME])
    if surv.direction != "below":
        return Pathway(
            cancer, "none", "No survival gap found", surv.persistence,
            "Five-year relative survival is at or above the national value.", caveats,
        )
    iv = survival_interval(data, cancer, county)
    evidence = "short" if iv is None else "interval_excludes_zero" if iv.excludes_zero else "interval_includes_zero"
    if iv and iv.excludes_zero:
        caveats.append(many_counties_caveat(iv))
    deaths_status, deaths = deaths_check(cancer, county) or (None, None)
    if deaths:
        caveats.append(deaths)
    no_split = "No public source gives stage, referral or waiting times per county, so the app cannot tell the steps apart."
    stage = stage_sentence(cancer, county, data.names[county])
    stage_note = [stage] if stage else []  # read after the note that no public source gives stage per county
    if too_new:
        return Pathway(
            cancer, "any", "Detection, referral, diagnosis or treatment", evidence,
            "Survival is below the national value. This data cannot tell which step of the pathway the gap "
            "comes from. This raises a question about every step.", caveats + [no_split] + stage_note, deaths_status,
        )
    if scr.direction == "below":
        if evidence == "interval_excludes_zero" and scr.persistence != "persistent":
            evidence = scr.persistence  # the attendance gap is the weaker half of the question
        return Pathway(
            cancer, "detection", STEPS["detection"], evidence,
            f"Survival and {ATTENDANCE} are both below the national value. "
            "This raises a question about detection.", caveats + [OUTSIDE_PROGRAMME] + stage_note, deaths_status,
        )
    return Pathway(
        cancer, "later",
        f"{STEPS['referral']}, {STEPS['diagnosis'].lower()} or {STEPS['treatment'].lower()}",
        evidence if scr.direction != "unknown" else "short",
        f"Survival is below the national value, but {ATTENDANCE} is not. "
        "This raises a question about the steps after detection.",
        caveats + ["No public source gives referral or waiting times per county, so the app cannot tell these three steps apart."] + stage_note,
        deaths_status,
    )


def deaths_check(cancer: str, county: str) -> tuple[str, str] | None:
    """Reads a survival gap against the county's deaths from the same cancer, a second register.

    Low survival with more deaths than the age structure predicts: two registers agree. Low survival
    without extra deaths: fewer deaths per diagnosed patient but no more deaths overall, which fits
    fewer diagnoses for the same deaths (fewer early cancers found) or chance. The two cover different
    years, so the sentence reports agreement, never a cause. Returns (agree | not_confirmed | too_few, sentence).
    """
    m = shared_mortality()
    if not m.ok or cancer not in m.causes:
        return None
    s = m.smr(cancer, county)
    if s.observed < DEATHS_TO_CHECK:
        return "too_few", (f"Too few deaths to check the survival gap against a second register: {s.observed} deaths from this "
                f"cancer in {s.years[0]} to {s.years[-1]}.")
    where = (f"{s.deaths_per_year:g} deaths per year in {s.years[0]} to {s.years[-1]}, "
             f"SMR {s.smr}, 95% interval {s.low} to {s.high}")
    if s.low > 100:
        return "agree", f"Deaths agree: more deaths from this cancer than the age structure predicts ({where})."
    expected = "fewer than expected" if s.high < 100 else "the interval includes the expected number"
    return "not_confirmed", (f"Deaths do not confirm the survival gap ({where}, {expected}). "
            "A survival gap without extra deaths can come from fewer early cancers found, which lowers survival "
            "without adding deaths, or from chance. Ask for stage at diagnosis before changing treatment.")


def _locate_from_national_evidence(cancer: str) -> Pathway:
    """Lung cancer: survival far below the Nordic level (NORDCAN), and the roadmap's statement
    that poor-prognosis cancers are often diagnosed at an advanced stage (page 22)."""
    return Pathway(
        cancer, "national", "Detection and diagnosis", "national",
        "Five-year survival in Finland is far below the Nordic level, and the roadmap reports that poor-prognosis "
        "cancers are often diagnosed at an advanced stage, with vague symptoms and smoking stigma delaying care "
        "(roadmap, page 22). This raises a question about detection and diagnosis in every county.",
        ["No public source gives lung cancer survival, stage or screening per county. The county view uses age-adjusted mortality.",
         "A lung cancer screening pilot started in 2026 in Helsinki and eight counties (roadmap, page 46).",
         "In a survey of Nordic lung cancer professionals, Finland had the lowest access to CT from primary care and "
         "the longest waits in primary care (Khalife and others, Acta Oncologica 2025)."],
    )


AGE_SHARE_LIMIT = ("The age pattern of deaths from this cancer stands in for the age pattern of new cases. "
                   "Patients die at an older age than they are diagnosed, so the estimate is somewhat high "
                   "for a county with many old people and somewhat low for a young county.")
POPULATION_SHARE_LIMIT = "It ignores the age structure of the county."


def estimated_cases(data: CountyData, county: str, national_cases: int | None, basis: str, source: str,
                    age_share: float | None = None) -> dict:
    """New cases per year in the county: the national count times the county's share.

    `age_share` is the share that the county's age structure predicts (`Mortality.expected_share`).
    Without it the share is the county's share of the population, which ignores age. Cancer is a
    disease of old age, so the two differ: Satakunta holds 3.7% of the people and 4.6% of the
    expected bowel cancer deaths. The result is an estimate in both cases, and `limit` says why.
    `basis` says where the national count comes from, for display.
    """
    pop = data.population.get(county)
    nat = data.population.get(NATIONAL)
    if national_cases is None or (age_share is None and (not pop or not nat)):
        return {"value": None, "status": "missing", "source": source}
    by_population = f"{pop / nat:.1%}" if pop and nat else None
    if age_share is not None:
        return {
            "value": round(national_cases * age_share),
            "status": "estimate", "basis": "age structure", "source": source,
            "method": f"{national_cases} new cases per year in Finland ({basis}) x {age_share:.1%}, the county's share "
                      "by age structure" + (f" (its share of the population is {by_population})" if by_population else ""),
            "limit": AGE_SHARE_LIMIT, "share_source": "statfin_mortality",
        }
    return {
        "value": round(national_cases * pop / nat),
        "status": "estimate", "basis": "population", "source": source,
        "method": f"{national_cases} new cases per year in Finland ({basis}) x county population share {by_population}",
        "limit": POPULATION_SHARE_LIMIT, "share_source": None,
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
