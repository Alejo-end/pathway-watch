"""Map a located gap to roadmap measures. Each recommendation names its measure and its evidence.

Pages refer to the measure headings in the roadmap PDF (page numbers as printed).
"""

from __future__ import annotations

from .analysis import Pathway, gap
from .indicators import CANCERS, has_county_survival
from .sotkanet import CountyData

MEASURES: dict[str, dict] = {
    "2.5.2": {
        "action": "Adopt standardized referral criteria so that patients with possible cancer symptoms go fast to diagnostic tests.",
        "detail": "Part of the national care pathways.",
        "nordic": "Denmark (Kræftpakkeforløb), Sweden (SVF) and Norway (Pakkeforløp)",
        "steps": ["later"],
        "actor": "County, with FICAN",
        "page": 52,
    },
    "3.1.2": {
        "action": "Publish the national care pathway for this cancer with defined target access times, and report the county against them.",
        "detail": "Five cancers by 2026–2028, all major cancers by 2029–2031. Indicator: patients start treatment within target times.",
        "nordic": None,
        "steps": ["later"],
        "actor": "FICAN and THL",
        "page": 56,
    },
    "2.5.1": {
        "action": "Add doctor resources in public primary care, for example by making the personal doctor model national.",
        "detail": "The roadmap reports that diagnosis took twice as long through public care as through private care in a study of lymphoma patients (page 11).",
        "nordic": None,
        "steps": ["later"],
        "actor": "County",
        "page": 51,
    },
    "1.3.1": {
        "action": "Raise screening attendance in language groups with targeted, community-based communication.",
        "detail": "Immigrants take part in screening less (roadmap, page 11).",
        "nordic": None,
        "steps": ["detection"],
        "actor": "County, with THL",
        "page": 33,
    },
    "2.4.5": {
        "action": "Use screening register data together with THL to find the groups that do not attend.",
        "detail": None,
        "nordic": None,
        "steps": ["detection"],
        "actor": "County and THL",
        "page": 50,
    },
    "1.3.2": {
        "action": "Run the national communication plan on cancer symptoms locally, so people seek care early.",
        "detail": None,
        "nordic": None,
        "steps": ["detection"],
        "actor": "THL and the county",
        "page": 34,
    },
    "2.3.4": {
        "action": "Extend the lung cancer screening pilot for long-term smokers, and invite first the counties with the most lung cancer deaths.",
        "detail": "The pilot started in 2026 in Helsinki and eight counties. The roadmap plans a regional extension in 2026–2028 to the target group of the EU recommendation.",
        "nordic": None,
        "steps": ["national"],
        "actor": "Ministry of Social Affairs and Health, THL and the counties",
        "page": 46,
    },
    "3.1.4": {
        "action": "Define national quality and effectiveness targets and indicators, so that every county reports how many patients start treatment within the target time.",
        "detail": "Sweden reports this share for every region each year. Finland reports it for none.",
        "nordic": "Sweden (SVF lead-time target: 80% of patients within the lead time)",
        "steps": ["data"],
        "actor": "FICAN and THL",
        "page": 58,
    },
    "3.2.1": {
        "action": "Create the legal basis for a national cancer care quality register at the THL Cancer Registry.",
        "detail": "Without county data on stage, waiting times and treatment, nobody can tell referral, diagnosis and treatment delays apart.",
        "nordic": None,
        "steps": ["data"],
        "actor": "Ministry of Social Affairs and Health, THL",
        "page": 59,
    },
}


def recommend(data: CountyData, pathway: Pathway, county: str) -> list[dict]:
    """The ordered list of recommendations. The first one is the first action.
    `evidence` holds the IDs of the facts that support a recommendation."""
    if has_county_survival(pathway.cancer):
        spec = CANCERS[pathway.cancer]
        surv = gap(data, spec["survival"], county).direction
        scr_gap = gap(data, spec["screening"], county)
        scr = scr_gap.direction
        evidence = [f"{spec['survival']}.gap"] + ([f"{spec['screening']}.gap"] if scr_gap.years else [])
    else:
        surv = scr = "unknown"
        evidence = [f"mort.{pathway.cancer}", f"nordcan.{pathway.cancer}"]

    if pathway.step == "national":
        ids = ["2.3.4", "1.3.2", "2.5.2", "3.2.1"]
    elif pathway.step in ("detection", "watch"):
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
            "why": _why(mid, surv, scr, pathway.step),
        })
    return out


def _why(mid: str, surv: str, scr: str, step: str) -> str:
    if mid == "3.2.1":
        return "The data to locate the gap more exactly does not exist in public form."
    if step == "national":
        return "Finland is far below the Nordic level, and the county's death count shows how many patients the gap concerns."
    if surv == "below" and scr == "below":
        return "Survival and screening attendance are both below the national value."
    if scr == "below":
        return "Screening attendance is below the national value, although survival is not yet."
    if surv == "below":
        return "Survival is below the national value while screening attendance is not."
    return "No survival gap. The measure keeps the pathway visible."
