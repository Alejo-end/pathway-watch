"""The gap, its persistence, the pathway rule and the simulation."""

from backend import analysis as A
from backend.indicators import NATIONAL
from backend.sotkanet import CountyData

FLAT = {2022: 70, 2023: 70, 2024: 70}


def make(values, county="09"):
    """A small in-memory data set: values = {indicator: {region: {year: value}}}."""
    return CountyData(values, {NATIONAL: "Finland", county: "Testland"}, {NATIONAL: 1000, county: 100}, {}, {})


def test_gap_is_the_latest_year_difference_and_not_an_average():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 60, 2023: 62, 2024: 67}}})
    g = A.gap(d, 1, "09")
    assert (g.year, g.county_value, g.national_value, g.gap, g.direction) == (2024, 67, 70, -3.0, "below")
    assert g.gap != round((60 + 62 + 67) / 3 - 70, 1)


def test_persistent_when_on_the_same_side_in_most_years():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 65, 2023: 70, 2024: 64}}})
    g = A.gap(d, 1, "09")
    assert (g.years_same_side, g.persistence) == (2, "persistent")


def test_mixed_when_the_latest_side_is_not_the_usual_side():
    nat = {y: 70 for y in range(2019, 2025)}
    d = make({1: {NATIONAL: nat, "09": {2019: 75, 2020: 74, 2021: 73, 2022: 66, 2023: 65, 2024: 64}}})
    g = A.gap(d, 1, "09")
    assert (g.direction, g.years_same_side, len(g.years), g.persistence) == ("below", 3, 6, "mixed")


def test_short_with_fewer_than_three_shared_years_and_for_no_data():
    d = make({1: {NATIONAL: {2023: 70, 2024: 70}, "09": {2023: 60, 2024: 60}}})
    assert A.gap(d, 1, "09").persistence == "short"
    g = A.gap(make({1: {NATIONAL: FLAT}}), 1, "09")
    assert (g.year, g.gap, g.direction, g.persistence) == (None, None, "unknown", "short")


def test_a_county_that_matches_finland_every_year_is_near_and_persistent():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 70, 2023: 70.5, 2024: 69.5}}})
    g = A.gap(d, 1, "09")
    assert (g.direction, g.years_same_side, g.persistence) == ("near", 3, "persistent")


def test_a_near_latest_year_after_years_that_swing_both_ways_is_mixed():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 75, 2023: 65, 2024: 70.5}}})
    g = A.gap(d, 1, "09")
    assert (g.direction, g.years_same_side, g.persistence) == ("near", 1, "mixed")


def test_gap_counts_every_shared_year():
    d = make({1: {NATIONAL: {2019: 50, **FLAT}, "09": {2019: 10, 2021: 99, **FLAT}}})
    assert A.gap(d, 1, "09").years == [2019, 2022, 2023, 2024]


def test_gap_refuses_an_indicator_that_is_not_loaded():
    import pytest
    with pytest.raises(KeyError):
        A.gap(make({1: {NATIONAL: FLAT}}), None, "09")


def test_pathway_rule():
    low = {"09": {2022: 60, 2023: 60, 2024: 60}}
    ok = {"09": {2022: 72, 2023: 72, 2024: 72}}

    def step(survival, screening):
        d = make({3627: {NATIONAL: FLAT, **survival}, 6103: {NATIONAL: FLAT, **screening}})
        return A.locate(d, "bowel", "09").step

    assert step(low, low) == "detection"
    assert step(low, ok) == "later"
    assert step(ok, low) == "watch"
    assert step(ok, ok) == "none"


def test_pathway_is_a_question_and_carries_the_weaker_evidence():
    nat = {y: 70 for y in range(2019, 2025)}
    low = {"09": {y: 60 for y in range(2019, 2025)}}
    newly_low = {"09": {2019: 75, 2020: 75, 2021: 75, 2022: 75, 2023: 60, 2024: 60}}
    p = A.locate(make({3627: {NATIONAL: nat, **low}, 6103: {NATIONAL: nat, **newly_low}}), "bowel", "09")
    assert (p.step, p.evidence) == ("detection", "mixed")
    assert "raises a question" in p.reason and "most likely" not in p.reason
    p = A.locate(make({3627: {NATIONAL: nat, **low}, 6103: {NATIONAL: nat}}), "bowel", "09")
    assert (p.step, p.evidence) == ("later", "short")  # no screening data for the county


def test_lung_cancer_step_comes_from_national_evidence():
    p = A.locate(make({}), "lung", "09")
    assert (p.step, p.evidence) == ("national", "national")


def test_simulation():
    assert A.simulate(100, 63, 68) == 5
    assert A.simulate(100, 70, 68) == 0
    assert A.simulate(100, 63, 68, share=0.5) == 2
    assert A.simulate(None, 63, 68) is None


def test_simulation_steps_cover_the_slider_and_agree_with_simulate():
    steps = A.simulation_steps(148, 63, 68)
    assert len(steps["survivors"]) == len(steps["reached"]) == 101
    assert steps["survivors"][0] == 0 and steps["survivors"][100] == A.simulate(148, 63, 68)
    assert steps["reached"][0] == 63 and steps["reached"][100] == 68
    assert A.simulation_steps(None, 63, 68) is None


def test_estimated_cases_split_by_population_share():
    c = A.estimated_cases(make({}), "09", 1000, "test", "nordcan")
    assert c["value"] == 100 and c["status"] == "estimate"
    assert A.estimated_cases(make({}), "09", None, "test", "nordcan")["value"] is None
