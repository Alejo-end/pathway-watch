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
from .timeline import PILOT, primary_care_days

MEASURES: dict[str, dict] = {
    "local_baseline": {
        "action": "Establish a county cancer-pathway baseline before changing care.",
        "detail": "No county signal is a finding of this public-data screen, not proof that the pathway is equal. Measure current operations before choosing an intervention.",
        "nordic": None,
        "steps": ["data"],
        "actor": "County cancer lead, primary care lead and hospital quality lead",
        "level": "account",
        "first_step": "Name the pilot owner, cohort, data controller and quarterly review group; approve a minimum data dictionary before extracting any records.",
        "success": "A baseline from last year's records and the first quarterly aggregate report, with at least 95% completeness for each required timestamp, suppression of cells below five patients, and a documented decision on whether to test a service change.",
        "success_source": "local_step",
        "page": None,
        "source": "local_step",
        "proposal": "Team proposal: county measurement baseline",
    },
    "pathway_audit": {
        "action": "Audit the pathway step by step to find where the days go, then choose the roadmap measure for that step.",
        "detail": "The public data show the gap but not its step: detection, referral, diagnosis or treatment. The audit is useful whichever step is slow, and it decides the intervention. The data do not choose it.",
        "proposal": "Team proposal: least-regret pathway audit",
        "nordic": None,
        "steps": ["any"],
        "actor": "County cancer lead, with the primary care lead and the hospital quality lead",
        "level": "account",
        "first_step": "In 90 days: name a sponsor and a clinical lead, agree the data route with the data protection officer, take the dates of each step for last year's patients from the county's records, and choose the measure for the slowest step.",
        "success": "A baseline of the median days in each step, per health centre or pooled group, with at least 95% of the dates present, and a written choice of measure: 1.3.2 if patients come late, 2.5.2 if the delay is before referral, 3.1.2 if it is in diagnosis or treatment.",
        "success_source": "local_step",
        "page": None,
        "source": "local_step",
    },
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
        "success": ("A larger share of lung cancers found at stage I or II (the strategy's target for all cancers is 70%), "
                    "then fewer lung cancer deaths than the age structure predicts. Do not judge the pilot by five-year "
                    "survival: screening finds a cancer earlier, so survival rises even when no death is avoided."),
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
    "local_baseline": "Name a county clinical owner, data controller and quarterly review group. Freeze the cohort and timestamp dictionary before looking for a delay.",
    "pathway_audit": "Take last year's patients with this cancer from the hospital records. Count the median days from first "
                     "contact to referral, to diagnosis and to treatment, per health centre with at least 20 patients "
                     "and for the smaller centres pooled.",
    "2.5.2": "For patients with alarm symptoms, count the days from the first contact to the physician appointment "
             "and to the referral. Report the two numbers every quarter on a rolling 12 months, for each health "
             "centre with at least 20 patients and for the smaller centres pooled.",
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


# The outcome loop of each measure: what the county does by day 30, 60 and 90, the number it reads before
# and after, and the rule that decides whether to go on. Our proposals, not roadmap text. The pathway audit
# uses the 90-day plan and the go or no go rule of the county pilot, so the two never disagree.
NO_GO_RECORDS = "No go: fix the records first and measure again in three months."
LOOPS: dict[str, dict] = {
    "local_baseline": {
        "days": ["Name the owner, the data controller and the review group. Freeze the cohort and the list of dates.",
                 "Take last year's dates from the county's records. Report the share of dates present.",
                 "The review group reads the baseline and decides whether to test one change."],
        "measure": "Before: no county number for the time to treatment. After: the median days from first contact "
                   "to treatment, every quarter on a rolling 12 months.",
        "go": "Go only if at least 95% of the dates are present and the group agrees one change with an owner. " + NO_GO_RECORDS,
    },
    "2.5.2": {
        "days": ["Count, for last year's patients with alarm symptoms, the days from the first contact to the physician "
                 "appointment and to the referral.",
                 "Agree the referral criteria and the direct routes to tests with the hospital. Start in one health centre.",
                 "Count the same days for the patients since the start, and compare them with the baseline."],
        "measure": "Before and after: the median days from first contact to referral, in the starting health centre "
                   "and in the others.",
        "go": "Go to all health centres if the days fall and no later step gets longer. No go: if the days do not "
              "fall, look at the steps after the referral first.",
    },
    "3.1.2": {
        "days": ["Write down the county's pathway for this cancer as it works today, step by step.",
                 "Add the median days of each step from last year's records.",
                 "Name the step furthest from the national target time, and its owner."],
        "measure": "Before: no written pathway with days. After: the median days of each step against the target times.",
        "go": "Go: act on the step furthest from its target, with an owner and a date to measure again. " + NO_GO_RECORDS,
    },
    "2.5.1": {
        "days": ["Count how many days patients with alarm symptoms waited for a physician appointment last year.",
                 "Keep physician appointments free each week for these patients in one health centre.",
                 "Count the wait again, and count how many of the free appointments were used."],
        "measure": "Before and after: the median days from first contact to the physician appointment for patients "
                   "with alarm symptoms.",
        "go": "Go to more health centres if the wait falls and most free appointments are used. No go: if they stay "
              "unused, give them back and look at the referral instead.",
    },
    "1.3.1": {
        "days": ["Ask the screening provider for attendance by area and by language.",
                 "Send plain-language invitations in the area with the lowest attendance.",
                 "Compare attendance in that area with the last round and with similar areas."],
        "measure": "Before and after: attendance in the public screening programme in the chosen area.",
        "go": "Go to other areas if attendance rises more than in similar areas. No go: ask the people who do not "
              "attend why, before a second attempt.",
    },
    "2.4.5": {
        "days": ["Ask the Cancer Registry for the county's attendance by age group and area. Name one person who "
                 "answers for the number.",
                 "Find the groups and areas with the lowest attendance.",
                 "Choose one group and one way to reach it, with a date to measure attendance again."],
        "measure": "Before and after: attendance in the public screening programme for the chosen group, from the "
                   "screening register.",
        "go": "Go if the register data names a group with low attendance. No go: if attendance is low everywhere, "
              "the cause is not one group, so look at the invitation itself.",
    },
    "1.3.2": {
        "days": ["Put the list of alarm symptoms and the number to call on the health centre's pages and at its reception.",
                 "Count the patients who call or come with alarm symptoms each week.",
                 "Compare the count with the same weeks last year, and the wait for an appointment with the baseline."],
        "measure": "Before and after: contacts for alarm symptoms per week. Once a year, the share of new cancers "
                   "found at stage I or II, from the hospital's records.",
        "go": "Go on if contacts rise and the wait for an appointment does not. No go: if the wait grows, add "
              "appointments first (measure 2.5.1).",
    },
    "2.3.4": {
        "days": ["Tell THL that the county is ready to join the extension, and name the unit that sends the invitations.",
                 "Agree the invitation list with THL: long-term smokers in the target age group.",
                 "Send the first invitations and count who attends."],
        "measure": "Before and after: attendance among the invited, and the share of lung cancers found at stage I or II.",
        "go": "Go on if the invited attend and every finding gets its follow-up test. No go: change the invitation "
              "before inviting more people.",
    },
    "3.1.4": {
        "days": ["Choose the target time and the date fields for the county's main cancers.",
                 "Count, from hospital records, the share of last year's patients who started treatment within the target time.",
                 "Publish the number and set the date of the next count."],
        "measure": "Before: no county number. After: the share of patients treated within the target time, once a year.",
        "go": "Go: publish if at least 95% of the dates are present. No go: publish the share of dates present "
              "first, and fix the records.",
    },
    "3.2.1": {
        "days": ["Agree with the hospital on one extract a year: stage, referral date and treatment start for each new cancer.",
                 "Agree the data route with the data protection officer.",
                 "Take the first extract and report the share of fields present."],
        "measure": "Before: stage and dates are missing for most patients in public data. After: one extract a year "
                   "with these fields for each new cancer.",
        "go": "Go on if at least 95% of the fields are present. No go: first raise the share of clinical "
              "notifications that the hospital sends to the Cancer Registry.",
    },
}
LOOPS["pathway_audit"] = {
    "days": [f"{title}. {text}" for _, title, text in PILOT["plan_90"]],
    "measure": "Before: no county number for any step. After: the median days of each step. The step that the "
               "chosen measure targets is measured again every quarter.",
    "go": PILOT["go_no_go"],
}


def local_step(mid: str) -> dict:
    """The local step of a measure. For 2.5.2 it adds the days this part took in the lymphoma study."""
    out = {"text": LOCAL_STEPS[mid], "evidence": None, "evidence_source": None}
    if mid in ("2.5.2", "pathway_audit"):
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
        # The step is open, so no intervention follows from the data. The first action measures each step,
        # and the measures after it are the candidates that the audit chooses between.
        ids = ["pathway_audit", "2.5.2", "1.3.2", "3.1.2", "3.2.1"]
    else:
        # A clean public-data screen is not evidence of equal care.  Give the county an owned
        # measurement action instead of pretending that a national register is its next move.
        ids = ["local_baseline", "3.2.1"]

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
            "source": m.get("source", "roadmap"),
            "proposal": m.get("proposal"),
            "page": m["page"],
            "evidence": evidence if "data" not in m["steps"] else [],
            "why": _why(mid, surv, scr, pathway.step),
            "note": None,
            "note_sources": [],
            "local": local_step(mid),
            "loop": LOOPS[mid],
        })
        if mid == "2.4.5" and pathway.cancer == "breast":
            out[-1] |= BREAST_ATTENDANCE
    return out


# The step of the pathway that makes each measure the right choice after an audit.
AUDIT_FINDS = {
    "2.5.2": "between the first contact and the referral",
    "1.3.2": "before the first contact, because patients come late",
    "3.1.2": "in diagnosis or treatment",
}


def _why(mid: str, surv: str, scr: str, step: str) -> str:
    if mid == "3.2.1":
        return "The data that would answer the question does not exist in public form."
    if step == "national":
        return "Finland is far below the Nordic level, and the county's death count shows how many patients the gap concerns."
    if step == "any":
        if mid == "pathway_audit":
            return ("Survival is below the national value, and the data cannot tell which step. National screening is "
                    "newer than most of these diagnoses. A measure chosen before the audit would be a guess.")
        return f"A candidate if the audit finds the delay {AUDIT_FINDS[mid]}."
    if surv == "below" and scr == "below":
        return f"Survival and {ATTENDANCE} are both below the national value."
    if scr == "below":
        return f"{ATTENDANCE[0].upper() + ATTENDANCE[1:]} is below the national value. Survival is not."
    if surv == "below":
        return f"Survival is below the national value while {ATTENDANCE} is not."
    return "No survival gap. The measure keeps the pathway visible."
