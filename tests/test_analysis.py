"""The gap, its confidence, the pathway rule and the simulation."""

from backend import analysis as A
from backend.indicators import NATIONAL
from backend.sotkanet import CountyData

FLAT = {2022: 70, 2023: 70, 2024: 70}


def make(values, county="09"):
    """A small in-memory data set: values = {indicator: {region: {year: value}}}."""
    return CountyData(values, {NATIONAL: "Finland", county: "Testland"}, {NATIONAL: 1000, county: 100}, {}, {})


def test_gap_high_confidence_when_below_all_three_years():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 65, 2023: 66, 2024: 64}}})
    g = A.gap(d, 1, "09")
    assert (g.avg_gap, g.direction, g.confidence) == (-5.0, "below", "high")


def test_gap_medium_when_one_year_disagrees_and_low_with_two_years_of_data():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 65, 2023: 70, 2024: 64}}})
    assert A.gap(d, 1, "09").confidence == "medium"
    d = make({1: {NATIONAL: {2023: 70, 2024: 70}, "09": {2023: 60, 2024: 60}}})
    assert A.gap(d, 1, "09").confidence == "low"


def test_a_county_that_matches_finland_every_year_is_near_with_high_confidence():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 70, 2023: 70.5, 2024: 69.5}}})
    g = A.gap(d, 1, "09")
    assert (g.direction, g.confidence) == ("near", "high")


def test_a_near_average_from_years_that_swing_both_ways_has_low_confidence():
    d = make({1: {NATIONAL: FLAT, "09": {2022: 75, 2023: 65, 2024: 70.5}}})
    g = A.gap(d, 1, "09")
    assert (g.direction, g.confidence) == ("near", "low")


def test_gap_uses_last_three_shared_years():
    d = make({1: {NATIONAL: {2019: 50, **FLAT}, "09": {2019: 10, **FLAT}}})
    assert A.gap(d, 1, "09").years == [2022, 2023, 2024]


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


def test_lung_cancer_step_comes_from_national_evidence():
    assert A.locate(make({}), "lung", "09").step == "national"


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
