import math

from core import BKEY, db
from engine.timing import fmt_time


def _bearing(a, b):
    y = math.sin(math.radians(b[1] - a[1])) * math.cos(math.radians(b[0]))
    x = math.cos(math.radians(a[0])) * math.sin(math.radians(b[0])) - math.sin(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.cos(math.radians(b[1] - a[1]))
    return round((math.degrees(math.atan2(y, x)) + 360) % 360)


def van_position(plan, coords, start, end, clock):
    """Where the van is at the demo clock, interpolated along its planned route."""
    if not plan or not plan.stops:
        return {"lat": start["lat"], "lon": start["lon"], "heading": 0, "state": "depot", "next_index": 0}
    s0, e0 = (start["lat"], start["lon"]), (end["lat"], end["lon"])
    legs = [(plan.start_departure, s0, None)]
    for i, r in enumerate(plan.stops):
        p = coords[r["stop_key"]]
        if clock < r["arrival"]:
            t0, a, _ = legs[-1]
            f = 0 if clock <= t0 else (clock - t0) / max(r["arrival"] - t0, 1e-6)
            state = "not_started" if clock < plan.start_departure else "driving"
            return {"lat": a[0] + (p[0] - a[0]) * f, "lon": a[1] + (p[1] - a[1]) * f, "heading": _bearing(a, p), "state": state, "next_index": i}
        if clock < r["departure"]:
            nxt = coords[plan.stops[i + 1]["stop_key"]] if i + 1 < len(plan.stops) else e0
            return {"lat": p[0], "lon": p[1], "heading": _bearing(p, nxt), "state": "at_stop", "next_index": i}
        legs.append((r["departure"], p, i))
    t0, a, _ = legs[-1]
    if clock >= plan.return_time:
        return {"lat": e0[0], "lon": e0[1], "heading": _bearing(a, e0), "state": "back", "next_index": len(plan.stops)}
    f = (clock - t0) / max(plan.return_time - t0, 1e-6)
    return {"lat": a[0] + (e0[0] - a[0]) * f, "lon": a[1] + (e0[1] - a[1]) * f, "heading": _bearing(a, e0), "state": "returning", "next_index": len(plan.stops)}


async def late_insight(unit_key):
    """Flag the time of day when this van runs late most, from run history."""
    runs = await db.run_history.find({"business_key": BKEY, "unit_key": unit_key}, {"_id": 0, "window_start": 1, "on_time": 1}).to_list(None)
    if not runs:
        return None
    overall = sum(r["on_time"] for r in runs) / len(runs)
    worst = None
    for cut in (720, 780, 840, 900):
        part = [r for r in runs if r["window_start"] >= cut]
        if len(part) < 10:
            continue
        rate = sum(r["on_time"] for r in part) / len(part)
        if worst is None or rate < worst[1]:
            worst = (cut, rate)
    if not worst or worst[1] >= 0.9 or overall - worst[1] < 0.05:
        return None
    label = fmt_time(worst[0]).replace(":00", "").replace(" ", "")
    return {"text": f"Late most often after {label}: {round(worst[1] * 100)}% on time", "after_minutes": worst[0], "on_time_rate": round(worst[1], 3)}
