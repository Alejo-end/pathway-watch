"""Every number and claim in the app points to one of these sources.

A source has an ID, a title, a link and, where it matters, a page.
"""

from __future__ import annotations

SOTKANET_API = "https://sotkanet.fi/rest/1.1"

STATIC_SOURCES: dict[str, dict] = {
    "strategy": {
        "title": "Kansallinen syöpästrategia 2026–2035, goals page (Goal 3)",
        "url": "https://files.hackjunction.app/resources/Kansallinen_syopastrategia_2026_2035_FINAL.pdf",
        "note": "Strategic goals and indicators on page 5. Goal 3: ensure equal and effective cancer care. Goal 2 includes 80% screening attendance in every county. File Kansallinen_syopastrategia_2026_2035_FINAL.pdf from the AstraZeneca resource pack.",
    },
    "roadmap": {
        "title": "Kansallisen syöpästrategian toimeenpanon tiekartta 2026–2031",
        "url": "https://files.hackjunction.app/resources/Kansallinen_syopastrategia_toimeenpanon_tiekartta_2026_2031.pdf",
        "note": "Implementation roadmap, file Kansallinen_syopastrategia_toimeenpanon_tiekartta_2026_2031.pdf from the AstraZeneca resource pack. In Finnish. Measure numbers and pages are quoted as written.",
    },
    "thl_21_2016": {
        "title": "THL guidance 21/2016 on monitoring access to cancer care",
        "url": None,
        "note": "Reference for treatment target times in Goal 3, indicator 3.",
    },
    "cancer_registry": {
        "title": "Finnish Cancer Registry, cancer statistics",
        "url": "https://syoparekisteri.fi/tilastot/",
        "note": "Holds case counts, stage and survival per region. The app does not read it: its statistics application has no open API that we found.",
    },
    "nordcan": {
        "title": "NORDCAN 2.0, Nordic cancer statistics",
        "url": "https://nordcan.iarc.who.int/en",
        "note": "Benchmark for the Nordic level in Goal 3.",
    },
    "pathway_rule": {
        "title": "Pathway Watch rule, computed by the app",
        "url": None,
        "note": "Low survival with low attendance in the public screening programme raises a question about detection. Low survival with normal attendance raises a question about referral, diagnosis or treatment. For bowel cancer the rule does not use attendance, because national screening started in 2022, after most of the diagnoses behind the survival value. The rule compares counties, not patients, so the result is a question to investigate, not a cause. Code: backend/analysis.py, locate().",
    },
    "survival_interval": {
        "title": "Rough 95% interval of a county survival gap, computed by the app",
        "url": None,
        "note": "Our estimate, not a published interval. Standard error of the county value = sqrt(p(1-p)/n), with n = estimated new cases per year times the ten diagnosis years behind one Sotkanet value. The rounding of both published values to whole percent is added. The true interval is wider: relative survival varies more than a plain share, the follow-up uses part of the ten years, and the county case count ignores the age structure. Code: backend/analysis.py, rough_interval().",
    },
    "fuhrmann_2024": {
        "title": "Fuhrmann J, Heinävaara S, Sarkeala T, Lehtinen M, Pankakoski M. Coverage of mammography imaging in and outside an organized breast cancer screening program: variation by age and sociodemographic groups. Acta Oncologica 2024;63:833-840",
        "url": "https://doi.org/10.2340/1651-226X.2024.40830",
        "note": "Finnish Cancer Registry study, found through PubMed (PMID 39473178). It links mammograms and ultrasounds made outside the programme to the programme data for Finland. The numbers are national, not per county.",
    },
    "acharya_2021": {
        "title": "Acharya A, Sounderajah V, Ashrafian H, Darzi A, Judah G. A systematic review of interventions to improve breast cancer screening health behaviours. Preventive Medicine 2021;153:106828",
        "url": "https://doi.org/10.1016/j.ypmed.2021.106828",
        "note": "Systematic review, found through PubMed (PMID 34624390). 54 studies with 80 interventions to raise attendance. Half of the interventions reported a significant effect.",
    },
    "statfin_mortality": {
        "title": "Statistics Finland, causes of death (tables 13u5 and 11az) and population by age (table 11re)",
        "url": "https://stat.fi/en/statistics/ksyyt",
        "api": "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/ksyyt/13u5.px",
        "note": "Open PxWeb API. The app age-adjusts deaths by indirect standardization with five-year age groups.",
    },
    "rcc_svf_2025": {
        "title": "Regionala cancercentrum i samverkan, Standardiserade vårdförlopp: annual report 2025, appendix 1 (2026-03-27)",
        "url": "https://cancercentrum.se/download/18.7c07b08019d24db18e31c22a/1774867469204/%C3%85rsapport%20%C3%B6verenskommelse%202025%20J%C3%A4mlik%20och%20effektiv%20cancerv%C3%A5rd%20med%20kortare%20v%C3%A4ntetider_bilaga%201%20SVF.pdf",
        "note": "Sweden's lead-time results per region (figure 5, page 12) and per pathway (figure 6, page 13). Data from the national waiting-time database at SKR.",
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
