"""Income and education: what a Finnish register study found, and what the app cannot show.

The app compares counties. The AstraZeneca briefing asks about income, education and the route into
care as well. No public source gives survival, stage or waiting times by income or education per
county, so this module holds national results only, copied by hand from the abstract of the study.
"""

from __future__ import annotations

# Lower against higher education. Each value is the ratio that the abstract gives, with its 95% interval.
ZAI = {
    "source": "zai_2025",
    "patients": 469522,
    "period": "2000 to 2019",
    "rows": [
        {"step": "Incidence", "what": "New cancers per person (rate ratio)", "men": 1.17, "men_ci": [1.16, 1.19], "women": 1.05, "women_ci": [1.04, 1.06]},
        {"step": "Detection", "what": "Odds of stage IV at diagnosis (odds ratio)", "men": 1.10, "men_ci": [1.08, 1.12], "women": 1.15, "women_ci": [1.13, 1.17]},
        {"step": "Outcome", "what": "Death rate after diagnosis (hazard ratio)", "men": 1.13, "men_ci": [1.10, 1.16], "women": 1.14, "women_ci": [1.11, 1.17]},
    ],
    "treatment": "Patients with lower education were also less likely to get surgery, chemotherapy and radiotherapy. "
                 "The pattern by income was similar.",
}

# Income and the first contact, from table 3 of the lymphoma study.
ROUTE = {
    "source": "kuitunen_2026",
    "high_income": {"private": 9, "private_n": 39, "public": 0, "public_n": 48},
    "low_income": {"private": 6, "private_n": 39, "public": 18, "public_n": 48},
}


def build() -> dict:
    def pct(k, n):
        return round(100 * k / n)
    rows = [{**r, "men_more": round((r["men"] - 1) * 100), "women_more": round((r["women"] - 1) * 100)} for r in ZAI["rows"]]
    hi, lo = ROUTE["high_income"], ROUTE["low_income"]
    return {
        "study": {**ZAI, "rows": rows},
        "route": {
            "source": ROUTE["source"],
            "high_income_private": pct(hi["private"], hi["private_n"]), "high_income_public": pct(hi["public"], hi["public_n"]),
            "low_income_private": pct(lo["private"], lo["private_n"]), "low_income_public": pct(lo["public"], lo["public_n"]),
        },
        "missing": "No public source gives survival, stage or waiting times by income or education for a county. "
                   "So this page compares counties only.",
    }
