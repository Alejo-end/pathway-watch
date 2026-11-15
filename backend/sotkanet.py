"""Loads the cached Sotkanet files: indicator values per county and year, county names and population."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .indicators import EXCLUDED, NATIONAL, POPULATION, SOTKANET
from .sources import STATIC_SOURCES, sotkanet_source

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"


@dataclass
class CountyData:
    """Indicator values keyed as values[indicator][region_code][year]."""

    values: dict[int, dict[str, dict[int, float]]]
    names: dict[str, str]
    population: dict[str, float]
    fetched: dict[int, str]
    titles: dict[int, str]
    # The count behind a value, where Sotkanet gives one, keyed like `values`. For a share it is the numerator.
    counts: dict[int, dict[str, dict[int, int]]] = field(default_factory=dict)

    @property
    def counties(self) -> list[str]:
        return sorted(c for c in self.names if c != NATIONAL and c not in EXCLUDED)

    def series(self, indicator: int, region: str) -> dict[int, float]:
        """Values by year, oldest first. Empty if the region has no data for the indicator."""
        return dict(sorted(self.values[indicator].get(region, {}).items()))

    def sources(self) -> dict[str, dict]:
        out = dict(STATIC_SOURCES)
        for ind, title in self.titles.items():
            out[f"sotkanet:{ind}"] = sotkanet_source(ind, title, self.fetched.get(ind))
        return out


def load(raw: Path = RAW) -> CountyData:
    regions = json.loads((raw / "regions.json").read_text())
    code_of = {r["id"]: r["code"] for r in regions}
    names = {r["code"]: english_name(r["title"]["fi"]) for r in regions}
    values: dict[int, dict[str, dict[int, float]]] = {}
    fetched: dict[int, str] = {}
    titles: dict[int, str] = {}
    population: dict[str, float] = {}
    counts: dict[int, dict[str, dict[int, int]]] = {}
    for ind, (label, _, _) in SOTKANET.items():
        doc = json.loads((raw / f"sotkanet_{ind}.json").read_text())
        table: dict[str, dict[int, float]] = {}
        count: dict[str, dict[int, int]] = {}
        for row in doc["rows"]:
            code = code_of.get(row["region"])
            if code is not None:
                table.setdefault(code, {})[row["year"]] = float(row["value"])
                if row.get("absValue") is not None:
                    count.setdefault(code, {})[row["year"]] = int(row["absValue"])
        if ind == POPULATION:
            population = {c: v[max(v)] for c, v in table.items()}
            continue
        values[ind] = table
        counts[ind] = count
        fetched[ind] = doc.get("fetched", "")
        titles[ind] = doc.get("title") or label
    return CountyData(values, names, population, fetched, titles, counts)


def english_name(fi: str) -> str:
    """The short English name of a county, from its Finnish Sotkanet title. An unknown title is returned as it is."""
    special = {
        "Helsingin kaupunki": "Helsinki",
        "Koko maa": "Finland",
        "Ahvenanmaa": "Åland",
        "Vantaan ja Keravan hyvinvointialue": "Vantaa-Kerava",
        "Itä-Uudenmaan hyvinvointialue": "East Uusimaa",
        "Keski-Uudenmaan hyvinvointialue": "Central Uusimaa",
        "Länsi-Uudenmaan hyvinvointialue": "West Uusimaa",
        "Varsinais-Suomen hyvinvointialue": "Southwest Finland",
        "Satakunnan hyvinvointialue": "Satakunta",
        "Kanta-Hämeen hyvinvointialue": "Kanta-Häme",
        "Pirkanmaan hyvinvointialue": "Pirkanmaa",
        "Päijät-Hämeen hyvinvointialue": "Päijät-Häme",
        "Kymenlaakson hyvinvointialue": "Kymenlaakso",
        "Etelä-Karjalan hyvinvointialue": "South Karelia",
        "Etelä-Savon hyvinvointialue": "South Savo",
        "Pohjois-Savon hyvinvointialue": "North Savo",
        "Pohjois-Karjalan hyvinvointialue": "North Karelia",
        "Keski-Suomen hyvinvointialue": "Central Finland",
        "Etelä-Pohjanmaan hyvinvointialue": "South Ostrobothnia",
        "Pohjanmaan hyvinvointialue": "Ostrobothnia",
        "Keski-Pohjanmaan hyvinvointialue": "Central Ostrobothnia",
        "Pohjois-Pohjanmaan hyvinvointialue": "North Ostrobothnia",
        "Kainuun hyvinvointialue": "Kainuu",
        "Lapin hyvinvointialue": "Lapland",
    }
    return special.get(fi, fi)
