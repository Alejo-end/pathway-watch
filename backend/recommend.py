"""Map a pathway question to roadmap measures. Each recommendation names its measure and its evidence.

`page` is the page of the measure heading in the roadmap PDF, as printed. `first_step` restates
the measure's own implementation paragraph ("Toteutus") on that page. `level` says who must act:
"account" is a wellbeing services county or its hospital, "national" is the ministry, THL or
FICAN, and "both" needs a national decision that each county then applies.
"""

from __future__ import annotations

from .analysis import ATTENDANCE, Pathway, gap
from .indicators import CANCERS, has_county_survival
from .sotkanet import CountyData
from .timeline import primary_care_days

MEASURES: dict[str, dict] = {
    "2.5.2": {
        "action": "Adopt standardized referral criteria so that patients with possible cancer symptoms go fast to diagnostic tests.",
        "detail": "Part of the national care pathways.",
        "nordic": "Denmark (Kræftpakkeforløb), Sweden (SVF) and Norway (Pakkeforløp)",
        "steps": ["later"],
        "actor": "County, with FICAN",
        "level": "both",
        "first_step": 'Describe the symptom-based procedures, the test responsibilities of primary care and the direct routes to tests. Train primary care staff to recognise cancer early.',
        "success": 'The share of patients who start treatment within the target time. Sweden reports it per region: 47% in 2025 against a target of 80%.',
        "success_source": "rcc_svf_2025",
        "page": 52,
    },
    "3.1.2": {
        "action": "Publish the national care pathway for this cancer with defined target access times, and report the county against them.",
        "detail": "Five cancers by 2026–2028, all major cancers by 2029–2031. Indicator: patients start treatment within target times.",
        "nordic": None,
        "steps": ["later"],
        "actor": "FICAN and THL",
        "level": "national",
        "first_step": 'Describe the national pathway with the Nordic models, then apply it as a regional pathway in each county.',
        "success": "The roadmap's own indicator: patients start treatment within the target times.",
        "success_source": "roadmap",
        "page": 56,
    },
    "2.5.1": {
        "action": "Add doctor resources in public primary care, for example by making the personal doctor model national.",
        "detail": "In a Finnish study of 160 lymphoma patients, the median time from first symptoms to treatment was 127 days through a public health centre and 76 days through private or occupational care (Kuitunen and others, Cancer Medicine 2026). The roadmap cites this study on page 11.",
        "nordic": None,
        "steps": ["later"],
        "actor": "County",
        "level": "both",
        "first_step": 'Add doctor capacity in primary care and support personal doctor models with state grants.',
        "success": 'Continuity of care and delays in access to care, which the roadmap says to follow. No public county figure exists yet.',
        "success_source": "roadmap",
        "page": 51,
    },
    "1.3.1": {
        "action": "If language groups are among the people who do not attend, raise their attendance with targeted, community-based communication.",
        "detail": "The roadmap reports that immigrants take part in screening less (page 11). The cause of low attendance in this county is not known.",
        "nordic": None,
        "steps": ["detection"],
        "actor": "County, with THL",
        "level": "account",
        "first_step": 'Produce multilingual, plain-language material and build targeted communication with language and cultural minority organisations.',
        "success": "Attendance of 80% in the screening programme in every county, the strategy's target. Sotkanet publishes it per county each year.",
        "success_source": "strategy",
        "page": 33,
    },
    "2.4.5": {
        "action": "Use screening register data together with THL to find which groups do not attend.",
        "detail": "The attendance figure counts the public programme only, so first learn who has no test at all.",
        "nordic": None,
        "steps": ["detection"],
        "actor": "County and THL",
        "level": "both",
        "first_step": 'Report all screening data monthly to the screening registers, so that the Cancer Registry can give each county a current picture.',
        "success": "Attendance of 80% in the screening programme in every county, the strategy's target. Sotkanet publishes it per county each year.",
        "success_source": "strategy",
        "page": 50,
    },
    "1.3.2": {
        "action": "Run the national communication plan on cancer symptoms locally, so people seek care early.",
        "detail": None,
        "nordic": None,
        "steps": ["detection"],
        "actor": "THL and the county",
        "level": "national",
        "first_step": "Write and run a national plan on cancer symptom awareness with the Cancer Society, FICAN and THL. The roadmap's model is the UK campaign Be Clear on Cancer.",
        "success": "At least 70% of cancers diagnosed at stage I or II, the strategy's target.",
        "success_source": "strategy",
        "page": 34,
    },
    "2.3.4": {
        "action": "Extend the lung cancer screening pilot for long-term smokers, and invite first the counties with the most lung cancer deaths.",
        "detail": "The pilot started in 2026 in Helsinki and eight counties. The roadmap plans a regional extension in 2026–2028 to the target group of the EU recommendation.",
        "nordic": None,
        "steps": ["national"],
        "actor": "Ministry of Social Affairs and Health, THL and the counties",
        "level": "national",
        "first_step": 'Extend the pilot regionally in 2026–2028 and invite the target group of the EU recommendation.',
        "success": 'Five-year lung cancer survival up by 14 points, the Goal 3 target.',
        "success_source": "strategy",
        "page": 46,
    },
    "3.1.4": {
        "action": "Define national quality and effectiveness targets and indicators, so that every county reports how many patients start treatment within the target time.",
        "detail": "Sweden reports this share for every region each year. Finland reports it for none.",
        "nordic": "Sweden (SVF lead-time target: 80% of patients within the lead time)",
        "steps": ["data"],
        "actor": "FICAN and THL",
        "level": "national",
        "first_step": 'Define the targets and indicators in the same process as the care pathways, and report them through the quality register.',
        "success": 'Every county reports the share of patients treated within the target time, as all 21 Swedish regions do.',
        "success_source": "rcc_svf_2025",
        "page": 58,
    },
    "3.2.1": {
        "action": "Create the legal basis for a national cancer care quality register at the THL Cancer Registry.",
        "detail": "Without county data on stage, waiting times and treatment, nobody can tell referral, diagnosis and treatment delays apart.",
        "nordic": None,
        "steps": ["data"],
        "actor": "Ministry of Social Affairs and Health, THL",
        "level": "national",
        "first_step": 'Update the ministry decree on THL quality registers to include cancer, and fund the register. The research project of THL, the Cancer Registry and FICAN runs to the end of 2027.',
        "success": 'The register publishes county data, first for five cancers.',
        "success_source": "roadmap",
        "page": 59,
    },
}


# What one health centre or one county can start next month, without a national decision.
# These are our proposals, not roadmap text. Source ID: local_step.
LOCAL_STEPS: dict[str, str] = {
    "2.5.2": "For patients with alarm symptoms, count the days from the first contact to the physician appointment "
             "and to the referral. Report the two numbers for each health centre every month.",
    "3.1.2": "Write down the county's pathway for this cancer as it works today, with the days that each step takes.",
    "2.5.1": "Keep physician appointments free each week for patients with alarm symptoms, and count the days "
             "that these patients wait.",
    "1.3.1": "Ask the screening provider for attendance by area. Test plain-language invitations in the area with "
             "the lowest attendance, and compare attendance before and after.",
    "2.4.5": "Ask the Cancer Registry for the county's attendance by age group and area. Name one person who "
             "answers for the number.",
    "1.3.2": "Put the list of alarm symptoms and the number to call on the health centre's pages and at its reception.",
    "2.3.4": "Tell THL that the county is ready to join the extension, and name the unit that sends the invitations.",
    "3.1.4": "Count, from hospital records, the share of the county's patients who start treatment within the "
             "target time. Publish the number once a year.",
    "3.2.1": "Agree with the hospital on one extract a year: stage, referral date and treatment start for each new cancer.",
}


def local_step(mid: str) -> dict:
    """The local step of a measure. For 2.5.2 it adds the days this part took in the lymphoma study."""
    out = {"text": LOCAL_STEPS[mid], "evidence": None, "evidence_source": None}
    if mid == "2.5.2":
        d = primary_care_days()
        out["evidence"] = (f"In a Finnish study of lymphoma patients, the time from first contact to referral was "
                           f"{d['public_days']} days through a public health centre and {d['private_days']} days through "
                           f"private or occupational care.")
        out["evidence_source"] = "kuitunen_2026"
    return out


# Breast cancer: what measure 2.4.5 means when attendance in the public programme is low.
# `note` is our reading of two studies, not text from the roadmap.
BREAST_ATTENDANCE = {
    "action": "Find who has no mammogram at all. Together with THL, link the screening register with the "
              "mammograms made outside the programme, then find which groups do not attend.",
    "note": "A Finnish Cancer Registry study made this link for the whole country. Upper-level employees used "
            "imaging outside the programme about twice as often as manual workers (8.2% against 3.6%). "
            "After the link, send reminders to the women with no mammogram in either place, and measure the "
            "effect. In a review of 54 studies, half of the tested ways to raise attendance had a clear effect.",
    "note_sources": ["fuhrmann_2024", "acharya_2021"],
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
        # The cause of low attendance is not known, so the first action finds who does not attend.
        ids = ["2.4.5", "1.3.1", "1.3.2", "3.2.1"]
    elif pathway.step == "later":
        ids = ["2.5.2", "3.1.2", "2.5.1", "3.2.1"]
    elif pathway.step == "any":
        # The step is open. Both first measures act on patients with symptoms, at first contact and at referral.
        ids = ["2.5.2", "1.3.2", "3.1.2", "3.2.1"]
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
            "level": m["level"],
            "first_step": m["first_step"],
            "success": m["success"],
            "success_source": m["success_source"],
            "source": "roadmap",
            "page": m["page"],
            "evidence": evidence if "data" not in m["steps"] else [],
            "why": _why(mid, surv, scr, pathway.step),
            "note": None,
            "note_sources": [],
            "local": local_step(mid),
        })
        if mid == "2.4.5" and pathway.cancer == "breast":
            out[-1] |= BREAST_ATTENDANCE
    return out


def _why(mid: str, surv: str, scr: str, step: str) -> str:
    if mid == "3.2.1":
        return "The data that would answer the question does not exist in public form."
    if step == "national":
        return "Finland is far below the Nordic level, and the county's death count shows how many patients the gap concerns."
    if step == "any":
        return ("Survival is below the national value, and the data cannot tell which step. National screening is "
                "newer than most of these diagnoses, and this measure acts on patients who come with symptoms.")
    if surv == "below" and scr == "below":
        return f"Survival and {ATTENDANCE} are both below the national value."
    if scr == "below":
        return f"{ATTENDANCE[0].upper() + ATTENDANCE[1:]} is below the national value. Survival is not."
    if surv == "below":
        return f"Survival is below the national value while {ATTENDANCE} is not."
    return "No survival gap. The measure keeps the pathway visible."
