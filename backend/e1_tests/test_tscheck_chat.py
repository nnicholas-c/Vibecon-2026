import uuid
def test_echo(c):
    msg = f"tscheck-chat-{uuid.uuid4().hex[:6]}"
    r = c.post("/agents/van-2/messages", json={"text": msg}); assert r.status_code in (200, 201), r.text
    th = c.get("/agents/van-2/thread").json()["turns"]
    assert any(msg in str(t) and "Echo from Van 2: " + msg in str(t) for t in th) or any(f"Echo from Van 2: {msg}" in str(t) for t in th)
    assert msg not in str(c.get("/agents/van-3/thread").json())
    assert c.post("/agents/van-2/messages", json={"text": "   "}).status_code in (400, 422)
