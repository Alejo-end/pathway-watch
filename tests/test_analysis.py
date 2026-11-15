"""The gap, its persistence, the rough interval, the pathway rule and the simulation."""

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


LOW = {"09": {2022: 60, 2023: 60, 2024: 60}}
OK = {"09": {2022: 72, 2023: 72, 2024: 72}}


def step(cancer, survival, screening):
    spec = A.CANCERS[cancer]
    d = make({spec["survival"]: {NATIONAL: FLAT, **survival}, spec["screening"]: {NATIONAL: FLAT, **screening}})
    return A.locate(d, cancer, "09").step


def test_pathway_rule_for_a_cancer_with_an_old_screening_programme():
    assert step("breast", LOW, LOW) == "detection"
    assert step("breast", LOW, OK) == "later"
    assert step("breast", OK, LOW) == "watch"
    assert step("breast", OK, OK) == "none"


def test_bowel_survival_gap_ignores_screening_because_the_programme_is_newer_than_the_diagnoses():
    """National bowel screening started in 2022. A 2024 survival value covers diagnoses from 2015 to 2024."""
    assert A.screening_is_too_new("bowel", 2024) and not A.screening_is_too_new("breast", 2024)
    assert not A.screening_is_too_new("bowel", 2031)  # the first value whose ten years all lie in the programme
    assert step("bowel", LOW, LOW) == step("bowel", LOW, OK) == "any"
    assert step("bowel", OK, LOW) == "watch"  # low attendance in the new programme is still an early warning
    assert step("bowel", OK, OK) == "none"
    d = make({3627: {NATIONAL: FLAT, **LOW}, 6103: {NATIONAL: FLAT, **LOW}})
    p = A.locate(d, "bowel", "09")
    assert p.label == "Detection, referral, diagnosis or treatment"
    assert "cannot tell which step" in p.reason and "attendance" not in p.reason
    assert any("started in 2022" in c for c in p.caveats)


def test_rough_interval_from_a_hand_made_case():
    """50% survival from 10 cases a year: n = 100, binomial standard error 5 points, 5.02 with the rounding."""
    iv = A.rough_interval(50, 60, 10)
    assert (iv.patients, iv.cases_per_year, iv.se) == (100, 10, 5.0)
    assert (iv.low, iv.high, iv.excludes_zero) == (-19.8, -0.2, True)
    wide = A.rough_interval(50, 55, 10)
    assert (wide.low, wide.high, wide.excludes_zero) == (-14.8, 4.8, False)
    assert A.rough_interval(None, 60, 10) is None and A.rough_interval(50, 60, None) is None


def test_a_one_point_gap_never_excludes_zero_because_the_values_are_rounded():
    iv = A.rough_interval(91, 92, 618)  # Helsinki, breast cancer: many patients, one point below
    assert not iv.excludes_zero and iv.high > 0


def test_pathway_is_a_question_and_its_evidence_is_the_interval_or_the_weaker_attendance():
    nat = {y: 70 for y in range(2019, 2025)}
    low = {"09": {y: 60 for y in range(2019, 2025)}}
    newly_low = {"09": {2019: 75, 2020: 75, 2021: 75, 2022: 75, 2023: 60, 2024: 60}}
    p = A.locate(make({3625: {NATIONAL: nat, **low}, 3621: {NATIONAL: nat, **low}}), "breast", "09")
    assert (p.step, p.evidence) == ("detection", "interval_excludes_zero")
    assert "raises a question" in p.reason and "most likely" not in p.reason
    p = A.locate(make({3625: {NATIONAL: nat, **low}, 3621: {NATIONAL: nat, **newly_low}}), "breast", "09")
    assert (p.step, p.evidence) == ("detection", "mixed")  # attendance was below in 2 of 6 years
    p = A.locate(make({3625: {NATIONAL: nat, **low}, 3621: {NATIONAL: nat}}), "breast", "09")
    assert (p.step, p.evidence) == ("later", "short")  # no attendance data for the county
    slightly_low = {"09": {y: 68.5 for y in range(2019, 2025)}}
    p = A.locate(make({3625: {NATIONAL: nat, **slightly_low}, 3621: {NATIONAL: nat, **low}}), "breast", "09")
    assert (p.step, p.evidence) == ("detection", "interval_includes_zero")


def test_the_lowest_county_gets_the_regression_to_the_mean_caveat():
    d = make({3625: {NATIONAL: FLAT, **LOW}, 3621: {NATIONAL: FLAT, **OK}})
    assert any("tends to look less extreme" in c for c in A.locate(d, "breast", "09").caveats)


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


def test_estimated_cases_use_the_age_share_and_fall_back_to_the_population_share():
    c = A.estimated_cases(make({}), "09", 1000, "test", "nordcan")
    assert (c["value"], c["status"], c["basis"]) == (100, "estimate", "population")
    assert "ignores the age structure" in c["limit"]
    aged = A.estimated_cases(make({}), "09", 1000, "test", "nordcan", age_share=0.13)
    assert (aged["value"], aged["basis"]) == (130, "age structure")
    assert "13.0%" in aged["method"] and "10.0%" in aged["method"] and "stands in" in aged["limit"]
    assert A.estimated_cases(make({}), "09", None, "test", "nordcan")["value"] is None


def test_the_strict_interval_of_a_hand_made_case():
    """Standard error 5.02 points: 1.96 of them is 9.8, and the limit for 22 comparisons (3.05) is 15.3."""
    iv = A.rough_interval(50, 60, 10, comparisons=22)
    assert (iv.low, iv.high, iv.excludes_zero) == (-19.8, -0.2, True)
    assert (iv.strict_low, iv.strict_high, iv.strict_excludes_zero) == (-25.3, 5.3, False)
    one = A.rough_interval(50, 60, 10)
    assert (one.strict_low, one.strict_high) == (one.low, one.high)  # one comparison: the same limit


def test_a_survival_gap_is_read_against_deaths_from_the_same_cancer():
    """The cached Statistics Finland deaths: Satakunta has extra bowel cancer deaths, Päijät-Häme does not,
    and North Karelia has too few cervical cancer deaths for an SMR to confirm anything."""
    assert A.deaths_check("bowel", "06")[0] == "agree"
    status, sentence = A.deaths_check("bowel", "09")
    assert status == "not_confirmed" and "stage at diagnosis" in sentence
    assert A.deaths_check("cervical", "14")[0] == "too_few"
    assert A.deaths_check("prostate", "09") is None
    from backend.sotkanet import load
    p = A.locate(load(), "bowel", "09")
    assert p.deaths == "not_confirmed" and any(c.startswith("Deaths do not confirm") for c in p.caveats)


def test_the_lung_screening_pilot_is_not_judged_by_survival():
    """Screening moves a diagnosis earlier, so five-year survival rises with no death avoided (lead time)."""
    from backend.recommend import MEASURES
    success = MEASURES["2.3.4"]["success"]
    assert "stage I or II" in success and "deaths" in success
    assert not success.startswith("Five-year")
