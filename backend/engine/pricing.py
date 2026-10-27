"""Prices from added cost (plain math, deterministic)."""
import math
from decimal import ROUND_HALF_UP, Decimal

DAY_NAMES = {"mon": "Mondays", "tue": "Tuesdays", "wed": "Wednesdays", "thu": "Thursdays", "fri": "Fridays"}
VISITS_PER_WEEKDAY = 4.3


def half_up(x, places=2):
    q = Decimal(1).scaleb(-places)
    return float(Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP))


def money_text(x):
    return f"${x:,.0f}" if abs(x - round(x)) < 1e-9 else f"${x:,.2f}"


def added_cost(minutes, miles, s):
    return half_up(minutes * s["wage_per_hour"] / 60 + miles * s["cost_per_mile"])


def hand_check(minutes, miles, cost, s):
    return f"{minutes} min x ${s['wage_per_hour'] / 60:.4f} + {miles:.1f} mi x ${s['cost_per_mile']:.2f} = ${cost:.2f}"


def join_days(days):
    names = [DAY_NAMES[d] for d in days]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def round_up_50(x):
    return math.ceil(half_up(x, 4) * 2 - 1e-9) / 2


def price_quote(minutes, miles, cost, unit_name, frequency, s):
    kind = frequency["type"]
    floor = s["floor_one_off"] if kind == "one_off" else s["floor_recurring"]
    usual = s["usual_one_off"] if kind == "one_off" else s["usual_recurring"]
    marked = cost * (1 + s["markup_pct"] / 100)
    raw = max(marked, floor)
    uncapped = max(round_up_50(raw), floor)
    capped = uncapped > usual + 1e-9
    price = usual if capped else uncapped
    margin = half_up(price - cost)
    monthly = None
    if kind == "weekday":
        monthly = half_up(price * s["weekdays_per_month"])
    elif kind == "weekdays":
        monthly = half_up(price * VISITS_PER_WEEKDAY * len(frequency["days"]))
    head = f"Adds {minutes} min and {miles:.1f} mi to {unit_name}, which costs ${cost:.2f}."
    if capped:
        rule = f"With your {s['markup_pct']:g}% markup that's {money_text(round_up_50(marked))}, so the quote is capped at your usual"
    elif marked > floor + 1e-9:
        rule = f"With your {s['markup_pct']:g}% markup, the quote is"
    else:
        rule = f"Your floor is {money_text(floor)}, so the quote is"
    if kind == "one_off":
        tail = f"{money_text(price)} for the run."
    elif kind == "weekday":
        tail = f"{money_text(price)} a visit, or {money_text(monthly)} a month."
    else:
        n = len(frequency["days"])
        tail = (f"{money_text(price)} a visit, or {money_text(monthly)} a month "
                f"({join_days(frequency['days'])}, {VISITS_PER_WEEKDAY:g} visits a month {'each' if n > 1 else ''}".rstrip() + ").")
    market = None
    if kind == "one_off":
        market = (f"A typical on-demand run in the Bay Area is {money_text(s['market_ref_low'])} "
                  f"to {money_text(s['market_ref_high'])}.")
    return {
        "price": price, "floor": floor, "usual": usual, "capped": capped,
        "loses_money": cost > usual + 1e-9, "hold_as_draft": cost > usual + 1e-9,
        "price_set_by": "usual" if capped else ("markup" if marked > floor + 1e-9 else "floor"),
        "margin": margin, "monthly_total": monthly, "per": "run" if kind == "one_off" else "visit",
        "explanation": f"{head} {rule} {tail}", "market_line": market,
        "hand_check": hand_check(minutes, miles, cost, s),
    }
