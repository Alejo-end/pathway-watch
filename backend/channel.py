"""Channel Gap: how much of working-age primary care goes through the public health centre.

The roadmap (page 11) reports that diagnosis took twice as long when a patient with symptoms
went to public health care instead of a private provider (an unpublished lymphoma study).
Finland has three parallel channels: public health centres, private clinics and occupational
health care. A county where more first contacts go through the public channel has more people
exposed to that delay.

No public source gives occupational health coverage per county. The app uses visits instead:
public share = public primary care physician visits / (public + occupational health physician
visits), both per 1000 people aged 15-64 (Sotkanet 293 and 2371). It is a proxy for channel
use, not for coverage. Private visits (Sotkanet 692) are a share of the whole population, so
they are shown beside the ratio, not inside it.
"""

from __future__ import annotations

from .analysis import Data, Fact, series
from .indicators import NATIONAL

PUBLIC, OCCUPATIONAL, PRIVATE = 293, 2371, 692


def channel(data: Data, region: str) -> dict | None:
    pub, occ, priv = (series(data, i, region) for i in (PUBLIC, OCCUPATIONAL, PRIVATE))
    years = sorted(set(pub) & set(occ))
    if not years:
        return None
    y = years[-1]
    share = round(100 * pub[y] / (pub[y] + occ[y]), 1)
    # Visit statistics changed with the 2023 reform, so only recent years are comparable.
    trend = {yr: round(100 * pub[yr] / (pub[yr] + occ[yr]), 1) for yr in years if yr >= 2022}
    return {
        "year": y,
        "public_visits": pub[y],
        "occupational_visits": occ[y],
        "private_share": priv.get(y),
        "public_share": share,
        "trend": trend,
    }


def channel_table(data: Data) -> dict:
    out = {c: channel(data, c) for c in data.counties}
    nat = channel(data, NATIONAL)
    ranked = sorted((c for c in out if out[c]), key=lambda c: out[c]["public_share"], reverse=True)
    for i, c in enumerate(ranked, 1):
        out[c]["rank"] = i  # 1 = most reliant on the public channel
    return {"national": nat, "counties": out, "n": len(ranked)}


def channel_facts(data: Data, county: str) -> list[Fact]:
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
