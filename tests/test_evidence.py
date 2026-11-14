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


def test_every_recommendation_carries_its_local_step():
    b = client.get("/api/county/09?cancer=bowel").json()
    sources = data.sources()
    assert "local_step" in sources
    for r in b["recommendations"]:
        assert r["local"]["text"] == LOCAL_STEPS[r["measure"]]
        assert r["local"]["evidence_source"] is None or r["local"]["evidence_source"] in sources
