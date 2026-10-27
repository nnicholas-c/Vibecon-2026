"""Activity feed entries, stored in the shared events collection next to the assistant's tool calls."""
from datetime import datetime, timezone

from core import BKEY, db


async def log(actor, line, kind):
    await db.events.insert_one({"business_key": BKEY, "ts": datetime.now(timezone.utc).isoformat(), "scope": "activity",
                                "kind": kind, "actor": actor, "line": line})
