import logging
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from core import (BKEY, client, data_lock, db, ensure_matrix, get_business, load_units,
                  rebuild_matrix, recompute_all, today_plans)
from engine.jobs import seed_jobs
from engine.timing import fmt_time
from engine_api import router as engine_router
from ai_api import router as ai_router
from ai import ladder
from agent import reply as agent_reply
from inbox_api import router as inbox_router
from phones_api import router as phones_router
from routes_api import router as routes_router
from google_api import router as google_router
from memory_api import router as memory_router
from live_api import router as live_router
from import_api import router as import_router
from activity import log as log_activity
from position import late_insight, van_position
from reading.locate import seed_geo_cache
from models import AgentThread, Business, DirectoryEntry, Prospect, Request, RoutePlan, RunRecord, Settings, Stop, Unit
from seed import data as D
from demo_core import (demo_date_label, ensure_indexes, first_seed, friendly, on_time_by_unit, reset_demo, today_pacific,  # noqa: F401
                       write_seed)

TRAVEL_KEYS = {"speed_sf_mph", "speed_eastbay_mph", "speed_cross_mph", "bridge_minutes", "road_factor"}
app = FastAPI(title="Drivepast API", version="phase-4", openapi_url="/api/openapi.json", docs_url="/api/docs", redoc_url=None)
api = APIRouter(prefix="/api")
logger = logging.getLogger("drivepast")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@app.exception_handler(HTTPException)
async def http_error(_, exc):
    msg = exc.detail if isinstance(exc.detail, str) else "Something went wrong. Try again in a moment."
    return friendly(exc.status_code, msg)


@app.exception_handler(RequestValidationError)
async def validation_error(_, exc):
    return friendly(422, "Some values need fixing.")


@app.exception_handler(Exception)
async def any_error(_, exc):
    logger.exception("Unhandled error: %s", exc)
    return friendly(500, "Something went wrong. Try again in a moment.")


# ---------- data helpers ----------

async def plan_stops(plan):
    if not plan:
        return []
    keys = [r["stop_key"] for r in plan.stops]
    docs = {d["key"]: Stop.from_mongo(d) async for d in db.stops.find({"business_key": BKEY, "key": {"$in": keys}})}
    return [docs[k] for k in keys if k in docs]


async def recompute_route_plans(settings: Dict[str, Any], demo_date, rebuild=False):
    started = time.perf_counter()
    if rebuild:
        await rebuild_matrix(settings)
    else:
        await ensure_matrix(settings)
    await recompute_all(settings, demo_date)
    return round((time.perf_counter() - started) * 1000, 1)


def stop_tags(s: Stop):
    tags = ["Done"] if getattr(s, "done_date", None) else []
    if getattr(s, "source", "seed") == "quote":
        tags.append("New")
        if s.recurrence == "one_off":
            tags.append("One day only")
        elif s.recurrence == "weekdays":
            from engine.pricing import join_days
            tags.append(join_days(s.weekdays))
        if getattr(s, "start_date", None):
            d = datetime.fromisoformat(s.start_date)
            tags.append(f"Starts {d.strftime('%a, %b ')}{d.day}")
    return tags


def unit_stats(unit: Unit, plan: Optional[RoutePlan], stops, settings, ontime):
    n = len(stops)
    minutes = plan.total_minutes if plan else 0
    miles = plan.total_miles if plan else 0
    cost_total = minutes * settings["wage_per_hour"] / 60 + miles * settings["cost_per_mile"]
    good, runs = ontime.get(unit.key, (0, 0))
    return {
        "stops_count": n,
        "spare_minutes": plan.spare_minutes if plan else 0,
        "busy_minutes": round(getattr(plan, "driving_minutes", 0) + getattr(plan, "service_minutes", 0)) if plan else 0,
        "route_minutes": round(minutes, 1),
        "route_miles": round(miles, 1),
        "revenue_per_day": round(sum(s.price_per_visit for s in stops), 2),
        "cost_per_stop": round(cost_total / n, 2) if n else 0,
        "on_time_rate": round(100 * good / runs, 1) if runs else None,
        "on_time_runs": good,
        "total_runs": runs,
        "feasible": plan.feasible if plan else False,
        "return_label": fmt_time(plan.return_time) if plan else "",
    }


def unit_summary(unit: Unit, stats):
    return {"key": unit.key, "kind": unit.kind, "name": unit.name, "nickname": unit.nickname,
            "driver_name": unit.driver_name, "color": unit.color, **stats}


async def business_summary(biz: Business):
    s = biz.settings
    return {"key": biz.key, "name": biz.name, "type": biz.type, "owner_name": biz.owner_name, "tagline": biz.tagline,
            "demo_date": biz.demo_date, "demo_date_label": demo_date_label(biz.demo_date),
            "demo_clock_minutes": s.demo_clock_minutes, "demo_clock_label": fmt_time(s.demo_clock_minutes)}


# ---------- seed and reset ----------

async def migrate_jobs(biz):
    """Add Phase 2 structured jobs to requests seeded before Phase 2, and keep van colors current."""
    for van in D.VANS:
        await db.units.update_one({"business_key": BKEY, "key": van["key"]}, {"$set": {"color": van["color"]}})
    if await db.requests.count_documents({"business_key": BKEY, "job_status": {"$exists": False}}):
        jobs = seed_jobs(datetime.fromisoformat(biz.demo_date).date())
        for num, fields in jobs.items():
            await db.requests.update_one({"business_key": BKEY, "number": num}, {"$set": fields})


@app.on_event("startup")
async def startup():
    from google_api import start_gmail_poller
    start_gmail_poller()
    async with data_lock:
        if not await db.businesses.find_one({"key": BKEY}):
            logger.info("No Bayline Courier data found, seeding")
            await first_seed([])
        else:
            await ensure_indexes()
            if await db.units.count_documents({"business_key": BKEY, "key": {"$nin": [v["key"] for v in D.VANS]}}):
                logger.warning("Stored fleet differs from the seed; press Reset to reseed (not done on startup)")
            biz = await get_business()
            await migrate_jobs(biz)
            await ensure_matrix(biz.settings.model_dump())
        await seed_geo_cache()
    from inbox_api import resume_stuck_reads
    await resume_stuck_reads()


@app.on_event("shutdown")
async def shutdown():
    from google_api import stop_gmail_poller
    await stop_gmail_poller()
    client.close()


# ---------- routes ----------

@api.get("/health")
async def health():
    return {"ok": True}


@api.get("/fleet")
async def fleet():
    biz = await get_business()
    settings = biz.settings.model_dump()
    plans, ontime = await today_plans(biz.demo_date), await on_time_by_unit()
    units = []
    for unit in await load_units():
        stops = await plan_stops(plans.get(unit.key))
        units.append(unit_summary(unit, unit_stats(unit, plans.get(unit.key), stops, settings, ontime)))
    inbox = await db.requests.count_documents({"business_key": BKEY, "status": {"$nin": ["quoted", "accepted", "declined"]}})
    return {"business": await business_summary(biz), "units": units, "inbox_new_count": inbox,
            "totals": {"stops": sum(u["stops_count"] for u in units), "spare_minutes": sum(u["spare_minutes"] for u in units),
                       "new_stops": await db.quotes.count_documents({"business_key": BKEY, "status": "accepted"}),
                       "revenue_per_day": round(sum(u["revenue_per_day"] for u in units), 2)}}


LATE_AFTER_PLAN_MIN = 10


@api.get("/brief")
async def morning_brief():
    data = await fleet()
    pipeline = [{"$match": {"business_key": BKEY}},
                {"$group": {"_id": "$unit_key", "runs": {"$sum": 1}, "late": {"$sum": {"$cond": [
                    {"$gt": [{"$subtract": ["$actual_arrival", "$planned_arrival"]}, LATE_AFTER_PLAN_MIN]}, 1, 0]}}}}]
    late = {r["_id"]: (r["late"], r["runs"]) async for r in db.run_history.aggregate(pipeline)}
    vans = [{"key": u["key"], "name": u["name"], "color": u["color"], "spare_minutes": u["spare_minutes"],
             "late_runs": late.get(u["key"], (0, 0))[0], "total_runs": late.get(u["key"], (0, 0))[1]} for u in data["units"]]
    worst = max(vans, key=lambda v: v["late_runs"] / v["total_runs"] if v["total_runs"] else 0)
    return {"vans": vans, "most_late": worst, "late_after_plan_minutes": LATE_AFTER_PLAN_MIN,
            "total_spare_minutes": data["totals"]["spare_minutes"]}


@api.get("/businesses")
async def businesses():
    return [{"key": b["key"], "name": b["name"], "type": b["type"]} async for b in db.businesses.find({}, {"key": 1, "name": 1, "type": 1})]


@api.get("/units/{unit_key}")
async def unit_page(unit_key: str):
    biz = await get_business()
    unit = Unit.from_mongo(await db.units.find_one({"business_key": BKEY, "key": unit_key}))
    if not unit:
        raise HTTPException(404, "We couldn't find that van.")
    settings = biz.settings.model_dump()
    plan = (await today_plans(biz.demo_date)).get(unit_key)
    stops = await plan_stops(plan)
    by_key = {s.key: s for s in stops}
    stats = unit_stats(unit, plan, stops, settings, await on_time_by_unit())
    clock = biz.settings.demo_clock_minutes
    from routes_api import current_shifts
    shifts = await current_shifts(unit_key)
    timeline = []
    for row in (plan.stops if plan else []):
        s = by_key.get(row["stop_key"])
        if not s:
            continue
        timeline.append({
            **row, "customer_name": s.customer_name, "customer_type": s.customer_type, "address": s.address,
            "kind": s.kind, "window_start": s.window_start, "window_end": s.window_end, "lat": s.lat, "lon": s.lon,
            "service_minutes_planned": s.service_minutes, "price_per_visit": s.price_per_visit,
            "arrival_label": fmt_time(row["arrival"]), "departure_label": fmt_time(row["departure"]),
            "window_label": f"{fmt_time(s.window_start)} to {fmt_time(s.window_end)}",
            "passed": row["departure"] <= clock, "source": getattr(s, "source", "seed"), "tags": stop_tags(s),
            "time_shift": shifts.get(row["stop_key"]),
        })
    return {
        "unit": {**unit_summary(unit, stats), "driver_phone": unit.driver_phone, "areas": unit.areas,
                 "shift_start_label": fmt_time(unit.shift_start), "shift_end_label": fmt_time(unit.shift_end),
                 "shift_minutes": unit.shift_end - unit.shift_start,
                 "start_location": unit.start_location, "end_location": unit.end_location, "capacity": unit.capacity},
        "plan": {"version": plan.version, "feasible": plan.feasible, "problems": plan.problems,
                 "total_minutes": plan.total_minutes, "total_miles": plan.total_miles, "spare_minutes": plan.spare_minutes,
                 "driving_minutes": getattr(plan, "driving_minutes", None), "service_minutes": getattr(plan, "service_minutes", None),
                 "spare_minutes_exact": plan.spare_minutes_exact, "return_time": plan.return_time,
                 "return_label": fmt_time(plan.return_time), "start_label": fmt_time(plan.start_departure),
                 "start_departure": plan.start_departure,
                 "computed_at": plan.computed_at} if plan else None,
        "timeline": timeline,
        "position": van_position(plan, {s.key: (s.lat, s.lon) for s in stops}, unit.start_location, unit.end_location, clock),
        "insight": await late_insight(unit_key),
        "demo_clock_minutes": clock, "demo_clock_label": fmt_time(clock),
    }


@api.get("/route-plans")
async def route_plans(unit_key: Optional[str] = None, include_previous: bool = False):
    q = {"business_key": BKEY}
    if unit_key:
        q["unit_key"] = unit_key
    if not include_previous:
        q["is_current"] = True
    return [RoutePlan.from_mongo(p).public() async for p in db.route_plans.find(q).sort([("unit_key", 1), ("version", -1)])]


@api.post("/route-plans/recompute")
async def recompute():
    biz = await get_business()
    async with data_lock:
        ms = await recompute_route_plans(biz.settings.model_dump(), biz.demo_date)
    return {"recomputed": True, "ms": ms}


@api.get("/stops")
async def list_stops(unit_key: Optional[str] = None):
    q = {"business_key": BKEY, **({"unit_key": unit_key} if unit_key else {})}
    return [Stop.from_mongo(s).public() async for s in db.stops.find(q).sort([("unit_key", 1), ("seq", 1)])]


@api.get("/run-history")
async def run_history(stop_key: Optional[str] = None, unit_key: Optional[str] = None):
    q = {"business_key": BKEY}
    if stop_key:
        q["stop_key"] = stop_key
    if unit_key:
        q["unit_key"] = unit_key
    return [RunRecord.from_mongo(r).public() async for r in db.run_history.find(q).sort([("stop_key", 1), ("date", 1)])]


@api.get("/run-history/summary")
async def run_history_summary():
    pipeline = [{"$match": {"business_key": BKEY}},
                {"$group": {"_id": "$stop_key", "runs": {"$sum": 1}, "avg_service": {"$avg": "$actual_service_minutes"},
                            "on_time": {"$sum": {"$cond": ["$on_time", 1, 0]}}, "dates": {"$addToSet": "$date"}}}]
    rows = [{"stop_key": r["_id"], "runs": r["runs"], "weekdays": len(r["dates"]), "on_time": r["on_time"],
             "avg_service_minutes": round(r["avg_service"], 2)} async for r in db.run_history.aggregate(pipeline)]
    return sorted(rows, key=lambda r: r["stop_key"])


@api.get("/directory")
async def directory():
    return [DirectoryEntry.from_mongo(d).public() async for d in db.directory.find({"business_key": BKEY}).sort("key", 1)]


@api.get("/prospects")
async def prospects(unit_key: Optional[str] = None):
    q = {"business_key": BKEY, **({"unit_key": unit_key} if unit_key else {})}
    return [Prospect.from_mongo(p).public() async for p in db.prospects.find(q).sort("key", 1)]


@api.get("/requests")
async def requests_list():
    return [Request.from_mongo(r).public() async for r in db.requests.find({"business_key": BKEY}).sort("number", 1)]


# ---------- placeholder agent chat ----------

async def agent_catalog():
    q = await db.quotes.find_one({"business_key": BKEY, "status": "accepted", "preloaded": {"$ne": True}}, sort=[("booking.at", -1)])
    b = (q or {}).get("booking") or {}
    why = [f"Why did {b['customer']}'s job go on {q['unit_name']}?"] if b.get("customer") else []  # REQ-1421
    agents = [{"key": "dispatch", "name": "Fleet", "kind": "dispatch", "color": "#FF5B1F",
               "suggested_prompts": D.DISPATCH_PROMPTS + why}]
    for u in await load_units():
        agents.append({"key": u.key, "name": u.name, "kind": "unit", "color": u.color, "nickname": u.nickname,
                       "suggested_prompts": D.UNIT_PROMPTS})
    return agents


async def find_agent(agent_key):
    agent = next((a for a in await agent_catalog() if a["key"] == agent_key), None)
    if not agent:
        raise HTTPException(404, "We couldn't find that agent.")
    return agent


class MessageIn(BaseModel):
    text: str


@api.get("/agents")
async def agents():
    return await agent_catalog()


@api.get("/agents/{agent_key}/thread")
async def get_thread(agent_key: str):
    agent = await find_agent(agent_key)
    doc = await db.agent_threads.find_one({"business_key": BKEY, "agent_key": agent_key})
    thread = AgentThread.from_mongo(doc) or AgentThread(business_key=BKEY, agent_key=agent_key, agent_name=agent["name"])
    return {"agent": agent, "turns": thread.turns}


@api.post("/agents/{agent_key}/messages")
async def send_message(agent_key: str, body: MessageIn):
    agent = await find_agent(agent_key)
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Type a message first.")
    if len(text) > 2000:
        raise HTTPException(422, "That message is too long. Keep it under 2,000 characters.")
    doc = await db.agent_threads.find_one({"business_key": BKEY, "agent_key": agent_key}, {"turns": 1})
    await log_activity("owner", f"Asked the {'Fleet' if agent_key == 'dispatch' else agent['name']} assistant: \"{text[:120]}\"", "ask")
    answer, tool_lines = await agent_reply(agent_key, text, (doc or {}).get("turns") or [])
    now = datetime.now(timezone.utc).isoformat()
    turns = [{"role": "owner", "text": text, "tool_calls": [], "at": now},
             {"role": "agent", "text": answer, "tool_calls": tool_lines, "at": now}]
    await db.agent_threads.update_one(
        {"business_key": BKEY, "agent_key": agent_key},
        {"$push": {"turns": {"$each": turns}}, "$set": {"agent_name": agent["name"], "updated_at": now},
         "$setOnInsert": {"business_key": BKEY, "agent_key": agent_key, "created_at": now}},
        upsert=True,
    )
    return await get_thread(agent_key)


# ---------- settings ----------

NUMBER_RULES = {
    "wage_per_hour": 0, "cost_per_mile": 0, "markup_pct": 0, "floor_recurring": 0, "floor_one_off": 0,
    "usual_recurring": 0, "usual_one_off": 0,
    "market_ref_low": 0, "market_ref_high": 0, "weekdays_per_month": 1, "speed_sf_mph": 1, "speed_eastbay_mph": 1,
    "speed_cross_mph": 1, "bridge_minutes": 0, "road_factor": 1, "minutes_per_new_stop": 1,
}
POSITIVE = {"weekdays_per_month", "speed_sf_mph", "speed_eastbay_mph", "speed_cross_mph", "road_factor", "minutes_per_new_stop"}
MAXES = {"weekdays_per_month": 31, "road_factor": 3, "markup_pct": 1000, "speed_sf_mph": 80, "speed_eastbay_mph": 80,
         "speed_cross_mph": 80, "bridge_minutes": 120, "minutes_per_new_stop": 120}


def validate_settings(patch: Dict[str, Any], current: Dict[str, Any]):
    errors, clean = {}, {}
    for key, value in patch.items():
        if key in NUMBER_RULES:
            if value is None or isinstance(value, bool) or value == "":
                errors[key] = "Enter a number."
                continue
            try:
                num = float(value)
            except (TypeError, ValueError):
                errors[key] = "Enter a number."
                continue
            if not math.isfinite(num):
                errors[key] = "Enter a number."
            elif num < 0:
                errors[key] = "Use 0 or more."
            elif key in POSITIVE and num <= 0:
                errors[key] = "Use a number above 0."
            elif key in MAXES and num > MAXES[key]:
                errors[key] = f"Use {MAXES[key]} or less."
            else:
                clean[key] = round(num, 4)
        elif key == "auto_send_cheapest":
            if not isinstance(value, bool):
                errors[key] = "Choose on or off."
            else:
                clean[key] = value
        elif key == "demo_clock_minutes":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not (0 <= value < 1440):
                errors[key] = "Pick a time of day."
            else:
                clean[key] = int(value)
        elif key == "texting_channel":
            if value not in ("sms", "whatsapp"):
                errors[key] = "Pick SMS or WhatsApp sandbox."
            else:
                clean[key] = value
        elif key == "team_numbers":
            if not isinstance(value, list) or len(value) > 10:
                errors[key] = "Add up to 10 phone numbers."
                continue
            nums = []
            for v in value:
                digits = "".join(c for c in str(v) if c.isdigit())
                if not isinstance(v, str) or not (7 <= len(digits) <= 15) or any(c not in "0123456789+()- ." for c in v):
                    errors[key] = "Each team number needs 7 to 15 digits."
                    break
                nums.append(v.strip())
            else:
                clean[key] = nums
    merged = {**current, **clean}
    if "market_ref_low" not in errors and "market_ref_high" not in errors and merged["market_ref_low"] > merged["market_ref_high"]:
        errors["market_ref_high"] = "The high end must be at least the low end."
    for fl, us, what in (("floor_recurring", "usual_recurring", "a visit"), ("floor_one_off", "usual_one_off", "for the run")):
        if fl not in errors and us not in errors and merged[fl] > merged[us]:
            errors[fl] = f"Your floor can't be above your usual price of ${merged[us]:g} {what}."
    return clean, errors


def connections(settings: Settings, ai_cfg):
    ours_ok = bool(ai_cfg.get("base_url") and ai_cfg.get("model") and (ai_cfg.get("last_test") or {}).get("ok"))
    backup_ok = bool(os.environ.get("EMERGENT_LLM_KEY")) and ai_cfg.get("mode") != "none"
    return [
        {"key": "our_model", "name": "Our model", "status": "connected" if ours_ok else "fallback",
         "label": "connected" if ours_ok else "using fallback",
         "detail": ai_cfg.get("model") if ours_ok else ("Saved, not connected yet" if ai_cfg.get("base_url") else "Not set up yet")},
        {"key": "backup_ai", "name": "Backup AI (Emergent universal key)", "status": "connected" if backup_ok else "fallback",
         "label": "connected" if backup_ok else "using fallback",
         "detail": f"Reading with {ladder.model_name(ai_cfg.get('reading_model') or 'claude-haiku-4-5')}" if backup_ok else "Off in No AI mode"},
        {"key": "osm", "name": "OpenStreetMap data", "status": "fallback", "label": "using fallback",
         "detail": "Using the 40 built-in nearby businesses. Live business data isn't connected yet."},
        {"key": "texting", "name": "Real texting", "status": "connected" if settings.real_texting else "fallback",
         "label": "connected" if settings.real_texting else "using fallback",
         "detail": "On" if settings.real_texting else "Off. Texts show on the demo phones."},
    ]


async def settings_payload(biz: Business):
    return {"settings": biz.settings.model_dump(), "demo_date": biz.demo_date, "demo_date_label": demo_date_label(biz.demo_date),
            "demo_clock_label": fmt_time(biz.settings.demo_clock_minutes), "business_type_label": "Courier",
            "connections": connections(biz.settings, await db.ai_config.find_one({"business_key": BKEY}) or {})}


@api.get("/settings")
async def get_settings():
    return await settings_payload(await get_business())


@api.put("/settings")
async def update_settings(patch: Dict[str, Any]):
    async with data_lock:
        biz = await get_business()
        current = biz.settings.model_dump()
        clean, errors = validate_settings(patch, current)
        if errors:
            return friendly(422, "Some values need fixing.", errors)
        changed_travel = any(k in TRAVEL_KEYS and clean[k] != current[k] for k in clean)
        merged = Settings(**{**current, **clean})
        await db.businesses.update_one({"key": BKEY}, {"$set": {"settings": merged.model_dump()}})
        ms = await recompute_route_plans(merged.model_dump(), biz.demo_date, rebuild=True) if changed_travel else None
    payload = await settings_payload(await get_business())
    return {**payload, "recomputed": changed_travel, "recompute_ms": ms}


api.post("/demo/reset")(reset_demo)


app.include_router(api)
app.include_router(engine_router)
app.include_router(ai_router)
app.include_router(inbox_router)
app.include_router(phones_router)
app.include_router(routes_router)
app.include_router(google_router)
app.include_router(memory_router)
app.include_router(live_router)
app.include_router(import_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
