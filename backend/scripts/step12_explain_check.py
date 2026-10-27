"""Step 12: explain_stop by exact key, misspelled name, street, and no match (returns stop names)."""
import asyncio
import sys

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")
import agent  # noqa: E402
from core import get_business  # noqa: E402
from routes_api import today_nodes  # noqa: E402


async def main():
    biz = await get_business()
    u = await agent._unit("van-2")
    nodes = await today_nodes(u, biz.demo_date)
    name = nodes[3]["customer_name"]
    typo = name[:2] + name[3:]
    for q in (nodes[3]["key"], name.upper(), typo, "Hollis", "zzzz qqqq xxxx"):
        r = await agent.t_explain_stop(biz, "van-2", q)
        print(repr(q), "->", {k: r.get(k) for k in ("name", "position", "arrival", "window", "added_minutes", "added_miles", "booked_today", "status")}
              if r.get("matched") is not False else f"no match, {len(r['stop_names'])} names e.g. {r['stop_names'][:3]}")

asyncio.run(main())
