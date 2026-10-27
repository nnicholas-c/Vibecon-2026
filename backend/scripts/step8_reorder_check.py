"""Step 8: move a stop through the assistant tool and mark a stop done from the driver phone; print reorder events."""
import asyncio
import json
import sys

import httpx

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")
import agent  # noqa: E402
from core import get_business  # noqa: E402

c = httpx.Client(base_url="http://localhost:8001/api", timeout=120)


async def main():
    c.post("/demo/reset")
    since = c.get("/events").json()["now"]
    biz = await get_business()
    route = json.loads(await agent.run_tool("van-2", "get_van_route", {"van_id": "van-2"}, biz))["stops"]
    print("move:", await agent.run_tool("van-2", "move_stop", {"van_id": "van-2", "stop_key": route[-1]["stop_key"], "new_position": len(route) - 2}, biz))
    print("driver done:", c.post("/phones/driver/messages", json={"text": "done"}).json())
    print("events:", c.get("/events", params={"since": since}).json()["events"])
asyncio.run(main())
