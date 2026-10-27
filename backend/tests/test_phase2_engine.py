"""Drivepast Phase 2 pricing engine tests - JRN-24..JRN-43.

Covers Engine test view data, run-all, price, what-if, accept, undo, stale
protection, settings-driven pricing, speed rebuild, demo clock, fleet/unit
stats and bad-input handling.
"""
import os
import time
import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ALLOWED_REASONS = {
    "the window has already passed",
    "can't reach it in time",
    "past shift end",
    "no room",
    "missing skill",
}


@pytest.fixture(scope="module", autouse=True)
def reset_before_and_after():
    r = requests.post(f"{API}/demo/reset", timeout=30)
    assert r.status_code == 200
    yield
    requests.post(f"{API}/demo/reset", timeout=30)


@pytest.fixture()
def run_all():
    r = requests.post(f"{API}/engine/run-all", timeout=30)
    assert r.status_code == 200
    return r.json()["results"]


def _price(req_key):
    r = requests.post(f"{API}/engine/price", json={"request_key": req_key}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


# ------- JRN-24 Engine test lists the seeded requests --------
def test_jrn24_engine_jobs_listing():
    r = requests.get(f"{API}/engine/jobs", timeout=10)
    assert r.status_code == 200
    jobs = r.json()
    assert len(jobs) == 14
    by_n = {j["number"]: j for j in jobs}
    for n in range(1, 11):
        j = by_n[n]
        assert j.get("job_summary"), f"request {n} missing one-line summary"
    for n in (6, 7):
        assert by_n[n]["job_status"] == "cant_price"
        reason = (by_n[n].get("job_reason") or "").lower()
        if n == 6:
            assert "missing" in reason or "address" in reason
        else:
            assert "city" in reason or "unclear" in reason


# ------- JRN-25/26 Request 1 winner on Van 2 --------
def test_jrn25_request1_winner_van2():
    d = _price("req-01")
    assert d["winner_unit_key"] == "van-2"
    w = d["winner"]
    assert w["added_cost"] < 4.0
    assert w["price"] == 11.0
    assert w["monthly_total"] == 231.0
    assert "Van 2" in w["explanation"]
    assert "$11 a visit" in w["explanation"]
    assert "$231 a month" in w["explanation"]
    pb = w["pass_by"]["line"].lower()
    assert "5100 shattuck" in pb
    assert "1:50pm" in pb
    # arrivals ordered: pickup then dropoff
    kinds = [n["kind"] for n in w["new_stops"]]
    assert kinds == ["pickup", "dropoff"]


def test_jrn26_handcheck_matches_added_cost():
    """Spec: minutes x (wage/60) + miles x cost_per_mile == added_cost within 1 cent."""
    s = requests.get(f"{API}/settings", timeout=10).json()["settings"]
    wage, cpm = s["wage_per_hour"], s["cost_per_mile"]
    checked = 0
    for n in (1, 2, 3, 5, 9, 10):
        d = _price(f"req-{n:02d}")
        w = d.get("winner")
        if not w:
            continue
        expected = round(w["added_minutes"] * (wage / 60) + w["added_miles"] * cpm, 2)
        assert abs(expected - w["added_cost"]) <= 0.01, (n, expected, w["added_cost"])
        hc = w["hand_check"]
        assert f"{w['added_minutes']} min" in hc
        assert f"{w['added_miles']:.1f} mi" in hc
        checked += 1
    assert checked >= 4


# ------- JRN-27 Request 2 same-day one-off --------
def test_jrn27_request2_same_day_oneoff():
    d = _price("req-02")
    w = d["winner"]
    assert w is not None, d
    assert w["price"] >= 35.0
    assert w["market_line"] and "$45 to $65" in w["market_line"]
    assert w["monthly_total"] in (None, 0)
    assert "a month" not in w["explanation"]
    # Pickup before dropoff, dropoff by 3:00pm (<=900 min)
    stops = w["new_stops"]
    assert stops[0]["kind"] == "pickup" and stops[1]["kind"] == "dropoff"
    assert stops[1]["arrival"] <= 900
    # Same-day: new stops after demo clock (10am = 600)
    assert stops[0]["arrival"] >= 600


# ------- JRN-28 Request 3 Mon/Thu monthly 4.3x2 --------
def test_jrn28_request3_monthly_4x3x2():
    d = _price("req-03")
    w = d["winner"]
    assert w is not None
    assert w["price"] >= 11.0
    expected_monthly = round(w["price"] * 4.3 * 2, 2)
    assert abs(w["monthly_total"] - expected_monthly) <= 0.05
    # price=11 -> monthly ~ 94.60
    if w["price"] == 11.0:
        assert w["monthly_total"] == 94.6
    assert d["winner_unit_key"] in ("van-5", "van-6")


# ------- JRN-29 Request 4 all vans past shift end, shifted 4:15pm on van-4 --------
def test_jrn29_request4_past_shift_end_and_shift():
    d = _price("req-04")
    assert d["winner_unit_key"] is None
    for r in d["results"]:
        assert r["feasible"] is False
        assert r["reason"] in ALLOWED_REASONS
        # At least some say "past shift end"
    assert any(r["reason"] == "past shift end" for r in d["results"])
    sh = d.get("shifted")
    assert sh and sh.get("found")
    sw = sh["winner"]
    assert sw["unit_key"] == "van-4"
    # pickup at 4:15pm (<4:30pm Lakeshore close)
    p = next(n for n in sw["new_stops"] if n["kind"] == "pickup")
    assert p["arrival"] < 16 * 60 + 30  # before 4:30pm
    assert p["arrival_label"].endswith("pm")


# ------- JRN-30 Request 5 multi-stop insertion --------
def test_jrn30_request5_multistop():
    d = _price("req-05")
    w = d.get("winner") or (d.get("shifted") or {}).get("winner")
    assert w, d
    # 4 pickups + 1 dropoff
    kinds = [n["kind"] for n in w["new_stops"]]
    assert kinds.count("pickup") == 4
    assert kinds.count("dropoff") == 1
    # dropoff is the last
    assert w["new_stops"][-1]["kind"] == "dropoff"
    # arrivals: pickups between 3:00pm (900) and 4:00pm (960), dropoff by 5pm (1020)
    for n in w["new_stops"][:-1]:
        assert 900 <= n["arrival"] <= 960, n
    assert w["new_stops"][-1]["arrival"] <= 1020


# ------- JRN-31 Request 8 impossible window, shifted delivery by 9:15am Van 2 --------
def test_jrn31_request8_impossible_then_shift():
    d = _price("req-08")
    assert d["winner_unit_key"] is None
    for r in d["results"]:
        assert r["feasible"] is False
        assert r["reason"] in ALLOWED_REASONS
    assert any(r["reason"] == "can't reach it in time" for r in d["results"])
    sh = d.get("shifted")
    assert sh and sh.get("found")
    sw = sh["winner"]
    drop = next(n for n in sw["new_stops"] if n["kind"] == "dropoff")
    assert drop["arrival"] > 8 * 60 + 15  # a later delivery than asked
    assert sw["feasible"] is True and sh["mode"] == "deadline_later"


# ------- JRN-32 Request 9 == Request 1; Request 10 approximate drops on Solano --------
def test_jrn32_request9_equals_request1_and_r10_approximate():
    d1 = _price("req-01")
    d9 = _price("req-09")
    w1, w9 = d1["winner"], d9["winner"]
    assert d9["winner_unit_key"] == d1["winner_unit_key"]
    for f in ("added_minutes", "added_miles", "added_cost", "price", "monthly_total"):
        assert w1[f] == w9[f], (f, w1[f], w9[f])

    d10 = _price("req-10")
    w10 = d10["winner"] or (d10.get("shifted") or {}).get("winner")
    assert w10
    # The two Solano Ave dropoffs are approximate
    drops = [n for n in w10["new_stops"] if n["kind"] == "dropoff"]
    assert len(drops) == 2
    for drop in drops:
        assert drop.get("approximate") is True, drop
        assert "solano" in drop["address"].lower()


# ------- JRN-33 Fast enough --------
def test_jrn33_engine_time_bounds():
    for _ in range(3):
        results = requests.post(f"{API}/engine/run-all", timeout=30).json()["results"]
        for r in results:
            if r.get("priceable") is False:
                continue
            ms = r.get("ms")
            assert ms is not None, r
            cap = 1000 if r["number"] == 5 else 500
            assert ms < cap, f"request {r['number']} took {ms}ms (cap {cap})"


# ------- JRN-34 Plain-words reasons only --------
def test_jrn34_reasons_whitelist(run_all):
    for r in run_all:
        if r.get("priceable") is False:
            continue
        for row in r.get("results", []):
            if row["feasible"]:
                continue
            assert row["reason"] in ALLOWED_REASONS, (r["number"], row)
            # No raw codes/JSON/NaN
            assert "nan" not in row["reason"].lower()
            # 'where' details for the comparison card
            assert row.get("where") is not None


# ------- JRN-35 What-if is read-only --------
def test_jrn35_what_if_read_only():
    stops = requests.get(f"{API}/stops?unit_key=van-1", timeout=10).json()
    # Pick a middle stop and move to van-2
    stop_key = stops[len(stops) // 2]["key"]
    before = requests.get(f"{API}/units/van-1", timeout=10).json()["unit"]
    r = requests.post(f"{API}/engine/what-if",
                      json={"stop_key": stop_key, "to_unit_key": "van-2"}, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["saved"] is False
    assert "from" in body and "to" in body
    assert body["from"]["minutes"] <= 0  # source saves minutes
    after = requests.get(f"{API}/units/van-1", timeout=10).json()["unit"]
    assert after["stops_count"] == before["stops_count"]


# ------- JRN-36/37/38 Accept, Undo, Stale --------
def test_jrn36_38_accept_undo_stale():
    # Fresh for stable arrivals.
    requests.post(f"{API}/demo/reset", timeout=30)

    before_v2 = requests.get(f"{API}/units/van-2", timeout=10).json()["unit"]
    before_count = before_v2["stops_count"]

    # Snapshot plan arrivals for undo diff
    plan_before = requests.get(f"{API}/route-plans?unit_key=van-2", timeout=10).json()[0]
    arrivals_before = {row["stop_key"]: row["arrival"] for row in plan_before["stops"]}

    # Price request 1, keep the Van-2 winner option
    d = _price("req-01")
    opt = next(r for r in d["results"] if r["unit_key"] == "van-2" and r["feasible"])
    opt_id = opt["option_id"]

    # JRN-36 Accept
    r = requests.post(f"{API}/engine/accept", json={"option_id": opt_id}, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True

    v2 = requests.get(f"{API}/units/van-2", timeout=10).json()["unit"]
    assert v2["stops_count"] == before_count + 2  # pickup + dropoff
    # Rail header / fleet show same stop count
    fleet_v2 = next(u for u in requests.get(f"{API}/fleet", timeout=10).json()["units"]
                    if u["key"] == "van-2")
    assert fleet_v2["stops_count"] == v2["stops_count"]
    assert fleet_v2["spare_minutes"] == v2["spare_minutes"]

    # JRN-38 Stale: price again and try accepting an older option --
    # Try to accept the SAME option_id again (route already changed).
    r_stale = requests.post(f"{API}/engine/accept", json={"option_id": opt_id}, timeout=20)
    assert r_stale.status_code == 409
    msg = r_stale.json()["detail"]["message"]
    assert "no longer free" in msg.lower() or "price it again" in msg.lower()

    # JRN-37 Undo
    r_u = requests.post(f"{API}/engine/undo", timeout=20)
    assert r_u.status_code == 200
    assert r_u.json()["ok"] is True

    v2_after = requests.get(f"{API}/units/van-2", timeout=10).json()["unit"]
    assert v2_after["stops_count"] == before_count
    plan_after = requests.get(f"{API}/route-plans?unit_key=van-2", timeout=10).json()[0]
    arrivals_after = {row["stop_key"]: row["arrival"] for row in plan_after["stops"]}
    # Arrivals must restore within a tiny float-precision tolerance (user-visible labels match)
    assert set(arrivals_after.keys()) == set(arrivals_before.keys())
    for k, v in arrivals_before.items():
        assert abs(arrivals_after[k] - v) < 0.5, (k, v, arrivals_after[k])

    # Second undo -> Nothing to undo
    r_u2 = requests.post(f"{API}/engine/undo", timeout=20)
    assert r_u2.status_code == 200
    body2 = r_u2.json()
    assert body2.get("ok") is False
    assert "Nothing to undo" in body2.get("message", "")


# ------- JRN-39 Settings drive the price --------
def test_jrn39_settings_drive_price():
    # JRN-57 supersedes JRN-39: a $15 floor needs a usual price of at least $15.
    try:
        r = requests.put(f"{API}/settings", json={"floor_recurring": 16}, timeout=15)
        assert r.status_code == 422 and "floor_recurring" in r.json()["detail"]["fields"]
        requests.put(f"{API}/settings", json={"usual_recurring": 20, "floor_recurring": 15}, timeout=15)
        d = _price("req-01")
        w = d["winner"]
        assert w["price"] == 15.0
        assert w["monthly_total"] == 315.0

        # Wage $40 -> hand check uses 40/60 = $0.6667
        requests.put(f"{API}/settings", json={"wage_per_hour": 40}, timeout=15)
        d = _price("req-01")
        w = d["winner"]
        assert "$0.6667" in w["hand_check"], w["hand_check"]
        # Added cost increases vs $19.27 wage
        assert w["added_cost"] > 2.65

        # No price below floor across all requests
        all_out = requests.post(f"{API}/engine/run-all", timeout=30).json()["results"]
        for r in all_out:
            if not r.get("results"):
                continue
            for row in r["results"]:
                if row.get("feasible") and row.get("price") is not None:
                    assert row["price"] >= 15.0 - 0.001
                    assert row["price"] <= row["usual"] + 0.001
    finally:
        requests.put(f"{API}/settings",
                     json={"floor_recurring": 11, "usual_recurring": 14, "wage_per_hour": 19.27}, timeout=15)


# ------- JRN-40 Speed rebuilds the matrix --------
def test_jrn40_speed_rebuilds_matrix():
    try:
        before = _price("req-01")["winner"]
        before_driving = before["added_driving_minutes_exact"]
        before_p1_arr = before["new_stops"][0]["arrival"]
        r = requests.put(f"{API}/settings", json={"speed_eastbay_mph": 15}, timeout=20)
        assert r.status_code == 200
        assert r.json().get("recomputed") is True
        after = _price("req-01")["winner"]
        # Driving part and arrival time must change (service minutes may dominate rounded total)
        assert after["added_driving_minutes_exact"] != before_driving, (
            before_driving, after["added_driving_minutes_exact"])
        assert after["new_stops"][0]["arrival"] != before_p1_arr
    finally:
        requests.put(f"{API}/settings", json={"speed_eastbay_mph": 22}, timeout=20)


# ------- JRN-41 Demo clock controls same-day feasibility --------
def test_jrn41_demo_clock_affects_same_day():
    try:
        # 4:00pm (960) -> request 2 window (ends 3:00pm) has already passed
        requests.put(f"{API}/settings", json={"demo_clock_minutes": 960}, timeout=15)
        d = _price("req-02")
        assert d["winner_unit_key"] is None
        for r in d["results"]:
            assert r["feasible"] is False
            assert r["reason"] == "the window has already passed", r

        # back to 10am
        requests.put(f"{API}/settings", json={"demo_clock_minutes": 600}, timeout=15)
        d2 = _price("req-02")
        assert d2["winner_unit_key"] is not None
    finally:
        requests.put(f"{API}/settings", json={"demo_clock_minutes": 600}, timeout=15)


# ------- JRN-42 Fleet + unit stats --------
def test_jrn42_fleet_and_unit_stats():
    fleet = requests.get(f"{API}/stats/fleet", timeout=15).json()
    assert "units" in fleet and len(fleet["units"]) == 6
    assert "week" in fleet and len(fleet["week"]) == 5
    required = {"stops_count", "spare_minutes_today", "spare_minutes_by_weekday",
                "spare_minutes_week_total", "revenue_per_day", "cost_per_stop",
                "on_time_rate", "morning_on_time_rate", "afternoon_on_time_rate",
                "late_runs", "average_minutes_late"}
    for u in fleet["units"]:
        assert required.issubset(u.keys()), (u["unit_key"], required - u.keys())
        assert len(u["spare_minutes_by_weekday"]) == 5

    # Van 6 lowest afternoon on-time, most late runs
    by_key = {u["unit_key"]: u for u in fleet["units"]}
    v6 = by_key["van-6"]
    others = [u for k, u in by_key.items() if k != "van-6"]
    assert v6["afternoon_on_time_rate"] == min(
        u["afternoon_on_time_rate"] for u in fleet["units"] if u["afternoon_on_time_rate"] is not None
    )
    assert v6["late_runs"] >= max(u["late_runs"] for u in others)

    # Unit stats endpoint matches fleet row
    r = requests.get(f"{API}/stats/units/van-6", timeout=10)
    assert r.status_code == 200
    one = r.json()
    for f in ("stops_count", "spare_minutes_today", "revenue_per_day", "cost_per_stop"):
        assert one[f] == v6[f], (f, one[f], v6[f])

    # Matches /api/fleet
    fleet_main = {u["key"]: u for u in requests.get(f"{API}/fleet", timeout=10).json()["units"]}
    assert fleet_main["van-6"]["stops_count"] == v6["stops_count"]
    assert fleet_main["van-6"]["spare_minutes"] == v6["spare_minutes_today"]
    assert fleet_main["van-6"]["revenue_per_day"] == v6["revenue_per_day"]
    assert fleet_main["van-6"]["cost_per_stop"] == v6["cost_per_stop"]


# ------- JRN-43 Bad job input returns plain error 422 --------
def test_jrn43_bad_job_input():
    # No stops
    r = requests.post(f"{API}/engine/price",
                      json={"job": {"stops": [], "pairs": [], "frequency": {"type": "weekday"}}},
                      timeout=10)
    assert r.status_code == 422
    assert r.json()["detail"]["message"].lower().startswith("this job has no stops")

    # Window ends before it starts
    r2 = requests.post(f"{API}/engine/price", json={"job": {
        "stops": [{"ref": "s1", "kind": "pickup", "name": "x",
                   "address": "x", "lat": 37.8, "lon": -122.3,
                   "window_start": 900, "window_end": 480, "items": 1}],
        "pairs": [], "frequency": {"type": "weekday"}}},
        timeout=10)
    assert r2.status_code == 422
    assert "ends before" in r2.json()["detail"]["message"]
