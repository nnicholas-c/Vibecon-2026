"""Step 20: start-URL scopes for both cases and a simulated origin=signin callback with an existing google_conn."""
import asyncio
import sys
import time
from urllib.parse import parse_qs, urlparse

import requests

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")
import google_api  # noqa: E402
from core import BKEY, db  # noqa: E402

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"


def scopes(origin):
    r = requests.get(f"{API}/auth/google/start", params={"origin": origin}, allow_redirects=False)
    loc = r.headers.get("location", "")
    q = parse_qs(urlparse(loc).query)
    return r.status_code, q.get("scope", [loc])[0], q.get("prompt", [""])[0]


async def main():
    saved = await db.google_conn.find_one({"business_key": BKEY})
    try:
        await db.google_conn.delete_many({"business_key": BKEY})
        print("no conn,   signin  :", scopes("signin"))
        await db.google_conn.insert_one({"business_key": BKEY, "email": "emergentcouriers413@gmail.com", "scopes": google_api.SCOPES,
                                         "access_token": "keep-me", "refresh_token": "keep-refresh"})
        print("with conn, signin  :", scopes("signin"))
        print("with conn, settings:", scopes("settings"))

        async def token(_):
            return {"access_token": "personal", "scope": "openid email profile", "expires_in": 3600}

        async def userinfo(_):
            return {"email": "someone.personal@gmail.com", "name": "Someone"}
        google_api.G.token, google_api.G.userinfo = token, userinfo
        for session_only in (True, False):
            nonce = f"test-{session_only}"
            await db.oauth_states.insert_one({"nonce": nonce, "redirect_uri": "x", "at": time.time(), "back": "/signin", "session_only": session_only})
            info, back = await google_api.finish_callback("code", f"{nonce}.{await google_api.sign(nonce)}", None)
            c = await db.google_conn.find_one({"business_key": BKEY})
            print(f"signin callback (session_only={session_only}) ->", info and info["email"], back, "| google_conn:", c["email"], c["access_token"], c["refresh_token"])
        info, back = await google_api.finish_callback("code", "bad.sig", None)
        c = await db.google_conn.find_one({"business_key": BKEY})
        print("failed callback ->", info, back, "| google_conn:", c["email"], c["access_token"])
    finally:
        await db.google_conn.delete_many({"business_key": BKEY})
        if saved:
            await db.google_conn.insert_one(saved)
        print("restored original conn:", bool(saved))

asyncio.run(main())
