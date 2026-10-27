from _s11 import run_and_book
def test_agent(c):
    run_and_book(c)
    r = c.post("/agents/van-2/messages", json={"text":"Why did the new stop go there?"}, timeout=120)
    assert r.status_code == 200, r.text[:300]
    t = r.text
    assert "couldn't reach the model" not in t and "Daily model limit" not in t, t[:500]
    assert "min" in t, t[:800]
    print(t[:1500])
