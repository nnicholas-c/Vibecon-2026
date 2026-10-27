def test_openapi_200(c):
    r = c.get("/openapi.json")
    assert r.status_code == 200 and "paths" in r.json()


def test_optimize_preview_van2(c):
    r = c.post("/units/van-2/optimize/preview", json={})
    assert r.status_code == 200, r.text[:300]


def test_seed_spare_minutes(c):
    assert c.get("/units/van-1").json()["unit"]["spare_minutes"] == 43
    u2 = c.get("/units/van-2").json()["unit"]
    assert u2["spare_minutes"] == 48 and u2["stops_count"] == 20
