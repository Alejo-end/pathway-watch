"""A screening campaign for one county: when to run it, who is in it, and what the county does.

The campaign reminds people who are already in a national screening programme. It adds no new test
and no new group. Every rule is a yes or no on a field of the programme's own records: date of birth,
sex, home municipality, and the invitation and the test of each round. No rule reads a diagnosis,
a medicine, a visit, income, education or language.

The programme records its own tests only. A person with a recent test in private or occupational care
looks like a person with no test, so the page says this next to every count.

The rules and the steps are our proposal. Source ID: campaign_rule.
"""

from __future__ import annotations

import math

from .indicators import CANCERS, NATIONAL
from .sotkanet import CountyData

TARGET = 80  # % attendance in every county, national cancer strategy, page 5

# Who the national programme invites, how often and with which test (source ID: fcr_screening).
# `outside` says what the app knows about tests outside the programme. `follow_up` is the test
# that a positive result needs, because a campaign adds work for that unit.
PROGRAMMES: dict[str, dict] = {
    "bowel": {
        "name": "bowel cancer screening",
        "group": "Women and men aged 56 to 74 from 2031. The programme grows by age group until then. "
                 "On the day we read it, the registry page named the ages 60 to 70.",
        "interval": "Every two years",
        "test": "A stool test (FIT) that comes by mail. The person does it at home.",
        "reminder": "Mail a new test kit with a short letter.",
        "outside": {"text": "The app has no source for stool tests or colonoscopies outside the programme.",
                    "source": "campaign_rule"},
        "follow_up": "A positive stool test needs a colonoscopy. Before the letters go out, ask the endoscopy unit how "
                     "many more it can do. No public source gives the wait for an endoscopy in a county.",
    },
    "breast": {
        "name": "breast cancer screening",
        "group": "Women aged 50 to 69.",
        "interval": "Every two years",
        "test": "Mammography.",
        "reminder": "First do the first action: link the screening register with the mammograms made outside the "
                    "programme. Then send a new appointment time to the women with no mammogram in either place.",
        "outside": {"text": "A Finnish Cancer Registry study counted mammograms outside the programme for the whole "
                            "country. Upper-level employees had them about twice as often as manual workers "
                            "(8.2% against 3.6%).",
                    "source": "fuhrmann_2024"},
        "follow_up": "A positive mammogram needs more imaging and often a tissue sample. Tell the breast unit how many "
                     "letters go out, and when.",
    },
    "cervical": {
        "name": "cervical cancer screening",
        "group": "Women aged 30 to 65. Some municipalities also invite women aged 25.",
        "interval": "Every five years",
        "test": "A Pap test or an HPV test.",
        "reminder": "Send a reminder letter. If the programme still has no test, mail a kit to take the sample at home.",
        "outside": {"text": "In a study in Espoo, about 20% of the women who came after a reminder had their last Pap "
                            "test five or more years before. For 70% to 75% the reminder only gave a test that they "
                            "did not need yet.",
                    "source": "virtanen_2010"},
        "follow_up": "A positive test needs a colposcopy. Tell the gynaecology unit how many letters go out, and when.",
    },
}

# A person is in the campaign when all three answers are yes.
PERSON_RULES = [
    {"rule": "The person is in the age and sex group of the national programme.",
     "field": "Date of birth and sex", "register": "Population register"},
    {"rule": "The person lives in the county.",
     "field": "Home municipality", "register": "Population register"},
    {"rule": "The programme invited the person in this round and has no test in the programme on the reply date.",
     "field": "Invitation and test of this round", "register": "The county's screening provider"},
]
# The order in which the county reminds people, if it cannot remind all of them at once.
ORDER = {
    "text": "If the county cannot remind everyone at once, it starts with the people who have never taken part in the programme.",
    "field": "Invitation and test of the earlier rounds", "register": "The county's screening provider",
    "evidence": "In the earlier Finnish bowel screening programme, about 80% of the people who did not take "
                "part in the first round also did not take part in the second.",
    "evidence_source": "jantti_2021",
}
NOT_USED = ["diagnoses", "medicines", "laboratory results", "visits to a doctor", "income", "education",
            "language", "country of birth"]


def size(attended: int, share: float) -> dict:
    """How many people the campaign concerns. Sotkanet gives the people who attended and their share of the
    invited, so the invited are attended / share. The share has one decimal, so the results are rounded to tens.
    `needed` rounds up, so a county below the target never shows zero."""
    invited = attended / (share / 100)
    tens = lambda x: int(round(x, -1))
    short = round(TARGET / 100 * invited - attended, 6)  # the division leaves float noise that ceil would turn into ten people
    return {
        "attended": attended,
        "invited": tens(invited),
        "not_attended": tens(invited - attended),
        "needed": math.ceil(short / 10) * 10 if share < TARGET else 0,
    }


def campaign(data: CountyData, cancer: str, county: str) -> dict:
    """The campaign for one cancer and one county. `status` is "campaign" when attendance in the public
    programme is below the target in the latest year, "target met" when it is not, and "no programme"
    when the cancer has no national screening programme."""
    ind = CANCERS[cancer]["screening"]
    if ind is None:
        return {"status": "no programme", "source": "campaign_rule",
                "text": "This cancer has no national screening programme, so there is no invitation list and no campaign. "
                        "The pilot of roadmap measure 2.3.4 decides its own group."}
    series = data.series(ind, county)
    if not series:
        return {"status": "no data", "source": "campaign_rule", "text": "No attendance value for this county."}
    year = max(series)
    share = series[year]
    attended = data.counts.get(ind, {}).get(county, {}).get(year)
    p = PROGRAMMES[cancer]
    below = share < TARGET
    return {
        "status": "campaign" if below else "target met",
        "programme": p,
        "programme_source": "fcr_screening",
        "year": year, "attendance": share, "national": data.series(ind, NATIONAL).get(year), "target": TARGET,
        "attendance_source": f"sotkanet:{ind}", "target_source": "strategy",
        "size": size(attended, share) if attended else None,
        "county_rule": {
            "text": f"The county runs a campaign when its attendance in the public programme is below {TARGET}% in the latest year.",
            "met": below,
        },
        "person_rules": PERSON_RULES,
        "not_used": NOT_USED,
        "order": ORDER,
        "outside": {
            "text": "The programme records its own tests only. A test in private or occupational care is not counted, "
                    "so some of these people have a recent test. " + p["outside"]["text"],
            "source": p["outside"]["source"],
        },
        "steps": [
            {"title": "Plan the follow-up tests", "text": p["follow_up"]},
            {"title": "Remind", "text": p["reminder"]},
            {"title": "Let the person act",
             "text": "The letter holds a link to a service that the county runs. The person logs in with strong "
                     "authentication, sees the open invitation, and orders a kit or books a time. "
                     "The service does not exist yet. Cancer Care Atlas has no access to it."},
            {"title": "Count the result",
             "text": "The county counts attendance before and after, for each area and age group. A group with "
                     "fewer than five people shows no value. Cancer Care Atlas gets these counts and no names."},
        ],
        "evidence": {
            "text": "In a randomized trial in Espoo, a reminder letter raised total attendance in cervical screening "
                    "from 65% to 74%, and a mailed self-sampling kit raised it from 65% to 76%. The letter and "
                    "then the kit raised it from 63% to 78%. The trial covers cervical screening only.",
            "source": "virtanen_2011",
        },
        "reading": "The rules and the steps are our proposal. They use the programme's own records: who it invited "
                   "and who took the test, in this round and in earlier rounds. We did not confirm with a county "
                   "which register holds each field. No county and no data protection officer reviewed the proposal.",
        "source": "campaign_rule",
    }
