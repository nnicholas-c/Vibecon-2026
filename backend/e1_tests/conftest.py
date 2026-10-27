import httpx, pytest
BASE = "http://localhost:8001/api"
@pytest.fixture(scope="session")
def c():
    with httpx.Client(base_url=BASE, timeout=60) as cl:
        yield cl
