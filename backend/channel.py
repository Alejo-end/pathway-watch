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

from .indicators import NATIONAL
from .sotkanet import CountyData

PUBLIC, OCCUPATIONAL, PRIVATE = 293, 2371, 692


def channel(data: CountyData, region: str) -> dict | None:
    pub, occ, priv = (data.series(i, region) for i in (PUBLIC, OCCUPATIONAL, PRIVATE))
    years = sorted(set(pub) & set(occ))
    if not years:
        return None
    y = years[-1]
    share = round(100 * pub[y] / (pub[y] + occ[y]), 1)
    return {
        "year": y,
        "public_visits": pub[y],
        "occupational_visits": occ[y],
        "private_share": priv.get(y),
        "public_share": share,
    }


def channel_table(data: CountyData) -> dict:
    """Every county and Finland. `rank` 1 is the county most reliant on the public channel."""
    out = {c: channel(data, c) for c in data.counties}
    nat = channel(data, NATIONAL)
    ranked = sorted((c for c in out if out[c]), key=lambda c: out[c]["public_share"], reverse=True)
    for i, c in enumerate(ranked, 1):
        out[c]["rank"] = i  # 1 = most reliant on the public channel
    return {"national": nat, "counties": out, "n": len(ranked)}
