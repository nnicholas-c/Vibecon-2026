"""Owner rules the engine enforces: 'van X not to area A after time T'. Other rules are assistant instructions only."""
import re

NEGATIVE = re.compile(r"\b(don'?t|do not|never|no|not|avoid|stop)\b", re.I)
VAN = re.compile(r"\bvan[\s-]*(\d+)\b", re.I)
AFTER = re.compile(r"\bafter\s+(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?", re.I)
AREAS = (("downtown", re.compile(r"\bdowntown\b", re.I)), ("sf", re.compile(r"\b(sf|san francisco)\b", re.I)))
AREA_NAMES = {"downtown": "Downtown Oakland", "sf": "San Francisco"}
DOWNTOWN = (37.795, 37.8135, -122.283, -122.262)
SF_EAST_LON = -122.355


def parse_rule(text):
    t = text.replace("\u2019", "'")
    van, after = VAN.search(t), AFTER.search(t)
    area = next((k for k, rx in AREAS if rx.search(t)), None)
    if not (NEGATIVE.search(t) and van and after and area):
        return None
    h, m, ap = int(after.group(1)), int(after.group(2) or 0), (after.group(3) or "").lower().replace(".", "")
    if ap == "pm" and h < 12:
        h += 12
    elif ap == "am" and h == 12:
        h = 0
    elif not ap and 1 <= h <= 7:
        h += 12
    if h > 23 or m > 59:
        return None
    return {"van": f"van-{van.group(1)}", "area": area, "after_minutes": h * 60 + m}


def in_area(stop, area):
    lat, lon = stop.get("lat"), stop.get("lon")
    if lat is None or lon is None:
        return False
    if area == "sf":
        return lon < SF_EAST_LON
    s, n, w, e = DOWNTOWN
    return s <= lat <= n and w <= lon <= e


def active_rules(docs):
    out = []
    for d in docs:
        p = parse_rule(d.get("text") or "")
        if d.get("active") and p:
            out.append({**p, "id": str(d["_id"]), "text": d["text"]})
    return out


def breaks(cand, rule):
    if cand["unit_key"] != rule["van"]:
        return False
    return any(in_area(n, rule["area"]) and n.get("arrival", 0) > rule["after_minutes"] for n in cand.get("new_stops") or [])


def apply_rules(cands, rules):
    """Drop candidates that break an active rule. Returns (kept, blocked rows, one per van)."""
    kept, blocked = [], {}
    for c in cands:
        hit = next((r for r in rules if breaks(c, r)), None)
        if hit:
            blocked.setdefault(c["unit_key"], {"unit_key": c["unit_key"], "unit_name": c["unit_name"], "rule_id": hit["id"],
                                               "reason": f"{c['unit_name']} can't: your rule '{hit['text']}'"})
        else:
            kept.append(c)
    return kept, list(blocked.values())


def rules_sig(rules):
    return ",".join(sorted(r["id"] for r in rules))
