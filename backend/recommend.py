"""Map a located gap to roadmap measures. Each recommendation names its measure and its evidence.

Pages are None until a team member reads the roadmap page and fills them in.
"""

from __future__ import annotations

from .analysis import Data, Pathway, gap
from .indicators import CANCERS

MEASURES: dict[str, dict] = {
    "2.5.2": {
        "action": "Adopt standardized referral criteria so that patients with possible cancer symptoms go fast to diagnostic tests.",
        "detail": "Part of the national care pathways.",
        "nordic": "Denmark (Kræftpakkeforløb), Sweden (SVF) and Norway (Pakkeforløp)",
        "steps": ["later"],
        "actor": "County, with FICAN",
        "page": None,
    },
    "3.1.2": {
        "action": "Publish the national care pathway for this cancer with defined target access times, and report the county against them.",
        "detail": "Five cancers by 2026–2028, all major cancers by 2029–2031. Indicator: patients start treatment within target times.",
        "nordic": None,
        "steps": ["later"],
        "actor": "FICAN and THL",
        "page": None,
    },
    "2.5.1": {
        "action": "Add doctor resources in public primary care, where the first contact happens.",
        "detail": "The roadmap reports that diagnosis took twice as long through public care as through private care in a study of lymphoma patients (page 11).",
        "nordic": None,
        "steps": ["later"],
        "actor": "County",
        "page": None,
    },
    "1.3.1": {
        "action": "Raise screening attendance in language groups with targeted, community-based communication.",
        "detail": "Immigrants take part in screening less (roadmap, page 11).",
        "nordic": None,
        "steps": ["detection"],
        "actor": "County, with THL",
        "page": 11,
    },
    "2.4.5": {
        "action": "Use screening register data together with THL to find the groups that do not attend.",
        "detail": None,
        "nordic": None,
        "steps": ["detection"],
        "actor": "County and THL",
        "page": None,
    },
    "1.3.2": {
        "action": "Run the national communication plan on cancer symptoms locally, so people seek care early.",
        "detail": None,
        "nordic": None,
        "steps": ["detection"],
        "actor": "THL and the county",
        "page": None,
    },
    "3.2.1": {
        "action": "Give the THL Cancer Registry the legal basis to collect waiting times and stage at diagnosis per county.",
        "detail": "Without this data, nobody can tell referral, diagnosis and treatment delays apart.",
        "nordic": None,
        "steps": ["data"],
        "actor": "Ministry of Social Affairs and Health, THL",
        "page": None,
    },
}


def recommend(data: Data, pathway: Pathway, county: str) -> list[dict]:
    """The ordered list of recommendations. The first one is the first action."""
    spec = CANCERS[pathway.cancer]
    surv = gap(data, spec["survival"], county)
    scr = gap(data, spec["screening"], county)
    evidence = [f"{spec['survival']}.gap"]
    if scr.avg_gap is not None:
        evidence.append(f"{spec['screening']}.gap")

    if pathway.step in ("detection", "watch"):
        ids = ["1.3.1", "2.4.5", "1.3.2", "3.2.1"]
    elif pathway.step == "later":
        ids = ["2.5.2", "3.1.2", "2.5.1", "3.2.1"]
    else:
        ids = ["3.2.1"]

    out = []
    for mid in ids:
        m = MEASURES[mid]
        out.append({
            "measure": mid,
            "action": m["action"],
            "detail": m["detail"],
            "nordic": m["nordic"],
            "actor": m["actor"],
            "source": "roadmap",
            "page": m["page"],
            "evidence": evidence if "data" not in m["steps"] else [],
            "why": _why(mid, surv.direction, scr.direction),
        })
    return out


def _why(mid: str, surv: str, scr: str) -> str:
    if mid == "3.2.1":
        return "The data to locate the gap more exactly does not exist in public form."
    if surv == "below" and scr == "below":
        return "Survival and screening attendance are both below the national value."
    if scr == "below":
        return "Screening attendance is below the national value, although survival is not yet."
    if surv == "below":
        return "Survival is below the national value while screening attendance is not."
    return "No survival gap. The measure keeps the pathway visible."
