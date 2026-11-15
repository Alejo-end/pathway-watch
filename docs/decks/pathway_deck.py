"""Build the evaluation deck of the AstraZeneca entry as a PDF.

    cd pathway-watch && PATHWAY_LLM=0 uv run uvicorn backend.app:app --port 8011
    python3 docs/decks/pathway_deck.py [http://localhost:8011]

The deck is a PDF, so it looks the same on every machine. Every number on a slide is read from the
running app's API, and every picture is a screenshot of the running app, so the deck cannot show a
value or a screen that the demo does not. Chromium takes the screenshots and prints the pages.
Set CHROME to a Chromium or Chrome binary if the script finds none.
"""

from __future__ import annotations

import base64
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

APP = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8011").rstrip("/")
OUT = Path(__file__).resolve().parent / "AstraZeneca - Cancer Care Atlas.pdf"
TEAM = "Team Kindergarten Engineering · Junction 2026"
COUNTY, CANCER = "06", "bowel"  # the demo case: bowel cancer in Satakunta
# Short names for the source line under a slide. The last slide gives the full titles.
SHORT = {"kuitunen_2026": "Kuitunen and others, Cancer Medicine 2026",
         "rcc_svf_2025": "Regionala cancercentrum i samverkan, annual report 2025"}


def chrome() -> str:
    found = [os.environ.get("CHROME")] + sorted(glob.glob(os.path.expanduser(
        "~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")), reverse=True) + [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"]
    for path in found:
        if path and os.path.exists(path):
            return path
    sys.exit("No Chromium found. Set CHROME to a Chromium or Chrome binary.")


def api(path: str):
    with urllib.request.urlopen(APP + path, timeout=20) as r:
        return json.load(r)


def shot(tmp: str, name: str, view: str, part: str = "", height: int = 1000) -> str:
    """A screenshot of one view of the app in the light theme, as a data address for an <img>."""
    query = urllib.parse.urlencode({"cancer": CANCER, "county": COUNTY, "view": view, "part": part, "theme": "light"},
                                   quote_via=urllib.parse.quote)
    png = os.path.join(tmp, name + ".png")
    subprocess.run([chrome(), "--headless", f"--screenshot={png}", f"--window-size=1400,{height}", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--virtual-time-budget=8000", f"{APP}/?{query}"],
                   check=True, capture_output=True)
    return "data:image/png;base64," + base64.b64encode(Path(png).read_bytes()).decode()


def main() -> None:
    name = re.search(r"<title>([^<]+)", urllib.request.urlopen(APP + "/").read().decode()).group(1).strip()
    b = api(f"/api/county/{COUNTY}?cancer={CANCER}")
    ev, hl, rank = api("/api/evidence"), api("/api/headlines"), api(f"/api/national/{CANCER}")
    sources = api("/api/meta")["sources"]
    c, t, m, camp = b["chart"], ev["timeline"], b["mirror"], b["campaign"]
    county = b["county"]["name"]
    own, nat = c["county"][str(c["year"])], c["national"][str(c["year"])]
    iv, first, size = c["interval"], b["recommendations"][0], camp["size"]
    g, o, study = t["groups"], t["by_owner"], t["study"]
    deaths = next(r for r in b["goal3"]["rows"] if r["cause"] == CANCER)
    strict = (f"It still excludes zero with the stricter limit for {iv['comparisons']} counties compared at once."
              if iv["strict_excludes_zero"] else f"With the stricter limit for {iv['comparisons']} counties it includes zero.")
    num = lambda v: f"{v:,}"
    pts = lambda v: f"{abs(v):g}"
    cite = lambda i: SHORT.get(i, sources[i]["title"])

    with tempfile.TemporaryDirectory() as tmp:
        pic = {
            "finding": shot(tmp, "finding", "finding"),
            "delays": shot(tmp, "delays", "evidence", "Delays"),
            "action": shot(tmp, "action", "act", "First action"),
            "campaign": shot(tmp, "campaign", "act", "Screening campaign", 1010),
        }
        slides = [
            f"""<section class="slide dark">
              <div class="kicker">AstraZeneca · Equal Care Across Finland</div>
              <h1 class="title">{name}</h1>
              <p class="lead">Where cancer patients in a county fall behind, and what the county can start next month.</p>
              <p class="foot">{TEAM}</p></section>""",

            f"""<section class="slide"><div class="eyebrow">The problem</div>
              <h2>Finland cannot see where its cancer patients wait.</h2>
              <div class="trio">
                <div class="fig"><b>{hl['mirror']['regions']} of {hl['mirror']['regions']}</b><span>Swedish regions report the share of patients who start treatment within the target time. In 2025 it was {m['national']['2025']['share']}% against a target of {m['target']}%.</span></div>
                <div class="fig bad"><b>0 of {hl['mirror']['finland_counties']}</b><span>Finnish wellbeing services counties have that number in any public source.</span></div>
                <div class="fig bad"><b>{g['public']['median_total']} against {g['private']['median_total']} days</b><span>Median time from first symptoms to treatment in one Finnish lymphoma study: first contact at a public health centre against private or occupational care. {g['public']['patients']} and {g['private']['patients']} of the study's {study['patients']} patients. The public group was older.</span></div>
              </div>
              <p class="say">So a county leader cannot tell which step of the pathway to fix. {name} shows what the open data can say, says what it cannot, and names the first step that a county can take itself.</p>
              <p class="src">Sources: {cite(m['source'])}. {cite(t['source'])}.</p></section>""",

            f"""<section class="slide split"><div><div class="eyebrow">Insight 1 of 2 · the gap</div>
              <h2>{b['cancer']['label']} in {county}: {pts(c['gap'])} points below Finland.</h2>
              <ul class="points">
                <li><b>{own:g}% against {nat:g}%</b> five-year relative survival in {c['year']}. Below Finland in {c['years_same_side']} of {c['n_years']} published years.</li>
                <li><b>Our rough 95% interval: {pts(iv['low'])} to {pts(iv['high'])} points below.</b> It is our estimate from about {num(iv['patients'])} patients, and the true interval is wider. {strict}</li>
                <li><b>Goal 3, cancer deaths:</b> {round(deaths['deaths_per_year'])} bowel cancer deaths per year, SMR {deaths['smr']} (95% interval {deaths['low']} to {deaths['high']}). 100 is the number that the age structure predicts.</li>
                <li>The page then says plainly: the open data cannot tell which step of the pathway the gap comes from.</li>
              </ul></div>
              <figure><img src="{pic['finding']}" alt=""><figcaption>The view "Finding". The map stays on screen in every view.</figcaption></figure></section>""",

            f"""<section class="slide split"><div><div class="eyebrow">Insight 2 of 2 · where on the pathway</div>
              <h2>The public route ends {t['total']['extra']} days later. Most of them pass before the hospital.</h2>
              <ul class="points">
                <li><b>{o['patient']['extra']} days</b> before the first contact.</li>
                <li><b>{o['primary care']['extra']} days</b> in primary care, from first contact to referral.</li>
                <li><b>{o['hospital']['extra']} days</b> in the hospital, from referral to treatment.</li>
                <li>One lymphoma study, {study['compared']} of its {study['patients']} patients. The figure is close to the paper's means ({t['means']['public']} and {t['means']['private']} days). The medians are {g['public']['median_total']} and {g['private']['median_total']} days. It shows where days add up in that study, not in {county}.</li>
              </ul></div>
              <figure><img src="{pic['delays']}" alt=""><figcaption>The view "Evidence", part "Delays".</figcaption></figure></section>""",

            f"""<section class="slide split"><div><div class="eyebrow">Action 1 of 2 · the first step</div>
              <h2>A step that one health centre can start next month.</h2>
              <ul class="points small">
                <li><b>Start locally:</b> {first['local']['text']}</li>
                <li>{f"<b>Roadmap measure {first['measure']}</b> (page {first['page']}): {first['action'][0].lower() + first['action'][1:]}" if first['source'] == 'roadmap' else f"<b>{first['proposal']}.</b> The audit chooses the roadmap measure. The data do not."}</li>
                <li><b>Success is:</b> {first['success'][0].lower() + first['success'][1:]}</li>
                <li><b>In {county}:</b> about {num(b['simulation']['cases']['value'])} new cases and {round(deaths['deaths_per_year'])} deaths per year.</li>
              </ul></div>
              <figure><img src="{pic['action']}" alt=""><figcaption>The view "Decision". The brief prints on one page.</figcaption></figure></section>""",

            f"""<section class="slide split"><div><div class="eyebrow">Action 2 of 2 · a reminder campaign</div>
              <h2>Three yes or no rules decide who gets a reminder.</h2>
              <ul class="points">
                <li><b>{camp['attendance']}%</b> of the invited took the bowel screening test in {county} in {camp['year']}. The target is {camp['target']}%.</li>
                <li><b>About {num(size['not_attended'])}</b> of about {num(size['invited'])} invited people have no test in the programme. <b>About {num(size['needed'])}</b> more tests reach the target.</li>
                <li>The rules use the programme's own records: age and sex, home municipality, invitation and test. <b>No diagnosis, no income, no language.</b></li>
                <li>The page warns that a test outside the programme is not counted, and it plans the follow-up tests first.</li>
              </ul></div>
              <figure><img src="{pic['campaign']}" alt=""><figcaption>The view "Decision", part "Screening campaign".</figcaption></figure></section>""",

            f"""<section class="slide"><div class="eyebrow">Data quality and transparency</div>
              <h2>Every number names its source, and code checks it.</h2>
              <div class="cols tight">
                <ul class="points">
                  <li><b>Open data only:</b> THL Sotkanet, Statistics Finland, NORDCAN, the national strategy and its roadmap, and published studies.</li>
                  <li><b>Computed or copied, and the page says which.</b> Code computes the county numbers. The values of one paper figure, of NORDCAN and of the Swedish report are copied by hand, and tests check their sums.</li>
                  <li><b>Where the AI is:</b> Verda Kimi writes the three source-linked summary sentences from code-selected, public aggregate facts. It receives no patient data and cannot choose the action.</li>
                  <li><b>Guardrails replace a bad answer with the fixed template.</b> Code removes a sentence with no source or an unsupported number. Tests trace the numbers to the raw files.</li>
                </ul>
                <ul class="points">
                  <li><b>Chance is counted.</b> The app compares {rank['counties']} counties, so about one 95% interval excludes zero by chance. {rank['survival_strict']} of {rank['survival_signals']} bowel cancer survival signals hold the stricter limit for {rank['counties']} comparisons.</li>
                  <li><b>Limits sit next to the numbers,</b> not in a footnote: the interval is our rough estimate, survival describes care up to ten years ago, and attendance counts the public programme only.</li>
                  <li><b>What is missing is a view of its own:</b> waiting times, stage and treatment per county, each with the roadmap measure that would collect it.</li>
                  <li><b>Our own proposals are marked:</b> the local steps and the campaign rules. No county reviewed them yet.</li>
                </ul>
              </div></section>""",

            f"""<section class="slide"><div class="eyebrow">Against the five criteria</div>
              <h2>Where {name} answers each criterion.</h2>
              <table>
                <tr><th>Criterion</th><th>Weight</th><th>Where to look</th></tr>
                <tr><td>Actionability</td><td>30%</td><td>View "Decision": a local step for next month, the first action, who acts and how success is measured. When the data cannot name the step, the first action is a pathway audit that chooses the roadmap measure. The reminder campaign with its three rules and its size.</td></tr>
                <tr><td>Insight</td><td>25%</td><td>View "Finding": the gap with its interval. View "Evidence": where the days add up on two routes into care. View "Finland": cancer deaths per county for Goal 3. View "Measurement gaps": what Sweden publishes and Finland does not.</td></tr>
                <tr><td>Data quality and transparency</td><td>20%</td><td>A numbered source on every number, the limits beside it, a stricter limit for 22 counties, and the list of missing data.</td></tr>
                <tr><td>Execution</td><td>15%</td><td>A live web app on cached open data. Data and fonts are local, so it needs no network in the room. A 90-day plan with a county ends in a go or no go rule.</td></tr>
                <tr><td>Clarity</td><td>10%</td><td>Four numbers and three sentences at the top. One view at a time. A one-page brief to take to a meeting.</td></tr>
              </table></section>""",

            f"""<section class="slide"><div class="eyebrow">What we say out loud, and what comes next</div>
              <h2>Three limits, and one follow-up project.</h2>
              <div class="cols">
                <ul class="points">
                  <li>The timeline is one study of one lymphoma type, and the public group was older.</li>
                  <li>Survival describes patients diagnosed up to ten years ago. The county rule compares counties, not patients, so it raises a question and names no cause.</li>
                  <li>The local steps and the campaign are our proposals. No county and no data protection officer reviewed them.</li>
                </ul>
                <div class="next"><div class="eyebrow">Next</div>
                  <p>A 90-day pilot with one wellbeing services county. The county holds the dates in its own records. The tool computes the five intervals from first symptoms to treatment, every quarter, for each large health centre and one pooled group of the small ones. Patient records never leave the county.</p>
                  <p class="small">{' '.join(f"<b>{w}, {t.lower()}.</b>" for w, t, _ in ev['pilot']['plan_90'])} The county names a sponsor, a clinical lead and a patient representative, and its data protection officer reviews the data route. {ev['pilot']['go_no_go']}</p>
                  <p class="small">The limit to public data applies to the hackathon. AstraZeneca answered that in a real setting an integrated solution can have access to the relevant patient data.</p></div>
              </div>
              <p class="src">{name} is a planning tool for a county. It gives no advice about one patient.</p></section>""",

            f"""<section class="slide"><div class="eyebrow">Sources</div>
              <h2>Sources behind the slides.</h2>
              <ol class="sources">{''.join(f"<li>{sources[i]['title']}{' ' + sources[i]['url'] if (sources[i].get('url') or '').startswith('https://doi.org/') else ''}</li>" for i in [c['source'], 'survival_interval', t['source'], m['source'], 'roadmap', 'strategy', camp['attendance_source'], 'fcr_screening', 'virtanen_2011', 'virtanen_2010', 'az_discord_2026', 'local_step', 'campaign_rule'] if i in sources)}</ol>
              <p class="src">The app lists every source with its link in the view "Sources".</p></section>""",
        ]
        n = len(slides)
        pages = "".join(s.replace("</section>", f'<div class="bar"><span>{name} · AstraZeneca, Equal Care Across Finland</span><span>{i + 1} / {n}</span></div></section>')
                        for i, s in enumerate(slides))
        html = os.path.join(tmp, "deck.html")
        Path(html).write_text(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{name}</title>{STYLE}</head><body>{pages}</body></html>")
        subprocess.run([chrome(), "--headless", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                        f"--print-to-pdf={OUT}", "file://" + html], check=True, capture_output=True)
    print(f"{n} slides written to {OUT}")


STYLE = """
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
@page { size: 13.333in 7.5in; margin: 0; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font: 400 17pt/1.42 "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif; color: #0f2228; }
.slide { position: relative; width: 13.333in; height: 7.5in; padding: .55in .7in .75in; overflow: hidden; break-after: page; background: #ffffff; border-top: .09in solid #006f7e; }
.slide.dark { background: #0c2a32; color: #ffffff; border-top-color: #f0935a; padding-top: 1.7in; }
.eyebrow, .kicker { font: 600 12.5pt "IBM Plex Sans Condensed", Arial, sans-serif; letter-spacing: .09em; text-transform: uppercase; color: #4b5d65; }
.eyebrow::before { content: ""; display: inline-block; width: .13in; height: .13in; margin-right: .1in; background: #006f7e; }
.kicker { color: #9dcfd6; }
h1, h2 { font-family: "IBM Plex Sans Condensed", Arial, sans-serif; margin: 0; }
h1.title { font-size: 76pt; font-weight: 700; letter-spacing: .03em; text-transform: uppercase; line-height: 1; margin: .2in 0 .3in; }
h2 { font-size: 31pt; font-weight: 700; line-height: 1.12; margin: .1in 0 .28in; max-width: 11.4in; }
.lead { font-size: 25pt; line-height: 1.25; max-width: 10in; margin: 0; }
.foot { position: absolute; left: .7in; bottom: .9in; font-size: 14pt; color: #9dcfd6; margin: 0; }
.trio { display: grid; grid-template-columns: repeat(3, 1fr); gap: .3in; }
.fig { border: 1px solid #d2dadd; border-left: .08in solid #006f7e; padding: .22in .26in .26in; font-size: 14.5pt; line-height: 1.36; }
.fig.bad { border-left-color: #b8440d; }
.fig b { display: block; font: 600 32pt/1.1 "IBM Plex Mono", Menlo, monospace; letter-spacing: -.03em; margin-bottom: .12in; }
.fig.bad b { color: #b8440d; }
.say { font-size: 19pt; line-height: 1.34; margin: .32in 0 0; max-width: 11.6in; }
.src { position: absolute; left: .7in; right: .7in; bottom: .62in; margin: 0; font-size: 10pt; color: #4b5d65; }
.split { display: grid; grid-template-columns: 3.95in 1fr; gap: .35in; align-items: start; }
.split h2 { font-size: 23pt; }
.split .points { font-size: 13.5pt; }
.split .points.small { font-size: 12.5pt; }
.points { list-style: none; margin: 0; padding: 0; font-size: 14.5pt; line-height: 1.36; }
.points li { padding: .11in 0 .11in .26in; border-top: 1px solid #d2dadd; position: relative; }
.points li::before { content: ""; position: absolute; left: 0; top: .21in; width: .1in; height: .1in; background: #006f7e; }
.points b { font-weight: 600; }
figure { margin: 0; }
figure img { display: block; width: 100%; max-height: 5.75in; object-fit: contain; object-position: top left; border: 1px solid #9fafb6; }
figcaption { font-size: 10.5pt; color: #4b5d65; margin-top: .07in; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: .5in; }
.cols .points { font-size: 17pt; }
.cols.tight .points { font-size: 14pt; }
table { border-collapse: collapse; width: 100%; font-size: 16pt; line-height: 1.34; }
th { font: 600 11.5pt "IBM Plex Sans Condensed", Arial, sans-serif; letter-spacing: .08em; text-transform: uppercase; color: #4b5d65; text-align: left; border-bottom: 2px solid #0f2228; padding: 0 .2in .08in 0; }
td { border-bottom: 1px solid #d2dadd; padding: .12in .2in .12in 0; vertical-align: top; }
td:first-child { font-weight: 600; width: 2.9in; } td:nth-child(2) { font: 600 15pt "IBM Plex Mono", Menlo, monospace; width: .95in; color: #006f7e; }
.next { background: #edf1f2; border-left: .08in solid #006f7e; padding: .24in .3in; font-size: 15.5pt; line-height: 1.38; }
.next p { margin: .1in 0 0; } .small { font-size: 12pt; color: #4b5d65; }
.sources { margin: 0; padding-left: .3in; font-size: 10.5pt; line-height: 1.35; columns: 2; column-gap: .5in; }
.sources li { break-inside: avoid; margin-bottom: .07in; }
.bar { position: absolute; z-index: 2; left: .7in; right: .7in; bottom: .18in; min-height: .22in; display: flex; align-items: center; justify-content: space-between; font: 500 9.5pt "IBM Plex Mono", Menlo, monospace; color: #7a8a91; background: #ffffff; }
.dark .bar { color: #7fa3ab; background: #0c2a32; }
</style>"""

if __name__ == "__main__":
    main()
