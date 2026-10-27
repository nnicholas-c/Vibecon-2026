"""Step 11 Q-851: one Gmail message handled 10 times creates exactly one request (source_key dedupe). Also shows the poller lease."""
import asyncio
import sys

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")
from core import db  # noqa: E402
import google_api as g  # noqa: E402

M = {"id": "test-msg-dedupe-1", "thread_id": None, "rfc_id": "<x@y>", "references": "", "subject": "Pickup",
     "from_name": "Dedupe Test", "from_email": "dedupe@example.com", "files": [],
     "text": "pickup 2 boxes at 1300 Clay St Oakland, deliver to 1261 Fallon St by 3pm today"}


async def main():
    await db.requests.create_index("source_key", unique=True, partialFilterExpression={"source_key": {"$type": "string"}})
    results = [await g.handle_message(dict(M), None) for _ in range(10)]
    n = await db.requests.count_documents({"source_key": M["id"]})
    print("results:", results, "| requests with this source_key:", n)
    print("poller lease:", await db.locks.find_one({"key": g.LEASE_KEY}, {"_id": 0}))
    await asyncio.sleep(8)
    await db.requests.delete_many({"source_key": M["id"]})

asyncio.run(main())
