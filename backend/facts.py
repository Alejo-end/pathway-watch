"""Facts: one computed statement each, with the ID of its source. A summary sentence may only cite these."""

from __future__ import annotations

from dataclasses import dataclass

from .analysis import Gap, Interval, Pathway, gap, rank, survival_interval
from .channel import channel_table
from .indicators import CANCERS, SOTKANET, SURVIVAL_WINDOW_YEARS, has_county_survival
from .mortality import GOAL3, LABELS, Mortality
from .sotkanet import CountyData


@dataclass
class Fact:
    id: str
    text: str
    value: float | None
    unit: str
    source: str


def survival_and_screening_facts(data: CountyData, cancer: str, county: str) -> list[Fact]:
    """County against Finland on the cancer's Sotkanet indicators. Empty for a cancer without them."""
    if not has_county_survival(cancer):
        return []
    name = data.names[county]
    out: list[Fact] = []
    for key in ("survival", "screening"):
        ind = CANCERS[cancer][key]
        g = gap(data, ind, county)
        if g.year is None:
            continue
        label = SOTKANET[ind][0].lower()
        src = f"sotkanet:{ind}"
        y = g.year
        out.append(Fact(f"{ind}.county.{y}", f"{name}, {label}, {y}: {g.county_value:g}%", g.county_value, "%", src))
        out.append(Fact(f"{ind}.national.{y}", f"Finland, {label}, {y}: {g.national_value:g}%", g.national_value, "%", src))
        out.append(Fact(
            f"{ind}.gap",
            f"{name}, {label}, {y}: {gap_phrase(g)}. {name} was {side_phrase(g)} in {g.years_same_side} of "
            f"{len(g.years)} published years ({g.years[0]} to {g.years[-1]}). The count of years describes, it is not "
            "a test. No confidence interval is published",
            g.gap, "points", src,
        ))
        iv = survival_interval(data, cancer, county) if key == "survival" else None
        if iv:
            out.append(Fact(
                f"{ind}.interval",
                f"{name}, {label}, {y}: a rough 95% interval for the gap is {interval_words(iv)}. It is our estimate "
                f"from about {iv.patients} patients ({iv.cases_per_year} estimated new cases per year times "
                f"{SURVIVAL_WINDOW_YEARS} diagnosis years, standard error {iv.se:g} points with the rounding of the "
                "published values). It is not a published interval, and the true interval is wider",
                iv.se, "points", "survival_interval",
            ))
        r, n = rank(data, ind, county)
        if r:
            lowest = (f". The lowest of {n} counties tends to look less extreme the next time it is measured, "
                      "so the interval matters more than the rank") if r == 1 and key == "survival" else ""
            out.append(Fact(f"{ind}.rank", f"{name} ranks {r} of {n} counties on {label} in {y} (1 = lowest){lowest}",
                            r, "rank", src))
    return out


def interval_words(iv: Interval) -> str:
    """The rough interval in words: '6.4 to 1.6 points below the national value'."""
    if iv.high < 0:
        return f"{abs(iv.low):g} to {abs(iv.high):g} points below the national value"
    if iv.low > 0:
        return f"{iv.low:g} to {iv.high:g} points above the national value"
    return f"from {abs(iv.low):g} points below to {iv.high:g} points above the national value"


def gap_phrase(g: Gap) -> str:
    """The latest-year gap in words: '4 points below the national value' or 'near the national value (+0.5 points)'."""
    if g.direction == "near":
        return f"near the national value ({g.gap:+g} points)"
    unit = "point" if abs(g.gap) == 1 else "points"
    return f"{abs(g.gap):g} {unit} {g.direction} the national value"


def side_phrase(g: Gap) -> str:
    """The side of the national value the county is on: 'below the national value'."""
    return f"{g.direction} the national value"


def mortality_facts(data: CountyData, mort: Mortality, cancer: str, county: str) -> list[Fact]:
    """Age-adjusted cancer mortality (Goal 3, indicators 1 and 2). Empty if the mortality file is missing."""
    if not mort.ok:
        return []
    name = data.names[county]
    out = []
    for cause in dict.fromkeys(GOAL3 + [cancer]):
        m = mort.smr(cause, county)
        out.append(Fact(
            f"mort.{cause}",
            f"{name}, {LABELS[cause].lower()} deaths {m.years[0]} to {m.years[-1]}: {m.observed} against {m.expected:g} expected "
            f"from the age structure, SMR {m.smr} (95% interval {m.low} to {m.high}, {interval_phrase(m)})",
            m.smr, "SMR", "statfin_mortality",
        ))
    m = mort.smr(cancer, county)
    out.append(Fact(
        f"mort.{cancer}.yearly",
        f"{name} has {round(m.deaths_per_year)} {LABELS[cancer].lower()} deaths per year on average in {m.years[0]} to {m.years[-1]}, "
        f"SMR {m.smr} (95% interval {m.low} to {m.high}, {interval_phrase(m)})",
        m.deaths_per_year, "deaths", "statfin_mortality",
    ))
    m = mort.smr("all", county)
    out.append(Fact(
        "mort.target",
        f"{name} has {round(m.deaths_per_year)} cancer deaths per year on average in {m.years[0]} to {m.years[-1]}. "
        f"The Goal 3 target of 10% fewer deaths means {round(m.deaths_per_year * 0.1)} fewer per year",
        round(m.deaths_per_year * 0.1), "deaths", "statfin_mortality",
    ))
    return out


def interval_phrase(m) -> str:
    """What the 95% interval of an SMR supports. Only an interval that leaves out 100 supports "more" or "fewer"."""
    if m.confidence != "high":
        return "the interval includes the expected number"
    return "more deaths than expected" if m.direction == "worse" else "fewer deaths than expected"


def nordic_facts(cancer: str, benchmark: dict) -> list[Fact]:
    """Finland against the Nordic level (a `nordcan.benchmark` result). Empty if the level is unknown."""
    if benchmark["gap"] is None:
        return []
    target = f" Goal 3 target: +{benchmark['target']} points" if benchmark.get("target") else ""
    return [Fact(
        f"nordcan.{cancer}",
        f"Five-year survival for {CANCERS[cancer]['label'].lower()} in Finland is {benchmark['finland']}% against a Nordic level of "
        f"{benchmark['nordic']}% (Sweden and Norway, NORDCAN {benchmark['period']}), a gap of {benchmark['gap']} points.{target}",
        benchmark["gap"], "points", "nordcan",
    )]


def channel_facts(data: CountyData, county: str) -> list[Fact]:
    """How much of working-age primary care in the county goes through public health centres."""
    t = channel_table(data)
    c, nat = t["counties"].get(county), t["national"]
    if not c or not nat:
        return []
    name = data.names[county]
    y = c["year"]
    return [
        Fact("channel.share",
             f"In {name} in {y}, {c['public_share']:g}% of working-age physician visits in primary and occupational care "
             f"went through public health centres, against {nat['public_share']:g}% in Finland",
             c["public_share"], "%", "sotkanet:293"),
        Fact("channel.visits",
             f"{name}, {y}: {c['public_visits']:g} public health centre and {c['occupational_visits']:g} occupational health "
             f"physician visits per 1000 people aged 15-64",
             c["public_visits"], "per 1000", "sotkanet:2371"),
        Fact("channel.rank",
             f"{name} ranks {c['rank']} of {t['n']} counties on reliance on the public channel in {y} (1 = most reliant)",
             c["rank"], "rank", "sotkanet:293"),
        Fact("channel.roadmap",
             "In one unpublished study of lymphoma patients, diagnosis took twice as long through public health care "
             "as through private providers (roadmap, page 11)",
             None, "", "roadmap"),
    ]


EVIDENCE = {
    "interval_excludes_zero": "the rough interval of the survival gap excludes zero",
    "interval_includes_zero": "the rough interval of the survival gap includes zero",
    "persistent": "seen in most published years",
    "mixed": "the published years disagree",
    "short": "few years of data",
    "national": "national evidence",
}


def pathway_and_action_facts(pathway: Pathway, recs: list[dict]) -> list[Fact]:
    """The pathway step to ask about and the first recommended roadmap measure."""
    out = [Fact("pathway", f"Question to investigate: {pathway.label} (evidence: {EVIDENCE[pathway.evidence]}). "
                f"{pathway.reason}", None, "", "pathway_rule")]
    if recs:
        r = recs[0]
        out.append(Fact(f"measure.{r['measure']}", f"Roadmap measure {r['measure']}: {r['action']}", None, "", "roadmap"))
    return out
