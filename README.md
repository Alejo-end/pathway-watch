# Cancer Care Atlas

**Where in Finland do cancer patients do worse, at which step of the care pathway, and what should a county do first?** One page answers in under two minutes, from public data, with every number linked to its source.

![Bowel cancer in Satakunta: the map of counties, the decision with its four checks, and the first action](docs/screenshots/county-view.png)

## For the judges, in one minute

| | |
|---|---|
| Challenge | AstraZeneca, "Equal Care Across Finland", Junction 2026 |
| User | A decision-maker in one of Finland's wellbeing services counties |
| Problem | Survival after cancer differs between counties, but nobody sees where, at which step, and which measure of the national roadmap to start with |
| What it does | 1. Shows where a county is behind the rest of Finland, with a 95% interval. 2. Names the pathway step to ask about. 3. Names the first action, with an owner, a first local step, how to measure success and a date for the next review |
| Why trust it | Code computes every number, and each number links to its source. A second register (deaths) checks each survival gap. A language model may only reword computed facts, and a check removes any sentence with a number that its facts do not hold |
| What is real | Public, aggregated data from THL Sotkanet, Statistics Finland, NORDCAN and THL's queues, cached in `data/raw/`. 92 tests |
| What it is not | Advice about one patient, a ranking of hospitals, or a claim about causes. Under our reading of EU guidance MDCG 2019-11 it is not a medical device |

## Try it

**Online:** https://alejo-end--cancer-care-atlas.us-east.modal.run (hosted on Modal, the same cached open data, the fixed template for the sentences).

On your machine:

```
uv sync
uv run uvicorn backend.app:app --port 8010
```

Open http://localhost:8010 and pick a county and a cancer. The cached data is in the repository, so it runs offline. `uv run pytest` runs the 92 tests.

## How it works

1. **Data:** Sotkanet survival, screening and queue indicators, deaths and population by age from Statistics Finland, Nordic survival from NORDCAN. Fetch scripts in `data/` refresh them, no key needed.
2. **Finding:** each county against Finland, with a rough 95% interval. The map shows survival, screening, mortality or the care channel (the share of working-age doctor visits at public health centres).
3. **Decision:** four checks stand under every gap. Is the interval below zero? Does the gap hold with the stricter limit for 22 counties? Do deaths agree, as a second register? Can the public data name the slow step?
4. **Pathway step:** a fixed rule names the step to ask about. Low screening attendance points to detection. Normal attendance points to the steps after it: referral, diagnosis or treatment. Bowel screening started in 2022, so for bowel cancer the step stays open. Lung cancer has no county survival, so the rule uses the Nordic gap for all of Finland. The app names a question, not a cause.
5. **First action:** the step picks it. An open step gets a 90-day audit of the days in each step, and the audit then chooses the roadmap measure. A known step gets the matching measure of the national cancer roadmap. A county with no gap gets a measurement baseline, because a clean public screen is not proof of equal care. The Screening campaign tab plans a reminder for people already in the programme.
6. **Sentences:** a fixed template writes them from the facts. With `VERDA_INFERENCE_API_KEY` set, a model on Verda may reword them, and the check keeps only sentences that cite a fact and repeat its numbers. Print brief gives the county a one-page copy.

## Limits we state

1. Sotkanet publishes no confidence interval, so the interval is our estimate, and the page says the true one is wider.
2. No public source gives cancer waiting times or stage at diagnosis per county. The page lists these as missing data.
3. Bowel screening started in 2022, so attendance cannot explain a bowel survival gap yet. The first action there is an audit of the days in each step.

## More

| Document | For |
|---|---|
| `deploy/modal_app.py` | How the online link is served on Modal |
| [HANDBOOK.md](HANDBOOK.md) | The app explained with maps, for anyone on the team |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | Every file, the statistics, and the reasoning per cancer |
| [PATHWAY_PLAN.md](PATHWAY_PLAN.md) | The build brief, with the sources of the roadmap |
| `docs/decks/` | The pitch deck (PDF) and its videos |

Built by team Kindergarten Engineering at Junction 2026.
