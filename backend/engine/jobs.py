"""Structured jobs: hand-built versions of the seeded requests, validation and one-line summaries."""
from datetime import date, timedelta

from engine.timing import fmt_time
from seed import data as D

DIR = {d[0]: {"name": d[0], "address": d[1], "lat": d[2], "lon": d[3], "hours": {"open": d[5], "close": d[6]}} for d in D.DIRECTORY}
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri"]


def _d(biz, ref, kind, ws, we, **extra):
    return {**DIR[biz], "ref": ref, "kind": kind, "window_start": ws, "window_end": we, "items": 1, **extra}


def _pt(ref, kind, name, address, lat, lon, ws, we, **extra):
    return {"ref": ref, "kind": kind, "name": name, "address": address, "lat": lat, "lon": lon,
            "window_start": ws, "window_end": we, "items": 1, "hours": None, **extra}


def next_weekday(d):
    d = d + timedelta(days=1)
    while d.weekday() > 4:
        d += timedelta(days=1)
    return d


def next_monday(d):
    return d + timedelta(days=(7 - d.weekday()) or 7)


def seed_jobs(demo_date: date):
    today = demo_date.isoformat()
    r1 = {"stops": [_d("Temescal Diagnostics Lab", "p1", "pickup", 825, 855),
                    _d("Ashby Medical Center", "d1", "dropoff", None, 915)],
          "pairs": [["p1", "d1"]], "frequency": {"type": "weekday", "start_date": next_monday(demo_date).isoformat()},
          "notes": "\"Around 2\" read as 1:45pm to 2:15pm. Drop-off within about an hour."}
    jobs = {
        1: ("ready", r1, None),
        2: ("ready", {"stops": [_d("Clay Street Law Group", "p1", "pickup", 480, 900, items=2),
                                _d("Fallon Street Courthouse", "d1", "dropoff", None, 900, items=2)],
                      "pairs": [["p1", "d1"]], "frequency": {"type": "one_off", "date": today},
                      "notes": "Same day, delivered by 3pm, 2 boxes."}, None),
        3: ("ready", {"stops": [_d("Third Street Print", "p1", "pickup", 660, 675),
                                _d("Montgomery Partners", "d1", "dropoff", None, 735)],
                      "pairs": [["p1", "d1"]], "frequency": {"type": "weekdays", "days": ["mon", "thu"]},
                      "notes": "\"At 11\" read as 11:00 to 11:15am. Drop-off within about an hour."}, None),
        4: ("ready", {"stops": [_d("Lakeshore Dental", "p1", "pickup", 1020, 1035),
                                _d("Piedmont Ave Lab", "d1", "dropoff", None, 1080)],
                      "pairs": [["p1", "d1"]], "frequency": {"type": "one_off", "date": today},
                      "notes": "Asked for 5pm today. Lakeshore Dental closes at 4:30pm."}, None),
        5: ("ready", {"stops": [_pt("p1", "pickup", "Clinic at 4100 Piedmont", "4100 Piedmont Ave, Oakland", 37.8281, -122.2538, 900, 960),
                                _pt("p2", "pickup", "Clinic at 5600 College", "5600 College Ave, Oakland", 37.8423, -122.2517, 900, 960),
                                _pt("p3", "pickup", "Clinic at 3100 Telegraph", "3100 Telegraph Ave, Oakland", 37.8203, -122.2685, 900, 960),
                                _d("Elmwood Pharmacy", "p4", "pickup", 900, 960, name="Clinic at 2900 College"),
                                _d("Emeryville Central Lab", "d1", "dropoff", None, 1020)],
                      "pairs": [["p1", "d1"], ["p2", "d1"], ["p3", "d1"], ["p4", "d1"]],
                      "frequency": {"type": "weekday", "start_date": None},
                      "notes": "Locations placed by hand. 3100 Telegraph Ave assumed to be in Oakland."}, None),
        6: ("cant_price", None, "The five delivery addresses in Montclair are missing, so there's nothing to place on a route yet."),
        7: ("cant_price", None, "The city is unclear: there's a 1450 Broadway and a Mission St in both Oakland and San Francisco."),
        8: ("ready", {"stops": [_pt("p1", "pickup", "Pickup at 2000 University", "2000 University Ave, Berkeley", 37.8719, -122.2681, 480, 495),
                                _pt("d1", "dropoff", "Mission Bay", "Mission Bay, San Francisco (approximate)", 37.7680, -122.3920, None, 495, approximate=True)],
                      "pairs": [["p1", "d1"]], "frequency": {"type": "one_off", "date": next_weekday(demo_date).isoformat()},
                      "notes": "No date given, so priced for the next weekday morning. Mission Bay placed at its center."}, None),
        9: ("ready", r1, None),
        10: ("ready", {"stops": [_d("Elmwood Pharmacy", "p1", "pickup", 690, 705),
                                 _pt("d1", "dropoff", "Drop 1 on Solano Ave", "Solano Ave, Berkeley (approximate)", 37.8913, -122.2805, None, 765, approximate=True),
                                 _pt("d2", "dropoff", "Drop 2 on Solano Ave", "Solano Ave, Albany (approximate)", 37.8907, -122.2880, None, 765, approximate=True)],
                       "pairs": [["p1", "d1"], ["p1", "d2"]], "frequency": {"type": "weekday", "start_date": None},
                       "notes": "The two Solano Ave drops have no house numbers, so they're placed approximately."}, None),
    }
    return {n: {"job_status": st, "job": job, "job_reason": why, "job_summary": summarize(job) if job else why}
            for n, (st, job, why) in jobs.items()}


def freq_text(f):
    if f["type"] == "one_off":
        return f"One-off on {date.fromisoformat(f['date']).strftime('%a, %b ')}{date.fromisoformat(f['date']).day}."
    if f["type"] == "weekdays":
        from engine.pricing import join_days
        return f"Every week on {join_days(f['days'])}."
    start = f.get("start_date")
    return f"Every weekday{' from ' + date.fromisoformat(start).strftime('%a, %b ') + str(date.fromisoformat(start).day) if start else ''}."


def summarize(job):
    parts = []
    for js in job["stops"]:
        where = js["name"] if js["name"] in DIR else js["address"]
        if js["kind"] == "dropoff":
            parts.append(f"drop-off at {where} by {fmt_time(js['window_end'])}")
        else:
            parts.append(f"pickup at {where} {fmt_time(js['window_start'])} to {fmt_time(js['window_end'])}")
    text = ", ".join(parts)
    return f"{text[0].upper()}{text[1:]}. {freq_text(job['frequency'])}"


def validate_job(job):
    """Return a plain-words problem, or None when the job can be priced."""
    if not isinstance(job, dict) or not job.get("stops"):
        return "This job has no stops to price."
    refs = set()
    for i, js in enumerate(job["stops"], 1):
        if not isinstance(js, dict) or not isinstance(js.get("lat"), (int, float)) or not isinstance(js.get("lon"), (int, float)):
            return f"Stop {i} has no location yet, so it can't be priced."
        if js.get("kind") not in ("pickup", "dropoff", "job"):
            return f"Stop {i} needs to be a pickup, a drop-off or a job."
        ws, we = js.get("window_start"), js.get("window_end")
        for v in (ws, we):
            if v is not None and (not isinstance(v, (int, float)) or not 0 <= v <= 1440):
                return f"Stop {i} has a time that isn't a time of day."
        if ws is not None and we is not None and we < ws:
            return f"Stop {i}'s time window ends before it starts."
        if js.get("service_minutes") is not None and (not isinstance(js["service_minutes"], (int, float)) or js["service_minutes"] <= 0):
            return f"Stop {i} needs stop minutes above 0."
        js.setdefault("ref", f"s{i}")
        refs.add(js["ref"])
    for pair in job.get("pairs") or []:
        if len(pair) != 2 or pair[0] not in refs or pair[1] not in refs:
            return "A pickup and drop-off pair points to a stop that isn't in the job."
    f = job.get("frequency") or {}
    if f.get("type") == "one_off":
        try:
            date.fromisoformat(f.get("date") or "")
        except ValueError:
            return "A one-off job needs a date."
    elif f.get("type") == "weekdays":
        if not f.get("days") or any(d not in WEEKDAYS for d in f["days"]):
            return "Pick at least one weekday, Monday to Friday."
    elif f.get("type") != "weekday":
        return "Say how often: one day, every weekday, or certain weekdays."
    return None
