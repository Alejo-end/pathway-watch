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
