from _s11 import run_and_book
def test_scripted_books(c):
    key,row = run_and_book(c)
    assert row["status"] == "booked", row
    live = c.get("/live").json()["last_booking"]
    assert live["toast"] == "Booked Ana, Hollis Street Bio, $35 instead of $55, Van 2 already passes 0.1 mi away."
    assert live["ruler"] == {"price":35.0,"usual":55.0}
    ev = c.get("/events").json()["events"]
    assert any(e["text"] == live["toast"] for e in ev)
    u = {x["key"]:x["stops_count"] for x in c.get("/fleet").json()["units"]}
    assert u == {"van-1":20,"van-2":22,"van-3":20}, u
