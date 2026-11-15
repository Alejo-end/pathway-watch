"""The screening campaign: the size comes from the raw Sotkanet rows, and no rule reads health data."""

import json

from backend.app import data
from backend.campaign import NOT_USED, ORDER, PERSON_RULES, PROGRAMMES, TARGET, campaign, size
from backend.indicators import CANCERS
from backend.sotkanet import RAW

HELSINKI, SATAKUNTA = "90", "06"


def raw_row(indicator: int, county: str, year: int) -> dict:
    region = next(r["id"] for r in json.loads((RAW / "regions.json").read_text()) if r["code"] == county)
    rows = json.loads((RAW / f"sotkanet_{indicator}.json").read_text())["rows"]
    return next(r for r in rows if r["region"] == region and r["year"] == year)


def test_the_size_reproduces_the_raw_count_and_share():
    for cancer, spec in CANCERS.items():
        if spec["screening"] is None:
            continue
        for county in data.counties:
            c = campaign(data, cancer, county)
            row = raw_row(spec["screening"], county, c["year"])
            assert c["attendance"] == row["value"] and c["size"]["attended"] == row["absValue"], (cancer, county)
            s = c["size"]
            # The invited are attended / share, so attended / invited gives the share back, within the rounding to tens.
            assert abs(s["attended"] / s["invited"] * 100 - row["value"]) < 0.1, (cancer, county)
            assert abs(s["invited"] - s["attended"] - s["not_attended"]) <= 10


def test_a_campaign_runs_only_below_the_target_and_then_names_how_many_more_people_it_needs():
    for cancer, spec in CANCERS.items():
        if spec["screening"] is None:
            continue
        for county in data.counties:
            c = campaign(data, cancer, county)
            below = c["attendance"] < TARGET
            assert c["status"] == ("campaign" if below else "target met")
            assert c["county_rule"]["met"] is below
            assert (c["size"]["needed"] > 0) is below, (cancer, county, c["size"])


def test_size_by_hand():
    assert size(700, 70.0) == {"attended": 700, "invited": 1000, "not_attended": 300, "needed": 100}
    assert size(850, 85.0)["needed"] == 0


def test_a_county_just_below_the_target_never_needs_zero_people():
    assert size(796, 79.6)["needed"] == 10
    assert size(7994, 79.96)["needed"] == 10


def test_every_count_comes_with_the_limit_that_tests_outside_the_programme_are_not_counted():
    sources = data.sources()
    for cancer, p in PROGRAMMES.items():
        c = campaign(data, cancer, SATAKUNTA)
        assert "is not counted" in c["outside"]["text"] and c["outside"]["source"] in sources, cancer
        assert "in the programme" in PERSON_RULES[2]["rule"]
        assert c["steps"][0]["title"] == "Plan the follow-up tests" and p["follow_up"], cancer


def test_breast_campaign_reminds_only_after_the_link_that_the_first_action_asks_for():
    assert "no mammogram in either place" in PROGRAMMES["breast"]["reminder"]


def test_helsinki_bowel_is_a_campaign_and_lung_has_none():
    assert campaign(data, "bowel", HELSINKI)["status"] == "campaign"
    lung = campaign(data, "lung", SATAKUNTA)
    assert lung["status"] == "no programme" and "size" not in lung


def test_no_rule_reads_health_or_income_data():
    fields = " ".join(r["field"] + " " + r["register"] for r in PERSON_RULES + [ORDER]).lower()
    for word in ("diagnos", "medicine", "laborator", "visit", "income", "education", "language", "kanta"):
        assert word not in fields, word
    assert {"diagnoses", "income", "education"} <= set(NOT_USED)


def test_every_campaign_source_exists():
    sources = data.sources()
    for cancer in CANCERS:
        c = campaign(data, cancer, SATAKUNTA)
        ids = [c["source"]] + [c[k] for k in ("programme_source", "attendance_source", "target_source") if k in c]
        if "order" in c:
            ids += [c["order"]["evidence_source"], c["evidence"]["source"], c["outside"]["source"]]
        assert all(i in sources for i in ids), (cancer, ids)
