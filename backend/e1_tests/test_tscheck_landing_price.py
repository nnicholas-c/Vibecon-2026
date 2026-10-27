def test_landing_price(c):
    r = c.get("/landing/price"); assert r.status_code == 200
    d = r.json()
    assert (d["time_cost"], d["mile_cost"], d["cost_with_markup"], d["offer"], d["usual"]) == (1.28, 0.46, 3.48, 11.0, 14.0), d
