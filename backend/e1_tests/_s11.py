import time
def run_and_book(c):
    assert c.post("/demo/run").status_code == 200
    time.sleep(6)
    r = c.post("/demo/scripted-email"); assert r.status_code == 200
    key = r.json()["request_key"]
    row = None
    for _ in range(15):
        reqs = c.get("/inbox").json()["requests"]
        row = next(x for x in reqs if x["key"] == key)
        if row["status"] == "booked": break
        time.sleep(1)
    return key, row
