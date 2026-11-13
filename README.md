# Pathway Watch

Pathway Watch shows a decision-maker in a wellbeing services county where cancer patients do worse than elsewhere in Finland, at which step of the care pathway the difference most likely starts, and which roadmap measure to act on first. The build brief is `../PATHWAY_PLAN.md`.

## Run

```
uv sync
uv run python data/fetch_sotkanet.py   # refresh the open data, no key needed
uv run uvicorn backend.app:app --port 8010
```

Open http://localhost:8010. The cached data in `data/raw/` and the map in `web/counties.geojson` are in the repository, so the fetch step is only for a refresh.

If the SDK finds Anthropic credentials, the language model rewords the three summary sentences. Set `PATHWAY_LLM=0` to always use the fixed template. In both cases `backend/analyst.py` removes a sentence that cites no fact, or that contains a number the cited facts do not contain.

## Files

| File | What it does |
|---|---|
| `data/fetch_sotkanet.py` | Downloads the Sotkanet indicators, the regions and the county map |
| `data/reference.json` | Values that no API gives: national case counts (approximate) and the Nordic level (missing) |
| `backend/analysis.py` | Gap, confidence, pathway rule, case estimate, simulation, facts with sources |
| `backend/recommend.py` | Located gap to roadmap measures |
| `backend/analyst.py` | Three sentences from the facts, and the source check |
| `backend/app.py` | FastAPI endpoints `/api/meta`, `/api/map/{indicator}`, `/api/county/{code}?cancer=` |
| `web/index.html` | The two-minute view |

## Open work

1. Check the national case counts in `data/reference.json` against the Cancer Registry and set their status to `checked`.
2. Add the NORDCAN five-year survival values to `data/reference.json`. The chart then draws the Nordic line.
3. Read the roadmap and fill in the page numbers in `backend/recommend.py`. Only measure 1.3.1 has a page now.
4. Add public links for the strategy, the roadmap and THL guidance 21/2016 in `backend/sources.py`.
