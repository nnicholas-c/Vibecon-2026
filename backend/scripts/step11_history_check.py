"""Step 11: history.list ids, the 404 fallback and the cursor advance, against a stubbed Gmail."""
import asyncio
import sys

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")
import google_api as g  # noqa: E402

calls = []


async def fake(method, path, token, **kw):
    calls.append((path, kw.get("params", {}).get("startHistoryId")))
    if path == "history":
        if kw["params"]["startHistoryId"] == "old":
            raise g.GoogleError(404, "notFound")
        return {"historyId": "205", "history": [{"messagesAdded": [{"message": {"id": "m1"}}]}, {"messagesAdded": [{"message": {"id": "m2"}}, {"message": {"id": "m1"}}]}]}
    return {}


async def main():
    g.G.gmail = fake
    print("history:", await g.history_ids("t", "200"))
    print("too old:", await g.history_ids("t", "old"))
    print("calls:", calls)

asyncio.run(main())
