"""Level 3: a no-AI keyword reader that fills record_request from plain patterns and the directory."""
import re

from ai.schema import RecordRequest
from seed import data as D

T = r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?"
GENERIC = {"lab", "center", "group", "the", "street", "st", "ave", "and", "of"}
AREA_WORDS = sorted({a.lower() for a in D.AREAS} | {"montclair"}, key=len, reverse=True)
CITIES = ["san francisco", "oakland", "berkeley", "emeryville", "albany", "piedmont", "sf"]
DAYS = {"monday": "mon", "tuesday": "tue", "wednesday": "wed", "thursday": "thu", "friday": "fri"}
SUFFIX = r"(?:st|street|ave|avenue|blvd|way|rd|dr)"


def _known_streets():
    words = set()
    for _, (_, streets) in D.STREETS.items():
        words |= {s[0].split()[0].lower() for s in streets}
    for d in D.DIRECTORY:
        words.add(d[1].split(",")[0].split()[1].lower())
    return sorted(words | {"broadway", "solano"}, key=len, reverse=True)


KNOWN = _known_streets()


def hm(h, m, ap):
    h, m = int(h), int(m or 0)
    ap = (ap or "").replace(".", "")
    if ap == "pm" and h < 12:
        h += 12
    elif ap == "am" and h == 12:
        h = 0
    elif not ap and 1 <= h <= 6:
        h += 12
    return f"{h:02d}:{m:02d}" if 0 <= h < 24 and m < 60 else None


def shift(t, mins):
    h, m = map(int, t.split(":"))
    total = h * 60 + m + mins
    return f"{total // 60:02d}:{total % 60:02d}"


def _time_between(t, out, said):
    m = re.search(rf"between\s+{T}\s+and\s+{T}", t)
    if m:
        ap = m.group(3) or m.group(6)
        out["start"], out["end"] = hm(m.group(1), m.group(2), ap), hm(m.group(4), m.group(5), m.group(6))
        said.append(m.group(0))


def _time_around(t, out, said):
    m2 = re.search(rf"around\s+{T}(?!\d)", t)
    if m2 and "start" not in out:
        mid = hm(*m2.groups())
        out["start"], out["end"] = shift(mid, -15), shift(mid, 15)
        said.append(m2.group(0))


def _time_by(t, out, said):
    m3 = re.search(rf"\bby\s+{T}(?!\d)", t)
    if m3:
        out["deliver_by"] = hm(*m3.groups())
        said.append(m3.group(0))


def _time_start(t, out, said):
    if "start" in out:
        return
    m4 = re.search(rf"\bat\s+{T}(?!\d)", t) or re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?", t) or re.search(r"\b(\d{1,2})()\s*(am|pm)\b", t)
    if m4:
        out["start"] = hm(*m4.groups())
        said.append(m4.group(0).strip())
    elif "afternoon" in t:
        out["start"], out["end"] = "12:00", "17:00"
        said.append("afternoons" if "afternoons" in t else "afternoon")


def read_time(text):
    t, out, said = text.lower(), {}, []
    for step in (_time_between, _time_around, _time_by, _time_start):
        step(t, out, said)
    out["as_written"] = ", ".join(said) or None
    out["confidence"] = "medium" if re.search(r"around|afternoon|morning|ish", t) else "high"
    return out


def read_frequency(text):
    t = text.lower()
    out = {"confidence": "high"}
    days = [v for k, v in DAYS.items() if re.search(rf"\b{k}s?\b", t)]
    once = re.search(r"\btoday\b|same day|tomorrow|one-off|one off", t)
    if re.search(r"\b(daily|every weekday|weekdays|each weekday|every day)\b", t):
        out.update(type="every_weekday", as_written=re.search(r"\b(daily|every weekday|weekdays|each weekday|every day)\b", t).group(0))
    elif days and not once:
        out.update(type="weekdays", days=days, as_written=", ".join(k for k in DAYS if DAYS[k] in days))
    else:
        out["type"] = "one_off"
        if re.search(r"\btoday\b|same day", t):
            out.update(date="today", as_written="today")
        elif "tomorrow" in t:
            out.update(date="tomorrow", as_written="tomorrow")
        else:
            out["confidence"] = "medium"
    if "next week" in t:
        out["starts"] = "next week"
    return out


def _name_pos(t, low):
    pos = t.find(low)
    toks = [w for w in re.findall(r"[a-z]+", low) if w not in GENERIC]
    if pos < 0 and len(toks) >= 2 and all(re.search(rf"\b{w}\b", t) for w in toks):
        pos = min(t.find(w) for w in toks)
    return pos


def _street_hit(t, addr):
    street = addr.split(",")[0].lower()
    num, word = street.split()[0], street.split()[1]
    return re.search(rf"\b{num}\s+{word}\b", t) if num.isdigit() else None


def _dir_entry(t, name, addr, low, pos, sm):
    first = min(p for p in (pos if pos >= 0 else None, sm.start() if sm else None) if p is not None)
    spans = ([sm.span()] if sm else []) + ([(pos, pos + len(low))] if t.find(low) >= 0 else [])
    return {"pos": first, "text": name, "business_name": name, "street": addr.split(",")[0],
            "city": addr.split(",")[-1].strip(), "span": spans}


def dir_matches(t):
    found = []
    for name, addr, *_ in D.DIRECTORY:
        low = name.lower()
        pos = _name_pos(t, low)
        sm = _street_hit(t, addr)
        if pos >= 0 or sm:
            found.append(_dir_entry(t, name, addr, low, pos, sm))
    return found


def street_matches(t, taken):
    out = []
    pat = rf"\b(\d{{2,5}})\s+((?:{'|'.join(KNOWN)})(?:\s+{SUFFIX})?\.?)(?:[\s,]+({'|'.join(CITIES)}))?\b"
    for m in re.finditer(pat, t):
        if any(a <= m.start() < b for a, b in taken):
            continue
        city = m.group(3)
        out.append({"pos": m.start(), "text": m.group(0).strip(" ,"), "street": f"{m.group(1)} {m.group(2)}".title(),
                    "city": ("San Francisco" if city in ("sf", "san francisco") else city.title()) if city else None})
    for m in re.finditer(rf"\b(?:on|to)\s+(?:the\s+)?([a-z]+)\s+({SUFFIX})\b", t):
        if any(a <= m.start(1) < b for a, b in taken) or m.group(1) not in KNOWN:
            continue
        taken.append(m.span())
        out.append({"pos": m.start(), "text": m.group(0).split(" ", 1)[1], "street": f"{m.group(1)} {m.group(2)}".title(), "city": None})
    for w in AREA_WORDS:
        m = next((x for x in re.finditer(rf"\b(?:in|to)\s+(?:about\s+\w+\s+homes\s+in\s+)?{w}\b", t)
                  if not any(a <= x.end() - len(w) < b for a, b in taken)), None)
        if m:
            taken.append(m.span())
            out.append({"pos": m.start(), "text": m.group(0).split(" ", 1)[1], "street": None, "city": w.title()})
    return out


def _ordered_locs(t):
    locs = dir_matches(t)
    taken = [s for loc in locs for s in loc.pop("span")]
    locs += [s for s in street_matches(t, taken) if not any(s["street"] and loc.get("street") and s["street"].lower() == loc["street"].lower() for loc in locs)]
    locs.sort(key=lambda x: x["pos"])
    return locs


def _loc_kind(loc, t, sender, cut_pos):
    own = loc.get("business_name") and loc["business_name"].lower() in (sender or "").lower()
    to_us = re.search(r"deliver\w*\s+to\s+(us|our)\b", t)
    return ("dropoff" if to_us else "pickup") if own else ("pickup" if loc["pos"] < cut_pos else "dropoff")


def _repeats(loc, kind, t):
    if kind == "dropoff" and loc.get("street") and not loc["street"][0].isdigit():
        m = re.search(r"\b(\d|two|three|four)\s+drops?\b", t)
        return {"two": 2, "three": 3, "four": 4}.get(m.group(1), int(m.group(1)) if m and m.group(1).isdigit() else 1) if m else 1
    return 1


def read_locations(text, sender):
    t = text.lower()
    locs = _ordered_locs(t)
    cut = re.search(r"deliver|drop|\bto\b", t)
    cut_pos = cut.start() if cut else len(t)
    out = []
    for loc in locs:
        kind = _loc_kind(loc, t, sender, cut_pos)
        for _ in range(_repeats(loc, kind, t)):
            out.append({"text": loc["text"], "business_name": loc.get("business_name"), "street": loc.get("street"),
                        "city": loc.get("city"), "kind": kind, "confidence": "high"})
    if out and all(x["kind"] == "dropoff" for x in out):
        out[0]["kind"] = "pickup"
    return sorted(out, key=lambda x: x["kind"] != "pickup")


def read_name(text, sender):
    m = re.search(r"thanks,?\s+([^\n]+)", text, re.I)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        name = parts[0]
        if len(parts) > 1 and not re.search(r"\d", parts[1]):
            name += f", {parts[1]}"
        return name
    m = re.search(r"this is (\w+) from ([A-Z][\w ]+?)(?: on |,|\.)", text)
    if m:
        return f"{m.group(1)}, {m.group(2)}"
    return None


def keyword_read(text, sender=""):
    t = text.lower()
    phone = re.search(r"\(?\d{3}\)?[ .-]?\d{3}[ .-]\d{4}", text)
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    items = re.search(r"(\d+)\s+(boxes|box|bags|packages|envelopes|items|crates)", t)
    notes = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if re.search(r"ignore|disregard|forget your", s, re.I)]
    name = read_name(text, sender)
    rec = {
        "customer_name": {"value": name, "confidence": "high" if name else "low"},
        "contact_phone": {"value": phone.group(0) if phone else None, "confidence": "high" if phone else "low"},
        "email": {"value": email.group(0) if email else None, "confidence": "high" if email else "low"},
        "locations": read_locations(text, sender),
        "time_window": read_time(text),
        "frequency": read_frequency(text),
        "items": {"count": int(items.group(1)) if items else None, "size": items.group(2) if items else None, "confidence": "high"},
        "notes": {"value": " ".join(notes) or None, "confidence": "high"},
        "missing_or_contradictory": [],
    }
    return RecordRequest.model_validate(rec).model_dump()


JOB_SPLIT = re.compile(r"(?mi)^\s*(?:\d\)|\d\.\s|job \d:)")


def keyword_jobs(text, sender=""):
    """Split numbered jobs ("1)", "2)") into separate record_requests; otherwise one."""
    parts = JOB_SPLIT.split(text)
    if len(parts) >= 3:
        jobs = []
        for part in parts[1:]:
            rec = keyword_read(part, sender)
            if rec["locations"]:
                whole = keyword_read(text, sender)
                for k in ("customer_name", "contact_phone", "email"):
                    rec[k] = whole[k]
                jobs.append(rec)
        if len(jobs) >= 2:
            return jobs
    return [keyword_read(text, sender)]
