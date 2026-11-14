"""The step timeline of one Finnish lymphoma study, and what a county pilot measures with it.

The study (Kuitunen and others, Cancer Medicine 2026) gives the days from the first symptoms to
each step of the pathway, for patients who started at a public health centre appointment and for
patients who started in private or occupational care. The app copies the cumulative days from
figure 1 and computes the length of each step and the difference between the two routes.

The study covers one lymphoma type and 160 patients. The public group was older. The paper tests
only the whole interval, not each step. So the panel shows where the days add up in this study.
It does not show that the route causes the delay, and it says nothing about other cancers.
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
    return {"source": raw["source"], "note": raw["note"], "groups": raw["groups"], "p_value_total": raw["p_value_total"],
            "steps": rows, "total": total, "by_owner": by_owner}


def primary_care_days() -> dict:
    """Days from first contact to referral on each route: the part that a health centre owns."""
    return build()["by_owner"]["primary care"]


# What the tool computes once a county connects its own records. The demo uses public data only.
PILOT = {
    "output": "For each health centre and each route, every month: the median days of each interval and the share "
              "of patients within the county's target time. A group with fewer than five patients shows no value.",
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
