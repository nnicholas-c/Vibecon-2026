import time, uuid
from _s11 import run_and_book
def test_clay(c):
    run_and_book(c)
    r = c.post("/inbox", json={"text":"pickup 2 boxes at 1300 Clay St Oakland, deliver to 1261 Fallon St by 3pm today"})
    assert r.status_code in (200,201), r.text[:300]
    print(r.text[:400])
    toast=None
    for _ in range(30):
        lb = c.get("/live").json().get("last_booking") or {}
        if lb.get("unit_key")=="van-3": toast=lb["toast"]; break
        time.sleep(1)
    assert toast, c.get("/live").json().get("last_booking",{}).get("toast")
    print(toast)
    assert toast.startswith("Booked Clay St") and "@" not in toast
