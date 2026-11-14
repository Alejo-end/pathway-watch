# Handbook: Pathway Watch

This handbook explains the AstraZeneca entry to anyone on the team. The build brief is `../PATHWAY_PLAN.md`.

## What it is

Pathway Watch is for a decision-maker in a Finnish wellbeing services county. In under two minutes it shows three things. First, where cancer patients in the county are behind the rest of Finland. Second, which step of the care pathway to ask questions about. Third, which measure of the national roadmap to act on first. Every number links to its source.

The design rule: code computes every number. If a number in a sentence is not in the facts that the sentence cites, the app removes the sentence.

## The map

![Two maps of Finnish counties in 2024](../docs/handbook/pathway-maps.svg)

| Finding | Value | Years |
|---|---|---|
| Helsinki has the lowest breast screening attendance of all counties | 74.3% in 2024, Finland 81.6% | Every published year, 2015 to 2024 |
| The three lowest counties for breast screening are all in Uusimaa | Helsinki, West Uusimaa, Vantaa-Kerava in 2024 | Every published year, 2015 to 2024 |
| Satakunta has the lowest bowel cancer survival | 57% to 61%, Finland 66% to 67% | 2019 to 2023 |
| Päijät-Häme has the lowest bowel cancer survival | 63%, Finland 68% | 2024 only. It is below Finland in 4 of 6 years |

## Why the app asks questions and does not name causes

![Satakunta against Finland, 2019 to 2024](../docs/handbook/pathway-satakunta.svg)

Each survival value covers patients diagnosed in that year and the nine years before. Two neighboring years share most of their patients. So the app does not average years, and it does not call agreement between years "confidence". It shows the gap in the latest year and says in how many published years the county was on the same side.

![The care pathway and its public data](../docs/handbook/pathway-care-path.svg)

The pathway rule compares counties, not patients. Low survival with low screening raises a question about detection. Low survival with normal screening raises a question about the later steps. Public data cannot tell the later steps apart, and the app says so.

## How a number reaches the page

![From the open source to the page](../docs/handbook/pathway-flow.svg)

## Run it

Run every command from `pathway-watch/`. You need `uv`.

1. Start the app: `uv run uvicorn backend.app:app --port 8010`.
2. Open `http://localhost:8010`.
3. Run the tests: `uv run pytest`. 49 tests pass.
4. To refresh the open data, run `uv run python data/fetch_sotkanet.py` and `uv run python data/fetch_statfin.py`. The cached data is in the repository, so the demo needs no network.

Set `PATHWAY_LLM=0` for the demo. Then the fixed template writes the three sentences. The language model path is not tested with a real key.

## Demo in two minutes

1. "You lead a wellbeing services county. Where do your cancer patients fall behind?"
2. Pick bowel cancer in Satakunta. Read the three sentences.
3. Show the chart: below Finland in 6 of 6 published years.
4. Show the first action: standardized referral criteria, roadmap measure 2.5.2.
5. Switch to breast cancer in Helsinki. Survival is near Finland, screening is lowest for ten years. The first action is to find who does not attend (measure 2.4.5). The cause is not known.
6. Show the Sweden panel and the "data that is missing" list. End on the follow-up project with a county.

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
2. Sotkanet publishes no confidence interval. "Below in 6 of 6 years" is a description, not a test.
3. Deaths are compared with a 95% interval. With 22 counties, about one county per cancer crosses that limit by chance.
4. "Diagnosis took twice as long through public care" is one unpublished study of lymphoma patients, cited in the roadmap on page 11.
5. The public share of doctor visits is a stand-in for channel use. No public source gives occupational health coverage per county.
6. The NORDCAN values and Sweden's waiting times were copied by hand from the sources. A test checks that Sweden's regions add up to the national value.
7. Case counts per county are the national count split by population. The page marks them as estimates.

## What is open

1. The mentor interviews: no notes are in the repository. Ask Kaisa Kaitila on Saturday whether the pathway rule is sound to a clinician.
2. A public link for THL guidance 21/2016 in `backend/sources.py`.

## Where things are

| Path | Content |
|---|---|
| `backend/analysis.py` | The gap, the persistence, the pathway rule, the simulation |
| `backend/mortality.py` | Deaths against the number expected from the age structure |
| `backend/facts.py`, `backend/analyst.py` | The facts, the three sentences and the sentence check |
| `backend/recommend.py` | Roadmap measures, with level, first step and measure of success |
| `backend/priorities.py` | Where to start in Finland |
| `backend/sources.py` | Every source the page cites |
| `data/raw/`, `data/nordcan.json`, `data/svf_sweden.json` | The cached data |
| `web/index.html` | The page |
