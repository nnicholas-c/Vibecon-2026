"""Plain-Python route optimizer: 2-opt and or-opt moves that keep every window, the shift end and capacity."""
from engine.timing import compute_route

MAX_MOVES = 40


def _pairs_ok(order):
    pos = {n["key"]: i for i, n in enumerate(order)}
    for n in order:
        p = n.get("paired_stop_key")
        if p in pos and n.get("kind") == "dropoff" and pos[p] > pos[n["key"]]:
            return False
    return True


def _two_opt(order, n):
    for i in range(n - 1):
        for j in range(i + 1, n):
            yield order[:i] + order[i:j + 1][::-1] + order[j + 1:]


def _or_opt(order, n):
    for size in (1, 2, 3):
        for i in range(n - size + 1):
            seg, rest = order[i:i + size], order[:i] + order[i + size:]
            for k in range(len(rest) + 1):
                if k != i:
                    yield rest[:k] + seg + rest[k:]


def optimize(unit, nodes, s, travel):
    """Returns the best feasible order found, with before/after route results."""
    before = compute_route(unit, nodes, s, travel=travel)
    best, best_r = list(nodes), before
    if not before["feasible"] or len(nodes) < 3:
        return {"order": best, "before": before, "after": best_r, "improved": False}

    def path_miles(order):
        pts = [unit["start_location"], *order, unit["end_location"]]
        return sum(travel(a, b)[0] for a, b in zip(pts, pts[1:]))

    best_m = path_miles(best)
    for _ in range(MAX_MOVES):
        found = False
        for gen in (_two_opt, _or_opt):
            for cand in gen(best, len(best)):
                m = path_miles(cand)
                if m >= best_m - 0.05 or not _pairs_ok(cand):
                    continue
                r = compute_route(unit, cand, s, travel=travel)
                if r["feasible"] and r["total_minutes"] <= best_r["total_minutes"] + 0.01:
                    best, best_r, best_m, found = cand, r, m, True
                    break
            if found:
                break
        if not found:
            break
    improved = best_r["total_miles"] < before["total_miles"] - 0.1
    return {"order": best if improved else list(nodes), "before": before, "after": best_r if improved else before, "improved": improved}
