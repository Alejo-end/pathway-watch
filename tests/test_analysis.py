"""Every number traced to a source. No sentence without a source."""

import json

import pytest

from backend import analysis as A
from backend.analyst import check, extra_facts, template
from backend.indicators import CANCERS, NATIONAL
from backend.recommend import MEASURES, recommend


@pytest.fixture(scope="module")
def data():
    return A.load()


def make(values, county="09"):
    """Tiny in-memory data set: values = {indicator: {region: {year: value}}}."""
    names = {NATIONAL: "Finland", county: "Testland"}
    return A.Data(values, names, {NATIONAL: 1000, county: 100}, {}, {},
                  {"national_new_cases_per_year": {"bowel": {"value": 1000, "source": "cancer_registry", "status": "approximate"}}})


def test_gap_high_confidence_when_below_all_three_years():
    d = make({3627: {NATIONAL: {2022: 70, 2023: 70, 2024: 70}, "09": {2022: 65, 2023: 66, 2024: 64}}})
    g = A.gap(d, 3627, "09")
    assert g.avg_gap == -5.0 and g.direction == "below" and g.confidence == "high"


def test_gap_medium_and_low_confidence():
    d = make({1: {NATIONAL: {2022: 70, 2023: 70, 2024: 70}, "09": {2022: 65, 2023: 70, 2024: 64}}})
    assert A.gap(d, 1, "09").confidence == "medium"
    d = make({1: {NATIONAL: {2023: 70, 2024: 70}, "09": {2023: 60, 2024: 60}}})
    assert A.gap(d, 1, "09").confidence == "low"  # only two years


def test_gap_uses_last_three_shared_years():
    d = make({1: {NATIONAL: {2019: 50, 2022: 70, 2023: 70, 2024: 70}, "09": {2019: 10, 2022: 70, 2023: 70, 2024: 70}}})
    g = A.gap(d, 1, "09")
    assert g.years == [2022, 2023, 2024] and g.direction == "near"


def test_pathway_rule():
    base = {NATIONAL: {2022: 70, 2023: 70, 2024: 70}}
    low = {"09": {2022: 60, 2023: 60, 2024: 60}}
    ok = {"09": {2022: 72, 2023: 72, 2024: 72}}
    d = make({3627: {**base, **low}, 6103: {**base, **low}})
    assert A.locate(d, "bowel", "09").step == "detection"
    d = make({3627: {**base, **low}, 6103: {**base, **ok}})
    assert A.locate(d, "bowel", "09").step == "later"
    d = make({3627: {**base, **ok}, 6103: {**base, **low}})
    assert A.locate(d, "bowel", "09").step == "watch"
    d = make({3627: {**base, **ok}, 6103: {**base, **ok}})
    assert A.locate(d, "bowel", "09").step == "none"


def test_simulation():
    assert A.simulate(100, 63, 68) == 5
    assert A.simulate(100, 70, 68) == 0
    assert A.simulate(100, 63, 68, share=0.5) == 2
    assert A.simulate(None, 63, 68) is None


def test_check_removes_sentences_without_source_or_with_new_numbers():
    facts = [A.Fact("a", "Survival was 63% in 2024", 63, "%", "sotkanet:3627")]
    kept, removed = check([
        {"text": "Survival was 63% in 2024.", "fact_ids": ["a"]},
        {"text": "Survival was 61%.", "fact_ids": ["a"]},
        {"text": "Things are bad.", "fact_ids": []},
        {"text": "Survival was 63%.", "fact_ids": ["zzz"]},
    ], facts)
    assert [s["text"] for s in kept] == ["Survival was 63% in 2024."]
    assert len(removed) == 3


@pytest.mark.parametrize("cancer", list(CANCERS))
def test_every_template_sentence_survives_the_check_for_every_county(data, cancer):
    sources = data.sources()
    for county in data.counties:
        p = A.locate(data, cancer, county)
        recs = recommend(data, p, county)
        facts = A.facts_for(data, cancer, county) + extra_facts(p, recs)
        assert all(f.source in sources for f in facts), "every fact names a known source"
        sentences = template(data, cancer, county, p, recs)
        kept, removed = check(sentences, facts)
        assert removed == [], (county, removed)
        assert kept


def test_facts_match_raw_api_values(data):
    """A fact value equals the value in the cached Sotkanet response."""
    raw = json.loads((A.RAW / "sotkanet_3627.json").read_text())
    regions = json.loads((A.RAW / "regions.json").read_text())
    rid = next(r["id"] for r in regions if r["code"] == "09")
    for f in A.facts_for(data, "bowel", "09"):
        if f.id.startswith("3627.county."):
            year = int(f.id.rsplit(".", 1)[1])
            row = next(r for r in raw["rows"] if r["region"] == rid and r["year"] == year)
            assert f.value == row["value"]


def test_recommendations_cite_known_measures(data):
    for county in data.counties:
        for cancer in CANCERS:
            for r in recommend(data, A.locate(data, cancer, county), county):
                assert r["measure"] in MEASURES and r["source"] == "roadmap"


def test_mortality_national_smr_is_100_and_population_adds_up():
    from backend.mortality import Mortality
    m = Mortality()
    assert m.smr("all", NATIONAL).smr == 100
    for y in m.years:
        counties = sum(sum(m.pop[c][str(y)].values()) for c in m.pop if c != NATIONAL)
        assert counties == sum(m.pop[NATIONAL][str(y)].values())


def test_byar_interval_contains_the_ratio():
    from backend.mortality import byar
    low, high = byar(120, 100)
    assert low < 120 < high and low > 95


def test_mortality_facts_cite_statfin(data):
    from backend.mortality import Mortality
    facts = A.mortality_facts(data, Mortality(), "bowel", "06")
    assert {f.source for f in facts} == {"statfin_mortality"}
    assert any(f.id == "mort.lung" for f in facts)


def test_nordcan_benchmark_needs_both_sweden_and_norway():
    from backend import nordcan
    nc = {"sites": {"x": {
        "finland-246": {"male": {"cases": 100, "surv5": 60.0}, "female": {"cases": 300, "surv5": 70.0}},
        "sweden-752": {"female": {"cases": 10, "surv5": 80.0}},
        "norway-578": None}}}
    assert nordcan.combined(nc, "x", "finland") == {"cases": 400, "surv5": 67.5}
    b = nordcan.benchmark(nc, "x")
    assert b["nordic"] is None and b["sweden"] == 80.0
    nc["sites"]["x"]["norway-578"] = {"female": {"cases": 10, "surv5": 70.0}}
    b = nordcan.benchmark(nc, "x")
    assert b["nordic"] == 75.0 and b["gap"] == -7.5


def test_channel_share_and_facts(data):
    from backend.channel import channel, channel_facts
    c = channel(data, "09")
    assert c["public_share"] == round(100 * c["public_visits"] / (c["public_visits"] + c["occupational_visits"]), 1)
    facts = channel_facts(data, "09")
    assert {f.source for f in facts} <= set(data.sources())


def test_svf_file_is_complete():
    import json
    svf = json.loads((A.ROOT / "data" / "svf_sweden.json").read_text())
    assert len(svf["regions"]) == 21
    assert all(0 < r["2025"] <= 100 for r in svf["regions"].values())


def test_headlines_cite_known_sources():
    from backend.app import data as appdata, headlines
    h = headlines()
    sources = appdata.sources()
    assert all(s["source"] in sources for s in h["screening"])
    assert h["nordic"] and all(b["gap"] is not None for b in h["nordic"])
    assert h["mirror"]["regions"] == 21
