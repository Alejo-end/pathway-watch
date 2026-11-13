"""The indicators the app uses, and how each one maps to a cancer and a pathway step."""

from __future__ import annotations

from dataclasses import dataclass

NATIONAL = "358"  # Sotkanet code for the whole country
EXCLUDED = {"91"}  # Åland is not a wellbeing services county and has gaps in the data


@dataclass(frozen=True)
class Indicator:
    id: int
    short: str
    cancer: str | None
    kind: str  # survival, screening, context
    step: str | None  # pathway step the indicator is a signal for
    unit: str = "%"


INDICATORS: dict[int, Indicator] = {
    3627: Indicator(3627, "Five-year survival, bowel cancer", "bowel", "survival", "outcome"),
    3625: Indicator(3625, "Five-year survival, breast cancer", "breast", "survival", "outcome"),
    3626: Indicator(3626, "Five-year survival, cervical cancer", "cervical", "survival", "outcome"),
    6103: Indicator(6103, "Bowel screening attendance", "bowel", "screening", "detection"),
    3621: Indicator(3621, "Breast screening attendance", "breast", "screening", "detection"),
    3620: Indicator(3620, "Cervical screening attendance", "cervical", "screening", "detection"),
    5643: Indicator(5643, "Cancer index, age-standardized", None, "context", None, unit="index"),
    5093: Indicator(5093, "Special refunds for cancer medicines, age-standardized", None, "context", None),
}

CANCERS = {
    "bowel": {"label": "Bowel cancer", "survival": 3627, "screening": 6103},
    "breast": {"label": "Breast cancer", "survival": 3625, "screening": 3621},
    "cervical": {"label": "Cervical cancer", "survival": 3626, "screening": 3620},
}

STEPS = {
    "detection": "Detection and first contact",
    "referral": "Referral from primary to specialist care",
    "diagnosis": "Diagnosis",
    "treatment": "Start of treatment",
}
