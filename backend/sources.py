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
    "khalife_2025": {
        "title": "Khalife G, Waris J, Bødtger U, Isaksson J, Neumann K, Harðardóttir H, Andersén H, Jekunen A, Lovén M, Vasankari T, Nurmi-Rantala S, Torkki P. Comparative study of lung cancer care and survival outcomes across the Nordic countries. Acta Oncologica 2025;64:734-741",
        "url": "https://doi.org/10.2340/1651-226X.2025.42778",
        "note": "Survey of health care professionals in the Nordic countries, found through PubMed (PMID 40468524). Finland had the lowest access to CT from primary care, the longest waiting times in primary care and no national tracking of outcomes. The answers are the views of professionals, not measured waiting times. One author works for MSD Finland.",
    },
    "kuitunen_2026": {
        "title": "Kuitunen J, Marin K, Tokola S, Pollari M, Jyrkkiö S, Suominen M, Partanen A, Vuolukka K, Sunela K, Rönkä A, Aromaa-Häyhä A, Klaavuniemi T, Hakalahti A, Kuusisto MEL, Kuitunen H, Kuittinen O. Socioeconomic Status and Access to Treatment in Diffuse Large B-Cell Lymphoma. Cancer Medicine 2026;15(5):e71920",
        "url": "https://doi.org/10.1002/cam4.71920",
        "note": "Prospective study in seven Finnish hospitals, 2014 to 2020, found through PubMed (PMID 42108510). It is the lymphoma study that the roadmap cites as unpublished on page 11, and AstraZeneca's challenge briefing of 13 November 2026 showed it. 160 patients with one lymphoma type. Median time from first symptoms to treatment: 127 days (mean 201) for 48 patients who started at a public health centre appointment, 76 days (mean 126) for 39 patients who started in private or occupational health care (p = 0.027). The public group was older: 44% over 70 years against 8%. The patients reported the date of the first symptoms themselves. The interval includes the time before the first contact.",
    },
    "tokola_2025": {
        "title": "Tokola S, Marin K, Kuusisto MEL, Kuitunen H, Pollari M, Jyrkkiö S, and others. Prolonged Time From Symptoms to Diagnosis Is Associated With an Inferior Progression-Free Survival in Diffuse Large B-Cell Lymphoma. Cancer Medicine 2025;14(22):e71409",
        "url": "https://doi.org/10.1002/cam4.71409",
        "note": "The same 160 patients as the 2026 study, found through PubMed (PMID 41275414). More than seven weeks from the first symptoms to the diagnostic biopsy went with a two-year progression-free survival of 74%, against 89% (p = 0.012). The whole interval from symptoms to treatment showed no such link.",
    },
    "zai_2025": {
        "title": "Zai X, Li P, Dei Bardi L, Korhonen K, Moretti M, Myrskylä M, Martikainen P. Disparities in cancer incidence, stage at diagnosis, treatment and mortality across socioeconomic groups in Finland: a register-based population study. BMJ Public Health 2025;3(2):e002829",
        "url": "https://doi.org/10.1136/bmjph-2025-002829",
        "note": "Register study of 469,522 Finnish patients diagnosed in 2000 to 2019, found through PubMed (PMID 41141305). The values are national and come from the abstract. The study gives no county values.",
    },
    "az_briefing_2026": {
        "title": "Kuitunen H. Equitable Cancer Care: How Can We Ensure It in Finland. AstraZeneca challenge briefing, Junction 2026, 13 November 2026",
        "url": None,
        "note": "Slides that AstraZeneca gave to the teams. The speaker is an oncologist at Oulu University Hospital, in the county of North Ostrobothnia. File in pathway-watch/docs/.",
    },
    "az_discord_2026": {
        "title": "AstraZeneca answer to a team question, Junction 2026 challenge channel, 14 November 2026",
        "url": None,
        "note": "Laura Aaltonen of AstraZeneca, passed on by the organizers: the limit to public data applies to the hackathon. In a real setting an integrated solution can have access to the relevant patient data. PATHWAY_PLAN.md holds the full answer.",
    },
    "local_step": {
        "title": "Pathway Watch proposal for a first local step, written by the team",
        "url": None,
        "note": "Our proposal for what one health centre or one county can start next month. It is not text of the roadmap. No county reviewed it. Code: backend/recommend.py, LOCAL_STEPS.",
    },
    "hanna_2020": {
        "title": "Hanna TP, King WD, Thibodeau S, Jalink M, Paulin GA, Harvey-Jones E, O'Sullivan DE, Booth CM, Sullivan R, Aggarwal A. Mortality due to cancer treatment delay: systematic review and meta-analysis. BMJ 2020;371:m4087",
        "url": "https://doi.org/10.1136/bmj.m4087",
        "note": "Systematic review, found through PubMed (PMID 33148535). 34 studies, seven cancers. For each four-week delay of surgery the risk of death was 6% to 8% higher (hazard ratio 1.06 to 1.08). For radiotherapy the result differed by indication: 1.09 for head and neck cancer, and no clear effect after breast-conserving surgery (0.98, interval 0.88 to 1.09). The studies are from many countries, none from this app's data.",
    },
    "borras_2015": {
        "title": "Borras JM, Lievens Y, Dunscombe P, Coffey M, Malicki J, Corral J, Gasparotto C, Defourny N, Barton M, Verhoeven R, van Eycken L, Primic-Zakelj M, Trojanowski M, Strojan P, Grau C. The optimal utilization proportion of external beam radiotherapy in European countries: An ESTRO-HERO analysis. Radiotherapy and Oncology 2015;116:38-44",
        "url": "https://doi.org/10.1016/j.radonc.2015.04.018",
        "note": "Estimate for European countries, found through PubMed (PMID 25981052). Between 47.0% and 53.2% of new cancer patients need radiotherapy at least once. In most of the 24 countries with data, actual use was lower. The abstract gives no value for Finland.",
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
