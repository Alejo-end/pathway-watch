"""The step timeline, the county pilot, the equity panel and the local steps."""

from fastapi.testclient import TestClient

from backend import equity, timeline
from backend.app import app, data
from backend.recommend import LOCAL_STEPS, MEASURES, local_step

client = TestClient(app)


def test_the_timeline_matches_figure_1_of_the_paper():
    t = timeline.build()
    assert [s["public_cumulative"] for s in t["steps"]] == [72, 94, 147, 204, 207]
    assert [s["private_cumulative"] for s in t["steps"]] == [42, 43, 77, 118, 123]
    assert t["total"] == {"public": 207, "private": 123, "extra": 84}


def test_the_steps_add_up_to_the_whole_interval():
    t = timeline.build()
    assert sum(s["public_days"] for s in t["steps"]) == t["total"]["public"]
    assert sum(s["private_days"] for s in t["steps"]) == t["total"]["private"]
    assert sum(s["extra"] for s in t["steps"]) == t["total"]["extra"]
    assert sum(o["extra"] for o in t["by_owner"].values()) == t["total"]["extra"]
    assert all(s["public_days"] >= 0 and s["private_days"] >= 0 for s in t["steps"])


def test_the_owners_split_the_extra_days():
    o = timeline.build()["by_owner"]
    assert (o["patient"]["extra"], o["primary care"]["extra"], o["hospital"]["extra"]) == (30, 40, 14)


def test_every_measure_has_a_local_step_and_the_referral_step_quotes_the_timeline():
    assert set(LOCAL_STEPS) == set(MEASURES)
    step = local_step("2.5.2")
    d = timeline.primary_care_days()
    assert f"{d['public_days']} days" in step["evidence"] and f"{d['private_days']} days" in step["evidence"]
    assert local_step("3.2.1")["evidence"] is None


def test_the_equity_shares_come_from_the_patient_counts():
    r = equity.build()["route"]
    assert (r["high_income_private"], r["high_income_public"]) == (23, 0)
    assert (r["low_income_private"], r["low_income_public"]) == (15, 38)
    assert all(row["men_more"] == round((row["men"] - 1) * 100) for row in equity.build()["study"]["rows"])


def test_the_evidence_endpoint_names_known_sources():
    e = client.get("/api/evidence").json()
    sources = data.sources()
    for sid in (e["timeline"]["source"], e["timeline"]["outcome"]["source"], e["pilot"]["basis_source"],
                e["pilot"]["host_source"], e["equity"]["study"]["source"], e["equity"]["route"]["source"]):
        assert sid in sources, sid
    assert e["radiotherapy"]["status"] == "protocol, not county performance data"
    assert {"borras_2015", "hanna_2020", "local_step"} <= set(e["radiotherapy"]["sources"])


def test_every_recommendation_carries_its_local_step():
    b = client.get("/api/county/09?cancer=bowel").json()
    sources = data.sources()
    assert "local_step" in sources
    for r in b["recommendations"]:
        assert r["local"]["text"] == LOCAL_STEPS[r["measure"]]
        assert r["local"]["evidence_source"] is None or r["local"]["evidence_source"] in sources


def test_the_two_routes_hold_part_of_the_study_and_the_figure_ends_near_the_means():
    """The paper gives medians, means and a figure for one comparison. The page must say which is which."""
    t = timeline.build()
    s = t["study"]
    assert s["compared"] == t["groups"]["public"]["patients"] + t["groups"]["private"]["patients"] == 87
    assert s["compared"] + sum(s["not_compared"].values()) == s["patients"] == 160
    assert s["patients"] - s["not_compared"]["a place that is not known"] == s["contact_known"]
    for route in ("public", "private"):
        mean, median, figure = t["means"][route], t["groups"][route]["median_total"], t["total"][route]
        assert abs(figure - mean) < abs(figure - median)  # the figure shows means, not medians


def test_the_county_queues_read_the_cached_sotkanet_files():
    """Päijät-Häme had the shortest primary care queue of 22 counties in 2025: 32.7% against 54.7%."""
    from backend.queues import county_queues
    from backend.sotkanet import load
    q = {x["indicator"]: x for x in county_queues(load(), "09")}
    assert (q[6411]["year"], q[6411]["county"], q[6411]["national"], q[6411]["side"]) == (2025, 32.7, 54.7, "shorter")
    assert (q[6411]["rank"], q[6411]["of"]) == (22, 22)
    assert q[3336]["step"] == "Referral to specialist appointment"


def test_every_county_has_a_verified_unit_or_says_it_has_none():
    """Lapland is served by Oulu, the only unit in Northern Finland. A county without a source gets no distance."""
    from backend import radiotherapy as R
    from backend.sotkanet import load
    rows = {r["county"]: r for r in R.access_all(load().counties)}
    assert len(rows) == 22
    assert (rows["21"]["city"], rows["21"]["in_county"]) == ("Oulu", False) and rows["21"]["farthest_km"] >= 500
    assert rows["90"]["in_county"] and rows["90"]["farthest_km"] <= 30
    assert all(r["verified"] for r in rows.values())  # every county names its unit, with a source
    assert rows["12"]["city"] == "Kuopio or Jyväskylä or Lappeenranta" and not rows["12"]["in_county"]
    assert R.access("99")["unit"] is None and R.access("99")["farthest_km"] is None  # no source: no unit, no distance
    assert all(r["url"].startswith("https://") for r in rows.values() if r["verified"])
    assert round(R.km(60.17, 24.94, 61.50, 23.76)) in range(155, 165)  # Helsinki to Tampere, about 160 km


def test_the_nordcan_values_lie_inside_their_published_intervals():
    """The second check against the fact sheets copied the 95% interval beside each survival value."""
    from backend import nordcan
    for site, entry in nordcan.load()["sites"].items():
        for country, sexes in entry.items():
            if country == "slug":
                continue
            for sex, v in sexes.items():
                if v["surv5"] is not None:
                    low, high = v["ci5"]
                    assert low <= v["surv5"] <= high, (site, country, sex)


def test_specialist_queues_pool_six_month_ends_and_hide_small_numbers():
    """South Savo: 19.8% of the gastroenterology queue had waited more than 90 days, against 7.0% in Finland.
    Päijät-Häme reports almost no one in that queue, so the app shows no share."""
    from backend.queues import specialist_queues
    q = {x["specialty"]: x for x in specialist_queues("bowel", "12")}
    assert (q["10G"]["share_over_90"], q["10G"]["national_over_90"], q["10G"]["months"]) == (19.8, 7.0, 6)
    assert {x["specialty"]: x["share_over_90"] for x in specialist_queues("bowel", "09")}["10G"] is None
    uusimaa = specialist_queues("lung", "02")
    assert all(x["provider"] == "HUS" and x["shared"] for x in uusimaa)
    assert [x["specialty"] for x in specialist_queues("cervical", "14")] == ["30", "65"]


def test_the_page_loads_nothing_from_the_network():
    import re
    page = client.get("/").text
    external = re.findall(r'<(?:link|script|img)[^>]+(?:href|src)="(https?://[^"]+)"', page)
    assert external == []
    css = client.get("/fonts/fonts.css")
    assert css.status_code == 200 and "fonts.gstatic" not in css.text
    for name in re.findall(r"/fonts/([\w.-]+\.woff2)", css.text):
        assert client.get(f"/fonts/{name}").headers["content-type"] == "font/woff2"
    assert client.get("/fonts/..%2Fapp.py").status_code == 404


def test_the_pilot_has_a_90_day_plan_that_ends_in_go_or_no_go():
    p = client.get("/api/evidence").json()["pilot"]
    assert [step[0] for step in p["plan_90"]] == ["Days 1 to 30", "Days 31 to 60", "Days 61 to 90"]
    text = " ".join(step[2] for step in p["plan_90"]) + p["governance"]
    for role in ("sponsor", "clinical lead", "patient representative", "data protection officer"):
        assert role in text, role
    assert "95%" in p["go_no_go"] and "no go" in p["go_no_go"]


def test_the_pilot_pools_small_centres_and_keeps_patient_rows_in_the_county():
    p = client.get("/api/evidence").json()["pilot"]
    assert "at least 20 patients" in p["small_numbers"] and "pooled" in p["small_numbers"]
    assert "every month" not in p["output"] and "rolling 12 months" in p["output"]
    assert "stay in the county's own environment" in p["privacy"] and "never receives a patient row" in p["privacy"]
