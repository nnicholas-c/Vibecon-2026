"""Step 8 CHECK: accept a request, then GET /api/units/van-3: no optimize field, spare == shift - driving - service, max arrival gap."""
import os

import httpx

c = httpx.Client(base_url=os.environ.get("API", "http://localhost:8001/api"), timeout=120)
c.post("/demo/reset")
since = c.get("/events").json()["now"]
d = c.post("/inbox/req-02/read").json()
opt = d["options"]["cards"][0]
print("accepting req-02:", opt.get("title"), opt["unit_name"], opt["price"], "pickup", opt["pickup_label"])
acc = c.post("/engine/accept", json={"option_id": opt["option_id"]}).json()
print("accept:", acc.get("message"), "| auto reorder:", (acc.get("optimized") or {}).get("text"))
u = c.get("/units/van-3").json()
flat = str(u).lower()
p, unit = u["plan"], u["unit"]
arr = [r["arrival"] for r in u["timeline"]]
gap = max(b - a for a, b in zip(arr, arr[1:]))
drive, svc = u["plan"].get("driving_minutes"), u["plan"].get("service_minutes")
print("1) optimize field present:", "optimize" in flat)
print(f"2) spare {p['spare_minutes']} vs shift {unit['shift_minutes']} - driving {drive} - service {svc} = {unit['shift_minutes'] - drive - svc:.2f}")
print(f"3) max gap between consecutive arrivals: {gap:.1f} min")
print("events since accept:", c.get("/events", params={"since": since}).json()["events"])
