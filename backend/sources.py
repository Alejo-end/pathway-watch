"""Every number and claim in the app points to one of these sources.

A source has an ID, a title, a link and, where it matters, a page.
"""

from __future__ import annotations

SOTKANET_API = "https://sotkanet.fi/rest/1.1"

STATIC_SOURCES: dict[str, dict] = {
    "strategy": {
        "title": "Kansallinen syöpästrategia 2026–2035, goals page (Goal 3)",
        "url": None,
        "note": "Goal 3: ensure equal and effective cancer care. File from the AstraZeneca challenge resource pack. Add the public link when the team has it.",
    },
    "roadmap": {
        "title": "Kansallisen syöpästrategian toimeenpanon tiekartta 2026–2031",
        "url": None,
        "note": "Implementation roadmap, from the AstraZeneca challenge resource pack. In Finnish. Measure numbers are quoted as written.",
    },
    "thl_21_2016": {
        "title": "THL guidance 21/2016 on monitoring access to cancer care",
        "url": None,
        "note": "Reference for treatment target times in Goal 3, indicator 3.",
    },
    "cancer_registry": {
        "title": "Finnish Cancer Registry, cancer statistics",
        "url": "https://syoparekisteri.fi/tilastot/",
        "note": "Source of the national yearly case counts. The values in data/reference.json are approximate and need a check against the registry.",
    },
    "nordcan": {
        "title": "NORDCAN 2.0, Nordic cancer statistics",
        "url": "https://nordcan.iarc.who.int/en",
        "note": "Benchmark for the Nordic level in Goal 3.",
    },
    "pathway_rule": {
        "title": "Pathway Watch rule, computed by the app",
        "url": None,
        "note": "Low survival with low screening points to detection. Low survival with normal screening points to referral, diagnosis or treatment. A 'most likely' step, not a cause. Code: backend/analysis.py, locate().",
    },
    "statfin_mortality": {
        "title": "Statistics Finland, causes of death (tables 13u5 and 11az) and population by age (table 11re)",
        "url": "https://stat.fi/en/statistics/ksyyt",
        "api": "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/ksyyt/13u5.px",
        "note": "Open PxWeb API. The app age-adjusts deaths by indirect standardization with five-year age groups.",
    },
    "statfi_map": {
        "title": "Statistics Finland, wellbeing services county boundaries 2024",
        "url": "https://geo.stat.fi/geoserver/tilastointialueet/wfs",
        "note": "Map layer hyvinvointialue4500k_2024.",
    },
}


def sotkanet_source(indicator: int, title: str, fetched: str | None) -> dict:
    return {
        "title": f"THL Sotkanet, indicator {indicator}: {title}",
        "url": f"https://sotkanet.fi/sotkanet/en/taulukko/?indicator={indicator}",
        "api": f"{SOTKANET_API}/json?indicator={indicator}&genders=total",
        "note": f"Open REST API, fetched {fetched}." if fetched else "Open REST API.",
    }
