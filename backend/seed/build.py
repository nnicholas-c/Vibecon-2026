"""Deterministic Bayline Courier seed builder. Returns plain documents per collection."""
import math
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from engine.timing import compute_route, fmt_time, haversine_miles, leg
from models import (Business, DirectoryEntry, Prospect, RoutePlan, RunRecord, Settings, Stop, Unit)
from seed import data as D

PACIFIC = ZoneInfo("America/Los_Angeles")
SHIFT_START, SHIFT_END = 480, 1020
PRICES = [9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0]
WIDTHS = [60, 75, 90, 90, 105, 120]


def ceil5(x):
    return int(math.ceil(x / 5.0 - 1e-9) * 5)


def round5(x):
    return int(5 * math.floor(x / 5.0 + 0.5))


def offset_point(rng, lat, lon, max_miles, min_miles=0.0):
    r = min_miles + (max_miles - min_miles) * math.sqrt(rng.random())
    th = rng.random() * 2 * math.pi
    return (lat + r * math.cos(th) / 69.0, lon + r * math.sin(th) / (69.0 * math.cos(math.radians(lat))))


def nearest_order(points, start, end=None):
    """Open path from start through every point toward end: nearest-neighbor, then 2-opt untangling."""
    left, out, cur = list(points), [], start
    while left:
        nxt = min(left, key=lambda p: haversine_miles(cur[0], cur[1], p[0], p[1]))
        left.remove(nxt)
        out.append(nxt)
        cur = nxt
    if end is None:
        return out
    d = lambda a, b: haversine_miles(a[0], a[1], b[0], b[1])  # noqa: E731
    path, improved = [start, *out, end], True
    while improved:
        improved = False
        for i in range(1, len(path) - 2):
            for j in range(i + 1, len(path) - 1):
                if d(path[i - 1], path[j]) + d(path[i], path[j + 1]) < d(path[i - 1], path[i]) + d(path[j], path[j + 1]) - 1e-9:
                    path[i:j + 1] = path[i:j + 1][::-1]
                    improved = True
    return path[1:-1]


class Namer:
    def __init__(self, rng):
        self.rng = rng
        self.used = {d[0] for d in D.DIRECTORY}

    def make(self, ctype, area, street):
        st = street.split(" ")[0] if not street[0].isdigit() else street.replace(" St", "")
        for _ in range(60):
            s, s2 = self.rng.sample(D.SURNAMES, 2)
            name = self.rng.choice(D.TEMPLATES[ctype]).format(
                w=self.rng.choice(D.WORDS), s=s, s2=s2, a=D.AREA_SHORT[area], st=st)
            if name not in self.used:
                self.used.add(name)
                return name
        name = f"{D.AREA_SHORT[area]} {ctype} {len(self.used)}"
        self.used.add(name)
        return name


def service_samples(rng, planned, n=20):
    return [round(min(6.0, max(3.0, planned + rng.uniform(-1.0, 1.5))), 1) for _ in range(n)]


def make_area_stops(rng, namer, used_addresses, area, count, prev, nxt=None):
    city, streets = D.STREETS[area]
    clat, clon = D.AREAS[area]
    edge = D.SHORELINE_LON.get(area)
    raw = [offset_point(rng, clat, clon, 0.5) for _ in range(count)]
    raw = [(la, lo if edge is None or lo <= edge else 2 * edge - lo) for la, lo in raw]
    pts = nearest_order(raw, prev, nxt)
    out = []
    for lat, lon in pts:
        street, lo, hi = rng.choice(streets)
        while True:
            num = lo + rng.randrange(0, max(1, hi - lo))
            address = f"{num} {street}, {city}"
            if address not in used_addresses:
                break
        used_addresses.add(address)
        ctype = rng.choice(D.AREA_TYPES[area])
        out.append({
            "customer_name": namer.make(ctype, area, street), "customer_type": ctype,
            "address": address, "street": street, "city": city, "area": area,
            "lat": round(lat, 6), "lon": round(lon, 6),
            "kind": "dropoff" if rng.random() < 0.25 else "pickup",
            "service_minutes": rng.randint(3, 6), "price_per_visit": rng.choice(PRICES),
        })
    return out


def avg2(values):
    return round(sum(values) / len(values), 2)


STEP_MAX, RETURN_BUFFER = 28, 20


def timing_pass(unit, segments, s, late_pm):
    """Spread windows across the shift so consecutive arrivals are at most STEP_MAX minutes apart (no long idle gaps)."""
    ordered = [st for sg in segments for st in sg["stops"]]
    pos, legs = unit["start_location"], []
    for st in ordered:
        legs.append(leg(pos, st, s)[1])
        pos = st
    ret = leg(pos, unit["end_location"], s)[1]
    svc = [avg2(st["_samples"]) for st in ordered]
    first = SHIFT_START + legs[0]
    n = len(ordered)
    step = min(STEP_MAX, (SHIFT_END - RETURN_BUFFER - ret - svc[-1] - first) / (n - 1)) if n > 1 else 0
    act = None
    for k, st in enumerate(ordered):
        ready = first if k == 0 else act + svc[k - 1] + legs[k]
        ws = int(math.floor(max(ready, first + k * step)))
        width = 60 if (late_pm and ws >= 720) else st["_width"]
        st["window_start"], st["window_end"] = max(SHIFT_START, ws), int(min(ws + width, 1080))
        act = max(ready, st["window_start"])


def weekdays_before(demo_date, n=20):
    out, d = [], demo_date - timedelta(days=1)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


def arrival_delta(rng, late):
    r = rng.random()
    if late:
        if r < 0.5:
            return rng.uniform(-5, 10)
        return rng.uniform(10, 25) if r < 0.75 else rng.uniform(25, 70)
    if r < 0.86:
        return rng.uniform(-5, 10)
    return rng.uniform(10, 20) if r < 0.96 else rng.uniform(20, 40)


DEMO_STOPS = 8
KEEP_STREETS = {"van-2": ("Telegraph", "Racine", "Clarke")}  # keeps Van 2 passing the demo requests' areas


def pick_demo_stops(ordered, keep):
    """Step 16: 8 stops per van, spread across the shift, keeping the stops on `keep` streets."""
    n = len(ordered)
    chosen = {next(i for i, st in enumerate(ordered) if w in st["address"]) for w in keep if any(w in st["address"] for st in ordered)}
    for k in range(DEMO_STOPS):
        t = round(k * (n - 1) / (DEMO_STOPS - 1))
        if len(chosen) < DEMO_STOPS and all(abs(t - c) > 1 for c in chosen):
            chosen.add(t)
    for i in range(n):
        if len(chosen) >= DEMO_STOPS:
            break
        chosen.add(i)
    return [ordered[i] for i in sorted(chosen)[:DEMO_STOPS]]


def build_seed(demo_date, team_numbers):
    rng = random.Random(D.SEED_NUMBER)
    s_model = Settings(team_numbers=list(team_numbers), floor_one_off=15, usual_one_off=55, markup_pct=100,
                       auto_send_cheapest=True, demo_clock_minutes=600)
    s = s_model.model_dump()
    now_iso = datetime.now(timezone.utc).isoformat()
    namer, used_addresses = Namer(rng), set()
    business = Business(
        key=D.BUSINESS_KEY, name="Bayline Courier", type="courier", settings=s_model,
        owner_name=D.OWNER_NAME, tagline=D.TAGLINE, depot=D.DEPOT, timezone="America/Los_Angeles",
        demo_date=demo_date.isoformat(), seeded_at=now_iso,
    )

    units, stops, runs, plans = [], [], [], []
    run_dates = weekdays_before(demo_date)
    for van in D.VANS:
        base = D.DEPOT if van["base"] == "depot" else D.SOMA_LOT
        unit = {
            "key": van["key"], "business_key": D.BUSINESS_KEY, "kind": "van", "name": van["name"],
            "nickname": van["nickname"], "driver_name": van["driver"], "driver_phone": van["phone"],
            "color": van["color"], "shift_start": SHIFT_START, "shift_end": SHIFT_END,
            "start_location": dict(base), "end_location": dict(base), "capacity": 40, "skills": [],
            "areas": sorted({sg["area"] if sg["type"] == "area" else sg["stop"]["area"] for sg in van["segments"]}),
        }
        segments, prev = [], (base["lat"], base["lon"])
        heads = [(sg["stop"]["lat"], sg["stop"]["lon"]) if sg["type"] == "fixed" else D.AREAS[sg["area"]] for sg in van["segments"]]
        for si, sg in enumerate(van["segments"]):
            nxt = heads[si + 1] if si + 1 < len(heads) else (base["lat"], base["lon"])
            items = [dict(sg["stop"])] if sg["type"] == "fixed" else make_area_stops(
                rng, namer, used_addresses, sg["area"], sg["count"], prev, nxt)
            for st in items:
                st["_samples"] = service_samples(rng, st["service_minutes"])
                st["_width"] = rng.choice(WIDTHS)
                st["_margin"] = rng.uniform(18, 45)
                st["_margin_tight"] = rng.uniform(12, 18)
            segments.append({"at": sg["at"], "stops": items, "fixed": sg["type"] == "fixed"})
            prev = (items[-1]["lat"], items[-1]["lon"])

        late_pm = bool(van.get("late_afternoons"))
        timing_pass(unit, segments, s, late_pm)

        ordered = pick_demo_stops([st for sg in segments for st in sg["stops"]], KEEP_STREETS.get(van["key"], ()))
        unit_stops = []
        for i, st in enumerate(ordered):
            st["key"] = f"{van['key']}-s{i + 1:02d}"
            unit_stops.append({
                "key": st["key"], "business_key": D.BUSINESS_KEY, "unit_key": van["key"], "seq": i + 1,
                "customer_name": st["customer_name"], "customer_type": st["customer_type"],
                "address": st["address"], "street": st["street"], "city": st["city"], "area": st["area"],
                "lat": st["lat"], "lon": st["lon"], "kind": st["kind"], "items": 1,
                "window_start": st["window_start"], "window_end": st["window_end"],
                "service_minutes": st["service_minutes"], "recurrence": "weekday", "weekdays": None,
                "date": None, "price_per_visit": st["price_per_visit"], "paired_stop_key": None,
                "source": "seed", "created_at": now_iso,
            })
        service_map = {st["key"]: avg2(st["_samples"]) for st in ordered}
        result = compute_route(unit, unit_stops, s, service_map)
        plans.append(RoutePlan(
            key=f"{van['key']}-weekday-v1", business_key=D.BUSINESS_KEY, unit_key=van["key"],
            day_type="weekday", date=None, version=1, is_current=True, computed_at=now_iso, **result,
        ).to_mongo())

        arrivals = {r["stop_key"]: r["arrival"] for r in result["stops"]}
        for st in ordered:
            planned = arrivals[st["key"]]
            late = late_pm and st["window_start"] >= 720
            for di, d in enumerate(run_dates):
                actual = round(max(planned + arrival_delta(rng, late), st["window_start"]), 1)
                runs.append(RunRecord(
                    business_key=D.BUSINESS_KEY, unit_key=van["key"], stop_key=st["key"], date=d.isoformat(),
                    planned_arrival=planned, actual_arrival=actual, actual_service_minutes=st["_samples"][di],
                    window_start=st["window_start"], window_end=st["window_end"],
                    on_time=st["window_start"] <= actual <= st["window_end"],
                ).to_mongo())
        for us, r in zip(unit_stops, result["stops"]):
            us["_arrival"] = r["arrival"]
        units.append(Unit(**unit).to_mongo())
        stops.extend(unit_stops)

    prospects = build_prospects(rng, namer, stops)
    for st in stops:
        st.pop("_arrival", None)
    stops = [Stop(**st).to_mongo() for st in stops]

    directory = [DirectoryEntry(
        key=f"dir-{i + 1:02d}", business_key=D.BUSINESS_KEY, name=n, address=a, lat=la, lon=lo, category=c,
        hours={"days": "Every day" if o == 0 and cl == 1440 else "Mon to Fri", "open": o, "close": cl, "label": lbl},
        phone=ph,
    ).to_mongo() for i, (n, a, la, lo, c, o, cl, lbl, ph) in enumerate(D.DIRECTORY)]

    requests = []  # step 16: Reset leaves the inbox empty (and makes zero model calls)

    return {
        "businesses": [business.to_mongo()], "units": units, "stops": stops, "route_plans": plans,
        "run_history": runs, "directory": directory, "prospects": prospects, "requests": requests,
    }


def build_prospects(rng, namer, stops, count=40):
    by_unit = {}
    for st in stops:
        by_unit.setdefault(st["unit_key"], []).append(st)
    unit_keys = sorted(by_unit)
    out = []
    for i in range(count):
        anchor = rng.choice(by_unit[unit_keys[i % len(unit_keys)]])
        lat, lon = offset_point(rng, anchor["lat"], anchor["lon"], 0.16, 0.04)
        cat, tag, open_m, close_m = rng.choice(D.PROSPECT_CATEGORIES)
        nearest = min(stops, key=lambda x, lat=lat, lon=lon: haversine_miles(lat, lon, x["lat"], x["lon"]))
        dist_m = haversine_miles(lat, lon, nearest["lat"], nearest["lon"]) * 1609.34
        num = int(anchor["address"].split(" ")[0]) + rng.choice([-40, -24, -12, 12, 26, 38]) if anchor["address"][0].isdigit() else 100
        out.append(Prospect(
            key=f"prospect-{i + 1:02d}", business_key=D.BUSINESS_KEY, unit_key=nearest["unit_key"],
            name=namer.make(cat, anchor["area"], anchor["street"]), category=cat, osm_tag=tag,
            address=f"{max(1, num)} {anchor['street']}, {anchor['city']}", lat=round(lat, 6), lon=round(lon, 6),
            phone=f"({'415' if anchor['city'] == 'San Francisco' else '510'}) 555-{2100 + i:04d}", website=None,
            opening_hours={"open": open_m, "close": close_m, "label": f"{fmt_time(open_m)} to {fmt_time(close_m)}"},
            source="seed", distance_to_route_m=round(dist_m, 1), nearest_stop_key=nearest["key"],
            pass_by_time=nearest["_arrival"], pass_by_label=fmt_time(nearest["_arrival"]),
            added_minutes=None, cost_to_serve=None, suggested_price=None, monthly_margin=None,
            fit_score=None, fit_reason=None, offer_text=None, status="new",
        ).to_mongo())
    return out
