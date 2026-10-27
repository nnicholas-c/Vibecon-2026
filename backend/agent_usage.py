"""Daily model-call budget shared by the assistant (agent.py) and the reader (ai/ladder.py)."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from core import BKEY, db

DAILY_LIMIT = int(os.environ.get("AGENT_DAILY_LIMIT", "100000"))
PACIFIC = ZoneInfo("America/Los_Angeles")


async def take_call():
    day = datetime.now(PACIFIC).date().isoformat()
    doc = await db.agent_usage.find_one_and_update(
        {"business_key": BKEY, "date": day}, {"$inc": {"model_calls_today": 1}}, upsert=True, return_document=True)
    return doc["model_calls_today"] <= DAILY_LIMIT


async def over_limit():
    doc = await db.agent_usage.find_one({"business_key": BKEY, "date": datetime.now(PACIFIC).date().isoformat()})
    return bool(doc) and doc.get("model_calls_today", 0) >= DAILY_LIMIT
