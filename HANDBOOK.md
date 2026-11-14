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
9. Attendance counts the public screening programme only. We do not know how many women in Helsinki have a mammogram elsewhere.
10. Reminders do not always work. In a review of 54 studies, half of the tested ways to raise attendance had a clear effect (Acharya and others, Preventive Medicine 2021). So the action says to measure the effect.
11. The language model only rewords the computed facts. Code picks the roadmap measure. The model does not read the roadmap.

## What is open

1. The mentor interviews: no notes are in the repository. Ask Kaisa Kaitila on Saturday whether the pathway rule is sound to a clinician.
2. A public link for THL guidance 21/2016 in `backend/sources.py`.

## Questions for the mentors

1. Does the Finnish Cancer Registry publish stage at diagnosis per wellbeing services county? Many late stages point to detection. Low survival within one stage points to treatment.
2. Does any register give the wait from referral to treatment per region?
3. How much mammography in Helsinki happens outside the public programme, in occupational or private care?
4. Is a binomial interval from estimated case counts acceptable as a first estimate, or does the registry give real intervals for regional survival?

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
