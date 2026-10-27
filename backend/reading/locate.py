"""Find each location: fictional directory, then geo_cache, then Nominatim (cached, 1 request a second)."""
import asyncio
import re
import time

import httpx

from core import db
from engine.jobs import DIR
from seed import data as D

UA = "Drivepast-demo/1.0 (Bayline Courier demo; contact demo@drivepast.example)"
VIEWBOX = "-122.55,37.95,-122.10,37.65"
AMBIGUOUS = {"broadway": ("Oakland", "San Francisco"), "mission st": ("San Francisco", "Oakland")}
GENERIC = {"lab", "center", "group", "the", "street", "st", "ave", "and", "of"}
NEIGHBORHOODS = {a.lower(): a for a in D.AREAS}
ABBR = [(r"\bstreet\b", "st"), (r"\bavenue\b", "ave"), (r"\bboulevard\b", "blvd"), (r"\bthird\b", "3rd"), (r"\bfourth\b", "4th")]
GEO_SEED = [
    ("4100 piedmont ave", "Oakland", 37.8281, -122.2538, False),
    ("5600 college ave", "Oakland", 37.8423, -122.2517, False),
    ("3100 telegraph ave", "Oakland", 37.8203, -122.2685, False),
    ("2000 university ave", "Berkeley", 37.8719, -122.2681, False),
    ("solano ave", "Berkeley", 37.8913, -122.2805, True),
    ("solano ave", "Albany", 37.8907, -122.2880, True),
    ("1100 gilman st", "Berkeley", 37.880562, -122.294721, False),
    ("700 parker st", "Berkeley", 37.857524, -122.297668, False),
    ("3220 grand ave", "Oakland", 37.8118801, -122.2476706, False),
    ("5600 bay st", "Emeryville", 37.833496, -122.293385, False),
]
_rate = {"lock": asyncio.Lock(), "last": 0.0}


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    for a, b in ABBR:
        s = re.sub(a, b, s)
    return re.sub(r"\s+", " ", s).strip()


def split_street(street):
    m = re.match(r"^(\d+)\s+(.*)$", norm(street))
    return (m.group(1), m.group(2)) if m else (None, norm(street))


def directory_hit(loc):
    text = norm(" ".join(filter(None, [loc.get("business_name"), loc.get("text")])))
    num, name = split_street(loc.get("street"))
    for d in DIR.values():
        low = norm(d["name"])
        toks = [w for w in low.split() if w not in GENERIC]
        named = low in text or (len(toks) >= 2 and all(re.search(rf"\b{w}\b", text) for w in toks))
        dn, dname = split_street(d["address"].split(",")[0])
        by_street = num and dn == num and dname.split()[0] == (name.split() or [""])[0]
        if named or by_street:
            return d
    return None


async def seed_geo_cache():
    for street, city, lat, lon, approx in GEO_SEED:
        await db.geo_cache.update_one({"key": f"{street}|{city.lower()}"},
                                      {"$setOnInsert": {"key": f"{street}|{city.lower()}", "street": street, "city": city, "lat": lat,
                                                        "lon": lon, "approximate": approx, "source": "geo_cache"}}, upsert=True)


async def cache_hit(street, city):
    key = norm(street)
    if city:
        return await db.geo_cache.find_one({"key": f"{key}|{norm(city)}"}, {"_id": 0})
    return await db.geo_cache.find_one({"street": key}, {"_id": 0}, sort=[("city", 1)])


_misses = {}  # q -> monotonic time of a failed lookup; not retried for 10 min so a slow Nominatim can't stall every read


async def nominatim(street, city):
    q = f"{street}, {city or ''}, California".replace(", ,", ",")
    if time.monotonic() - _misses.get(q, -1e9) < 600:
        return None
    async with _rate["lock"]:
        wait = 1.0 - (time.monotonic() - _rate["last"])
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(timeout=4, headers={"User-Agent": UA}) as c:
                r = await c.get("https://nominatim.openstreetmap.org/search",
                                params={"q": q, "format": "jsonv2", "limit": 1, "viewbox": VIEWBOX, "bounded": 1, "addressdetails": 1})
            hits = r.json() if r.status_code == 200 else []
        except (httpx.HTTPError, ValueError):
            hits = []
        finally:
            _rate["last"] = time.monotonic()
    if not hits:
        _misses[q] = time.monotonic()
        return None
    h = hits[0]
    a = h.get("address", {})
    found_city = city or a.get("city") or a.get("town") or ""
    doc = {"key": f"{norm(street)}|{norm(found_city)}", "street": norm(street), "city": found_city, "lat": float(h["lat"]),
           "lon": float(h["lon"]), "approximate": False, "source": "nominatim"}
    await db.geo_cache.update_one({"key": doc["key"]}, {"$set": doc}, upsert=True)
    return doc


def _point(name, address, lat, lon, source, approximate=False, hours=None, city=None):
    return {"found": True, "name": name, "address": address, "lat": lat, "lon": lon, "source": source,
            "approximate": approximate, "hours": hours, "city": city}


async def resolve(loc):
    """Returns a dict with found/name/address/lat/lon/source/approximate and, when stuck, a problem."""
    d = directory_hit(loc)
    if d:
        return _point(d["name"], d["address"], d["lat"], d["lon"], "directory", hours=d["hours"], city=d["address"].split(",")[-1].strip())
    street, city = (loc.get("street") or "").strip(), (loc.get("city") or "").strip() or None
    num, name = split_street(street)
    if street and not city and (name in AMBIGUOUS or name.split(" ")[0] in AMBIGUOUS):
        cities = AMBIGUOUS.get(name) or AMBIGUOUS[name.split(" ")[0]]
        pretty = street if num else street.title()
        q = (f"Which city is {pretty} in, {cities[0]} or {cities[1]}?" if num else
             f"Where on {pretty} should we go, and is it in {cities[0]} or {cities[1]}?")
        return {"found": False, "problem": q, "problem_kind": "ambiguous", "street": pretty}
    if street:
        hit = await cache_hit(street, city)
        if not hit and num:
            hit = await nominatim(street, city)
        if hit:
            label = f"{street.title() if not num else street}, {hit['city']}" + (" (approximate)" if hit.get("approximate") else "")
            return _point(label.split(",")[0], label, hit["lat"], hit["lon"], hit.get("source", "geo_cache"),
                          bool(hit.get("approximate")) or not num, city=hit["city"])
        return {"found": False, "problem": f"We couldn't find {loc.get('text') or street}.", "problem_kind": "not_found"}
    area = None
    for cand in (loc.get("text"), loc.get("business_name"), city):
        low = norm(cand)
        area = NEIGHBORHOODS.get(low) or next((v for k, v in NEIGHBORHOODS.items() if low and re.search(rf"\b{k}\b", low)), None)
        if area:
            break
    if area:
        lat, lon = D.AREAS[area]
        return _point(area, f"{area} (approximate)", lat, lon, "area", True, city=area)
    where = city or loc.get("text") or "the area"
    what = "delivery" if loc.get("kind") == "dropoff" else "pickup"
    return {"found": False, "problem": f"We need the {what} addresses in {where}.", "problem_kind": "missing", "what": what}
