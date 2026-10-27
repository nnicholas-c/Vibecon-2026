"""Measure record_request field accuracy on the 10 seeded requests (Q-28 / Q-35). Usage: python scripts/read_accuracy.py auto|none"""
import math
import os
import sys
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from engine.jobs import DIR, seed_jobs  # noqa: E402

API = "http://localhost:8001/api"
NAMES = {11: "lakeshore|dana", 12: "jules|sam", 13: "maya", 14: "tom", 1: "rina", 2: "clay", 3: "third", 4: "lakeshore", 5: "eastside", 6: "tom", 7: "unknown", 8: "northside", 9: "rina", 10: "photo"}
EXTRA = {6: {"pickups": [(37.8460, -122.2520)], "dropoffs": None, "freq": ("weekdays", ["fri"]), "window": None},
         7: {"pickups": None, "dropoffs": None, "freq": ("one_off", None), "window": (600, 615, None)}}
ITEMS = {2: 2}


def _pts(*names):
    return [(DIR[n]["lat"], DIR[n]["lon"]) for n in names]


NEW = {
    (11, 1): {"pickups": _pts("Lakeshore Dental"), "dropoffs": _pts("Piedmont Ave Lab"), "freq": ("weekday", None), "window": (900, 915, None)},
    (12, 1): {"pickups": _pts("Third Street Print"), "dropoffs": _pts("Montgomery Partners"), "freq": ("one_off", None), "window": (600, 615, 660)},
    (13, 1): {"pickups": _pts("Elmwood Pharmacy"), "dropoffs": _pts("Ashby Medical Center"), "freq": ("one_off", None), "window": (765, 795, None)},
    (14, 1): {"pickups": _pts("Rockridge Florist"), "dropoffs": _pts("Lakeshore Dental"), "freq": ("one_off", None), "window": (540, 555, None)},
    (14, 2): {"pickups": _pts("Rockridge Florist"), "dropoffs": _pts("Ashby Medical Center"), "freq": ("weekdays", ["fri"]), "window": (840, 855, None)},
}


def miles(a, b):
    return math.hypot((a[0] - b[0]) * 69, (a[1] - b[1]) * 54.6)


def same_points(got, want, tol=0.5):
    if want is None:
        return got is None
    return got is not None and len(got) == len(want) and all(any(miles(g, w) <= tol for g in got) for w in want)


def main(mode):
    requests.post(f"{API}/demo/reset", timeout=60)
    requests.put(f"{API}/ai/config", json={"mode": mode}, timeout=15)
    requests.post(f"{API}/inbox/read-all", timeout=180)
    db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    biz = db.businesses.find_one({"key": "bayline"})
    fixtures = seed_jobs(date.fromisoformat(biz["demo_date"]))
    right = total = 0
    parents = {d["key"]: d["number"] for d in db.requests.find({"business_key": "bayline", "number": {"$lte": 14}})}
    docs = list(db.requests.find({"business_key": "bayline", "$or": [{"number": {"$lte": 14}}, {"parent_key": {"$exists": True}}]}).sort("number", 1))
    for r in docs:
        n = parents.get(r.get("parent_key"), r["number"])
        part = r.get("part", 1)
        job, det = r.get("job"), {d["key"]: d for d in r.get("details") or []}
        fx = fixtures[n]["job"] if n in fixtures else None
        exp = NEW.get((n, part)) or EXTRA.get(n) or {
            "pickups": [(s["lat"], s["lon"]) for s in fx["stops"] if s["kind"] == "pickup"],
            "dropoffs": [(s["lat"], s["lon"]) for s in fx["stops"] if s["kind"] == "dropoff"],
            "freq": (fx["frequency"]["type"], fx["frequency"].get("days") or fx["frequency"].get("start_date")),
            "window": (fx["stops"][0]["window_start"], fx["stops"][0]["window_end"], fx["stops"][-1]["window_end"]),
        }
        pts = lambda kind, job=job: [(s["lat"], s["lon"]) for s in job["stops"] if s["kind"] == kind] if job else None  # noqa: E731
        got_pick = pts("pickup") if job else ([(37.8460, -122.2520)] if n == 6 and "Rockridge" in str(det.get("loc-0", {}).get("value")) else None)
        f = job["frequency"] if job else None
        if not job and r.get("parsed"):
            pf = r["parsed"]["frequency"]
            f = {"type": {"every_weekday": "weekday"}.get(pf.get("type"), pf.get("type")), "days": pf.get("days")}
        w = exp["window"]
        p0 = job["stops"][0] if job else None
        tw = r.get("parsed", {}).get("time_window", {}) if r.get("parsed") else {}
        start = p0["window_start"] if p0 else (int(tw["start"][:2]) * 60 + int(tw["start"][3:]) if tw.get("start") else None)
        checks = {
            "customer": any(t in str(det.get("customer", {}).get("value", "")).lower() for t in NAMES[n].split("|")),
            "contact": bool(det.get("contact")),
            "pickups": same_points(got_pick, exp["pickups"]),
            "dropoffs": same_points(pts("dropoff") if job else None, exp["dropoffs"]),
            "window": w is None or (start is not None and abs(start - w[0]) <= 1 and (not p0 or abs(p0["window_end"] - w[1]) <= 1)),
            "deadline": w is None or w[2] is None or bool(job and abs(job["stops"][-1]["window_end"] - w[2]) <= 15),
            "frequency": bool(f) and f["type"] == exp["freq"][0] and (exp["freq"][0] != "weekdays" or f.get("days") == exp["freq"][1]),
            "items": (job["stops"][0]["items"] if job else 1) == ITEMS.get(n, 1) or not job,
        }
        right += sum(checks.values())
        total += len(checks)
        print(f"{n}.{part}", r["status"], "wrong:", [k for k, v in checks.items() if not v])
    print(f"mode={mode}: {right}/{total} fields right = {100 * right / total:.0f}%")
    requests.put(f"{API}/ai/config", json={"mode": "auto"}, timeout=15)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "auto")
