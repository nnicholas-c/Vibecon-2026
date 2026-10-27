"""Turn record_request fields into details with confidence marks, problems (checked in code), a job and a summary."""
import re
from datetime import date, datetime

from engine.jobs import freq_text, next_monday, next_weekday, summarize, validate_job
from engine.timing import fmt_time

RANK = {"high": 3, "medium": 2, "low": 1}
NAME = {3: "high", 2: "medium", 1: "low"}
CAP = {"directory": "high", "geo_cache": "medium", "nominatim": "medium", "area": "low"}
VAGUE = re.compile(r"around|about|afternoon|morning|ish|evening", re.I)
SERVICE = 4


def lower(*marks):
    return NAME[min(RANK.get(m or "medium", 2) for m in marks)]


def mins(t):
    m = re.match(r"^(\d{1,2}):(\d{2})", t or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def windows(tw):
    ps, pe, by = mins(tw.get("start")), mins(tw.get("end")), mins(tw.get("deliver_by"))
    said = tw.get("as_written") or ""
    around = bool(re.search(r"around|about|ish", said, re.I))
    missing = ps is None and pe is None and by is None
    if missing:
        ps, pe = 480, 960
    elif ps is None and pe is None:
        ps, pe = 480, by
    elif ps is None:
        ps = 480
    elif pe is None:
        pe = ps + 15
    asked = None if missing else ((ps + pe) / 2 if around else (ps if mins(tw.get("start")) is not None else None))
    return {"ps": ps, "pe": pe, "drop": by if by is not None else pe + 60, "by": by, "asked": asked,
            "vague": bool(VAGUE.search(said)), "missing": missing}


TODAY_WORDS = re.compile(r"\btoday\b|same[- ]day|tonight|\basap\b|right now|this (morning|afternoon|evening)", re.I)


def frequency(f, demo, text=""):
    t, d = f.get("type"), date.fromisoformat(demo)
    if t == "every_weekday":
        starts = (f.get("starts") or "").lower()
        return {"type": "weekday", "start_date": next_monday(d).isoformat() if "next week" in starts else None}
    if t == "weekdays" and f.get("days"):
        return {"type": "weekdays", "days": [x for x in ["mon", "tue", "wed", "thu", "fri"] if x in f["days"]]}
    raw = (f.get("date") or "").lower()
    if raw in ("today", "same day", demo) and not TODAY_WORDS.search(text or ""):
        raw = ""
    if raw in ("today", "same day"):
        day = d
    elif raw == "tomorrow":
        day = next_weekday(d)
    else:
        try:
            day = date.fromisoformat(raw)
        except ValueError:
            day = d  # REQ-1050: no date given means the current demo day
    return {"type": "one_off", "date": day.isoformat()}


def place_label(p):
    return p.get("city") if p.get("source") != "area" else p["name"]


def stop_sig(locs):
    return sorted(f"{l['kind']}:{p['lat']:.3f},{p['lon']:.3f}" for l, p in locs if p.get("found"))


def duplicate_problem(doc, sig, earlier):
    if not sig:
        return None
    mine = datetime.fromisoformat(doc["received_at"])
    best = None
    for e in earlier:
        if e["key"] == doc["key"] or e.get("sender_contact") != doc.get("sender_contact") or e.get("stop_sig") != sig:
            continue
        gap = (mine - datetime.fromisoformat(e["received_at"])).total_seconds() / 60
        if 0 <= gap <= 1440 and (not best or gap < best[1]):
            best = (e, gap)
    if not best:
        return None
    gap = round(best[1])
    when = f"{gap} minute{'s' if gap != 1 else ''}" if gap < 60 else f"{round(gap / 60)} hour{'s' if round(gap / 60) != 1 else ''}"
    return {"kind": "duplicate", "text": f"Looks like a copy of request {best[0]['number']} from {when} earlier.", "detail": None,
            "when": when}


def build(doc, rec, locs, demo, travel, earlier):
    """locs: list of (location fields, resolved point). Returns the fields to store on the request."""
    tw, problems, details = windows(rec["time_window"]), [], []
    named = rec["customer_name"].get("value")
    cust = named or doc.get("sender")
    details.append({"key": "customer", "label": "Customer", "value": cust,
                    "confidence": lower(rec["customer_name"]["confidence"], "high") if named else "medium"})
    contact = rec["contact_phone"].get("value") or rec["email"].get("value") or doc.get("sender_contact")
    if contact:
        details.append({"key": "contact", "label": "Contact", "value": contact, "confidence": "high"})
    for i, (loc, p) in enumerate(locs):
        key = f"loc-{i}"
        label = "Pickup" if loc["kind"] == "pickup" else "Drop-off"
        if p.get("found"):
            value = p["address"] if p["name"] in p["address"] else f"{p['name']}, {p['address']}"
            cap = "low" if p.get("approximate") else CAP.get(p["source"], "medium")
            details.append({"key": key, "label": label, "value": value, "as_written": loc["text"], "source": p["source"],
                            "confidence": lower(loc.get("confidence"), cap)})
        else:
            details.append({"key": key, "label": label, "value": loc["text"], "as_written": loc["text"], "source": None, "confidence": "low"})
            problems.append({"kind": p["problem_kind"], "text": p["problem"], "detail": key, "street": p.get("street"),
                             "what": p.get("what"), "where": loc.get("city") or loc["text"]})
    if not any(l["kind"] == "dropoff" for l, _ in locs):
        problems.append({"kind": "missing", "text": "We need the delivery address.", "detail": None, "what": "delivery", "where": ""})
    found = [(l, p) for l, p in locs if p.get("found")]
    time_cap = "low" if tw["missing"] else ("medium" if tw["vague"] else "high")
    for l, p in found:
        h = p.get("hours")
        if l["kind"] == "pickup" and h and h["close"] < 1440:
            if tw["ps"] >= h["close"] - SERVICE:
                problems.append({"kind": "hours", "text": f"{p['name']} closes at {fmt_time(h['close'])}.", "detail": "time"})
            elif tw["pe"] <= h["open"]:
                problems.append({"kind": "hours", "text": f"{p['name']} opens at {fmt_time(h['open'])}.", "detail": "time"})
    picks = [p for l, p in found if l["kind"] == "pickup"]
    drops = [p for l, p in found if l["kind"] == "dropoff"]
    for P in picks[:1]:
        for Dp in drops[:1]:
            t = travel(P, Dp)[1]
            if tw["by"] is not None and max(tw["ps"], 480) + SERVICE + t > tw["drop"] + 1e-6:
                problems.append({"kind": "impossible", "detail": "time",
                                 "text": f"{place_label(P)} to {place_label(Dp)} takes about {int(5 * round(t / 5))} min, "
                                         f"so {fmt_time(tw['drop'])} can't work."})
    if any(pr["detail"] == "time" for pr in problems):
        time_cap = "low"
    said = rec["time_window"].get("as_written")
    tval = (f'"{said}", ' if said else "") + f"{fmt_time(tw['ps'])} to {fmt_time(tw['pe'])}"
    if tw["by"] is not None:
        tval += f", delivered by {fmt_time(tw['drop'])}"
    if tw["missing"]:
        tval = "No time given"
    details.append({"key": "time", "label": "Time", "value": tval, "confidence": lower(rec["time_window"]["confidence"], time_cap)})
    freq = frequency(rec["frequency"], demo, doc.get("raw_text", ""))
    fcap = "low" if not rec["frequency"].get("type") else ("medium" if freq["type"] == "one_off" and not rec["frequency"].get("date") else "high")
    details.append({"key": "frequency", "label": "How often", "value": freq_text(freq).rstrip("."),
                    "as_written": rec["frequency"].get("as_written"), "confidence": lower(rec["frequency"]["confidence"], fcap)})
    if rec["items"].get("count"):
        n_items = rec["items"]["count"]
        details.append({"key": "items", "label": "Items", "value": f"{n_items} {rec['items'].get('size') or ('item' if n_items == 1 else 'items')}",
                        "confidence": rec["items"]["confidence"]})
    if rec["notes"].get("value"):
        details.append({"key": "notes", "label": "Notes", "value": rec["notes"]["value"], "confidence": "high"})
    sig = stop_sig(locs)
    dup = duplicate_problem(doc, sig, earlier)
    if dup:
        problems.append(dup)
    flagged = {pr["detail"] for pr in problems if pr["detail"]}
    for d in details:
        d["needs_clarification"] = d["confidence"] == "low" or d["key"] in flagged
    job, reason = None, None
    blocking = next((pr for pr in problems if pr["kind"] in ("missing", "ambiguous", "not_found")), None)
    if blocking:
        reason = {"missing": f"We need the {blocking.get('what') or 'delivery'} addresses.",
                  "ambiguous": f"We need to know which city {blocking.get('street')} is in.",
                  "not_found": blocking["text"].replace("We couldn't", "We couldn't")}[blocking["kind"]]
    else:
        stops, refs = [], {"pickup": 0, "dropoff": 0}
        for l, p in found:
            refs[l["kind"]] += 1
            ref = f"{'p' if l['kind'] == 'pickup' else 'd'}{refs[l['kind']]}"
            pick = l["kind"] == "pickup"
            stops.append({"ref": ref, "kind": l["kind"], "name": p["name"], "address": p["address"], "lat": p["lat"], "lon": p["lon"],
                          "window_start": tw["ps"] if pick else None, "window_end": tw["pe"] if pick else tw["drop"],
                          "items": int(rec["items"].get("count") or 1), "hours": p.get("hours"), "approximate": p.get("approximate", False)})
        ps = [s["ref"] for s in stops if s["kind"] == "pickup"]
        ds = [s["ref"] for s in stops if s["kind"] == "dropoff"]
        pairs = [[p, d] for p in ps for d in ds] if len(ps) == 1 or len(ds) == 1 else [[p, d] for p, d in zip(ps, ds)]
        job = {"stops": stops, "pairs": pairs, "frequency": freq, "asked_minutes": tw["asked"],
               "notes": "Read from the request."}
        reason = validate_job(job)
        if reason:
            job = None
    summary = summarize(job) if job else template_summary(locs, freq)
    return {"details": details, "problems": problems, "stop_sig": sig, "job": job,
            "job_status": "ready" if job else "cant_price", "job_reason": reason,
            "job_summary": summary if job else reason, "summary": summary,
            "needs_clarification": any(d["needs_clarification"] for d in details) or bool(problems),
            "status": "needs_info" if problems else ("priced" if job else "needs_info")}


def template_summary(locs, freq):
    parts = [f"{'pickup at' if l['kind'] == 'pickup' else 'drop-off at'} {p['name'] if p.get('found') else l['text']}" for l, p in locs]
    text = ", ".join(parts) or "a request with no places yet"
    return f"{text[0].upper()}{text[1:]}. {freq_text(freq)}"


NUM = re.compile(r"\d+(?::\d+)?(?:\.\d+)?")


def question_template(problem, first):
    hi = f"Hi {first}," if first else "Hi,"
    k = problem["kind"]
    if k == "ambiguous":
        return f"{hi} thanks for your request. {problem['text']}"
    if k == "missing":
        where = f" in {problem['where']}" if problem.get("where") else ""
        return f"{hi} thanks for your request. Could you send us the {problem.get('what') or 'delivery'} addresses{where}?"
    if k == "hours":
        return f"{hi} thanks for your request. {problem['text']} Could we pick up earlier, before it closes?"
    if k == "impossible":
        return f"{hi} thanks for your request. {problem['text']} Would a later delivery time work for you?"
    if k == "duplicate":
        return f"{hi} is this the same request you sent {problem.get('when', 'a little')} earlier, or a new one?"
    return f"{hi} thanks for your request. {problem['text']} Could you send the full address?"


def numbers_ok(text, allowed):
    ok = set(NUM.findall(allowed))
    return bool(text) and len(text) < 400 and "?" in text and set(NUM.findall(text)) <= ok
