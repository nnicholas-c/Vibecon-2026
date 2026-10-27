"""Cached travel matrix (travel_matrix collection) plus on-the-fly legs for new points."""
from engine.timing import leg

TRAVEL_KEYS = ("road_factor", "speed_sf_mph", "speed_eastbay_mph", "speed_cross_mph", "bridge_minutes")
_cache = {"sig": None, "pairs": {}}


def signature(s):
    return [float(s[k]) for k in TRAVEL_KEYS]


def node_key(p):
    key = p.get("key")
    if key and not key.startswith("new:"):
        return key
    return f"pt:{p['lat']:.6f},{p['lon']:.6f}"


def make_travel(s):
    """Return travel(a, b) -> (miles, minutes) using the cache, computing and memoizing new legs."""
    sig = signature(s)
    if _cache["sig"] != sig:
        _cache["sig"], _cache["pairs"] = sig, {}
    pairs = _cache["pairs"]

    def travel(a, b):
        k = (node_key(a), node_key(b))
        hit = pairs.get(k)
        if hit is None:
            hit = pairs[k] = leg(a, b, s)
        return hit

    return travel


async def build_matrix(db, s, points):
    """Precompute every pair among seeded stops and start/end locations and store it."""
    _cache["sig"], _cache["pairs"] = signature(s), {}
    travel = make_travel(s)
    docs = []
    for a in points:
        row = []
        for b in points:
            if a is not b:
                miles, mins = travel(a, b)
                row.append([node_key(b), miles, mins])
        docs.append({"origin": node_key(a), "sig": signature(s), "dest": row})
    await db.travel_matrix.delete_many({})
    if docs:
        await db.travel_matrix.insert_many(docs)
    return len(points) * (len(points) - 1)


def invalidate():
    _cache["sig"], _cache["pairs"] = None, {}
