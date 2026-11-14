"""The Sotkanet indicators the app reads, the cancers it covers and the steps of the care pathway."""

from __future__ import annotations

NATIONAL = "358"  # Sotkanet code for the whole country
EXCLUDED = {"91"}  # Åland is not a wellbeing services county and has gaps in the data
WINDOW = 3  # years pooled for mortality, because yearly death counts for one cancer are small

POPULATION = 127  # population on 31 December

# Indicator ID -> (label, first year to fetch, last year to fetch).
SOTKANET: dict[int, tuple[str, int, int]] = {
    3627: ("Five-year survival, bowel cancer", 2015, 2024),
    3625: ("Five-year survival, breast cancer", 2015, 2024),
    3626: ("Five-year survival, cervical cancer", 2015, 2024),
    6103: ("Bowel screening attendance", 2022, 2024),
    3621: ("Breast screening attendance", 2015, 2024),
    3620: ("Cervical screening attendance", 2015, 2024),
    2371: ("Occupational health physician visits per 1000 aged 15-64", 2020, 2024),
    293: ("Public primary care physician visits per 1000 aged 15-64", 2020, 2024),
    692: ("Kela-reimbursed private physician visits, % of population", 2020, 2024),
    POPULATION: ("Population on 31 December", 2024, 2024),
}

# A cancer with county survival and screening indicators gets the county rule.
# Lung cancer has neither, so its view uses county mortality and national survival.
CANCERS = {
    "bowel": {"label": "Bowel cancer", "survival": 3627, "screening": 6103},
    "breast": {"label": "Breast cancer", "survival": 3625, "screening": 3621},
    "cervical": {"label": "Cervical cancer", "survival": 3626, "screening": 3620},
    "lung": {"label": "Lung cancer", "survival": None, "screening": None},
}


def has_county_survival(cancer: str) -> bool:
    return CANCERS[cancer]["survival"] is not None


STEPS = {
    "detection": "Detection and first contact",
    "referral": "Referral from primary to specialist care",
    "diagnosis": "Diagnosis",
    "treatment": "Start of treatment",
}
