"""Route timing in plain Python. Reused by the Phase 2 insertion engine."""
import math

EARTH_RADIUS_MILES = 3958.8
SF_EAST_EDGE_LON = -122.35
EPS = 1e-6


def haversine_miles(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def in_sf(point):
    return point["lon"] < SF_EAST_EDGE_LON


def leg(a, b, s):
    """Return (road miles, minutes) between two points using the settings travel model."""
    miles = haversine_miles(a["lat"], a["lon"], b["lat"], b["lon"]) * s["road_factor"]
    a_sf, b_sf = in_sf(a), in_sf(b)
    if a_sf and b_sf:
        return miles, miles / s["speed_sf_mph"] * 60
    if not a_sf and not b_sf:
        return miles, miles / s["speed_eastbay_mph"] * 60
    return miles, miles / s["speed_cross_mph"] * 60 + s["bridge_minutes"]


def fmt_time(minutes):
    """Minutes since midnight -> '1:50pm'."""
    if minutes is None:
        return ""
    total = int(math.floor(minutes + 0.5)) % 1440
    h, m = divmod(total, 60)
    suffix = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}{suffix}"


def compute_route(unit, stops, s, service_minutes=None, travel=None):
    """Time an ordered stop list for one unit. service_minutes maps stop key -> learned minutes."""
    service_minutes = service_minutes or {}
    travel = travel or (lambda a, b: leg(a, b, s))
    shift_start, shift_end = float(unit["shift_start"]), float(unit["shift_end"])
    capacity = unit.get("capacity")
    t, pos, load = shift_start, unit["start_location"], 0
    rows, problems = [], []
    total_miles = drive_total = wait_total = service_total = 0.0

    for i, stop in enumerate(stops):
        miles, mins = travel(pos, stop)
        ready = t + mins
        arrival = max(ready, float(stop["window_start"]))
        wait = arrival - ready
        service = float(service_minutes.get(stop["key"], stop["service_minutes"]))
        departure = arrival + service
        if stop.get("done_at") is not None:
            # Marked done by the driver: later stops re-time from the done time.
            departure = float(stop["done_at"])
            arrival = min(arrival, departure)
            wait = max(0.0, arrival - ready)
            service = departure - arrival
        in_window = arrival <= stop["window_end"] + EPS
        items = stop.get("items", 1)
        load = load + items if stop.get("kind") != "dropoff" else max(0, load - items)
        if not in_window:
            problems.append(
                f"Gets to {stop.get('customer_name', 'a stop')} at {fmt_time(arrival)}, "
                f"after its window closes at {fmt_time(stop['window_end'])}."
            )
        if capacity is not None and load > capacity:
            problems.append(f"Carries more than {capacity} items after {stop.get('customer_name', 'a stop')}.")
        rows.append({
            "stop_key": stop["key"],
            "seq": i + 1,
            "travel_miles": round(miles, 3),
            "travel_minutes": round(mins, 2),
            "ready_at": round(ready, 2),
            "arrival": round(arrival, 2),
            "wait_minutes": round(wait, 2),
            "service_minutes_used": round(service, 2),
            "departure": round(departure, 2),
            "in_window": in_window,
            "load_after": load,
        })
        total_miles += miles
        drive_total += mins
        wait_total += wait
        service_total += service
        t, pos = departure, stop

    miles, mins = travel(pos, unit["end_location"])
    return_time = t + mins
    total_miles += miles
    drive_total += mins
    if return_time > shift_end + EPS:
        problems.append(f"Gets back at {fmt_time(return_time)}, after the shift ends at {fmt_time(shift_end)}.")

    duration = return_time - shift_start
    spare = (shift_end - shift_start) - drive_total - service_total
    return {
        "stops": rows,
        "start_departure": shift_start,
        "return_leg_miles": round(miles, 3),
        "return_leg_minutes": round(mins, 2),
        "return_time": round(return_time, 2),
        "total_minutes": round(duration, 2),
        "total_miles": round(total_miles, 2),
        "driving_minutes": round(drive_total, 2),
        "waiting_minutes": round(wait_total, 2),
        "service_minutes": round(service_total, 2),
        "spare_minutes_exact": round(spare, 2),
        "spare_minutes": int(math.floor(spare + 0.5)),
        "feasible": not problems,
        "problems": problems,
    }
