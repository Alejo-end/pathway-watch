# Pathway Watch

Pathway Watch shows a decision-maker in a wellbeing services county where cancer patients do worse than elsewhere in Finland, at which step of the care pathway the difference most likely starts, and which roadmap measure to act on first. The build brief is `../PATHWAY_PLAN.md`.

## Run

```
uv sync
uv run python data/fetch_sotkanet.py   # refresh the Sotkanet data, no key needed
uv run python data/fetch_statfin.py    # refresh deaths and population by age, no key needed
uv run uvicorn backend.app:app --port 8010
```

Open http://localhost:8010. The cached data in `data/raw/` and the map in `web/counties.geojson` are in the repository, so the fetch step is only for a refresh.

A fixed template writes the three summary sentences from the computed facts. If the SDK finds Anthropic credentials, the language model rewords them instead. Set `PATHWAY_LLM=0` to always use the template. In both cases `backend/analyst.py` removes a sentence that cites no fact, or that holds a number or a quantity word that its cited facts do not hold. The check compares numbers. It does not read meaning, so it cannot catch a correct number given to the wrong place. The template cannot make that error, and the model path is not tested yet. Use `PATHWAY_LLM=0` for the demo until it is.

## Files

| File | What it does |
|---|---|
| `data/fetch_sotkanet.py` | Downloads the Sotkanet indicators listed in `backend/indicators.py`, the regions and the county map |
| `data/fetch_statfin.py` | Downloads cancer deaths per county and age, and population per age, from Statistics Finland |
| `data/nordcan.json` | National case counts and five-year survival for Finland, Sweden and Norway, read from the NORDCAN fact sheets |
| `data/svf_sweden.json` | Sweden's share of patients treated within the SVF lead time, per region (RCC report 2025) |
| `backend/indicators.py` | The Sotkanet indicators, the cancers and the pathway steps |
| `backend/sotkanet.py` | Loads the cached Sotkanet files |
| `backend/analysis.py` | Gap, confidence, pathway rule, case estimate, simulation |
| `backend/mortality.py` | Age-adjusted cancer mortality per county (SMR) for Goal 3 |
| `backend/nordcan.py` | Finland against the Nordic level (the average of Sweden and Norway) |
| `backend/channel.py` | Channel Gap: share of working-age physician visits that go through public health centres |
| `backend/facts.py` | The computed facts, each with its source |
| `backend/recommend.py` | Located gap to roadmap measures |
| `backend/analyst.py` | Three sentences from the facts, and the sentence check |
| `backend/app.py` | FastAPI endpoints: `/api/meta`, `/api/headlines`, `/api/map/{indicator}`, `/api/mortality-map/{cause}`, `/api/channel-map`, `/api/county/{code}?cancer=` |
| `web/index.html` | The two-minute view |
| `tests/` | `test_analysis.py` covers the rules. `test_sources.py` traces numbers to the raw files and checks every source ID |

## Open work

1. Add public links for the strategy, the roadmap and THL guidance 21/2016 in `backend/sources.py`. The page numbers are filled in from the PDFs.
2. Find occupational health coverage per county (Kela). The Channel Gap uses visits as a proxy.
3. Test the language model path with `ANTHROPIC_API_KEY` set.

## Lung cancer

Lung cancer has no county survival data and no screening programme, so its view differs. The three sentences use county mortality (SMR) and national NORDCAN survival against the Nordic level. The pathway step comes from national evidence (roadmap, page 22). The first action is roadmap measure 2.3.4 (page 46): extend the lung cancer screening pilot, and invite first the counties with significantly more lung cancer deaths than their age structure predicts. The slider shows what reaching the Nordic level would mean for the county's yearly patients.

## Goal 3 coverage

The app covers Goal 3 indicators 1 and 2 with age-adjusted cancer mortality per county. It shows the standardized mortality ratio (SMR): observed deaths divided by the deaths that the county's age structure predicts, times 100. It shows all cancers and the three poor-prognosis cancers (lung, pancreas, liver). The national total for 2024 is 13,316 deaths, which matches the "about 13,300" in the strategy. Indicator 3 (treatment within target times) has no public data per county, and the app reports that gap.
