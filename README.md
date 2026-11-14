# Pathway Watch

Pathway Watch is for a decision-maker in a wellbeing services county. It shows where cancer patients do worse than elsewhere in Finland and which step of the care pathway to ask about. It also shows which roadmap measure to act on first. Read `HANDBOOK.md` for an explanation with maps. The build brief is `../PATHWAY_PLAN.md`.

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
| `backend/analysis.py` | Gap in the latest year, rough 95% interval of a survival gap, pathway rule, case estimate, simulation |
| `backend/mortality.py` | Age-adjusted cancer mortality per county (SMR) for Goal 3 |
| `backend/nordcan.py` | Finland against the Nordic level (the average of Sweden and Norway) |
| `backend/channel.py` | Channel Gap: share of working-age physician visits that go through public health centres |
| `backend/facts.py` | The computed facts, each with its source |
| `backend/recommend.py` | Pathway question to roadmap measures, each with its level, first step, local step and measure of success |
| `data/dlbcl_timeline.json` | Days from first symptoms to each step for two routes into care, copied by hand from figure 1 of Kuitunen and others (Cancer Medicine 2026) |
| `backend/timeline.py` | The length of each step, the extra days on the public route, and what a county pilot measures |
| `backend/equity.py` | National values by income and education (Zai and others, BMJ Public Health 2025) |
| `backend/priorities.py` | Where to start in Finland: counties ranked by how many registers show them behind |
| `backend/analyst.py` | Three sentences from the facts, and the sentence check |
| `backend/app.py` | FastAPI endpoints: `/api/meta`, `/api/headlines`, `/api/map/{indicator}`, `/api/mortality-map/{cause}`, `/api/channel-map`, `/api/evidence`, `/api/national/{cancer}`, `/api/county/{code}?cancer=` |
| `web/index.html` | The two-minute view |
| `tests/` | `test_analysis.py` covers the rules. `test_sources.py` traces numbers to the raw files and checks every source ID. `test_evidence.py` covers the timeline, the local steps and the equity values |

## Open work

1. Add a public link for THL guidance 21/2016 in `backend/sources.py`. The strategy and the roadmap have their links.
2. Find occupational health coverage per county (Kela). The Channel Gap uses visits as a proxy.
3. Test the language model path with `ANTHROPIC_API_KEY` set.
4. Ask the Finnish Cancer Registry for stage at diagnosis per county. Stage tells detection from the later steps.

## Evidence for a survival gap

Sotkanet publishes no confidence interval. The app computes a rough 95% interval for each county survival gap in `backend/analysis.py`, `rough_interval()`. The standard error is binomial, from the estimated new cases per year times the ten diagnosis years behind one value. The rounding of the published values to whole percent is added. The page labels the interval as our estimate and says that the true interval is wider.

## Bowel cancer

National bowel screening started in 2022. Each survival value covers ten years of diagnoses, so attendance cannot explain a bowel cancer survival gap. For such a gap, the pathway step is "any": the data cannot tell which step. Low attendance in the new programme is still shown as an early warning.

## Attendance in the public programme

The Sotkanet attendance indicators count the public screening programme only. For breast cancer, the first action (measure 2.4.5) is to find who has no mammogram at all. The page cites Fuhrmann and others (Acta Oncologica 2024, https://doi.org/10.2340/1651-226X.2024.40830) for mammograms outside the programme. It cites Acharya and others (Preventive Medicine 2021, https://doi.org/10.1016/j.ypmed.2021.106828) for the mixed effect of reminders.

## Lung cancer

Lung cancer has no county survival data and no screening programme, so its view differs. The three sentences use county mortality (SMR) and national NORDCAN survival against the Nordic level. The pathway step comes from national evidence (roadmap, page 22). The first action is roadmap measure 2.3.4 (page 46): extend the lung cancer screening pilot, and invite first the counties with significantly more lung cancer deaths than their age structure predicts. The slider shows what reaching the Nordic level would mean for the county's yearly patients. The view also cites a survey of Nordic lung cancer professionals: Khalife and others, Acta Oncologica 2025, https://doi.org/10.2340/1651-226X.2025.42778. In it, Finland had the lowest access to CT from primary care. No public source gives the wait for the tests before treatment per county: endoscopy, scan and pathology. The page lists these waits as missing data. It also lists the treatment that patients got, because the app has no data on surgery, radiotherapy or medicines.

## Intended use

Pathway Watch is a planning tool for a wellbeing services county. It works on county statistics and gives no advice about one patient. Under our reading of the EU guidance MDCG 2019-11, such software is not a medical device. `HANDBOOK.md` gives the reasons and the limits.

## Goal 3 coverage

The app covers Goal 3 indicators 1 and 2 with age-adjusted cancer mortality per county. It shows the standardized mortality ratio (SMR): observed deaths divided by the deaths that the county's age structure predicts, times 100. It shows all cancers and the three poor-prognosis cancers (lung, pancreas, liver). The national total for 2024 is 13,316 deaths, which matches the "about 13,300" in the strategy. Indicator 3 (treatment within target times) has no public data per county, and the app reports that gap.
