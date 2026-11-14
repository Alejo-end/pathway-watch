"""Numbers traced to their raw source files, and sentences held to their facts."""

import json
import re
import types

import pytest

from backend import analysis as A
from backend import analyst, facts as F, nordcan
from backend.analyst import check, template
from backend.app import WEB, _briefing, data, headlines, mort, nc, svf
from backend.channel import channel
from backend.indicators import CANCERS, NATIONAL
from backend.recommend import MEASURES
from backend.sotkanet import RAW

REGION_ID = {r["code"]: r["id"] for r in json.loads((RAW / "regions.json").read_text())}


def raw_value(indicator: int, county: str, year: int) -> float:
    rows = json.loads((RAW / f"sotkanet_{indicator}.json").read_text())["rows"]
    return next(r["value"] for r in rows if r["region"] == REGION_ID[county] and r["year"] == year)


def all_briefings():
    return [(cancer, county, _briefing(cancer, county)) for cancer in CANCERS for county in data.counties]


# ---------- the sentence check ----------

FACTS = [F.Fact("a", "Päijät-Häme, survival, 2024: 63%", 63, "%", "s"),
         F.Fact("r", "Diagnosis took twice as long through public care", None, "", "roadmap")]


@pytest.mark.parametrize("sentence, kept", [
    ({"text": "Survival was 63% in 2024.", "fact_ids": ["a"]}, True),
    ({"text": "Survival was 61%.", "fact_ids": ["a"]}, False),             # a number the fact does not hold
    ({"text": "Things are bad.", "fact_ids": []}, False),                   # no source
    ({"text": "Survival was 63%.", "fact_ids": ["zzz"]}, False),            # unknown source
    ({"text": "Survival was 63%.", "fact_ids": ["a", "zzz"]}, False),       # one unknown source among known ones
    ({"text": "Diagnosis takes twice as long.", "fact_ids": ["r"]}, True),  # quantity word present in the fact
    ({"text": "Survival is half the national value.", "fact_ids": ["a"]}, False),  # quantity word not in the fact
])
def test_check(sentence, kept):
    assert bool(check([sentence], FACTS)[0]) is kept


def test_template_sentences_all_survive_the_check():
    for cancer, county, b in all_briefings():
        assert b["summary"]["removed"] == [], (cancer, county)
        assert len(b["summary"]["sentences"]) >= 2, (cancer, county)


def test_no_sentence_or_fact_averages_years_or_claims_where_a_gap_starts():
    for cancer, county, b in all_briefings():
        texts = [s["text"] for s in b["summary"]["sentences"]] + [f["text"] for f in b["facts"].values()]
        texts.append(b["pathway"]["reason"])
        for t in texts:
            assert "most likely" not in t.lower() and "confidence)" not in t, (cancer, county, t)
        # "average" stays only in the mortality facts, where deaths per year are a real average of pooled years.
        assert all("average" not in s["text"] for s in b["summary"]["sentences"]), (cancer, county)
        assert all("average" not in f["text"] for i, f in b["facts"].items() if not i.startswith("mort.")), (cancer, county)


def _fake_anthropic(stop_reason: str, text: str):
    """A stand-in for anthropic.Anthropic whose one call returns a fixed answer."""
    resp = types.SimpleNamespace(stop_reason=stop_reason, content=[types.SimpleNamespace(type="text", text=text)])
    messages = types.SimpleNamespace(create=lambda **kw: resp)
    return lambda *a, **kw: types.SimpleNamespace(beta=types.SimpleNamespace(messages=messages))


GOOD_ANSWER = json.dumps({"sentences": [{"text": "Survival was 63% in 2024.", "fact_ids": ["a"]}]})


@pytest.mark.parametrize("stop_reason, text, usable", [
    ("end_turn", GOOD_ANSWER, True),
    ("max_tokens", GOOD_ANSWER, False),      # cut off: the JSON may be incomplete
    ("refusal", "", False),
    ("end_turn", "not json at all", False),
    ("end_turn", '["a list, not an object"]', False),
])
def test_a_model_answer_that_stops_early_or_is_not_json_is_not_used(monkeypatch, stop_reason, text, usable):
    monkeypatch.setenv("PATHWAY_LLM", "1")
    monkeypatch.setattr("anthropic.Anthropic", _fake_anthropic(stop_reason, text))
    drafted = analyst.llm_sentences(FACTS)
    assert (drafted is not None) is usable
    pathway = A.locate(data, "bowel", "06")
    fact_list = F.survival_and_screening_facts(data, "bowel", "06") + F.pathway_and_action_facts(pathway, [])
    out = analyst.summarize(data, "bowel", "06", pathway, [], fact_list)
    # The good answer cites a fact this briefing does not have, so the template takes over in every case.
    assert out["writer"] == "template" and out["sentences"]


def test_a_model_draft_that_fails_the_check_falls_back_to_the_template(monkeypatch):
    monkeypatch.setattr(analyst, "llm_sentences", lambda facts: [{"text": "Survival fell by 99 points.", "fact_ids": ["pathway"]}])
    pathway = A.locate(data, "bowel", "09")
    fact_list = F.survival_and_screening_facts(data, "bowel", "09") + F.pathway_and_action_facts(pathway, [])
    out = analyst.summarize(data, "bowel", "09", pathway, [], fact_list)
    assert out["writer"] == "template" and out["sentences"]
    assert out["removed"][0]["text"] == "Survival fell by 99 points."


# ---------- every ID resolves ----------

def test_every_fact_names_a_known_source_and_every_cited_fact_exists():
    sources = data.sources()
    for cancer, county, b in all_briefings():
        assert all(f["source"] in sources for f in b["facts"].values())
        cited = [i for s in b["summary"]["sentences"] for i in s["fact_ids"]]
        cited += [i for r in b["recommendations"] for i in r["evidence"]]
        cited.append(b["goal3"]["target_fact"])
        assert all(i in b["facts"] for i in cited), (cancer, county)
        assert all(r["measure"] in MEASURES for r in b["recommendations"])
        assert all(m["source"] in sources for m in b["missing"])


def test_every_source_the_page_cites_by_name_exists():
    cited = set(re.findall(r'cite\("([^"]+)"\)', (WEB / "index.html").read_text()))
    assert cited, "the pattern found no citations, so this test would pass on anything"
    assert cited <= set(data.sources())


# ---------- numbers traced to the raw files ----------

def test_survival_and_screening_facts_equal_the_raw_sotkanet_values():
    seen = 0
    for cancer in ("bowel", "breast", "cervical"):
        for f in F.survival_and_screening_facts(data, cancer, "09"):
            m = re.fullmatch(r"(\d+)\.county\.(\d+)", f.id)
            if m:
                assert f.value == raw_value(int(m[1]), "09", int(m[2]))
                seen += 1
    assert seen == 6  # survival and screening for three cancers


def test_headline_screening_values_equal_the_raw_minimum():
    for h, ind in zip(headlines()["screening"], (6103, 3621)):
        raw = min(raw_value(ind, c, h["year"]) for c in data.counties)
        assert h["value"] == raw
        assert h["below_target"] == sum(raw_value(ind, c, h["year"]) < h["target"] for c in data.counties)


def test_helsinki_has_the_lowest_breast_screening_attendance_in_every_published_year():
    bowel, breast = headlines()["screening"]
    assert breast["lowest"] == "Helsinki"
    assert breast["lowest_years"] == breast["n_years"] >= 6
    years = sorted(data.series(3621, "90"))
    assert (breast["first_year"], breast["year"], breast["n_years"]) == (years[0], years[-1], len(years))
    for y in years:
        assert raw_value(3621, "90", y) == min(raw_value(3621, c, y) for c in data.counties)
    # Bowel screening is different: Helsinki is lowest in the latest year, but not in every year.
    assert bowel["lowest"] == "Helsinki" and bowel["lowest_years"] < bowel["n_years"]


def test_satakunta_bowel_survival_is_below_finland_in_every_published_year():
    g = A.gap(data, 3627, "06")
    assert data.names["06"] == "Satakunta"
    assert (g.direction, g.persistence) == ("below", "persistent")
    assert g.years_same_side == len(g.years) == 6 and (g.years[0], g.year) == (2019, 2024)
    assert g.gap == raw_value(3627, "06", 2024) - data.series(3627, NATIONAL)[2024]
    b = _briefing("bowel", "06")
    assert (b["pathway"]["step"], b["pathway"]["evidence"]) == ("later", "persistent")
    assert b["recommendations"][0]["measure"] == "2.5.2"
    assert b["facts"]["pathway"]["text"].startswith("Question to investigate:")


def test_map_layer_gives_the_latest_year_gap_and_the_persistence():
    from backend.app import map_layer
    d = map_layer(3627)["counties"]["06"]
    assert (d["latest"], d["year"], d["gap"], d["direction"]) == (64, 2024, -4.0, "below")
    assert (d["persistence"], d["years_same_side"], d["n_years"]) == ("persistent", 6, 6)
    assert "confidence" not in d


def test_channel_share_equals_the_raw_visit_counts():
    c = channel(data, "16")
    pub, occ = raw_value(293, "16", c["year"]), raw_value(2371, "16", c["year"])
    assert (c["public_visits"], c["occupational_visits"]) == (pub, occ)
    assert c["public_share"] == round(100 * pub / (pub + occ), 1)


def test_mortality_observed_deaths_equal_the_raw_statfin_counts():
    raw = json.loads((RAW / "statfin_mortality.json").read_text())
    m = mort.smr("lung", "21")
    assert m.observed == sum(raw["county_deaths"]["21"]["11"][str(y)] for y in m.years)


def test_national_smr_is_100_and_county_populations_add_up_to_the_national_one():
    assert mort.smr("all", NATIONAL).smr == 100
    for y in mort.years:
        counties = sum(sum(mort.pop[c][str(y)].values()) for c in mort.pop if c != NATIONAL)
        assert counties == sum(mort.pop[NATIONAL][str(y)].values())


def test_byar_interval_contains_the_ratio():
    from backend.mortality import byar
    low, high = byar(120, 100)
    assert 95 < low < 120 < high


def test_hand_read_swedish_regions_reproduce_the_published_national_share():
    """The 21 regional shares, weighted by their patient counts, must give the national 47%."""
    regions = svf["regions"].values()
    assert len(regions) == 21
    assert sum(r["n2025"] for r in regions) == svf["national"]["2025"]["n"]
    weighted = sum(r["2025"] * r["n2025"] for r in regions) / svf["national"]["2025"]["n"]
    assert abs(weighted - svf["national"]["2025"]["share"]) < 1


def test_nordic_level_is_the_mean_of_sweden_and_norway_and_needs_both():
    site = {"finland-246": {"male": {"cases": 100, "surv5": 60.0}, "female": {"cases": 300, "surv5": 70.0}},
            "sweden-752": {"female": {"cases": 10, "surv5": 80.0}}, "norway-578": None}
    sample = {"sites": {"x": site}}
    assert nordcan.combined(sample, "x", "finland") == {"cases": 400, "surv5": 67.5}
    assert nordcan.benchmark(sample, "x")["nordic"] is None
    site["norway-578"] = {"female": {"cases": 10, "surv5": 70.0}}
    b = nordcan.benchmark(sample, "x")
    assert (b["nordic"], b["gap"]) == (75.0, -7.5)


def test_every_cancer_in_the_picker_has_a_nordic_level():
    assert all(nordcan.benchmark(nc, c)["gap"] is not None for c in CANCERS)


# ---------- the API ----------

def test_every_endpoint_answers_for_every_county_and_cancer():
    from fastapi.testclient import TestClient
    from backend.app import app
    client = TestClient(app)
    for url in ("/", "/counties.geojson", "/api/meta", "/api/headlines", "/api/channel-map",
                "/api/map/3627", "/api/map/6103", "/api/mortality-map/lung", "/api/mortality-map/all",
                "/api/national/bowel", "/api/national/lung"):
        assert client.get(url).status_code == 200, url
    for cancer in CANCERS:
        for county in data.counties:
            b = client.get(f"/api/county/{county}?cancer={cancer}").json()
            assert b["chart"]["county"] and b["simulation"]["steps"], (cancer, county)
    assert client.get("/api/county/99").status_code == 404
    assert client.get("/api/county/09?cancer=x").status_code == 404
    assert client.get("/api/map/1").status_code == 404


# ---------- recommendations and the national ranking ----------

def test_every_measure_says_who_acts_how_to_start_and_what_success_is():
    sources = data.sources()
    for mid, m in MEASURES.items():
        assert m["level"] in ("account", "national", "both"), mid
        assert m["first_step"] and m["success"] and m["page"], mid
        assert m["success_source"] in sources, mid


def test_low_screening_first_asks_who_does_not_attend_and_does_not_presume_a_cause():
    """The cause of low attendance is not known, so the first action is to find the groups, not to target one."""
    for cancer, county, b in all_briefings():
        if b["pathway"]["step"] in ("detection", "watch"):
            assert [r["measure"] for r in b["recommendations"]][:2] == ["2.4.5", "1.3.1"], (cancer, county)
    assert MEASURES["1.3.1"]["action"].startswith("If language groups are among")
    assert _briefing("breast", "90")["recommendations"][0]["measure"] == "2.4.5"  # Helsinki


def test_the_strategy_and_the_roadmap_have_public_links():
    sources = data.sources()
    assert sources["strategy"]["url"].endswith("Kansallinen_syopastrategia_2026_2035_FINAL.pdf")
    assert sources["roadmap"]["url"].endswith("toimeenpanon_tiekartta_2026_2031.pdf")


def test_ranking_puts_counties_behind_in_more_registers_first():
    from backend.priorities import ranking
    r = ranking(data, mort, "bowel")
    registers = [row["registers"] for row in r["rows"]]
    assert registers == sorted(registers, reverse=True)
    assert len(r["rows"]) + r["without_signal"] == len(data.counties)
    assert sum(r["by_measure"].values()) == len(r["rows"])
    sources = data.sources()
    assert all(s["source"] in sources for row in r["rows"] for s in row["signals"])


def test_a_signal_needs_a_persistent_gap_and_deaths_count_as_one_register():
    from backend.priorities import ranking, signals
    for cancer in CANCERS:
        for row in ranking(data, mort, cancer)["rows"]:
            kinds = {s["kind"].split(":")[0] for s in row["signals"]}
            assert row["registers"] == len(kinds) <= 3
            for s in row["signals"]:
                if s["kind"] in ("survival", "screening"):
                    g = A.gap(data, CANCERS[cancer][s["kind"]], row["code"])
                    assert (g.direction, g.persistence) == ("below", "persistent"), (cancer, row["name"])
    # Päijät-Häme, bowel cancer: survival is below Finland in 4 of 6 years, screening is not below.
    kinds = [s["kind"] for s in signals(data, mort, "bowel", "09")]
    assert "survival" in kinds and "screening" not in kinds
    # Helsinki, breast cancer: survival is 1 point below in 2024 but was not below in most years, so it is no signal.
    assert "survival" not in [s["kind"] for s in signals(data, mort, "breast", "90")]
