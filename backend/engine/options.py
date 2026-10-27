"""Three labeled quote options (Cheapest, Soonest, Preferred window), other options and customer lines."""
from engine.pricing import money_text
from engine.timing import fmt_time

LABELS = ("Cheapest", "Soonest", "Preferred window")
HIDDEN = ("nodes", "base_keys", "_extras", "pass_by_ahead")
MAX_CARDS = 2


def title_for(labels):
    if "Cheapest" in labels and "Soonest" in labels:
        rest = [lb for lb in labels if lb not in ("Cheapest", "Soonest")]
        return " + ".join(["Cheapest and soonest", *rest])
    return " + ".join(labels)


def first_pickup(r):
    stops = r["new_stops"]
    return next((n for n in stops if n["kind"] != "dropoff"), stops[0])


def last_dropoff(r):
    drops = [n for n in r["new_stops"] if n["kind"] == "dropoff"]
    return max(drops, key=lambda n: n["arrival"]) if drops else None


def asked_times(job):
    pick = next((js for js in job["stops"] if js["kind"] != "dropoff"), job["stops"][0])
    target = job.get("asked_minutes")
    if target is None:
        ws, we = pick.get("window_start"), pick.get("window_end")
        target = (ws if we - ws <= 15 else (ws + we) / 2) if ws is not None and we is not None else ws
    deadlines = [js["window_end"] for js in job["stops"] if js["kind"] == "dropoff" and js.get("window_end") is not None]
    return target, (min(deadlines) if deadlines else None)


def customer_line(r, job):
    one_off = job["frequency"]["type"] == "one_off"
    usual, pb = r["usual"], r.get("pass_by")
    if r["price"] < usual - 1e-9 and pb:
        d = pb["miles"]
        dist = "less than 0.1 miles" if d < 0.05 else f"{d:.1f} miles"
        per = "for the run" if one_off else "a visit"
        return (f"{r['unit_name']} already passes {dist} from you at {fmt_time(pb['time'])}, "
                f"so it's {money_text(r['price'])} {per} instead of our usual {money_text(usual)}.")
    return f"Our usual price for this run is {money_text(usual)}." if one_off else \
        f"Our usual price for this run is {money_text(usual)} a visit."


def card(r, job, labels, reasons):
    pick, drop = first_pickup(r), last_dropoff(r)
    out = {k: v for k, v in r.items() if k not in HIDDEN}
    out.update(labels=labels, title=title_for(labels), reasons=reasons, pickup_label=pick["arrival_label"],
               dropoff_label=drop["arrival_label"] if drop else None, customer_line=customer_line(r, job))
    return out


def build_options(cands, job, s, shifted=False, plan=None):
    if not cands:
        return {"cards": [], "others": [], "from_shifted": shifted}
    target, deadline = asked_times(job)
    by_delivery = shifted and deadline is not None and all(
        last_dropoff(r) and last_dropoff(r)["arrival"] > deadline + 1e-6 for r in cands)
    aim_pick, aim_drop = target, deadline
    if plan:
        mode, k = plan
        if mode == "A":
            aim_pick = target - 15 * k if target is not None else None
            aim_drop = deadline + 15 * k if deadline is not None else None
        else:
            aim_pick = target + k if target is not None else None
            aim_drop = deadline + k if deadline is not None else None

    def pick_t(r):
        return first_pickup(r)["arrival"]

    def drop_t(r):
        d = last_dropoff(r)
        return d["arrival"] if d else 0

    def pref_score(r):
        if by_delivery:
            return abs(drop_t(r) - aim_drop)
        return abs(pick_t(r) - aim_pick) if aim_pick is not None else pick_t(r)

    chosen = {
        "Cheapest": min(cands, key=lambda r: (r["added_cost"], r["added_minutes"], r["unit_key"], pick_t(r))),
        "Soonest": min(cands, key=lambda r: (pick_t(r), drop_t(r), r["added_cost"])),
        "Preferred window": min(cands, key=lambda r: (pref_score(r), r["added_cost"], r["unit_key"])),
    }

    aim = {"target": target, "deadline": deadline, "by_delivery": by_delivery, "pick": aim_pick, "drop": aim_drop}

    def reason(label, r):
        return reason_for(label, r, aim)

    labels = ("Cheapest", "Preferred window", "Soonest") if job.get("asked_minutes") is not None else LABELS[:2]
    groups = []
    for label in labels:
        r = chosen[label]
        g = next((g for g in groups if g[0] is r or (g[0]["unit_key"] == r["unit_key"] and abs(g[0]["price"] - r["price"]) < 1e-9)), None)
        if g:
            g[1].append(label)
            g[2].append(reason(label, r))
        else:
            groups.append((r, [label], [reason(label, r)]))
    groups = groups[:MAX_CARDS]
    if len(groups) == 1:
        # REQ-1253: one merged card left, so show the best-priced engine option on a different van.
        van = groups[0][0]["unit_key"]
        alt = min((r for r in cands if r["unit_key"] != van), key=lambda r: (r["price"], r["added_cost"], pick_t(r)), default=None)
        if alt:
            groups.append((alt, ["Another van"], [f"Best price on another van: adds {alt['added_minutes']} min to {alt['unit_name']}."]))
    picked = {id(g[0]) for g in groups}
    rest = sorted((r for r in cands if id(r) not in picked), key=lambda r: (r["price"], r["added_cost"], pick_t(r)))
    others, per_van = [], {}
    for r in rest:
        if per_van.get(r["unit_key"], 0) >= 2:
            continue
        per_van[r["unit_key"]] = per_van.get(r["unit_key"], 0) + 1
        others.append(r)
        if len(others) == 5:
            break
    return {"cards": [card(r, job, lb, rs) for r, lb, rs in groups],
            # "See other options" lines only count stops still ahead of the van; the main cards keep their pass-by.
            "others": [card({**r, "pass_by": r.get("pass_by_ahead") or r.get("pass_by")}, job, [], []) for r in others],
            "from_shifted": shifted, "aim": aim,
            "_raw": [g[0] for g in groups] + others}


def reason_for(label, r, aim):
    if label == "Cheapest":
        return f"Lowest cost: adds {r['added_minutes']} min to {r['unit_name']}."
    if label == "Soonest":
        return f"Earliest pickup: {r['unit_name']} can be there at {first_pickup(r)['arrival_label']}."
    if aim["by_delivery"]:
        return f"Closest to the {fmt_time(aim['deadline'])} you asked for: delivery at {last_dropoff(r)['arrival_label']}."
    if aim["target"] is None:
        return f"Closest to the time you asked for: pickup at {first_pickup(r)['arrival_label']}."
    return f"Closest to the {fmt_time(aim['target'])} you asked for: pickup at {first_pickup(r)['arrival_label']}."


def label_key(label, aim):
    def drop(r):
        d = last_dropoff(r)
        return d["arrival"] if d else 0
    if label == "Cheapest":
        return lambda r: (r["added_cost"], r["added_minutes"], first_pickup(r)["arrival"])
    if label == "Soonest":
        return lambda r: (first_pickup(r)["arrival"], drop(r), r["added_cost"])
    if aim.get("by_delivery"):
        return lambda r: (abs(drop(r) - aim["drop"]), r["added_cost"])
    return lambda r: (abs(first_pickup(r)["arrival"] - aim["pick"]) if aim.get("pick") is not None else first_pickup(r)["arrival"], r["added_cost"])


def reject_option(opts, option_id):
    """Hide one option. For each label it held, the next best remaining option takes the label (REQ-266)."""
    cards = [c for c in opts["cards"] if c["option_id"] != option_id]
    others = [o for o in opts["others"] if o["option_id"] != option_id]
    gone = next((c for c in opts["cards"] if c["option_id"] == option_id), None)
    rejected = (opts.get("rejected") or []) + [option_id]
    aim = opts.get("aim") or {"target": None, "deadline": None, "by_delivery": False, "pick": None, "drop": None}
    for label in (gone or {}).get("labels", []):
        if not others:
            break
        if label == "Another van":
            continue
        best = min(others, key=label_key(label, aim))
        holder = next((c for c in cards if c["option_id"] == best["option_id"]), None)
        if not holder:
            holder = {**best, "labels": [], "reasons": []}
            others = [o for o in others if o["option_id"] != best["option_id"]]
            cards.append(holder)
        holder["labels"].append(label)
        holder["reasons"].append(reason_for(label, holder, aim))
    order = {lb: i for i, lb in enumerate((*LABELS, "Another van"))}
    cards.sort(key=lambda c: min(order[lb] for lb in c["labels"]))
    merged = []
    for c in cards:
        m = next((x for x in merged if x["unit_key"] == c["unit_key"] and abs(x["price"] - c["price"]) < 1e-9), None)
        if m:
            m["labels"] += c["labels"]
            m["reasons"] += c["reasons"]
        else:
            merged.append(c)
    others = merged[MAX_CARDS:] + others
    cards = merged[:MAX_CARDS]
    for c in cards:
        c["title"] = title_for(c["labels"])
    return {**opts, "cards": cards, "others": others, "rejected": rejected}
