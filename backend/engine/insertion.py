"""Insertion engine: cheapest feasible slot per unit, plain-words reasons, window search."""
from dataclasses import dataclass
from typing import Callable, Optional

from engine.pricing import added_cost, half_up, price_quote
from engine.timing import compute_route, fmt_time, haversine_miles, in_sf

EPS = 1e-6
STEP, MAX_STEPS = 15, 8
REASONS = ("the window has already passed", "can't reach it in time", "past shift end", "no room", "missing skill")


def _node_window(js, svc, mode, k, clock):
    is_drop = js["kind"] == "dropoff"
    ws = js.get("window_start")
    ws = 480.0 if ws is None or (is_drop and ws < 480) else float(ws)
    we = float(js.get("window_end") if js.get("window_end") is not None else 1020)
    if mode == "A":
        ws, we = (ws, we + STEP * k) if is_drop else (ws - STEP * k, we)
    elif mode == "B":
        ws, we = (ws if is_drop else ws + k), we + k
    hours = js.get("hours")
    if hours:
        ws, we = max(ws, hours["open"]), min(we, hours["close"] - svc)
    if clock is not None:
        ws = max(ws, float(clock))
    return ws, we


def build_nodes(job, s, mode=None, k=0, clock=None):
    """Turn job stops into route nodes with effective windows (shift mode, opening hours, demo clock)."""
    nodes = []
    for js in job["stops"]:
        svc = float(js.get("service_minutes") or s["minutes_per_new_stop"])
        ws, we = _node_window(js, svc, mode, k, clock)
        nodes.append({
            "key": f"new:{js['ref']}", "ref": js["ref"], "is_new": True, "kind": js["kind"],
            "customer_name": js.get("name") or "New stop", "address": js.get("address") or "",
            "lat": js["lat"], "lon": js["lon"], "window_start": ws, "window_end": we,
            "service_minutes": svc, "items": int(js.get("items") or 1), "approximate": bool(js.get("approximate")),
        })
    return nodes


def pickups_of(job):
    out = {}
    for p, d in job.get("pairs", []):
        out.setdefault(d, set()).add(p)
    return out


def _simulate(base, seq, i0, last_new):
    """Walk the new sequence from index i0 (the van leaves base.before(i0)); returns a late reason or None."""
    unit, base_arr, travel = base.unit, base.base_arr, base.travel
    t, prev = base.before(i0)
    for k in range(i0, len(seq)):
        n = seq[k]
        a = max(t + travel(prev, n)[1], n["window_start"])
        if a > n["window_end"] + EPS:
            return "new_late" if n.get("is_new") else "existing_late"
        if k > last_new and a <= base_arr.get(n["key"], -1) + EPS:
            return None
        t, prev = a + n["service_minutes"], n
    ret = t + travel(prev, unit["end_location"])[1]
    return None if ret <= unit["shift_end"] + EPS else "return_late"


def current_position(unit, nodes, result, clock, travel):
    """Where the van is at the demo clock when it's mid-leg: (index to insert at, position node), else None."""
    rows = result["stops"]
    k = sum(1 for r in rows if r["arrival"] < clock - EPS)
    start_t = float(unit["shift_start"]) if k == 0 else rows[k - 1]["departure"]
    if clock <= start_t + EPS or (k == len(nodes) and clock >= result["return_time"] - EPS):
        return None
    src = unit["start_location"] if k == 0 else nodes[k - 1]
    dst = nodes[k] if k < len(nodes) else unit["end_location"]
    mins = travel(src, dst)[1]
    f = 1.0 if mins <= EPS else min(1.0, (clock - start_t) / mins)
    lat, lon = src["lat"] + (dst["lat"] - src["lat"]) * f, src["lon"] + (dst["lon"] - src["lon"]) * f
    return k, {"key": f"pos:{lat:.6f},{lon:.6f}", "is_pos": True, "kind": "position", "customer_name": "where the van is now",
               "address": "", "lat": lat, "lon": lon, "window_start": float(clock), "window_end": float(unit["shift_end"]),
               "service_minutes": 0.0, "items": 0, "area": dst.get("area") or src.get("area")}


class Base:
    """Timing of the current route, used for cheap incremental checks."""

    def __init__(self, unit, nodes, s, travel, clock):
        self.unit, self.s, self.travel = unit, s, travel
        nodes = list(nodes)
        self.result = compute_route(unit, nodes, s, travel=travel)
        pos_i = next((i for i, n in enumerate(nodes) if n.get("is_pos")), None)
        if pos_i is None and clock is not None:
            hit = current_position(unit, nodes, self.result, float(clock), travel)
            if hit:
                pos_i, node = hit
                nodes.insert(pos_i, node)
                self.result = compute_route(unit, nodes, s, travel=travel)
        self.nodes = nodes
        rows = self.result["stops"]
        self.arr = [r["arrival"] for r in rows]
        self.dep = [r["departure"] for r in rows]
        self.base_arr = {n["key"]: a for n, a in zip(nodes, self.arr)}
        if pos_i is not None:
            self.min_pos = pos_i + 1
        else:
            self.min_pos = sum(1 for a in self.arr if a < clock - EPS) if clock is not None else 0

    def before(self, i):
        if i == 0:
            return float(self.unit["shift_start"]), self.unit["start_location"]
        return self.dep[i - 1], self.nodes[i - 1]

    def after(self, i):
        return self.nodes[i] if i < len(self.nodes) else self.unit["end_location"]

    def delta(self, a, x, b):
        tr = self.travel
        m1, t1 = tr(a, x)
        m2, t2 = tr(x, b)
        m0, t0 = tr(a, b)
        return t1 + t2 - t0, m1 + m2 - m0


def _cost(dmins, dmiles, s):
    return dmins * s["wage_per_hour"] / 60 + dmiles * s["cost_per_mile"]


def _finish(base, seq, fails):
    final = compute_route(base.unit, seq, base.s, travel=base.travel)
    if final["feasible"]:
        return final
    fails.add("no_room")
    return None


def try_pair(base, P, D, i, j, fails):
    seq = base.nodes[:i] + [P] + base.nodes[i:j] + [D] + base.nodes[j:]
    why = _simulate(base, seq, i, j + 1)
    if why:
        fails.add(why)
        return None, None
    final = _finish(base, seq, fails)
    return (seq, final) if final else (None, None)


def insert_pair(base, P, D, fails):
    for _, i, j in pair_cands(base, P, D, fails):
        seq, final = try_pair(base, P, D, i, j, fails)
        if seq:
            return seq, final
    return None, None


def pair_cands(base, P, D, fails):
    n, s, tr = len(base.nodes), base.s, base.travel
    cands = []
    for i in range(base.min_pos, n + 1):
        t, prev = base.before(i)
        if t + tr(prev, P)[1] > P["window_end"] + EPS:
            fails.add("new_late")
            continue
        for j in range(i, n + 1):
            if j == i:
                mP, tP = tr(prev, P)
                mD, tD = tr(D, base.after(i))
                m0, t0 = tr(prev, base.after(i))
                dm, dmi = tP + tr(P, D)[1] + tD - t0, mP + tr(P, D)[0] + mD - m0
            else:
                d1, e1 = base.delta(prev, P, base.after(i))
                if base.dep[j - 1] + tr(base.nodes[j - 1], D)[1] > D["window_end"] + EPS:
                    fails.add("new_late")
                    continue
                d2, e2 = base.delta(base.nodes[j - 1], D, base.after(j))
                dm, dmi = d1 + d2, e1 + e2
            cands.append((_cost(dm, dmi, s), i, j))
    cands.sort()
    return cands


def insert_single(base, X, after_keys, fails):
    n, s, tr = len(base.nodes), base.s, base.travel
    lo = base.min_pos
    for idx, node in enumerate(base.nodes):
        if node["key"] in after_keys:
            lo = max(lo, idx + 1)
    cands = []
    for i in range(lo, n + 1):
        t, prev = base.before(i)
        if t + tr(prev, X)[1] > X["window_end"] + EPS:
            fails.add("new_late")
            continue
        dm, dmi = base.delta(prev, X, base.after(i))
        cands.append((_cost(dm, dmi, s), i))
    cands.sort()
    for _, i in cands:
        seq = base.nodes[:i] + [X] + base.nodes[i:]
        why = _simulate(base, seq, i, i)
        if why:
            fails.add(why)
            continue
        final = _finish(base, seq, fails)
        if final:
            return seq, final
    return None, None


def swap_pass(unit, seq, final, s, travel, min_pos, pickups):
    """Swap neighboring stops (at least one new) once each; keep swaps that shorten the drive."""
    for k in range(max(min_pos, 0), len(seq) - 1):
        a, b = seq[k], seq[k + 1]
        if not (a.get("is_new") or b.get("is_new")):
            continue
        if a.get("ref") and a["ref"] in pickups.get(b.get("ref"), set()):
            continue
        trial = seq[:k] + [b, a] + seq[k + 2:]
        r = compute_route(unit, trial, s, travel=travel)
        if r["feasible"] and r["driving_minutes"] < final["driving_minutes"] - EPS:
            seq, final = trial, r
    return seq, final


def region_of(node):
    if in_sf(node):
        return "San Francisco"
    return node.get("area") or node.get("city") or "the East Bay"


def where_is(base, t):
    nodes, arr, dep = base.nodes, base.arr, base.dep
    if not nodes:
        return {"area": base.unit["start_location"]["name"], "until": base.unit["shift_end"], "until_label": fmt_time(base.unit["shift_end"])}
    if t >= base.result["return_time"]:
        end = base.unit["end_location"]
        return {"area": f"the {end['name']}", "until": base.unit["shift_end"], "until_label": fmt_time(base.unit["shift_end"])}
    k = max([i for i, a in enumerate(arr) if a <= t] or [0])
    label = region_of(nodes[k])
    while k + 1 < len(nodes) and region_of(nodes[k + 1]) == label:
        k += 1
    return {"area": label, "until": dep[k], "until_label": fmt_time(dep[k])}


def classify(fails, nodes, unit):
    if any(n["window_start"] >= unit["shift_end"] for n in nodes):
        return "past shift end"
    if any(n["window_start"] > n["window_end"] + EPS for n in nodes) or fails == {"new_late"} or not fails:
        return "can't reach it in time"
    if "return_late" in fails and "existing_late" not in fails:
        return "past shift end"
    return "no room"


def short_address(addr):
    street = (addr or "").split(",")[0].strip()
    for suf in (" Ave", " St", " Blvd", " Rd", " Way", " Dr"):
        if street.endswith(suf):
            return street[: -len(suf)]
    return street


def pass_by(unit_name, base, first_new, ahead_only=False):
    real = [i for i, n in enumerate(base.nodes) if not n.get("is_pos") and (not ahead_only or i >= base.min_pos)]
    if not real:
        return None
    best = min(real, key=lambda i: haversine_miles(first_new["lat"], first_new["lon"], base.nodes[i]["lat"], base.nodes[i]["lon"]))
    stop = base.nodes[best]
    d = haversine_miles(first_new["lat"], first_new["lon"], stop["lat"], stop["lon"])
    dist = "less than 0.1 miles" if d < 0.05 else f"{d:.1f} miles"
    return {"stop_key": stop["key"], "stop_name": stop["customer_name"], "time": base.arr[best],
            "miles": round(d, 2),
            "line": f"{unit_name} stops at {short_address(stop['address'])} at {fmt_time(base.arr[best])}, {dist} from you."}


def extra_slots(unit, base, nodes, s, out, skip, limit):
    """Other feasible pickup/drop-off placements on this unit, cheapest first."""
    found = []
    P, D = nodes
    for _, i, j in pair_cands(base, P, D, set()):
        seq, final = try_pair(base, P, D, i, j, set())
        if not seq or tuple(n["key"] for n in seq) in skip:
            continue
        found.append(_result(unit, base, seq, final, nodes, s, out))
        if len(found) >= limit:
            break
    return found


@dataclass(frozen=True)
class PriceCtx:
    """The job being priced and the settings it is priced under (same for every unit)."""
    job: dict
    nodes: list
    s: dict
    travel: Callable
    clock: Optional[float] = None
    skill: Optional[str] = None
    extras: int = 0


def _is_pair(nodes):
    return len(nodes) == 2 and nodes[0]["kind"] == "pickup" and nodes[1]["kind"] == "dropoff"


def _insert_all(unit, base, ctx, pickups, fails):
    if _is_pair(ctx.nodes):
        return insert_pair(base, ctx.nodes[0], ctx.nodes[1], fails)
    seq, final, cur = None, None, base
    for x in ctx.nodes:
        need = {f"new:{p}" for p in pickups.get(x["ref"], set())}
        seq, final = insert_single(cur, x, need, fails)
        if not seq:
            break
        cur = Base(unit, seq, ctx.s, ctx.travel, ctx.clock)
    return seq, final


def price_unit(unit, base_nodes, ctx):
    """Price one unit. Returns a result dict (feasible or with a plain reason)."""
    nodes, s, travel = ctx.nodes, ctx.s, ctx.travel
    out = {"unit_key": unit["key"], "unit_name": unit["name"], "color": unit.get("color")}
    base = Base(unit, base_nodes, s, travel, ctx.clock)
    req_time = nodes[0]["window_start"] if nodes else unit["shift_start"]
    if ctx.skill and ctx.skill not in (unit.get("skills") or []):
        return {**out, "feasible": False, "reason": "missing skill", "where": where_is(base, req_time)}
    pickups = pickups_of(ctx.job)
    fails = set()
    seq, final = _insert_all(unit, base, ctx, pickups, fails)
    if not seq:
        return {**out, "feasible": False, "reason": classify(fails, nodes, unit), "where": where_is(base, req_time)}
    raw = tuple(n["key"] for n in seq)
    seq, final = swap_pass(unit, seq, final, s, travel, base.min_pos, pickups)
    best = _result(unit, base, seq, final, nodes, s, out)
    if ctx.extras and _is_pair(nodes):
        best["_extras"] = extra_slots(unit, base, nodes, s, out, {raw, tuple(best["sequence"])}, ctx.extras)
    return best


def _result(unit, base, seq, final, nodes, s, out):
    d_drive = final["driving_minutes"] - base.result["driving_minutes"]
    d_miles = final["total_miles"] - base.result["total_miles"]
    service = sum(n["service_minutes"] for n in nodes)
    minutes = int(half_up(max(0.0, d_drive) + service, 0))
    miles = half_up(max(0.0, d_miles), 1)
    rows = {r["stop_key"]: r for r in final["stops"]}
    real = [n for n in seq if not n.get("is_pos")]
    placed = []
    for idx, n in enumerate(real):
        if n.get("is_new"):
            prev = real[idx - 1] if idx else None
            r = rows[n["key"]]
            placed.append({"ref": n["ref"], "name": n["customer_name"], "address": n["address"], "kind": n["kind"],
                           "key": n["key"], "lat": n["lat"], "lon": n["lon"],
                           "position": idx + 1, "after": prev["customer_name"] if prev else unit["start_location"]["name"],
                           "arrival": r["arrival"], "arrival_label": fmt_time(r["arrival"]),
                           "window_start": n["window_start"], "window_end": n["window_end"],
                           "approximate": n.get("approximate", False)})
    return {
        **out, "feasible": True, "added_minutes": minutes, "added_miles": miles, "added_cost": added_cost(minutes, miles, s),
        "added_driving_minutes_exact": round(d_drive, 2), "added_miles_exact": round(d_miles, 3), "service_minutes": service,
        "new_stops": placed, "sequence": [n["key"] for n in real], "base_keys": [n["key"] for n in base.nodes if not n.get("is_pos")],
        "new_spare_minutes": final["spare_minutes"], "new_return_label": fmt_time(final["return_time"]),
        "pass_by": pass_by(unit["name"], base, nodes[0]), "pass_by_ahead": pass_by(unit["name"], base, nodes[0], ahead_only=True), "nodes": [n for n in seq if n.get("is_new")],
    }


def price_all(units_ctx, job, nodes, s, travel, clock, skill, extras=0):
    ctx = PriceCtx(job, nodes, s, travel, clock, skill, extras)
    res = [price_unit(u, b, ctx) for u, b in units_ctx]
    cands = []
    for r in res:
        if r["feasible"]:
            cands += [r] + r.pop("_extras", [])
    for r in cands:
        r.update(price_quote(r["added_minutes"], r["added_miles"], r["added_cost"], r["unit_name"], job["frequency"], s))
    feas = [r for r in res if r["feasible"]]
    winner = min(feas, key=lambda r: (r["added_cost"], r["added_minutes"], r["unit_key"])) if feas else None
    if extras:
        return res, winner, cands
    return res, winner


def _shift_line(job, mode, k, winner):
    asked = {js["ref"]: js for js in job["stops"]}
    parts = []
    for n in winner["new_stops"]:
        js = asked[n["ref"]]
        if n["kind"] != "dropoff" and js.get("window_start") is not None and abs(n["arrival"] - js["window_start"]) > 0.5 and (mode == "B" or n["arrival"] < js["window_start"]):
            parts.append(f"the pickup at {n['arrival_label']} instead of {fmt_time(js['window_start'])}")
        if n["kind"] == "dropoff" and js.get("window_end") is not None and n["arrival"] > js["window_end"] + EPS:
            parts.append(f"delivery by {fmt_time(n['window_end'])} instead of {fmt_time(js['window_end'])}")
    if not parts:
        moved = f"{abs(k)} minutes {'later' if k > 0 else 'earlier'}" if mode == "B" else f"{STEP * k} minutes"
        parts.append(f"the time moved {moved}")
    return f"Works on {winner['unit_name']} with " + " and ".join(parts[:2]) + "."


def window_search(units_ctx, job, s, travel, clock, skill):
    plans = [("A", k) for k in range(1, MAX_STEPS + 1)] if job.get("pairs") else []
    for k in range(1, MAX_STEPS + 1):
        plans += [("B", -STEP * k), ("B", STEP * k)]
    for mode, k in plans:
        nodes = build_nodes(job, s, mode, k, clock)
        if any(n["window_start"] > n["window_end"] + EPS for n in nodes):
            continue
        res, winner = price_all(units_ctx, job, nodes, s, travel, clock, skill)
        if winner:
            return {"found": True, "mode": "deadline_later" if mode == "A" else "both_moved",
                    "shift_minutes": STEP * k if mode == "A" else k, "line": _shift_line(job, mode, k, winner),
                    "winner": winner, "_plan": (mode, k)}
    return {"found": False, "line": "No time within 2 hours works."}


EXTRAS_PER_VAN = 8


def candidates(units_ctx, job, s, travel, clock, skill, plan=None):
    nodes = build_nodes(job, s, plan[0] if plan else None, plan[1] if plan else 0, clock)
    _, _, cands = price_all(units_ctx, job, nodes, s, travel, clock, skill, EXTRAS_PER_VAN)
    return cands


def run_engine(units_ctx, job, s, travel, clock=None, same_day=False, with_options=False, rules=None):
    out = _run(units_ctx, job, s, travel, clock, same_day)
    if with_options:
        from engine.options import build_options
        from engine.rules import apply_rules
        eff = clock if same_day else None
        sh = out["shifted"]
        cands = []
        if out["winner"]:
            cands = candidates(units_ctx, job, s, travel, eff, job.get("skill"))
        elif sh and sh.get("found"):
            cands = candidates(units_ctx, job, s, travel, eff, job.get("skill"), sh["_plan"])
        cands, blocked = apply_rules(cands, rules or [])
        out["options"] = build_options(cands, job, s, shifted=not out["winner"], plan=sh.get("_plan") if sh and not out["winner"] else None)
        out["options"]["blocked"] = blocked
    if out["shifted"]:
        out["shifted"].pop("_plan", None)
    return out


def _run(units_ctx, job, s, travel, clock=None, same_day=False):
    nodes = build_nodes(job, s, None, 0, clock if same_day else None)
    eff_clock = clock if same_day else None
    skill = job.get("skill")
    if same_day and any((js.get("window_end") if js.get("window_end") is not None else 1020) <= clock for js in job["stops"]):
        res = []
        for u, b in units_ctx:
            base = Base(u, b, s, travel, None)
            res.append({"unit_key": u["key"], "unit_name": u["name"], "color": u.get("color"), "feasible": False,
                        "reason": "the window has already passed", "where": where_is(base, clock)})
        winner = None
    else:
        res, winner = price_all(units_ctx, job, nodes, s, travel, eff_clock, skill)
    shifted = None if winner else window_search(units_ctx, job, s, travel, eff_clock, skill)
    return {"results": res, "winner_unit_key": winner["unit_key"] if winner else None, "winner": winner, "shifted": shifted}
