"""Where to start in Finland: counties ranked by how many registers show them behind.

A survival signal counts when the county is below Finland in the latest year and our rough
95% interval of the gap excludes zero (`analysis.rough_interval`). An attendance signal counts
when the county is below Finland in the latest year and in most published years. Sotkanet
publishes no confidence interval, so the first is our estimate and the second is a description.
With 22 counties, about one such interval excludes zero by chance, so each survival signal also says
if it holds with the stricter limit for that many comparisons (`strict`).
A deaths signal counts when the county has more deaths than expected with a 95% interval above
100 (Statistics Finland). Survival, screening and
deaths come from different registers, but survival and deaths for one cancer are related
outcomes, so two signals are not two separate proofs. Deaths from the chosen cancer and from
all cancers come from the same register, so together they count as one.
"""

from __future__ import annotations

from .analysis import gap, locate, survival_interval
from .indicators import CANCERS, has_county_survival
from .mortality import LABELS, Mortality
from .recommend import recommend
from .sotkanet import CountyData


def signals(data: CountyData, mort: Mortality, cancer: str, county: str) -> list[dict]:
    """The signals for one county. Each has a kind, a short text and the ID of its source."""
    out = []
    if has_county_survival(cancer):
        g = gap(data, CANCERS[cancer]["survival"], county)
        iv = survival_interval(data, cancer, county)
        if g.direction == "below" and iv and iv.excludes_zero:
            out.append({"kind": "survival", "text": f"Survival {g.gap:+g} points in {g.year}", "size": abs(g.gap),
                        "source": f"sotkanet:{g.indicator}", "strict": iv.strict_excludes_zero})
        g = gap(data, CANCERS[cancer]["screening"], county)
        if g.direction == "below" and g.persistence == "persistent":
            out.append({"kind": "screening", "text": f"Programme attendance {g.gap:+g} points in {g.year}",
                        "size": abs(g.gap), "source": f"sotkanet:{g.indicator}"})
    if mort.ok:
        for cause in dict.fromkeys([cancer, "all"]):
            m = mort.smr(cause, county)
            if m.direction == "worse" and m.confidence == "high":
                out.append({"kind": f"deaths:{cause}", "text": f"{LABELS[cause]} deaths {m.smr - 100:+.0f}%", "size": m.smr - 100,
                            "source": "statfin_mortality"})
    return out


def ranking(data: CountyData, mort: Mortality, cancer: str) -> dict:
    """Counties with at least one signal. Most registers agreeing first, then most signals, then the largest.
    `by_measure` counts how many of them share each first action."""
    rows = []
    for county in data.counties:
        found = signals(data, mort, cancer, county)
        if not found:
            continue
        pathway = locate(data, cancer, county)
        first = recommend(data, pathway, county)[0]
        rows.append({"code": county, "name": data.names[county], "signals": found,
                     "registers": len({s["kind"].split(":")[0] for s in found}),
                     "step": pathway.step, "step_label": pathway.label,
                     "measure": first["measure"], "action": first["action"], "level": first["level"]})
    rows.sort(key=lambda r: (-r["registers"], -len(r["signals"]), -max(s["size"] for s in r["signals"])))
    by_measure: dict[str, int] = {}
    for r in rows:
        by_measure[r["measure"]] = by_measure.get(r["measure"], 0) + 1
    # Lung cancer has no county survival or screening data, so deaths are its only register.
    survival = [s for r in rows for s in r["signals"] if s["kind"] == "survival"]
    return {"cancer": cancer, "rows": rows, "by_measure": by_measure,
            "survival_signals": len(survival), "survival_strict": sum(1 for s in survival if s["strict"]),
            "registers": 3 if has_county_survival(cancer) else 1,
            "without_signal": len(data.counties) - len(rows), "counties": len(data.counties)}
