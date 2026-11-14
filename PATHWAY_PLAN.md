# Pathway Watch: demo plan

This file is the build brief for Pathway Watch. Team Kindergarten Engineering builds it at Junction 2026 for the AstraZeneca challenge "Equal Care Across Finland". Any person or coding agent who joins the work starts here. For a short explanation with maps, read `pathway-watch/HANDBOOK.md` first.

## Goal

A decision-maker in a wellbeing services county opens Pathway Watch. In under two minutes, the person sees three things. First, where cancer patients in the county do worse than elsewhere in Finland. Second, at which step of the care pathway the difference most likely starts. Third, which action to take first. Every number and every claim shows its source.

The design rule: the language model explains and drafts. Code computes every number, and every sentence needs a source. If a sentence has no source, the app removes it before display.

## Status and pitch headline

Pathway Watch is our second entry, after the Safe Kitchen Agent. An originality test showed that a dashboard with an AI analyst is the obvious idea for this brief. So the pitch leads with two findings that a model cannot give other teams, because they come from Finnish sources and live data:

1. Diagnosis takes twice as long through public care. The roadmap cites an unpublished lymphoma study on page 11.
2. Helsinki has the lowest attendance in the public breast screening programme in every published year, 2015 to 2024 (Sotkanet). The three lowest areas are all in Uusimaa in each of those years.
3. Satakunta has the lowest bowel cancer survival in every year from 2019 to 2023 (Sotkanet).

The first finding is one unpublished study of lymphoma patients, and the pitch says so.

The app also shows a data gap view: which indicators are missing for each county, and the minimum data to collect. The brief says closing the data gap is part of the challenge.

A rerun of the originality test on 13 November (three models, 10 ideas each) confirmed the pattern. The gap map, the AI analyst, early warning and the simulator appeared in every run. The two findings above appeared in none. Two fresh features build on them:

1. Channel Gap (lead feature). For each county, show how many working-age people have occupational health care and how many rely only on public health centers. Combined with the roadmap's finding that diagnosis takes twice as long through public care, this is a map of who is exposed to the referral delay. Data to find first: Kela open data on occupational health care coverage by region. If it does not exist by county, use the national figure and say so.
2. Nordic Mirror. Sweden publishes waiting times for its standardized cancer pathways (SVF) by region. The tool shows the picture Finland gets with the same measurement, and turns the data gap into a concrete proposal that matches roadmap measure 3.1.2. Data to find first: whether the Swedish regional waiting times are public and current.

Do not build an early warning replay. It needs a history of waiting times by county, and we found no public source for it. A replay with invented data breaks the rule that every claim has a source.

## Corrected assumptions (review on 14 November)

We read the Sotkanet indicator definitions and six years of data. Four earlier statements were wrong or too strong.

1. The survival figure is not a one-year value. Each year covers patients diagnosed in that year and the nine years before, followed for five years. The figure is age-standardized. So two neighboring years share most of their patients. A three-year average does not reduce noise, and the plan no longer asks for one.
2. The headline county was wrong. Päijät-Häme is lowest only in 2024. Satakunta has the lowest bowel cancer survival in every year from 2019 to 2023. It is 5 to 9 points below Finland in those years, and 4 points below in 2024. Use Satakunta in the demo.
3. Survival describes care given up to ten years ago. It does not show how the pathway works today. Do not present "extra survivors" as the effect of an action now. Label the slider as an illustration of the size of the gap.
4. The "how sure are we" marker cannot come from year-to-year agreement, because the years overlap. Take confidence intervals from the Cancer Registry statistics app. If they are not available, say "uncertainty not published".
5. The Helsinki screening finding is stronger than we said. Helsinki has the lowest breast screening attendance in all ten published years, 2015 to 2024. The three lowest areas are all in Uusimaa. The cause is not known. Possible explanations are tests in private care that the program does not count, people who move often, and language barriers. Present these as questions, and ask the mentors.
6. The "twice as long through public care" finding is one unpublished study of lymphoma patients. Quote it as that. Do not apply it to all cancers.
7. The rule "low survival with normal screening points to referral or treatment" compares whole counties, not patients. Call the result "a question to investigate", never a located cause.
8. Update of 14 November, 02:30: the code now follows items 1, 3, 4, 6 and 7. It shows the gap of the latest year and the number of years on the same side. It no longer averages years, and it no longer says "confidence" for Sotkanet values. A gap of one point counts as "near", because Sotkanet rounds survival to whole percent.
9. The first action for low screening was outreach to language groups. That assumed the cause. The first action is now to find who does not attend (measure 2.4.5).
10. Update of 14 November, afternoon: three more assumptions were wrong, and the code now follows the items below.
11. Bowel cancer: national screening started in 2022, and each survival value covers ten years of diagnoses. The rule no longer uses attendance for a bowel survival gap. The app says that the data cannot tell which step the gap comes from.
12. Evidence: the count of years on the same side is a description only. The app now computes a rough 95% interval from patient counts. For Satakunta in 2024, the gap is 4 points and the interval is 6.5 to 1.5 points below Finland. The interval is our estimate, and the true interval is wider.
13. Attendance: the Sotkanet figure counts the public programme only. A Finnish Cancer Registry study found mammograms outside the programme, most among upper-level employees (Fuhrmann and others, Acta Oncologica 2024). For breast cancer, the first action is now to find who has no mammogram at all.
14. The lowest of 22 counties tends to look less extreme the next time it is measured. The page says so for the lowest county.

## What AstraZeneca asks

1. Identify the gap: differences in access to cancer care or in outcomes.
2. Locate the gap in the pathway: detection, referral from primary to specialist care, diagnosis, or start of treatment.
3. Recommend what to do. This part matters most. Give concrete proposals for national or county level.
4. Cover at least one indicator of Goal 3 of the national cancer strategy.
5. Show the source for every claim.
6. Submit a working demo. Slides alone do not count.
7. A non-technical decision-maker understands the result in under two minutes.

AstraZeneca also says that data on cancer care in Finland is limited, and that closing this gap is part of the challenge.

## Goal 3 of the national cancer strategy

Source: Kansallinen syöpästrategia 2026–2035, the strategy goals page. Goal 3 is "Varmistetaan yhdenvertainen ja vaikuttava syövänhoito" (ensure equal and effective cancer care). Its indicators:

1. Five-year survival for cancers with a poor prognosis reaches the Nordic level. The targets are +14 percentage points for lung cancer, +6 for pancreatic cancer and +14 for liver cancer, compared with the 2023 NORDCAN level. "Nordic level" means the average of Sweden and Norway.
2. Cancer mortality falls by 10%. Today about 13,300 people die of cancer each year.
3. Patients start treatment within the target times. The reference is THL guidance 21/2016 on monitoring access to cancer care.

A theme that crosses all goals is equality. Regional and socioeconomic differences in incidence, care and mortality must be visible and must steer action.

## Roadmap measures to cite in recommendations

Source: Toimeenpanon tiekartta 2026–2031 (the implementation roadmap).

| Measure | What it says | Pathway step it fits |
|---|---|---|
| 2.5.2 | Standardized referral criteria in the national care pathways, so that patients with possible cancer symptoms go fast to diagnostic tests. Modeled on Denmark (Kræftpakkeforløb), Sweden (SVF) and Norway (Pakkeforløp) | Referral from primary to specialist care |
| 2.5.1 | Better access to care through more doctor resources in primary care | Detection and first contact |
| 3.1.2 | National care pathway descriptions per cancer, with defined target access times: five cancers by 2026–2028, all major cancers by 2029–2031. Indicator: patients start treatment within target times | Diagnosis and start of treatment |
| 3.1.4 | National quality and effectiveness targets and indicators | Missing or unclear indicators |
| 3.2.1 | A legal basis for the THL Cancer Registry to collect the data | Missing data |
| 2.3 and 2.4 | Screening programs: criteria, quality handbooks, targeted invitations | Detection, where screening participation is low |

Read the roadmap pages before citing a measure. The pages are in Finnish. Quote the measure number and the page.

More measures for outreach:

| Measure | What it says | Pathway step it fits |
|---|---|---|
| 1.3.1 | Raise participation in vaccinations and cancer screening among language groups, through targeted, community-based communication | Detection |
| 1.3.2 | A national communication plan on cancer symptoms, so people seek care early | Detection |
| 2.4.5 | Use screening register data to develop the screening program together with the counties | Detection |

## Insights from AstraZeneca's documents

These come from the three resource files: the strategy, the roadmap and the source list.

1. Diagnosis takes twice as long through public care. An unpublished study of lymphoma patients found it. It compares patients with symptoms who go to public health care with patients who go to a private provider (roadmap, page 11). Primary care in Finland has three parallel channels: public health centers, private clinics and occupational health. The roadmap calls public health centers heavily under-resourced. This is the strongest available evidence for a gap at the referral step.
2. Inequality is socioeconomic as well as regional. For patients with low income or little education, the roadmap names four suspected causes of worse results: later diagnosis, weaker access to care, less intense treatment and lower screening participation. Client fees, medicine costs and travel costs can delay care (roadmap, page 10).
3. Immigrants take part in screening less. At the end of 2023, almost 7% of Finland's population was born abroad. In Uusimaa, the figure was one in ten. In the working-age population, it was 13.3% nationally and 21.6% in Uusimaa. Cervical cancer can be more common and more deadly in some immigrant groups (roadmap, page 11).
4. Our Sotkanet data fits this pattern. In 2024, Helsinki had the lowest attendance of all counties in both colorectal screening (69.6%) and breast screening (74.3%). This is a correlation, not a proven cause. It is a strong opening for roadmap measure 1.3.1.
5. Older patients are a cross-cutting focus of the strategy. Measure 3.4.1 adds systematic assessment of functional ability to their diagnosis and treatment.
6. The cancer burden grows over the next ten years as the population ages (strategy summary).

## Source list links

The AstraZeneca source list links to these data sources:

| Source | Link |
|---|---|
| Finnish Cancer Registry statistics app and screening statistics | https://syoparekisteri.fi/tilastot/ |
| FICAN cancer registry and quality registers | https://fican.fi/toiminta/arviointi-ja-seuranta/syopien-laaturekisterit/ |
| THL data and statistics, Sotkanet | https://thl.fi/data-ja-tilastot |
| Statistics Finland, causes of death | https://stat.fi/fi/tilasto/ksyyt |
| Kela open data and medicine refund rights | https://tietotarjotin.fi/tilastodata/2242438/avoin-data |
| NORDCAN 2.0 | https://nordcan.iarc.who.int/en |
| Findata, permits for health data | https://findata.fi/ |
| FinRegistry | https://www.finregistry.fi/finnish-registry-data |

Findata, FinRegistry and the biobanks need research permits. A hackathon cannot get them, so the demo uses public aggregate data only.

## Data we found

Sotkanet, the THL indicator bank, has an open REST API with no key. It returns values per wellbeing services county (`HYVINVOINTIALUE`) and for the whole country (`MAA`).

| Indicator ID | Indicator | Years by county |
|---|---|---|
| 3627 | Five-year relative survival, bowel cancer, % | 2019–2024 |
| 3625 | Five-year relative survival, breast cancer, % | 2019–2024 |
| 3626 | Five-year relative survival, cervical cancer, % | 2019–2024 |
| 6103 | Colorectal cancer screening, share of invited who attended, % | 2022–2024 |
| 3621 | Breast cancer screening, share of invited who attended, % | 2015–2024 |
| 3620 | Cervical cancer screening, share of invited who attended, % | 2015–2024 |
| 5643 | Cancer index, age-standardized | 2019–2024, not used by the app |
| 5093 | Entitled to special refunds on cancer medicines, age-standardized % | not fetched |
| 293, 2371, 692 | Doctor visits in public, occupational and private care | 2020–2024 |

Example calls:

```
https://sotkanet.fi/rest/1.1/regions
https://sotkanet.fi/rest/1.1/json?indicator=3627&years=2024&genders=total
```

First result (fetched on 13 November 2026, Åland excluded): five-year bowel cancer survival in 2024 ranges from 63% in Päijät-Häme to 74% in Keski-Uusimaa. Each value covers ten years of diagnoses. Satakunta is lowest in every year from 2019 to 2023. The national value is 68%. The highest county changes from year to year.

Other sources:

1. NORDCAN (nordcan.iarc.fr): Nordic survival and mortality. This is the benchmark for the "Nordic level" in Goal 3.
2. The Finnish Cancer Registry statistics app (tilastot.syoparekisteri.fi): incidence and survival, possibly with stage at diagnosis by region. Find out what it offers by region.
3. Statistics Finland: causes of death in StatFin.
4. The AstraZeneca background pack, source list and roadmap on the Junction platform.
5. Interviews with AstraZeneca mentors. Record the answers in `docs/interviews.md`, with the mentor's name and permission.

No public source that we found gives waiting times per county. That missing data is the first finding of the app.

## The analysis

### Step 1: find the gap

For each county and indicator, compute the difference from the national value. Do not average years to reduce noise, because the yearly values share most of their patients. Show a "how sure are we" marker:

1. Published: the Cancer Registry gives a confidence interval, and the app shows it. We did not find one in open data.
2. Rough interval: for survival, the app computes a 95% interval from the estimated number of patients. The page labels it as our estimate.
3. Persistent: for attendance, the county is on the same side of the national value in most published years. This is a description, not a test.

### Step 2: locate the gap in the pathway

Use the indicators that belong to each pathway step:

| Pathway step | Signal in public data |
|---|---|
| Detection | Screening participation. Stage at diagnosis, from the Cancer Registry, where it exists by region |
| Referral | No public regional data. Mentor interviews only |
| Diagnosis | Stage at diagnosis, where it exists |
| Start of treatment | No public regional waiting times. Survival differences with normal screening point here |

A simple rule for the demo: low survival with low attendance in the public screening programme raises a question about detection. Low survival with normal attendance raises a question about referral, diagnosis or treatment. The rule compares counties, not patients. The app calls the result "a question to investigate" and never claims a cause.

The rule does not apply to bowel cancer. Colorectal screening started nationally in 2022, and the five-year survival figures describe patients diagnosed years earlier. For a bowel cancer survival gap, the app says that the data cannot tell which step. Stage at diagnosis per county is the data that tells the steps apart.

### Step 3: recommend

Map each located gap to a roadmap measure (see the table above). Each recommendation has:

1. The action in one sentence.
2. The roadmap measure and page.
3. The evidence: the county's numbers and the Nordic model it follows.
4. Who acts: the county, FICAN or THL.

### Step 4: simulate

A slider illustrates the size of the gap: the county at the national survival level. Survival describes care given up to ten years ago, so the app labels the result "an illustration, not a forecast". Extra five-year survivors = new cases per year × (national survival − county survival). New cases per county come from the Cancer Registry. If the registry does not give counts per county, use a clearly marked estimate and say so.

## Architecture

```
data/fetch_sotkanet.py  -> data/raw/*.json      (open API, no key)
data/fetch_statfin.py   -> data/raw/statfin_mortality.json (open API, no key)
data/nordcan.json       -> NORDCAN values, copied by hand from the fact sheets
data/svf_sweden.json    -> Sweden's waiting times, copied by hand from the RCC report
backend/analysis.py     -> gaps, rough interval, pathway step (plain code)
backend/recommend.py    -> gap type to roadmap measure, with citations
backend/analyst.py      -> language model writes 3 sentences from computed facts only
backend/app.py          -> FastAPI endpoints
web/                    -> county picker, map, the two-minute view
tests/                  -> every number traced to a source, no sentence without a source
```

## The two-minute view

1. A map of Finland's counties, colored by the chosen indicator, with the confidence marker.
2. Pick a county.
3. Three sentences: the gap, the most likely pathway step, the first action.
4. One chart: the county against the national value and the Nordic level, over the years.
5. The first action card, with the roadmap measure and the sources.
6. The simulation slider.
7. A "data we are missing" box, for example "no public waiting times for this county".

## Tonight's tasks by role

Most AstraZeneca mentors are only at the venue on Friday evening. On Saturday, only Kaisa Kaitila (Medical Affairs) is there.

| Role | Task | Done when |
|---|---|---|
| UX | Interview the mentors. Ask the questions below. Sketch the two-minute view | Answers written in `docs/interviews.md` |
| Automation | Write `fetch_sotkanet.py` for the indicators above. Cache the raw JSON | All indicators saved for all counties and years |
| ML and testing | Write the gap and confidence code with tests. Look for stage data by region in the Cancer Registry app | Gap table for bowel and breast cancer |
| Full stack | Set up FastAPI and a first page with the county picker and one chart | One county shows its bowel cancer survival over time |

Questions for the mentors:

1. Which Goal 3 indicator matters most to you?
2. Is there any regional data on referral or waiting times, public or from reports?
3. Which county is a likely host for a follow-up project? What does its decision-maker need?
4. Which cancers are the best focus for the demo?
5. Is our pathway rule (screening against survival) sound to a clinician?
6. Does the Cancer Registry publish stage at diagnosis per wellbeing services county?
7. How much mammography in Helsinki happens outside the public programme?
8. Does any register give the wait for each test before treatment per county: colonoscopy, scan, pathology?
9. Is our reading right that a planning tool on county statistics is not a medical device?

## Saturday

1. Morning: confidence markers, the pathway step, the recommendation cards with citations.
2. Afternoon: the language model analyst, constrained to computed facts. Simulation slider. Show it to Kaisa Kaitila.
3. 18:00: feature freeze.
4. Evening: polish the two-minute view, three rehearsals, backup video.

## Demo script (two minutes)

1. "You lead a wellbeing services county. Where do your cancer patients fall behind?"
2. Pick Satakunta. The map and the three sentences appear.
3. Show the chart against the national value and the Nordic level.
4. Show the first action: standardized referral criteria (roadmap measure 2.5.2), with the Nordic models it follows.
5. Show the Helsinki screening finding, with the possible explanations as open questions.
6. Show the "data we are missing" box, with the waits for the tests before treatment. End on the follow-up project with a county.

## Constraints

1. Use public, aggregate data only. No patient data.
2. Give no advice about one patient. Software that does is a medical device and needs a CE mark. `pathway-watch/HANDBOOK.md` gives our reading of the rule.
3. Show the source for every number and claim.
4. Do not put secrets in the repository. It becomes public under the MIT license.
5. Final submission by Sunday 08:00. The hard deadline is 10:00. Judging starts at 14:00.

## Still unknown

1. Whether the Cancer Registry statistics app gives stage at diagnosis and case counts by county.
2. What the mentors answered on Friday. No interview notes are in the repository.
3. What the AstraZeneca background pack adds. It is in Finnish, on the Junction platform.
