# Handbook: Pathway Watch

This handbook explains the AstraZeneca entry to anyone on the team. The build brief is `../PATHWAY_PLAN.md`.

## What it is

Pathway Watch is for a decision-maker in a Finnish wellbeing services county. In under two minutes it shows three things. First, where cancer patients in the county are behind the rest of Finland. Second, which step of the care pathway to ask questions about. Third, which measure of the national roadmap to act on first. Every number links to its source.

The design rule: code computes every number. If a number in a sentence is not in the facts that the sentence cites, the app removes the sentence.

## The map

![Two maps of Finnish counties in 2024](../docs/handbook/pathway-maps.svg)

| Finding | Value | Years |
|---|---|---|
| Helsinki has the lowest attendance in the public breast screening programme | 74.3% in 2024, Finland 81.6% | Every published year, 2015 to 2024 |
| The three lowest counties for that attendance are all in Uusimaa | Helsinki, West Uusimaa, Vantaa-Kerava in 2024 | Every published year, 2015 to 2024 |
| Satakunta has the lowest bowel cancer survival | 57% to 61%, Finland 66% to 67% | 2019 to 2023 |
| Satakunta is 4 points below Finland in bowel cancer survival | 64%, Finland 68%. Our rough 95% interval: 6.5 to 1.5 points below | 2024 |
| Päijät-Häme has the lowest bowel cancer survival | 63%, Finland 68%. Our rough 95% interval: 7.6 to 2.4 points below | 2024 only. It is below Finland in 4 of 6 years |

The attendance figure counts the public programme only. A mammogram in occupational or private care is not in it. A Finnish Cancer Registry study (Fuhrmann and others, Acta Oncologica 2024) counted such mammograms for the whole country. Upper-level employees had them about twice as often as manual workers. So low attendance in Helsinki does not show how many women have no mammogram at all.

The lowest of 22 counties tends to look less extreme the next time it is measured. This effect is called regression to the mean. So the interval matters more than the rank.

## Why the app asks questions and does not name causes

![Satakunta against Finland, 2019 to 2024](../docs/handbook/pathway-satakunta.svg)

Each survival value covers patients diagnosed in that year and the nine years before. Two neighboring years share most of their patients. So the app does not average years, and it does not call agreement between years "confidence".

The evidence for a survival gap is a rough 95% interval that the app computes from patient counts. Example: Satakunta has about 153 new bowel cancer cases per year, so one survival value covers about 1,530 patients. The standard error of the gap is then 1.3 points. The gap of 4 points has an interval from 6.5 to 1.5 points below Finland, so it excludes zero.

This interval is our estimate, and the true interval is wider. Sotkanet publishes no interval. Relative survival varies more than a plain share. The county case count is the national count split by population, so it ignores the age structure. The page says all of this next to the number. The count "below in 6 of 6 years" stays on the page as a description only.

![The care pathway and its public data](../docs/handbook/pathway-care-path.svg)

The pathway rule compares counties, not patients. For breast and cervical cancer, low survival with low attendance in the public screening programme raises a question about detection. Low survival with normal attendance raises a question about the later steps. Public data cannot tell the later steps apart, and the app says so.

Bowel cancer is different. National bowel screening started in 2022. Each survival value covers ten years of diagnoses, so most of those patients were diagnosed before the programme. Attendance cannot explain their survival. For a bowel cancer survival gap, the app says that the data cannot tell which step the gap comes from. Low attendance in the new programme is shown as an early warning of its own.

## The waits before treatment, and the intended use

### What the sources say about waits

Before treatment, a patient needs tests, for example a colonoscopy, a tissue sample and a scan. The national roadmap counts the whole wait from referral to treatment, not the wait for each test.

1. The wait matters. In a review of 34 studies, each four-week delay of cancer surgery went with a 6% to 8% higher risk of death ([Hanna and others, BMJ 2020](https://doi.org/10.1136/bmj.m4087)). For radiotherapy the result differed by cancer: 9% for head and neck cancer, and no clear effect after breast-conserving surgery.
2. In a survey of Nordic lung cancer professionals, Finland had the lowest access to CT from primary care and the longest waits in primary care ([Khalife and others, Acta Oncologica 2025](https://doi.org/10.2340/1651-226X.2025.42778)). The survey holds the views of professionals, not measured waits. One author works for the drug company MSD. The app cites it on the lung cancer view only.
3. Between 47% and 53% of new cancer patients need radiotherapy at least once ([Borras and others, Radiotherapy and Oncology 2015](https://doi.org/10.1016/j.radonc.2015.04.018)). The app has no treatment data.

We found no public source that gives the wait for any of these tests per county. So the app lists these waits as missing data. We do not claim that one test is the slow step in any county.

### Intended use

Pathway Watch answers a planner's question about a county. It gives no advice about one patient. The EU guidance on medical software, [MDCG 2019-11 revision 1 of June 2025](https://health.ec.europa.eu/document/download/b45335c5-1679-4c71-a91c-fc7a4d37f12b_en), says in decision step 4 that software "intended only to aggregate population data" is not for the benefit of individual patients. We read this to mean that Pathway Watch is not a medical device. This is our reading. No regulatory expert reviewed it, so the pitch does not claim it.

Patient-level register data needs a permit from Findata, the Finnish permit authority for health data.

## How a number reaches the page

![From the open source to the page](../docs/handbook/pathway-flow.svg)

## Run it

Run every command from `pathway-watch/`. You need `uv`.

1. Start the app: `uv run uvicorn backend.app:app --port 8010`.
2. Open `http://localhost:8010`.
3. Run the tests: `uv run pytest`. 56 tests pass.
4. To refresh the open data, run `uv run python data/fetch_sotkanet.py` and `uv run python data/fetch_statfin.py`. The cached data is in the repository, so the demo needs no network.

Set `PATHWAY_LLM=0` for the demo. Then the fixed template writes the three sentences. The language model path is not tested with a real key.

## Demo in two minutes

1. "You lead a wellbeing services county. Where do your cancer patients fall behind?"
2. Pick bowel cancer in Satakunta. Read the three sentences.
3. Show the chart: 4 points below Finland in 2024, with a rough interval of 6.5 to 1.5 points below.
4. Say that the data cannot tell which step. Show the first action: standardized referral criteria, roadmap measure 2.5.2. It acts on patients who come with symptoms.
5. Switch to breast cancer in Helsinki. Survival is near Finland. Attendance in the public programme is lowest for ten years.
6. Show the first action there (measure 2.4.5): find who has no mammogram at all, then remind those women. The cause of the low attendance is not known.
7. Show the Sweden panel and the "data that is missing" list. End on the follow-up project with a county.

## How the judges score

| Criterion | Weight | Where the app answers it |
|---|---|---|
| Actionability | 30% | The first action card: the roadmap measure, who acts, the first step and how success is measured |
| Insight | 25% | The gap, the pathway picture and the question to investigate |
| Data quality and transparency | 20% | A source for every number, the limits below, and the list of missing data |
| Execution | 15% | A live demo with cached data, so it needs no network |
| Clarity | 10% | Three sentences at the top of the page |

## Limits to say out loud

1. Survival describes care given up to ten years ago. The slider is an illustration of the size of the gap, not a forecast.
2. Sotkanet publishes no confidence interval. The interval on the page is our rough estimate, and the true interval is wider. "Below in 6 of 6 years" is a description, not a test.
3. Deaths are compared with a 95% interval. With 22 counties, about one county per cancer crosses that limit by chance.
4. "Diagnosis took twice as long through public care" is one unpublished study of lymphoma patients, cited in the roadmap on page 11.
5. The public share of doctor visits is a stand-in for channel use. No public source gives occupational health coverage per county.
6. The NORDCAN values and Sweden's waiting times were copied by hand from the sources. A test checks that Sweden's regions add up to the national value.
7. Case counts per county are the national count split by population. The page marks them as estimates.
8. For bowel cancer, the app cannot tell detection from the later steps. Stage at diagnosis per county tells them apart, and no public source gives it.
9. Attendance counts the public screening programme only. We do not know how many women in Helsinki have a mammogram elsewhere. Tests outside the programme are common for cervical cancer too. In 2010 to 2014, 86.0% of women had a cervical test within or outside the programme ([Pankakoski and others, Preventive Medicine 2020](https://doi.org/10.1016/j.ypmed.2020.106219)).
10. Reminders do not always work. In a review of 54 studies, half of the tested ways to raise attendance had a clear effect (Acharya and others, Preventive Medicine 2021). So the action says to measure the effect.
11. The language model only rewords the computed facts. Code picks the roadmap measure. The model does not read the roadmap.
12. No county data exists on the wait for each test before treatment. The one survey we cite is about lung cancer and holds views, not measured waits.
13. "Not a medical device" is our reading of the EU guidance MDCG 2019-11. No regulatory expert reviewed it, and the pitch does not claim it.
14. "Bowel cancer" joins colon cancer and rectal cancer. Their care differs: rectal cancer often gets radiotherapy before surgery, and colon cancer does not. The Sotkanet value cannot tell them apart.
15. Screening finds a cancer earlier. Five-year survival then rises with no longer life for any patient. This effect is called lead-time bias. A county with more screening shows better survival for this reason alone. Cancer deaths against the expected number do not have this bias, and the app shows them.
16. Relative survival removes the deaths that people of the same age and sex have anyway. It does not adjust for stage or for other illness. So a gap can come from sicker patients and not from care.
17. Stage per county helps, with one caution. A county that scans more finds more spread and moves patients to a higher stage. Survival within each stage then rises with no change for any patient ([Feinstein and others, New England Journal of Medicine 1985](https://doi.org/10.1056/NEJM198506203122504)).
18. The app treats treatment as one step. It has no data on surgery, radiotherapy or medicines per county.

## What is open

1. The mentor interviews: no notes are in the repository. Ask Kaisa Kaitila on Saturday whether the pathway rule is sound to a clinician.
2. A public link for THL guidance 21/2016 in `backend/sources.py`.

## Questions for the mentors

1. Does the Finnish Cancer Registry publish stage at diagnosis per wellbeing services county? Many late stages point to detection. Low survival within one stage points to treatment.
2. Does any register give the wait from referral to treatment per region?
3. How much mammography in Helsinki happens outside the public programme, in occupational or private care?
4. Is a binomial interval from estimated case counts acceptable as a first estimate, or does the registry give real intervals for regional survival?
5. Which test before treatment has the longest queue in a county: colonoscopy, scan, pathology or the team meeting? Does any register record these waits?
6. Is our reading right that a planning tool on county statistics is not a medical device?
7. Does the Cancer Registry give survival for colon cancer and rectal cancer apart, per county?
8. Does any register record the time from the treatment decision to the first radiotherapy session?

## Where things are

| Path | Content |
|---|---|
| `backend/analysis.py` | The gap, the rough interval, the pathway rule, the simulation |
| `backend/mortality.py` | Deaths against the number expected from the age structure |
| `backend/facts.py`, `backend/analyst.py` | The facts, the three sentences and the sentence check |
| `backend/recommend.py` | Roadmap measures, with level, first step and measure of success |
| `backend/priorities.py` | Where to start in Finland |
| `backend/sources.py` | Every source the page cites |
| `data/raw/`, `data/nordcan.json`, `data/svf_sweden.json` | The cached data |
| `web/index.html` | The page |
