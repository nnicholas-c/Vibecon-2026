"""Step 6: Memory rules + Activity feed backend tests."""
import copy
import os
import sys
import pathlib

import pytest
import requests
from bson import ObjectId

sys.path.insert(0, str(pathlib.Path("/app/backend")))

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://drivepast-preview.preview.emergentagent.com"
# use the public URL from frontend/.env for consistency
with open("/app/frontend/.env") as f:
    for line in f:
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE}/api"


@pytest.fixture(scope="module")
def mongo():
    from pymongo import MongoClient
    url = open("/app/backend/.env").read()
    import re
    mu = re.search(r'MONGO_URL="?([^"\n]+)"?', url).group(1)
    dn = re.search(r'DB_NAME="?([^"\n]+)"?', url).group(1)
    return MongoClient(mu)[dn]


@pytest.fixture(scope="module")
def bkey():
    sys.path.insert(0, "/app/backend")
    from core import BKEY
    return BKEY


@pytest.fixture(autouse=True, scope="module")
def reset_before_and_after():
    # reset demo at start
    requests.post(f"{API}/demo/reset", timeout=30)
    yield
    requests.post(f"{API}/demo/reset", timeout=30)


# --- Memory rules CRUD ---
class TestMemoryRulesCRUD:
    def test_list_empty_after_reset(self):
        r = requests.get(f"{API}/memory/rules", timeout=15)
        assert r.status_code == 200
        assert r.json()["rules"] == []

    def test_delete_invalid_id_returns_404(self):
        r = requests.delete(f"{API}/memory/rules/not-an-objectid", timeout=15)
        assert r.status_code == 404

    def test_patch_invalid_id_returns_404(self):
        r = requests.patch(f"{API}/memory/rules/not-an-objectid", json={"active": True}, timeout=15)
        assert r.status_code == 404

    def test_patch_valid_but_missing_returns_404(self):
        r = requests.patch(f"{API}/memory/rules/507f1f77bcf86cd799439011", json={"active": True}, timeout=15)
        assert r.status_code == 404

    def test_rule_insert_list_patch_delete(self, mongo, bkey):
        rid = str(mongo.agent_rules.insert_one({
            "business_id": bkey, "text": "Don't send Van 2 downtown after 3",
            "active": True, "created_at": "2026-10-25T00:00:00+00:00"
        }).inserted_id)
        try:
            lst = requests.get(f"{API}/memory/rules", timeout=15).json()["rules"]
            match = [r for r in lst if r["id"] == rid]
            assert match, "rule listed"
            rule = match[0]
            assert rule["active"] is True
            assert rule["enforced"] is True
            assert rule["enforced_line"] and "Van 2" in rule["enforced_line"] and "Downtown Oakland" in rule["enforced_line"]
            # patch active=false
            pr = requests.patch(f"{API}/memory/rules/{rid}", json={"active": False}, timeout=15)
            assert pr.status_code == 200
            assert pr.json()["active"] is False
            # Verify persisted
            lst2 = requests.get(f"{API}/memory/rules", timeout=15).json()["rules"]
            assert [r for r in lst2 if r["id"] == rid][0]["active"] is False
            # delete
            dr = requests.delete(f"{API}/memory/rules/{rid}", timeout=15)
            assert dr.status_code == 200
            lst3 = requests.get(f"{API}/memory/rules", timeout=15).json()["rules"]
            assert all(r["id"] != rid for r in lst3)
        finally:
            mongo.agent_rules.delete_one({"text": "Don't send Van 2 downtown after 3"})


# --- Rule enforcement in engine ---
class TestRuleEnforcement:
    def _job(self, mongo):
        job = copy.deepcopy(mongo.requests.find_one({"key": "req-02"})["job"])
        job["stops"][0].update(window_start=915, window_end=960)
        job["stops"][1].update(window_end=1020)
        return job

    def _vans(self, job):
        r = requests.post(f"{API}/engine/price", json={"job": job}, timeout=60)
        assert r.status_code == 200, r.text
        opts = r.json()["options"]
        return {x["unit_key"] for x in opts["cards"] + opts["others"]}, opts.get("blocked", [])

    def test_rule_blocks_van2_downtown(self, mongo, bkey):
        job = self._job(mongo)
        before, _ = self._vans(job)
        assert "van-2" in before, f"Expected van-2 initially; got {before}"

        rid = str(mongo.agent_rules.insert_one({
            "business_id": bkey, "text": "Don't send Van 2 downtown after 3",
            "active": True, "created_at": "2026-10-25T00:00:00+00:00"
        }).inserted_id)
        try:
            after, blocked = self._vans(job)
            assert "van-2" not in after, f"van-2 should be blocked; got {after}"
            match = [b for b in blocked if b["unit_key"] == "van-2"]
            assert match, f"blocked list has van-2; got {blocked}"
            assert "Van 2 can't: your rule" in match[0]["reason"]

            # toggle off
            requests.patch(f"{API}/memory/rules/{rid}", json={"active": False}, timeout=15)
            again, blocked2 = self._vans(job)
            assert "van-2" in again
            assert not any(b["unit_key"] == "van-2" for b in blocked2)
        finally:
            requests.delete(f"{API}/memory/rules/{rid}", timeout=15)

    def test_sf_rule_enforced(self, mongo, bkey):
        rid = str(mongo.agent_rules.insert_one({
            "business_id": bkey, "text": "Never send Van 1 to SF after 3pm",
            "active": True, "created_at": "2026-10-25T00:00:00+00:00"
        }).inserted_id)
        try:
            rules = requests.get(f"{API}/memory/rules", timeout=15).json()["rules"]
            m = [r for r in rules if r["id"] == rid][0]
            assert m["enforced"] is True
            assert "San Francisco" in m["enforced_line"]
        finally:
            mongo.agent_rules.delete_one({"_id": ObjectId(rid)})

    def test_non_area_rule_not_enforced(self, mongo, bkey):
        rid = str(mongo.agent_rules.insert_one({
            "business_id": bkey, "text": "Always mention the floor price",
            "active": True, "created_at": "2026-10-25T00:00:00+00:00"
        }).inserted_id)
        try:
            rules = requests.get(f"{API}/memory/rules", timeout=15).json()["rules"]
            m = [r for r in rules if r["id"] == rid][0]
            assert m["enforced"] is False
            assert m["enforced_line"] is None

            job = copy.deepcopy(mongo.requests.find_one({"key": "req-02"})["job"])
            before = requests.post(f"{API}/engine/price", json={"job": job}, timeout=60).json()["options"]
            # Non-area rule should NOT block anyone
            assert before.get("blocked") in ([], None) or not any(True for _ in before["blocked"])
        finally:
            mongo.agent_rules.delete_one({"_id": ObjectId(rid)})


# --- Activity feed ---
class TestActivity:
    def test_activity_after_reset_is_empty(self):
        requests.post(f"{API}/demo/reset", timeout=30)
        r = requests.get(f"{API}/activity", timeout=15)
        assert r.status_code == 200
        assert r.json()["events"] == []

    def test_inbox_read_logs_assistant_row(self):
        requests.post(f"{API}/demo/reset", timeout=30)
        r = requests.post(f"{API}/inbox/req-01/read", timeout=30)
        assert r.status_code == 200
        ev = requests.get(f"{API}/activity", timeout=15).json()["events"]
        assert ev, "expected activity"
        top = ev[0]
        assert top["actor"] == "assistant"
        assert "Read request #1" in top["line"]
        for k in ("id", "ts", "actor", "line", "tool"):
            assert k in top

    def test_rule_toggle_delete_logs_owner(self, mongo, bkey):
        requests.post(f"{API}/demo/reset", timeout=30)
        rid = str(mongo.agent_rules.insert_one({
            "business_id": bkey, "text": "Don't send Van 2 downtown after 3",
            "active": True, "created_at": "2026-10-25T00:00:00+00:00"
        }).inserted_id)
        requests.patch(f"{API}/memory/rules/{rid}", json={"active": False}, timeout=15)
        requests.delete(f"{API}/memory/rules/{rid}", timeout=15)
        ev = requests.get(f"{API}/activity", timeout=15).json()["events"]
        lines = [e["line"] for e in ev if e["actor"] == "owner"]
        assert any("Deleted the rule" in l for l in lines)
        assert any("Turned off" in l or "Turned on" in l for l in lines)


# --- Reset + openapi + landing ---
class TestResetAndStatic:
    def test_demo_reset_clears(self, mongo, bkey):
        # seed some data
        mongo.agent_rules.insert_one({"business_id": bkey, "text": "Don't send Van 2 downtown after 3",
                                      "active": True, "created_at": "2026-10-25T00:00:00+00:00"})
        requests.post(f"{API}/inbox/req-01/read", timeout=30)
        r = requests.post(f"{API}/demo/reset", timeout=30)
        assert r.status_code == 200
        assert requests.get(f"{API}/memory/rules", timeout=15).json()["rules"] == []
        assert requests.get(f"{API}/activity", timeout=15).json()["events"] == []

    def test_landing_price_values(self):
        r = requests.get(f"{API}/landing/price", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["time_cost"] == 1.28
        assert d["mile_cost"] == 0.46
        assert d["cost_with_markup"] == 3.48
        assert d["floor"] == 11
        assert d["offer"] == 11
        assert d["usual"] == 14

    def test_openapi_reachable(self):
        r = requests.get(f"{API}/openapi.json", timeout=15)
        assert r.status_code == 200
        assert "paths" in r.json()
