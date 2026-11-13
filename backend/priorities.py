"""Where to start in Finland: counties ranked by how many independent sources show them behind.

A signal counts only if it is confident: a Sotkanet gap below Finland with high or medium
confidence, or more deaths than expected with a 95% interval above 100 (Statistics Finland).
Survival, screening and deaths come from different registers, so a county that is behind in
two of them is stronger evidence than one large gap. Deaths from the chosen cancer and from
all cancers come from the same register, so together they count as one.
"""

from __future__ import annotations

from .analysis import gap, locate
from .indicators import CANCERS, has_county_survival
from .mortality import LABELS, Mortality
from .recommend import recommend
from .sotkanet import CountyData


def signals(data: CountyData, mort: Mortality, cancer: str, county: str) -> list[dict]:
    """The confident signals for one county. Each has a kind, a short text and the ID of its source."""
    out = []
    if has_county_survival(cancer):
        for kind in ("survival", "screening"):
            g = gap(data, CANCERS[cancer][kind], county)
            if g.direction == "below" and g.confidence in ("high", "medium"):
                out.append({"kind": kind, "text": f"{kind.capitalize()} {g.avg_gap:+g} points", "size": abs(g.avg_gap),
                            "source": f"sotkanet:{g.indicator}"})
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
    return {"cancer": cancer, "rows": rows, "by_measure": by_measure,
            "registers": 3 if has_county_survival(cancer) else 1,
            "without_signal": len(data.counties) - len(rows), "counties": len(data.counties)}
