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
        "title": "Sillanpää M, Pylkkänen L, Häkkinen P. Hoitoonpääsyn seuranta syövän hoidossa: määrittelyt ja ohjeistus. THL Ohjaus 21/2016",
        "url": "https://urn.fi/URN:ISBN:978-952-302-782-4",
        "note": "Reference for treatment target times in Goal 3, indicator 3.",
    },
    "cancer_registry": {
        "title": "Finnish Cancer Registry, cancer statistics",
        "url": "https://syoparekisteri.fi/tilastot/",
        "note": "Holds case counts and survival per region. Stage at diagnosis (2020-2024) is published for the whole country only: with a county selected, the stage option of the statistics application disappears. Nationally, 11115 of 20421 bowel cancers in 2020-2024 have unknown stage. The app does not read this application: it has no open API that we found.",
    },
    "fcr_clinical": {
        "title": "Finnish Cancer Registry, clinical notifications by wellbeing services county",
        "url": "https://tilastot.syoparekisteri.fi/syopalaatu/",
        "note": "Share of new cancers for which the treating unit sent its clinical notification, the summary that the registry records stage from. Bowel, breast and lung cancer, 2020 to 2024, read from the chart data of the application on 2026-11-14 into data/raw/fcr_clinical_notifications.json. Licence CC BY 4.0. A low share is a fact about reporting, not about the quality of care. Code: backend/registry.py.",
    },
    "nordcan": {
        "title": "NORDCAN 2.0, Nordic cancer statistics",
        "url": "https://nordcan.iarc.who.int/en",
        "note": "Benchmark for the Nordic level in Goal 3.",
    },
    "pathway_rule": {
        "title": "Cancer Care Atlas rule, computed by the app",
        "url": None,
        "note": "Low survival with low attendance in the public screening programme raises a question about detection. Low survival with normal attendance raises a question about referral, diagnosis or treatment. For bowel cancer the rule does not use attendance, because national screening started in 2022, after most of the diagnoses behind the survival value. The rule compares counties, not patients, so the result is a question to investigate, not a cause. Code: backend/analysis.py, locate().",
    },
    "survival_interval": {
        "title": "Rough 95% interval of a county survival gap, computed by the app",
        "url": None,
        "note": "Our estimate, not a published interval. Standard error of the county value = sqrt(p(1-p)/n), with n = estimated new cases per year times the ten diagnosis years behind one Sotkanet value. The rounding of both published values to whole percent is added. The true interval is wider: relative survival varies more than a plain share, the follow-up uses part of the ten years, and the county case count is an estimate. The estimate splits the national count by the county's age structure, with the age pattern of deaths as a stand-in for the age pattern of new cases. The app compares 22 counties with Finland, so about one such interval excludes zero by chance. The page also gives the interval with the stricter limit for 22 comparisons (Bonferroni). Code: backend/analysis.py, rough_interval().",
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
        "title": "Cancer Care Atlas proposal for a first local step, written by the team",
        "url": None,
        "note": "Our proposal for what one health centre or one county can start next month. It is not text of the roadmap. No county reviewed it. Code: backend/recommend.py, LOCAL_STEPS.",
    },
    "radiotherapy_pilot": {
        "title": "Cancer Care Atlas radiotherapy equity baseline, written by the team",
        "url": None,
        "note": "A proposed aggregate measurement protocol. It is not a clinical guideline, a treatment recommendation or a county performance dataset. No radiation oncology department, data controller or medical physics team reviewed it. Code: backend/radiotherapy.py.",
    },
    "fcr_screening": {
        "title": "Finnish Cancer Registry, cancer screening pages: who is invited to each national programme",
        "url": "https://cancerregistry.fi/screening/",
        "note": "Read on 14 November 2026. Breast: women aged 50 to 69, every two years, mammography. Cervical: women aged 30 to 65, every five years, and some municipalities also invite women aged 25. Bowel: a stool test (FIT) by mail every two years, all people aged 56 to 74 in 2031. The bowel page named the ages 60 to 70 as the current group.",
    },
    "virtanen_2011": {
        "title": "Virtanen A, Nieminen P, Luostarinen T, Anttila A. Self-sample HPV tests as an intervention for nonattendees of cervical cancer screening in Finland: a randomized trial. Cancer Epidemiology, Biomarkers & Prevention 2011;20(9):1960-9",
        "url": "https://doi.org/10.1158/1055-9965.EPI-11-0307",
        "note": "Randomized trial in Espoo, found through PubMed (PMID 21752985). Women who did not attend after the first invitation got a self-sampling kit (2,397 women) or a reminder letter (6,302 women). Total attendance rose from 65% to 76% with the kit and from 65% to 74% with the letter. The letter and then the kit raised it from 63% to 78%. One municipality and cervical screening only.",
    },
    "virtanen_2010": {
        "title": "Virtanen A, Anttila A, Luostarinen T, Nieminen P. Self-sampling versus reminder letter: effects on cervical cancer screening attendance and coverage in Finland. International Journal of Cancer 2011;128(11):2681-7",
        "url": "https://doi.org/10.1002/ijc.25581",
        "note": "Randomized study in Espoo in 2008, found through PubMed (PMID 20669228). Of the women who took part after a kit or a reminder letter, about 20% had their last Pap test five or more years before. For 70% to 75% the second contact only gave a test that they did not need yet. The women reported their earlier tests themselves.",
    },
    "jantti_2021": {
        "title": "Jäntti M, Heinävaara S, Malila N, Sarkeala T. Sociodemographic features and patterns of non-participation in colorectal cancer screening in Finland. European Journal of Public Health 2021;31(4):890-894",
        "url": "https://doi.org/10.1093/eurpub/ckab074",
        "note": "Register study of 233,211 people invited to the earlier Finnish bowel screening programme in 2004 to 2016, found through PubMed (PMID 34347069). 31.6% did not take part: 38.8% of men and 24.6% of women. About 80% of the people who did not take part in the first round also did not take part in the second. That programme used another stool test than the programme of 2022.",
    },
    "campaign_rule": {
        "title": "Cancer Care Atlas proposal for a screening campaign, written by the team",
        "url": None,
        "note": "Our proposal for when a county runs a reminder campaign, who is in it and what the county does. The rules use the fields that a screening programme holds to send its invitations. No county and no data protection officer reviewed it. The size of the campaign is our estimate: Sotkanet gives the people who attended and their share of the invited. Code: backend/campaign.py.",
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
    "tanderup_2016": {
        "title": "Tanderup K, Fokdal LU, Sturdza A, Haie-Meder C, Mazeron R, van Limbergen E, and others. Effect of tumor dose, volume and overall treatment time on local control after radiochemotherapy including MRI guided brachytherapy of locally advanced cervical cancer. Radiotherapy and Oncology 2016;120:441-446",
        "url": "https://doi.org/10.1016/j.radonc.2016.05.014",
        "note": "Multicentre series (retroEMBRACE), found through PubMed (PMID 27350396). 488 patients. Longer overall treatment time went with worse local control (hazard ratio 1.023 per day). About 5 Gy more dose was needed to make up for one extra week. Not Finnish data.",
    },
    "thl_eshjono": {
        "title": "THL, access to specialised health care: patients waiting for treatment by specialty and wellbeing services county (Sampo cube eshjono/jonotilanne)",
        "url": "https://sampo.thl.fi/pivot/prod/fi/eshjono/jonotilanne/fact_eshjono_jonotilanne",
        "note": "Open THL data, downloaded with data/fetch_thl_queues.py on 2026-11-14 for the six month-ends from April to September 2026. Non-urgent queues only: a patient with a cancer referral is often treated as urgent and is not in them. THL reports by provider, so HUS stands for the four Uusimaa counties and Helsinki. Counties code sub-specialties differently, so a county without a value may book the same work under another specialty.",
    },
    "rt_units": {
        "title": "Radiotherapy units in Finland and the unit that serves each county, compiled by Cancer Care Atlas from each unit's own service page",
        "url": "https://www.suomi.fi/palvelut/palvelupiste/oysin-sadehoidon-yksikko-pohjois-pohjanmaan-hyvinvointialue/6ef3eba4-7471-4c77-8f6d-578b809dfa37",
        "note": "Compiled by hand on 2026-11-14. Each unit, and each county served from another county, links to its own source in data/radiotherapy_units.json. Units: HUS (all of Uusimaa), Tyks, Satasairaala, Vaasa, Tays, Lahti, Kotka, Lappeenranta, Jyväskylä, Kuopio, Joensuu and Oulu (the only unit in Northern Finland, so also Kainuu and Lapland). Served from another county: Kanta-Häme by Tays, South Ostrobothnia mainly by Vaasa, South Savo by Kuopio, Jyväskylä or Lappeenranta, Central Ostrobothnia mainly by Oulu and Vaasa. The distance is a straight line to the nearest of the county's units, not a travel time.",
    },
    "fast_forward": {
        "title": "Murray Brunt A, Haviland JS, Wheatley DA, and others. Hypofractionated breast radiotherapy for 1 week versus 3 weeks (FAST-Forward): 5-year efficacy and late normal tissue effects results from a multicentre, non-inferiority, randomised, phase 3 trial. Lancet 2020;395:1613-1626",
        "url": "https://doi.org/10.1016/S0140-6736(20)30932-6",
        "note": "Randomised trial, found through PubMed (PMID 32580883). 4096 patients after surgery for early breast cancer. 26 Gy in five fractions over one week was non-inferior to 40 Gy in 15 fractions over three weeks for local relapse at five years, with similar normal tissue effects. UK data.",
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
