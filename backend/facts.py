"""Facts: one computed statement each, with the ID of its source. A summary sentence may only cite these."""

from __future__ import annotations

from dataclasses import dataclass

from .analysis import Pathway, gap, rank
from .channel import channel_table
from .indicators import CANCERS, SOTKANET, has_county_survival
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
        if not g.years:
            continue
        label = SOTKANET[ind][0].lower()
        src = f"sotkanet:{ind}"
        y = g.years[-1]
        out.append(Fact(f"{ind}.county.{y}", f"{name}, {label}, {y}: {g.county_values[-1]:g}%", g.county_values[-1], "%", src))
        out.append(Fact(f"{ind}.national.{y}", f"Finland, {label}, {y}: {g.national_values[-1]:g}%", g.national_values[-1], "%", src))
        out.append(Fact(
            f"{ind}.gap",
            f"{name}, {label}: {g.avg_gap:+g} points against the national value, average {g.years[0]}–{g.years[-1]} "
            f"({g.direction}, {g.years_agreeing} of {len(g.years)} single years agree, {g.confidence} confidence)",
            g.avg_gap, "points", src,
        ))
        r, n = rank(data, ind, county)
        if r:
            out.append(Fact(f"{ind}.rank", f"{name} ranks {r} of {n} counties on {label} in {y} (1 = lowest)", r, "rank", src))
    return out


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
            f"{name}, {LABELS[cause].lower()} deaths {m.years[0]}–{m.years[-1]}: {m.observed} against {m.expected:g} expected "
            f"from the age structure, SMR {m.smr} (95% interval {m.low}–{m.high}, {m.confidence} confidence)",
            m.smr, "SMR", "statfin_mortality",
        ))
    m = mort.smr(cancer, county)
    out.append(Fact(
        f"mort.{cancer}.yearly",
        f"{name} has {round(m.deaths_per_year)} {LABELS[cancer].lower()} deaths per year on average in {m.years[0]}–{m.years[-1]}, "
        f"SMR {m.smr} (95% interval {m.low}–{m.high}, {m.confidence} confidence)",
        m.deaths_per_year, "deaths", "statfin_mortality",
    ))
    m = mort.smr("all", county)
    out.append(Fact(
        "mort.target",
        f"{name} has {round(m.deaths_per_year)} cancer deaths per year on average in {m.years[0]}–{m.years[-1]}. "
        f"The Goal 3 target of 10% fewer deaths means {round(m.deaths_per_year * 0.1)} fewer per year",
        round(m.deaths_per_year * 0.1), "deaths", "statfin_mortality",
    ))
    return out


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
             "In an unpublished study of lymphoma patients, diagnosis took twice as long through public health care "
             "as through private providers (roadmap, page 11)",
             None, "", "roadmap"),
    ]


def pathway_and_action_facts(pathway: Pathway, recs: list[dict]) -> list[Fact]:
    """The located pathway step and the first recommended roadmap measure."""
    out = [Fact("pathway", f"Most likely pathway step: {pathway.label} ({pathway.confidence} confidence). {pathway.reason}",
                None, "", "pathway_rule")]
    if recs:
        r = recs[0]
        out.append(Fact(f"measure.{r['measure']}", f"Roadmap measure {r['measure']}: {r['action']}", None, "", "roadmap"))
    return out
