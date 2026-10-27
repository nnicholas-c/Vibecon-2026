"""Memory (owner rules) and Activity (timeline) API."""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from activity import log
from core import BKEY, db
from engine.rules import AREA_NAMES, parse_rule
from engine.timing import fmt_time

router = APIRouter(prefix="/api")


def rule_view(d):
    p = parse_rule(d.get("text") or "")
    line = f"Keeps {p['van'].replace('van-', 'Van ')} out of {AREA_NAMES[p['area']]} after {fmt_time(p['after_minutes'])}." if p else None
    return {"id": str(d["_id"]), "text": d.get("text", ""), "active": bool(d.get("active")), "created_at": d.get("created_at"),
            "enforced": bool(p), "enforced_line": line}


def oid(rule_id):
    try:
        return ObjectId(rule_id)
    except (InvalidId, TypeError):
        raise HTTPException(404, "We couldn't find that rule.")


@router.get("/memory/rules")
async def list_rules():
    return {"rules": [rule_view(d) async for d in db.agent_rules.find({"business_id": BKEY}).sort("created_at", -1)]}


class RulePatch(BaseModel):
    active: bool


@router.patch("/memory/rules/{rule_id}")
async def toggle_rule(rule_id: str, body: RulePatch):
    d = await db.agent_rules.find_one_and_update({"_id": oid(rule_id), "business_id": BKEY}, {"$set": {"active": body.active}},
                                                 return_document=True)
    if not d:
        raise HTTPException(404, "We couldn't find that rule.")
    await log("owner", f"Turned {'on' if body.active else 'off'} the rule '{d['text']}'.", "rule")
    return rule_view(d)


@router.delete("/memory/rules/{rule_id}")
async def delete_rule(rule_id: str):
    d = await db.agent_rules.find_one_and_delete({"_id": oid(rule_id), "business_id": BKEY})
    if not d:
        raise HTTPException(404, "We couldn't find that rule.")
    await log("owner", f"Deleted the rule '{d['text']}'.", "rule")
    return {"ok": True}


def van_name(args):
    return (args.get("van_id") or "a van").replace("van-", "Van ")


TOOL_LINES = {
    "get_fleet_summary": lambda a: "Looked up the fleet summary.",
    "get_van_route": lambda a: f"Looked up {van_name(a)}'s route for today.",
    "explain_stop": lambda a: f"Explained why {a.get('stop_key', 'a stop')} sits where it does on {van_name(a)}.",
    "get_options": lambda a: f"Looked up the options for {a.get('request_key', 'a request')}.",
    "move_stop": lambda a: f"Moved {a.get('stop_key', 'a stop')} to position {a.get('new_position')} on {van_name(a)}.",
    "save_rule": lambda a: f"Saved the rule '{a.get('text', '')}'.",
}


def event_view(e):
    if e.get("tool"):
        args = e.get("args") or {}
        line = TOOL_LINES.get(e["tool"], lambda a: f"Used {e['tool']}.")(args)
        if '"error"' in (e.get("result_summary") or "")[:12]:
            line += " It didn't work."
        return {"id": str(e["_id"]), "ts": e["ts"], "actor": "assistant", "line": line, "kind": "tool", "tool": e["tool"],
                "scope": e.get("scope")}
    return {"id": str(e["_id"]), "ts": e["ts"], "actor": e.get("actor", "owner"), "line": e.get("line", ""),
            "kind": e.get("kind"), "tool": None, "scope": e.get("scope")}


@router.get("/activity")
async def activity(limit: int = 300):
    rows = [event_view(e) async for e in db.events.find({}).sort("ts", -1).limit(max(1, min(limit, 1000)))]
    return {"events": rows}
