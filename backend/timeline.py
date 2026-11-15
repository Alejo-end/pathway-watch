"""The step timeline of one Finnish lymphoma study, and what a county pilot measures with it.

The study (Kuitunen and others, Cancer Medicine 2026) gives the days from the first symptoms to
each step of the pathway, for patients who started at a public health centre appointment and for
patients who started in private or occupational care. The app copies the cumulative days from
figure 1 and computes the length of each step and the difference between the two routes.

The study covers one lymphoma type and 160 patients. The two routes hold 87 of them: 48 and 39.
The other patients started at an emergency service or elsewhere. The public group was older. The
paper tests only the whole interval, not each step. So the panel shows where the days add up in
this study. It does not show that the route causes the delay, and it says nothing about other cancers.

The paper gives three pairs of numbers for the whole interval. The medians are 127 and 76 days,
the means are 201 and 126 days, and figure 1 ends at 207 and 123 days. The figure is close to the
means. A few very long waits (up to 1,124 days) raise a mean, so the medians are lower.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "dlbcl_timeline.json"

# The interval that ends at each step: its name, who owns it, and the record a county holds on it.
# `record` is our reading of the Finnish registers. The county must confirm the fields.
INTERVALS = {
    "contact": {
        "name": "First symptoms to first contact",
        "owner": "patient",
        "record": "No register holds the date of the first symptoms. The study asked the patients. "
                  "A pilot asks one question at the first visit.",
    },
    "physician": {
        "name": "First contact to physician appointment",
        "owner": "primary care",
        "record": "Primary care visit records (Avohilmo): the date of the contact and the date of the visit.",
    },
    "referral": {
        "name": "Physician appointment to referral",
        "owner": "primary care",
        "record": "Primary care records: the date of the visit and the date of the referral.",
    },
    "specialist": {
        "name": "Referral to specialist appointment",
        "owner": "hospital",
        "record": "Hospital records (Hilmo): the date the referral arrived and the date of the first visit.",
    },
    "treatment": {
        "name": "Specialist appointment to start of treatment",
        "owner": "hospital",
        "record": "Hospital records: the date of the first visit and the date of the first treatment.",
    },
}


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(PATH.read_text())


def build() -> dict:
    """Each step with its length in days per route and the extra days on the public route."""
    raw = load()
    rows, before = [], {"public": 0, "private": 0}
    for s in raw["steps"]:
        public, private = s["public"] - before["public"], s["private"] - before["private"]
        rows.append({
            "key": s["key"], "label": s["label"], **INTERVALS[s["key"]],
            "public_cumulative": s["public"], "private_cumulative": s["private"],
            "public_days": public, "private_days": private, "extra": public - private,
        })
        before = {"public": s["public"], "private": s["private"]}
    total = {"public": before["public"], "private": before["private"], "extra": before["public"] - before["private"]}
    by_owner = {}
    for owner in ("patient", "primary care", "hospital"):
        part = [r for r in rows if r["owner"] == owner]
        by_owner[owner] = {k: sum(r[k] for r in part) for k in ("public_days", "private_days", "extra")}
    study = raw["study"] | {"compared": sum(g["patients"] for g in raw["groups"].values())}
    return {"source": raw["source"], "note": raw["note"], "groups": raw["groups"], "p_value_total": raw["p_value_total"],
            "study": study, "means": raw["means"], "steps": rows, "total": total, "by_owner": by_owner}


def primary_care_days() -> dict:
    """Days from first contact to referral on each route: the part that a health centre owns."""
    return build()["by_owner"]["primary care"]


# What the tool computes once a county connects its own records. The demo uses public data only.
# The rule for small health centres. The pilot view gives it with the Satakunta example, the printed packet with
# the county's own number of new cases.
SMALL_NUMBERS_RULE = ("So a health centre gets its own median only when its group holds at least 20 patients. Smaller "
                      "centres are pooled into one group, and the county reports every quarter on a rolling 12 months, "
                      "not every month. A median from a handful of patients is not shown.")
PILOT = {
    "title": "County pathway baseline: establish the measurement system before changing care",
    "status": "protocol, not county performance data",
    "unit": "One new cancer pathway; report aggregate results by health centre and route.",
    "cohort": {
        "include": "New patients with an alarm symptom or a cancer referral in the defined pilot cancer pathway.",
        "exclude": "Emergency-only routes, patients who decline investigation, and records without a usable first-contact date; publish every exclusion count.",
    },
    "fields": [
        "First patient contact, physician appointment, referral sent and referral received dates.",
        "First specialist appointment, diagnostic confirmation, MDT decision and treatment-start dates.",
        "Route at first contact, health centre, tumour site, age band and a missing-data flag; no free-text reason field in the pilot extract.",
    ],
    "quality": "Freeze a data dictionary; reconcile a sample against the source records each month; publish completeness for every timestamp before publishing a delay.",
    "privacy": "Patient records stay in the county's own environment, and the county's analyst computes the counts there. "
               "The Atlas receives only aggregates, after the county's legal review, data protection officer review and "
               "governance approval. A cell with fewer than five patients shows no value. The Atlas never receives a patient row.",
    "small_numbers": "Most health centres see few patients with one cancer: about 190 new bowel cancers a year in "
                     "Satakunta, spread over all its health centres. " + SMALL_NUMBERS_RULE,
    "small_numbers_rule": SMALL_NUMBERS_RULE,
    "governance": "The county names a sponsor, a clinical lead, a patient representative, a data controller, a primary-care lead and a hospital lead before extraction. The data protection officer reviews the legal basis and the retention.",
    "decision_rule": "After the baseline and the first quarterly report, review a difference only if completeness is at least 95%, case mix is reviewed and the multidisciplinary governance group agrees an operational change and re-measurement date.",
    # Our proposal for the first 90 days with a county. No county reviewed it.
    "plan_90": [
        ["Days 1 to 30", "Team and permission",
         "The county names a sponsor from its management, a clinical lead and a patient representative. The data "
         "protection officer reviews the purpose, the legal basis and the data-sharing route: aggregates only, cells "
         "under five patients suppressed. The group fixes the cohort and the list of dates."],
        ["Days 31 to 60", "Baseline",
         "The county's analyst takes the dates for last year's patients from its own records. The Atlas receives the "
         "median days of each step per health centre or pooled group of small centres, and the share of dates present."],
        ["Days 61 to 90", "Decision",
         "The group reads the baseline with the patient representative and decides: go, with one roadmap measure for "
         "the slowest step and a date to measure again, or no go."],
    ],
    "go_no_go": "Go only if at least 95% of the dates are present, the slowest step holds at least 20 patients, and "
                "the group agrees one change with an owner. Otherwise no go: fix the records first and measure again "
                "in three months.",
    "output": "For each health centre with at least 20 patients, and for one pooled group of the smaller centres, every "
              "quarter on a rolling 12 months: the median days of each interval and the share of patients within the "
              "county's target time. A cell with fewer than five patients shows no value.",
    "basis": "AstraZeneca answered a team on 14 November 2026 that the limit to public data applies to the hackathon. "
             "In a real setting an integrated solution can have access to the relevant patient data.",
    "basis_source": "az_discord_2026",
    "legal": "The output stays a statistic of a county or a health centre, and it gives no advice about one patient. "
             "The county confirms the legal basis for the use of its own records.",
    "host": "The speaker of the AstraZeneca briefing works in the county of North Ostrobothnia, where the ethics "
            "committee approved the lymphoma study. We did not ask the county yet.",
    "host_source": "az_briefing_2026",
}

# The same patients: a longer wait before the tissue sample went with a worse outcome.
OUTCOME = {
    "text": "In the same group of patients, more than seven weeks from symptoms to the tissue sample went with a "
            "two-year progression-free survival of 74%, against 89% for a shorter wait.",
    "source": "tokola_2025",
}
