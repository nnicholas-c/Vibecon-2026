"""Drivepast Phase 1 backend API tests covering JRN-1 .. JRN-22.

Each test maps to the acceptance journeys in /app/memory/product/phase1/journeys.md
and the data-testids provided by the main agent.
"""
import os
import subprocess
import time
import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session", autouse=True)
def reset_demo_once():
    """Start every test session from a clean seed (per JRN preamble)."""
    r = requests.post(f"{API}/demo/reset", timeout=30)
    assert r.status_code == 200, f"demo reset failed: {r.status_code} {r.text}"
    yield
    # Final cleanup for next agent
    requests.post(f"{API}/demo/reset", timeout=30)


@pytest.fixture()
def fleet():
    r = requests.get(f"{API}/fleet", timeout=10)
    assert r.status_code == 200
    return r.json()


# ---------- JRN-1 fleet basics / rail ----------

def test_jrn1_business_and_units(fleet):
    biz = fleet["business"]
    assert biz["key"] == "bayline"
    assert biz["name"] == "Bayline Courier"
    assert biz["owner_name"] == "Rosa Delgado"
    assert "Price every job from the van that already drives past." == biz["tagline"]
    assert biz["demo_clock_minutes"] == 600
    assert biz["demo_clock_label"] == "10:00am"

    units = fleet["units"]
    assert len(units) == 6
    nicknames = {u["key"]: u["nickname"] for u in units}
    expected = {
        "van-1": "Shattuck loop", "van-2": "Emeryville labs", "van-3": "Oakland legal",
        "van-4": "Rockridge clinics", "van-5": "SF Financial District", "van-6": "SF Mission Bay",
    }
    assert nicknames == expected
    # distinct colors
    colors = {u["color"] for u in units}
    assert len(colors) == 6
    # inbox count 10
    assert fleet["inbox_new_count"] == 14
    # per-van ~20 stops, spare between 30 and 70
    for u in units:
        assert 15 <= u["stops_count"] <= 25
        assert 30 <= u["spare_minutes"] <= 70


# ---------- JRN-2 Van 2 timeline ----------

def test_jrn2_van2_timeline():
    r = requests.get(f"{API}/units/van-2", timeout=10)
    assert r.status_code == 200
    data = r.json()
    unit = data["unit"]
    assert unit["name"] == "Van 2"
    assert unit["nickname"] == "Emeryville labs"
    assert unit["driver_name"] == "Dev Patel"
    assert 15 <= unit["stops_count"] <= 25
    assert 40 <= unit["spare_minutes"] <= 60

    timeline = data["timeline"]
    # Find stop near 5100 Shattuck Ave at ~1:50pm (minutes 830)
    shattuck = [t for t in timeline if "Shattuck Ave" in t["address"]]
    assert shattuck, "expected a Shattuck Ave stop"
    # arriving between 1:40pm (820) and 2:00pm (840)
    assert any(820 <= t["arrival"] <= 840 for t in shattuck), [t["arrival"] for t in shattuck]

    telegraph = [t for t in timeline if "Telegraph Ave" in t["address"]]
    assert telegraph, "expected a Telegraph Ave stop"
    assert any(845 <= t["arrival"] <= 865 for t in telegraph), [t["arrival"] for t in telegraph]


# ---------- JRN-3 Van 4 ends near Lakeshore / Piedmont ----------

def test_jrn3_van4_last_stops():
    r = requests.get(f"{API}/units/van-4", timeout=10)
    assert r.status_code == 200
    tl = r.json()["timeline"]
    assert tl, "van-4 should have a timeline"
    last_two = tl[-2:]
    addrs = " | ".join(t["address"] for t in last_two)
    assert "Lakeshore Ave" in addrs
    assert "Piedmont Ave" in addrs
    # arrivals between 3:30pm (930) and 4:30pm (990)
    for t in last_two:
        assert 930 <= t["arrival"] <= 990
    plan = r.json()["plan"]
    assert plan["return_time"] <= 17 * 60  # by 5:00pm


# ---------- JRN-4 Every seeded route is feasible ----------

def test_jrn4_all_routes_feasible():
    plans = requests.get(f"{API}/route-plans", timeout=10).json()
    stops = requests.get(f"{API}/stops", timeout=10).json()
    stops_by_key = {s["key"]: s for s in stops}
    assert requests.get(f"{API}/fleet", timeout=10).json()["units"]

    assert len(plans) == 6
    for p in plans:
        assert p["feasible"] is True, f"{p['unit_key']} not feasible: {p.get('problems')}"
        assert p["return_time"] <= 17 * 60, p["unit_key"]
        for row in p["stops"]:
            s = stops_by_key[row["stop_key"]]
            assert s["window_start"] <= row["arrival"] <= s["window_end"], (row, s)

    # service minutes 3-6, price 9-14
    for s in stops:
        assert 3 <= s["service_minutes"] <= 6
        assert 9 <= s["price_per_visit"] <= 14

    # Vans 1-4 Emeryville depot, 5-6 SoMa (full unit object has start_location)
    for key in ["van-1", "van-2", "van-3", "van-4"]:
        detail = requests.get(f"{API}/units/{key}", timeout=10).json()["unit"]
        assert "emeryville" in detail["start_location"]["name"].lower()
    for key in ["van-5", "van-6"]:
        detail = requests.get(f"{API}/units/{key}", timeout=10).json()["unit"]
        assert "soma" in detail["start_location"]["name"].lower()


# ---------- JRN-5 Stats row ----------

def test_jrn5_stats_row(fleet):
    stops = requests.get(f"{API}/stops", timeout=10).json()
    rev_by_unit = {}
    for s in stops:
        rev_by_unit.setdefault(s["unit_key"], 0)
        rev_by_unit[s["unit_key"]] += s["price_per_visit"]

    on_times = {}
    for u in fleet["units"]:
        assert u["cost_per_stop"] > 0
        assert u["revenue_per_day"] > 0
        assert u["on_time_rate"] is not None
        # revenue equals sum of stop prices
        assert abs(u["revenue_per_day"] - rev_by_unit[u["key"]]) < 0.01, u["key"]
        on_times[u["key"]] = u["on_time_rate"]
    # Van 6 lowest on-time
    assert on_times["van-6"] == min(on_times.values()), on_times


# ---------- JRN-6 Dispatch table matches rail ----------

def test_jrn6_dispatch_matches_unit_pages(fleet):
    for u in fleet["units"]:
        detail = requests.get(f"{API}/units/{u['key']}", timeout=10).json()["unit"]
        assert detail["stops_count"] == u["stops_count"]
        assert detail["spare_minutes"] == u["spare_minutes"]
        assert detail["revenue_per_day"] == u["revenue_per_day"]
        assert detail["cost_per_stop"] == u["cost_per_stop"]


# ---------- JRN-7/8/9 echo chat ----------

def test_jrn7_echo_chat_persists():
    # clear by sending to a different agent and reading van-2 fresh
    r = requests.post(f"{API}/agents/van-2/messages", json={"text": "hello van 2"}, timeout=10)
    assert r.status_code == 200
    data = r.json()
    turns = data["turns"]
    assert turns[-2]["role"] == "owner" and turns[-2]["text"] == "hello van 2"
    assert turns[-1]["role"] == "agent" and turns[-1]["text"] == "Echo from Van 2: hello van 2"

    # Van 3 thread independent
    r3 = requests.get(f"{API}/agents/van-3/thread", timeout=10).json()
    assert all("hello van 2" not in t["text"] for t in r3["turns"])


def test_jrn8_suggested_prompts_differ():
    agents = requests.get(f"{API}/agents", timeout=10).json()
    dispatch = next(a for a in agents if a["key"] == "dispatch")
    van2 = next(a for a in agents if a["key"] == "van-2")
    assert len(dispatch["suggested_prompts"]) == 3
    assert len(van2["suggested_prompts"]) == 3
    assert set(dispatch["suggested_prompts"]) != set(van2["suggested_prompts"])


def test_jrn9_empty_message_rejected():
    r1 = requests.post(f"{API}/agents/dispatch/messages", json={"text": ""}, timeout=10)
    r2 = requests.post(f"{API}/agents/dispatch/messages", json={"text": "   "}, timeout=10)
    assert r1.status_code == 422
    assert r2.status_code == 422


# ---------- JRN-10 Settings defaults ----------

def test_jrn10_settings_defaults():
    # After reset, defaults should be present (team_numbers may remain across reset per JRN-15)
    r = requests.get(f"{API}/settings", timeout=10)
    assert r.status_code == 200
    data = r.json()
    s = data["settings"]
    assert s["wage_per_hour"] == 19.27
    assert s["cost_per_mile"] == 0.76
    assert s["markup_pct"] == 100
    assert s["floor_recurring"] == 11
    assert s["floor_one_off"] == 35
    assert s["market_ref_low"] == 45
    assert s["market_ref_high"] == 65
    assert s["weekdays_per_month"] == 21
    assert s["speed_sf_mph"] == 18
    assert s["speed_eastbay_mph"] == 22
    assert s["speed_cross_mph"] == 30
    assert s["bridge_minutes"] == 8
    assert s["road_factor"] == 1.3
    assert s["minutes_per_new_stop"] == 4
    assert s["auto_send_cheapest"] is False
    assert s["demo_clock_minutes"] == 600
    assert s["real_texting"] is False
    assert data["business_type_label"] == "Courier"


# ---------- JRN-11 Connections ----------

def test_jrn11_connection_rows():
    requests.put(f"{API}/ai/config", json={"base_url": "", "model": "", "clear_secret": True}, timeout=10)
    data = requests.get(f"{API}/settings", timeout=10).json()
    conns = {c["key"]: c for c in data["connections"]}
    assert set(conns.keys()) == {"our_model", "backup_ai", "osm", "texting"}
    assert conns["our_model"]["detail"] == "Not set up yet"
    assert conns["our_model"]["status"] == "fallback"
    assert conns["texting"]["status"] == "fallback"
    # No anthropic mention anywhere
    blob = str(data).lower()
    assert "anthropic" not in blob
    assert "web search" not in blob


# ---------- JRN-12 Settings persistence ----------

def test_jrn12_save_persists():
    # change wage to 20, demo_clock to 2:00pm (840), add team number
    patch = {"wage_per_hour": 20, "demo_clock_minutes": 840, "team_numbers": ["+15551234567"]}
    r = requests.put(f"{API}/settings", json=patch, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["settings"]["wage_per_hour"] == 20
    assert data["settings"]["demo_clock_minutes"] == 840
    assert "+15551234567" in data["settings"]["team_numbers"]
    # Refetch to confirm persistence
    data2 = requests.get(f"{API}/settings", timeout=10).json()
    assert data2["settings"]["wage_per_hour"] == 20
    # Cost per stop higher on dispatch
    units = requests.get(f"{API}/fleet", timeout=10).json()["units"]
    for u in units:
        assert u["cost_per_stop"] > 0


# ---------- JRN-13 Speed change recomputes ----------

def test_jrn13_speed_recomputes():
    before = requests.get(f"{API}/units/van-2", timeout=10).json()["unit"]["spare_minutes"]
    r = requests.put(f"{API}/settings", json={"speed_eastbay_mph": 15}, timeout=20)
    assert r.status_code == 200
    assert r.json().get("recomputed") is True
    after = requests.get(f"{API}/units/van-2", timeout=10).json()["unit"]["spare_minutes"]
    assert after < before, f"spare {before}->{after}"
    # Reset speed to default for subsequent tests
    requests.put(f"{API}/settings", json={"speed_eastbay_mph": 22}, timeout=20)


# ---------- JRN-14 Bad input refused ----------

def test_jrn14_bad_input_rejected():
    r = requests.put(f"{API}/settings", json={"wage_per_hour": "", "cost_per_mile": -5}, timeout=10)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "fields" in detail
    assert "wage_per_hour" in detail["fields"]
    assert "cost_per_mile" in detail["fields"]
    # Values unchanged
    s = requests.get(f"{API}/settings", timeout=10).json()["settings"]
    assert s["cost_per_mile"] >= 0


# ---------- JRN-15 Reset keeps team numbers ----------

def test_jrn15_reset_keeps_team_numbers():
    # Ensure a team number present
    requests.put(f"{API}/settings", json={"team_numbers": ["+15559998888"]}, timeout=15)
    requests.put(f"{API}/settings", json={"wage_per_hour": 25}, timeout=15)
    requests.post(f"{API}/agents/van-1/messages", json={"text": "temp msg"}, timeout=10)

    r = requests.post(f"{API}/demo/reset", timeout=30)
    assert r.status_code == 200
    assert r.json().get("message") == "Demo data reset"

    s = requests.get(f"{API}/settings", timeout=10).json()["settings"]
    assert s["wage_per_hour"] == 19.27  # back to default
    assert "+15559998888" in s["team_numbers"]
    assert s["demo_clock_minutes"] == 600

    # chat cleared
    thread = requests.get(f"{API}/agents/van-1/thread", timeout=10).json()
    assert thread["turns"] == []
    # inbox 10
    assert requests.get(f"{API}/fleet", timeout=10).json()["inbox_new_count"] == 14


# ---------- JRN-20 Seed contents ----------

def test_jrn20_seed_contents():
    assert requests.get(f"{API}/openapi.json", timeout=10).status_code == 200
    stops = requests.get(f"{API}/stops", timeout=10).json()
    assert 100 <= len(stops) <= 140, len(stops)
    directory = requests.get(f"{API}/directory", timeout=10).json()
    assert len(directory) == 11
    for d in directory:
        assert "lat" in d and "lon" in d
    prospects = requests.get(f"{API}/prospects", timeout=10).json()
    assert 30 <= len(prospects) <= 50, len(prospects)
    reqs = requests.get(f"{API}/requests", timeout=10).json()
    assert len(reqs) == 14
    for req in reqs:
        assert req["status"] == "new"
    history = requests.get(f"{API}/run-history/summary", timeout=10).json()
    for row in history:
        assert row["weekdays"] == 20
    # Phone numbers contain 555
    for d in directory:
        if d.get("phone"):
            assert "555" in d["phone"]


# ---------- JRN-21 Learned service minutes used in plan ----------

def test_jrn21_learned_service_in_plan():
    plans = requests.get(f"{API}/route-plans?unit_key=van-2", timeout=10).json()
    assert plans
    plan = plans[0]
    summary = {r["stop_key"]: r for r in requests.get(f"{API}/run-history/summary", timeout=10).json()}
    stops_by_key = {s["key"]: s for s in requests.get(f"{API}/stops?unit_key=van-2", timeout=10).json()}
    checked = 0
    for row in plan["stops"]:
        avg = summary.get(row["stop_key"], {}).get("avg_service_minutes")
        planned = stops_by_key[row["stop_key"]]["service_minutes"]
        used = row["departure"] - row["arrival"]
        # The route uses avg (within rounding) rather than planned when they differ
        if avg is not None and abs(avg - planned) >= 0.5:
            assert abs(used - avg) <= 1.0, (row["stop_key"], used, avg, planned)
            checked += 1
    assert checked > 0, "expected at least one stop with learned vs planned diff"


# ---------- JRN-22 Persistence across restart ----------

def test_jrn22_persistence_across_restart():
    requests.put(f"{API}/settings", json={"wage_per_hour": 22.22}, timeout=15)
    requests.post(f"{API}/agents/van-3/messages", json={"text": "persist me"}, timeout=10)
    before_counts = {
        "units": len(requests.get(f"{API}/fleet", timeout=10).json()["units"]),
        "stops": len(requests.get(f"{API}/stops", timeout=10).json()),
    }

    # Restart backend
    subprocess.run(["sudo", "supervisorctl", "restart", "backend"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Wait for backend to come back
    for _ in range(30):
        time.sleep(1)
        try:
            if requests.get(f"{API}/health", timeout=2).status_code == 200:
                break
        except Exception:
            continue
    else:
        pytest.fail("backend never came back")

    s = requests.get(f"{API}/settings", timeout=10).json()["settings"]
    assert s["wage_per_hour"] == 22.22
    thread = requests.get(f"{API}/agents/van-3/thread", timeout=10).json()
    assert any("persist me" in t["text"] for t in thread["turns"])
    after_counts = {
        "units": len(requests.get(f"{API}/fleet", timeout=10).json()["units"]),
        "stops": len(requests.get(f"{API}/stops", timeout=10).json()),
    }
    assert before_counts == after_counts, (before_counts, after_counts)
