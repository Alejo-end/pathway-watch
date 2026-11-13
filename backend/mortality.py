"""Cancer mortality per county, age-adjusted by indirect standardization. Goal 3, indicators 1 and 2.

Expected deaths = sum over five-year age groups of (national death rate in the group x county
population in the group). The standardized mortality ratio (SMR) is observed / expected x 100.
SMR 100 means the county has as many deaths as its age structure predicts. Above 100 is worse.
Three years are pooled because yearly counts for single cancers are small.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from .indicators import NATIONAL, WINDOW

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "data" / "raw" / "statfin_mortality.json"

LABELS = {
    "all": "All cancers",
    "lung": "Lung cancer",
    "pancreas": "Pancreatic cancer",
    "liver": "Liver cancer",
    "bowel": "Bowel cancer",
    "breast": "Breast cancer",
    "cervical": "Cervical cancer",
}
GOAL3 = ["all", "lung", "pancreas", "liver"]


@dataclass
class Smr:
    cause: str
    county: str
    years: list[int]
    observed: int
    expected: float
    smr: float
    low: float
    high: float
    deaths_per_year: float
    yearly: dict[int, float]
    direction: str  # worse, better, near
    confidence: str  # high, medium, low


class Mortality:
    def __init__(self, path: Path = FILE):
        self.ok = path.exists()
        if not self.ok:
            return
        d = json.loads(path.read_text())
        self.fetched = d["fetched"]
        self.causes = d["causes"]
        self.cd = d["county_deaths"]
        self.nd = d["national_deaths_by_age"]
        self.pop = d["population_by_age"]
        years = sorted({int(y) for y in self.cd[NATIONAL][self.causes["all"][0]]})
        self.years = years[-WINDOW:]

    def _observed(self, cause: str, county: str, year: int) -> float:
        return sum(self.cd.get(county, {}).get(code, {}).get(str(year)) or 0 for code in self.causes[cause])

    def _expected(self, cause: str, county: str, year: int) -> float:
        y = str(year)
        nat_pop = self.pop[NATIONAL][y]
        own = self.pop.get(county, {}).get(y, {})
        total = 0.0
        for code in self.causes[cause]:
            deaths = self.nd.get(code, {}).get(y, {})
            for age, n in deaths.items():
                if nat_pop.get(age):
                    total += n / nat_pop[age] * own.get(age, 0)
        return total

    def smr(self, cause: str, county: str) -> Smr:
        obs = sum(self._observed(cause, county, y) for y in self.years)
        exp = sum(self._expected(cause, county, y) for y in self.years)
        yearly = {}
        for y in self.years:
            e = self._expected(cause, county, y)
            yearly[y] = round(100 * self._observed(cause, county, y) / e, 1) if e else None
        ratio = 100 * obs / exp if exp else float("nan")
        low, high = byar(obs, exp)
        if low > 100:
            direction, confidence = "worse", "high"
        elif high < 100:
            direction, confidence = "better", "high"
        else:
            direction = "near" if abs(ratio - 100) < 5 else ("worse" if ratio > 100 else "better")
            sign = 1 if direction == "worse" else -1
            same = sum(1 for v in yearly.values() if v is not None and (v - 100) * sign >= 5)
            confidence = "medium" if direction != "near" and same >= WINDOW - 1 else "low"
        return Smr(cause, county, self.years, int(obs), round(exp, 1), round(ratio), round(low), round(high),
                   round(obs / len(self.years), 1), yearly, direction, confidence)


_SHARED: "Mortality | None" = None


def shared() -> "Mortality":
    """One loaded instance for the whole process."""
    global _SHARED
    if _SHARED is None:
        _SHARED = Mortality()
    return _SHARED


def all_years(m: "Mortality", cause: str, county: str) -> dict[int, float]:
    """SMR for every year with data, for the chart. Single years are noisy for one county."""
    years = sorted({int(y) for y in m.cd[NATIONAL][m.causes["all"][0]]})
    out = {}
    for y in years:
        e = m._expected(cause, county, y)
        if e:
            out[y] = round(100 * m._observed(cause, county, y) / e)
    return out


def byar(observed: float, expected: float) -> tuple[float, float]:
    """95% confidence interval of the SMR (Byar's approximation of the exact Poisson interval)."""
    if expected <= 0:
        return float("nan"), float("nan")
    o = observed
    low = 0.0 if o == 0 else o * (1 - 1 / (9 * o) - 1.96 / (3 * math.sqrt(o))) ** 3
    o1 = o + 1
    high = o1 * (1 - 1 / (9 * o1) + 1.96 / (3 * math.sqrt(o1))) ** 3
    return 100 * low / expected, 100 * high / expected
