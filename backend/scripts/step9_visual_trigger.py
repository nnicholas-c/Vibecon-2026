"""Step 9 visual check helper: wait, trigger a reorder (assistant move_stop on Van 2), then book the Hollis demo quote."""
import asyncio
import json
import sys
import time

import httpx

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")
import agent  # noqa: E402
from core import get_business  # noqa: E402

c = httpx.Client(base_url="http://localhost:8001/api", timeout=120)
HOLLIS = ("Hi Bayline, can you pick up a box of samples today at 5900 Hollis St, Emeryville and get it to "
          "Emeryville Central Lab, 1400 Powell St, Emeryville by 3pm? Thanks, Ana, Hollis Street Bio")


async def main(wait, gap):
    time.sleep(wait)
    biz = await get_business()
    route = json.loads(await agent.run_tool("van-2", "get_van_route", {"van_id": "van-2"}, biz))["stops"]
    print("move:", await agent.run_tool("van-2", "move_stop", {"van_id": "van-2", "stop_key": route[-1]["stop_key"], "new_position": len(route) - 2}, biz), flush=True)
    time.sleep(gap)
    r = c.post("/inbox", json={"text": HOLLIS, "source": "email", "sender": "Ana at Hollis Street Bio"}).json()
    d = c.post(f"/inbox/{r['key']}/read").json()
    q = c.post(f"/inbox/{r['key']}/send", json={"option_id": d["options"]["cards"][0]["option_id"]}).json()
    print("accept:", c.post(f"/quotes/{q['key']}/accept").json().get("booking", {}).get("toast"), flush=True)

asyncio.run(main(float(sys.argv[1]), float(sys.argv[2])))
