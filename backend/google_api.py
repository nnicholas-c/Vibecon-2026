"""Google sign-in (the team's own OAuth client), Gmail reading and sending, and the public /q quote links."""
import asyncio
import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from email.utils import parseaddr
from html import escape
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pymongo.errors import DuplicateKeyError

from core import BKEY, db
from email_send import send_managed

router = APIRouter(prefix="/api")
logger = logging.getLogger("drivepast.google")

GMAIL_READ = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_SEND = "https://www.googleapis.com/auth/gmail.send"
SHEETS = "https://www.googleapis.com/auth/spreadsheets.readonly"
SCOPES = ["openid", "email", "profile", GMAIL_READ, GMAIL_SEND, SHEETS]
SCOPE_NAMES = {GMAIL_READ: "Gmail reading", GMAIL_SEND: "Gmail sending", SHEETS: "Google Sheets"}
FAIL = "Google sign-in didn't finish. Nothing was connected."
EXPIRED = "Google connection expired. Sign in with Google again."
UNREACHABLE = "Couldn't check Gmail just now. Try again in a minute."
LIMITED = "30 emails read this hour. The rest wait for the next hour."
HOURLY = 30
INVALID = "This link isn't valid."
ANSWERED = "This quote was already answered."
FILLED = "That time just filled up. We'll email you a new one."
DECLINED = "No problem. Thanks for asking."
YES = {"yes", "yes please", "ok", "okay", "sounds good", "book it", "accept", "deal", "yep", "sure", "great", "perfect", "confirmed", "confirm"}
SENDER_NAME = "Bayline Courier"
DELIVERY_WORDS = re.compile(r"\b(pick ?ups?|deliver|drop|courier|runs?\b|stops?\b|route|ship|parcel|package|box(es)?\b|samples?\b|specimens?|documents?)", re.I)



def looks_like_request(subject, body, sender):
    """Cheap pre-check before the reader: delivery words and at least one place the keyword reader can find."""
    text = f"{subject} {body}"
    if not DELIVERY_WORDS.search(text):
        return False
    from ai.keyword import read_locations
    return bool(read_locations(text, sender or ""))


_check_lock = asyncio.Lock()
answer_lock = asyncio.Lock()


class GoogleError(Exception):
    def __init__(self, status, error=""):
        super().__init__(f"{status} {error}")
        self.status, self.error = status, error


class GoogleHttp:
    """The only code that talks to Google. Tests swap `G` for a fake."""
    # Public Google endpoint URLs (published in Google's OAuth/Gmail docs), not credentials.
    # The OAuth client id/secret are never in source; they come from env (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET).
    PUBLIC_OAUTH2_HOST = "https://oauth2.googleapis.com"
    AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN = f"{PUBLIC_OAUTH2_HOST}/token"
    USERINFO = "https://openidconnect.googleapis.com/v1/userinfo"
    REVOKE = f"{PUBLIC_OAUTH2_HOST}/revoke"
    GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me/"

    async def _call(self, method, url, **kw):
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.request(method, url, **kw)
        if r.status_code >= 400:
            try:
                err = r.json().get("error", "")
                err = err.get("status", "") if isinstance(err, dict) else err
            except ValueError:
                err = ""
            raise GoogleError(r.status_code, err)
        return r.json() if r.content else {}

    async def token(self, data):
        return await self._call("POST", self.TOKEN, data=data)

    async def userinfo(self, access):
        return await self._call("GET", self.USERINFO, headers={"Authorization": f"Bearer {access}"})

    async def revoke(self, token):
        return await self._call("POST", self.REVOKE, data={"token": token})

    async def gmail(self, method, path, access, **kw):
        return await self._call(method, self.GMAIL + path, headers={"Authorization": f"Bearer {access}"}, **kw)


G = GoogleHttp()


class Expired(Exception):
    pass


def configured():
    secret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    return bool(os.environ.get("GOOGLE_CLIENT_ID") and secret and secret != "placeholder")


async def app_secret():
    await db.app_secrets.update_one({"key": "links"}, {"$setOnInsert": {"key": "links", "value": secrets.token_hex(32)}}, upsert=True)
    return (await db.app_secrets.find_one({"key": "links"}))["value"]


async def sign(text):
    return hmac.new((await app_secret()).encode(), text.encode(), hashlib.sha256).hexdigest()[:32]


def served_base(request: Request):
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    host = host.split(",")[0].strip()
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme).split(",")[0].strip()
    if not host.startswith(("localhost", "127.0.0.1")):
        proto = "https"
    return f"{proto}://{host}"


def is_local(base):
    return base.split("://")[-1].startswith(("localhost", "127.0.0.1"))


_saved_base = {"value": None}


async def remember_base(request: Request):
    """Save the public address the app is served from (never localhost), so email links point at the live site."""
    base = served_base(request)
    if not is_local(base) and base != _saved_base["value"]:
        await db.app_secrets.update_one({"key": "public_base"}, {"$set": {"value": base}}, upsert=True)
        _saved_base["value"] = base


async def public_base():
    """The saved public address; PUBLIC_APP_URL is only a last resort before any public visit has been seen."""
    doc = await db.app_secrets.find_one({"key": "public_base"})
    if doc and doc.get("value") and not is_local(doc["value"]):
        return doc["value"]
    return (os.environ.get("PUBLIC_APP_URL") or "").rstrip("/")


async def get_conn():
    return await db.google_conn.find_one({"business_key": BKEY})


async def last_email():
    doc = await db.google_meta.find_one({"business_key": BKEY})
    return doc.get("last_email") if doc else None


def status_view(conn, last, note=None):
    out = {"configured": configured(), "connected": False, "email": None, "expired": False, "missing": [],
           "sheets_allowed": False, "last_email": last, "line": None, "last_check": None,
           "message": "Not connected" if configured() else "Google sign-in isn't set up yet."}
    if conn:
        scopes = set(conn.get("scopes") or [])
        out.update(connected=not conn.get("expired"), email=conn["email"], expired=bool(conn.get("expired")),
                   missing=[f"Not allowed: {SCOPE_NAMES[s]}" for s in (GMAIL_READ, GMAIL_SEND, SHEETS) if s not in scopes],
                   sheets_allowed=SHEETS in scopes, last_check=conn.get("last_check"),
                   line=f"Email a request to {conn['email']} and it gets priced." if GMAIL_READ in scopes else None,
                   message=EXPIRED if conn.get("expired") else f"Connected as {conn['email']}")
    return out


@router.get("/auth/google/start")
async def google_start(request: Request, origin: str = "settings"):
    back = "/settings" if origin == "settings" else "/signin"
    if not configured():
        return RedirectResponse(f"{back}?google=not_set", status_code=302)
    await remember_base(request)
    # REQ-1302: the login screen never swaps an existing inbox, so it only asks for who you are.
    session_only = origin != "settings" and bool(await db.google_conn.find_one({"business_key": BKEY}, {"_id": 1}))
    scopes = ["openid", "email", "profile"] if session_only else SCOPES
    nonce = secrets.token_urlsafe(16)
    redirect = served_base(request) + "/api/auth/google/callback"
    await db.oauth_states.insert_one({"nonce": nonce, "redirect_uri": redirect, "at": time.time(), "back": back, "session_only": session_only})
    state = f"{nonce}.{await sign(nonce)}"
    params = {"client_id": os.environ["GOOGLE_CLIENT_ID"], "redirect_uri": redirect, "response_type": "code",
              "scope": " ".join(scopes), "access_type": "offline", "prompt": "select_account" if session_only else "consent",
              "include_granted_scopes": "false", "state": state}
    return RedirectResponse(f"{GoogleHttp.AUTH}?{urlencode(params)}", status_code=302)


async def finish_callback(code, state, error):
    """Returns (profile or None, where to send the browser back)."""
    nonce, _, sig = (state or "").partition(".")
    st = await db.oauth_states.find_one_and_delete({"nonce": nonce}) if nonce else None
    back = (st or {}).get("back", "/settings")
    if error or not code or not st or not hmac.compare_digest(sig, await sign(nonce)) or time.time() - st["at"] > 600:
        return None, back
    try:
        tok = await G.token({"code": code, "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                             "redirect_uri": st["redirect_uri"], "grant_type": "authorization_code"})
        info = await G.userinfo(tok["access_token"])
    except Exception as e:  # noqa: BLE001
        logger.warning("Google token exchange failed: %s", type(e).__name__)
        return None, back
    now = time.time()
    if back == "/signin" and (st.get("session_only") or await db.google_conn.find_one({"business_key": BKEY}, {"_id": 1})):
        return info, back
    await db.google_conn.replace_one({"business_key": BKEY}, {
        "business_key": BKEY, "email": info.get("email"), "name": info.get("name"), "scopes": (tok.get("scope") or "").split(),
        "access_token": tok["access_token"], "refresh_token": tok.get("refresh_token"), "expires_at": now + tok.get("expires_in", 3600),
        "connected_at": datetime.now(timezone.utc).isoformat(), "connected_epoch": int(now), "expired": False}, upsert=True)
    await db.google_meta.update_one({"business_key": BKEY}, {"$set": {"last_email": info.get("email")}}, upsert=True)
    _poller["catchup"] = 0  # REQ-1422: the new inbox is read from its connect time; the old one's cursor went with replace_one
    return info, back


SESSION_COOKIE = "dp_session"
SESSION_DAYS = 30


def _sid_hash(sid):
    return hashlib.sha256(sid.encode()).hexdigest()


async def start_session(response, info):
    sid = secrets.token_urlsafe(32)
    await db.sessions.insert_one({"sid_hash": _sid_hash(sid), "email": info.get("email"), "name": info.get("name") or info.get("email"),
                                  "picture": info.get("picture"), "created_at": time.time(), "expires_at": time.time() + SESSION_DAYS * 86400})
    response.set_cookie(SESSION_COOKIE, f"{sid}.{await sign('session:' + sid)}", max_age=SESSION_DAYS * 86400, path="/",
                        secure=True, httponly=True, samesite="lax")


async def current_session(request: Request):
    raw = request.cookies.get(SESSION_COOKIE) or ""
    sid, _, sig = raw.partition(".")
    if not sid or not sig or not hmac.compare_digest(sig, await sign("session:" + sid)):
        return None
    s = await db.sessions.find_one({"sid_hash": _sid_hash(sid)}, {"_id": 0})
    return s if s and s["expires_at"] > time.time() else None


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    await remember_base(request)
    info, back = await finish_callback(code, state, error)
    if not info:
        return RedirectResponse(f"{back}?google=failed", status_code=302)
    resp = RedirectResponse("/dispatch" if back == "/signin" else "/settings?google=connected", status_code=302)
    await start_session(resp, info)
    return resp


@router.get("/auth/me")
async def auth_me(request: Request):
    s = await current_session(request)
    return {"signed_in": bool(s), "name": s and s["name"], "email": s and s["email"], "picture": s and s.get("picture"),
            "google_configured": configured()}


@router.post("/auth/logout")
async def auth_logout(request: Request):
    raw = request.cookies.get(SESSION_COOKIE) or ""
    if raw:
        await db.sessions.delete_many({"sid_hash": _sid_hash(raw.partition(".")[0])})
    resp = JSONResponse({"ok": True, "signed_in": False})
    resp.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    return resp


@router.post("/dev/test-session")
async def dev_test_session(request: Request):
    """Test-only: a signed-in browser session without Google. Off unless DEV_TEST_SESSION_ENABLED=true."""
    if os.environ.get("DEV_TEST_SESSION_ENABLED", "false").lower() != "true":
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    resp = JSONResponse({"ok": True})
    await start_session(resp, {"email": "tester@example.com", "name": "Test Owner", "picture": None})
    return resp


@router.get("/google/status")
async def google_status():
    return status_view(await get_conn(), await last_email())


@router.post("/google/disconnect")
async def google_disconnect():
    conn = await get_conn()
    if conn:
        try:
            await G.revoke(conn.get("refresh_token") or conn["access_token"])
        except Exception as e:  # noqa: BLE001
            logger.info("Google revoke didn't answer: %s", type(e).__name__)
        await db.google_conn.delete_many({"business_key": BKEY})
    return status_view(None, await last_email())


async def access_token(conn):
    if conn.get("expired"):
        raise Expired()
    if conn["expires_at"] - 60 > time.time():
        return conn["access_token"]
    try:
        tok = await G.token({"refresh_token": conn.get("refresh_token") or "", "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
                             "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""), "grant_type": "refresh_token"})
    except GoogleError as e:
        if e.status in (400, 401):
            await db.google_conn.update_one({"business_key": BKEY}, {"$set": {"expired": True}})
            raise Expired() from e
        raise
    await db.google_conn.update_one({"business_key": BKEY}, {"$set": {"access_token": tok["access_token"], "expires_at": time.time() + tok.get("expires_in", 3600)}})
    return tok["access_token"]


def _b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _walk(part):
    yield part
    for p in part.get("parts") or []:
        yield from _walk(p)


def parse_message(msg):
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    plain, html, files = "", "", []
    for p in _walk(msg.get("payload", {})):
        mime, body = p.get("mimeType", ""), p.get("body", {})
        if p.get("filename") and body.get("attachmentId"):
            if mime == "application/pdf" or mime.startswith("image/"):
                files.append({"name": p["filename"], "mime": mime, "attachment_id": body["attachmentId"]})
        elif mime == "text/plain" and body.get("data") and not plain:
            plain = _b64d(body["data"]).decode("utf-8", "replace")
        elif mime == "text/html" and body.get("data") and not html:
            html = _b64d(body["data"]).decode("utf-8", "replace")
    text = plain or re.sub(r"<[^>]+>", " ", html)
    name, addr = parseaddr(headers.get("from", ""))
    return {"id": msg["id"], "thread_id": msg.get("threadId"), "subject": headers.get("subject", "(no subject)"),
            "from_name": name or addr, "from_email": addr.lower(), "rfc_id": headers.get("message-id"),
            "references": headers.get("references", ""), "text": re.sub(r"\n{3,}", "\n\n", text).strip(), "files": files}


def reply_only(text):
    """The customer's own words, without the quoted thread below."""
    cut = re.split(r"\n\s*On .{0,200}wrote:|\n\s*>|\n-{2,}\s*Original Message", text, maxsplit=1)[0]
    return cut.strip()


async def read_attachments(m, token):
    from storage import put_object
    texts, image, stored = [], None, []
    for f in m["files"][:3]:
        data = _b64d((await G.gmail("GET", f"messages/{m['id']}/attachments/{f['attachment_id']}", token)).get("data", ""))
        ext = "pdf" if f["mime"] == "application/pdf" else f["mime"].split("/")[-1].replace("jpeg", "jpg")
        try:
            meta = await put_object(f"gmail/{m['id']}-{len(stored)}.{ext}", data, f["mime"])
            stored.append({"name": f["name"], "path": meta.get("path"), "content_type": f["mime"], "size": len(data)})
        except Exception as e:  # noqa: BLE001
            logger.warning("Attachment storage failed: %s", type(e).__name__)
        if ext == "pdf":
            try:
                import io

                from pypdf import PdfReader
                texts.append("\n".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(data)).pages[:5]))
            except Exception:  # noqa: BLE001
                pass
        elif image is None:
            image = base64.b64encode(data).decode()
    return "\n\n".join(t for t in texts if t.strip()), image, stored


async def thread_quote(thread_id):
    req = await db.requests.find_one({"business_key": BKEY, "gmail.thread_id": thread_id}, sort=[("number", -1)])
    if not req:
        return None, None
    q = await db.quotes.find_one({"business_key": BKEY, "request_key": req["key"], "status": "sent"}, {"_id": 0}, sort=[("created_at", -1)])
    return req, q


async def handle_message(m, token):
    from inbox_api import new_request, read_bg
    from phones_api import accept_quote
    if await db.requests.find_one({"business_key": BKEY, "source_key": m["id"]}, {"_id": 1}):
        return "skipped"
    req, q = await thread_quote(m["thread_id"]) if m["thread_id"] else (None, None)
    if req:
        words = reply_only(m["text"])
        if q and re.sub(r"[^a-z ]", "", words.lower().splitlines()[0] if words else "").strip() in YES:
            async with answer_lock:
                fresh = await db.quotes.find_one({"business_key": BKEY, "key": q["key"]}, {"_id": 0})
                if fresh["status"] == "sent":
                    await accept_quote(fresh)
            return "accepted"
        raw = f"{req.get('raw_text', '')}\n\nCustomer reply: {words}".strip()
        await db.requests.update_one({"_id": req["_id"]}, {"$set": {"raw_text": raw}})
        await read_bg(await db.requests.find_one({"_id": req["_id"]}))
        return "reread"
    extra, image, stored = await read_attachments(m, token) if m["files"] else ("", None, [])
    body = "\n\n".join(t for t in (m["text"], extra) if t)
    if not image and not looks_like_request(m["subject"], body, m.get("from_name")):
        return "skipped"  # REQ-1424/1425: not a pickup or delivery request, so no Inbox entry and never a reply
    text = f"Subject: {m['subject']}\n\n{body}".strip()
    r = await new_request("gmail", text, m["from_name"], m["from_email"], stored[0] if stored else None)
    try:
        await db.requests.update_one({"_id": r["_id"]}, {"$set": {"source_key": m["id"], "gmail": {
            "message_id": m["id"], "thread_id": m["thread_id"], "rfc_id": m["rfc_id"], "references": m["references"],
            "subject": m["subject"], "from_email": m["from_email"], "attachments": stored, "internal_ms": m.get("internal_ms"),
            "demo": bool(m.get("demo"))}}})
    except DuplicateKeyError:
        await db.requests.delete_one({"_id": r["_id"]})
        return "skipped"
    await read_bg(await db.requests.find_one({"_id": r["_id"]}), image)
    return "created"


async def check_inbox():
    conn = await get_conn()
    if not conn:
        return {"ok": False, "connected": False, "message": "Not connected"}
    try:
        token = await access_token(conn)
    except Expired:
        return {"ok": False, "expired": True, "message": EXPIRED}
    except Exception:  # noqa: BLE001
        return {"ok": False, "message": UNREACHABLE}
    try:
        listing = await G.gmail("GET", "messages", token, params={"q": "newer_than:1d", "maxResults": 100})
    except Exception:  # noqa: BLE001
        return {"ok": False, "message": UNREACHABLE}
    return await ingest_ids(conn, token, [x["id"] for x in listing.get("messages", [])][::-1])


async def ingest_ids(conn, token, ids):
    """Handle new Gmail message ids, oldest first. gmail_seen/gmail_sent dedupe; reads run in their own tasks."""
    await db.gmail_seen.create_index([("business_key", 1), ("message_id", 1)], unique=True)
    used = await db.gmail_seen.count_documents({"business_key": BKEY, "counted": True, "at": {"$gte": time.time() - 3600}})
    counts = {"created": 0, "skipped": 0, "accepted": 0, "reread": 0, "waiting": 0}
    for mid in ids:
        if await db.gmail_seen.find_one({"business_key": BKEY, "message_id": mid}) or await db.gmail_sent.find_one({"business_key": BKEY, "message_id": mid}):
            continue
        if used >= HOURLY:
            counts["waiting"] += 1
            continue
        try:
            raw = await G.gmail("GET", f"messages/{mid}", token, params={"format": "full"})
            m = parse_message(raw)
            m["internal_ms"] = int(raw.get("internalDate") or 0) or None
        except Exception:  # noqa: BLE001
            return {"ok": False, "message": UNREACHABLE, **counts}
        old = int(raw.get("internalDate") or 0) / 1000 < conn.get("connected_epoch", 0)
        try:
            await db.gmail_seen.insert_one({"business_key": BKEY, "message_id": mid, "counted": not old, "at": time.time()})
        except DuplicateKeyError:
            continue
        if old:
            continue
        used += 1
        counts[await handle_message(m, token)] += 1
    notes = []
    if counts["skipped"]:
        notes.append(f"{counts['skipped']} emails skipped (not a delivery request)")
    if counts["waiting"]:
        notes.append(LIMITED)
    summary = {"at": datetime.now(timezone.utc).isoformat(), "notes": notes, **counts}
    await db.google_conn.update_one({"business_key": BKEY}, {"$set": {"last_check": summary}})
    return {"ok": True, **summary}


@router.post("/gmail/check")
async def gmail_check(request: Request):
    await remember_base(request)
    async with _check_lock:
        return await check_inbox()


POLL_SECONDS = 10
LEASE_KEY = "gmail_poller"
_poller = {"task": None, "owner": uuid.uuid4().hex}


async def take_lease(key=LEASE_KEY):
    """One poller across reloads and workers: a 30 s lease in Mongo, renewed each loop by its owner."""
    now, owner = time.time(), _poller["owner"]
    try:
        doc = await db.locks.find_one_and_update({"key": key, "$or": [{"owner": owner}, {"until": {"$lt": now}}]},
                                                 {"$set": {"owner": owner, "until": now + 30}}, upsert=True, return_document=True)
    except DuplicateKeyError:
        return False
    return bool(doc) and doc.get("owner") == owner


CATCHUP_SECONDS = 60


async def history_ids(token, start):
    """New INBOX message ids since `start` from users.history.list, plus the new cursor. None if `start` is too old."""
    ids, page, latest = [], None, start
    while True:
        params = {"startHistoryId": start, "historyTypes": "messageAdded", "labelId": "INBOX", "maxResults": 500}
        if page:
            params["pageToken"] = page
        try:
            res = await G.gmail("GET", "history", token, params=params)
        except GoogleError as exc:
            if exc.status == 404:
                return None, None
            raise
        for h in res.get("history", []):
            ids += [x["message"]["id"] for x in h.get("messagesAdded", []) if x["message"]["id"] not in ids]
        latest = str(res.get("historyId") or latest)
        page = res.get("nextPageToken")
        if not page:
            return ids, latest


async def poll_once():
    """History list is the instant new-mail signal; messages.list q=newer_than:1d is a 60 s catch-up (and the fallback on 404)."""
    conn = await get_conn()
    if not conn or conn.get("expired"):
        return None
    try:
        token = await access_token(conn)
        start = conn.get("last_history_id")
        ids, latest = await history_ids(token, start) if start else (None, None)
    except Exception:  # noqa: BLE001
        return None
    due = ids is None or time.time() - _poller.get("catchup", 0) >= CATCHUP_SECONDS
    if due:
        try:
            latest = latest or str((await G.gmail("GET", "profile", token)).get("historyId") or "")
        except Exception:  # noqa: BLE001
            return None
    async with _check_lock:
        res = await ingest_ids(conn, token, ids) if ids else {"ok": True}
        if due and res.get("ok"):
            _poller["catchup"] = time.time()
            res = await check_inbox()
    if latest and res.get("ok") and not res.get("waiting"):
        await db.google_conn.update_one({"business_key": BKEY}, {"$set": {"last_history_id": latest}})
    return res


async def gmail_poller():
    await db.locks.create_index("key", unique=True)
    await db.requests.create_index("source_key", unique=True, partialFilterExpression={"source_key": {"$type": "string"}})
    while True:
        try:
            if await take_lease():
                await poll_once()
        except Exception:  # noqa: BLE001
            logger.exception("Gmail poll failed")
        await asyncio.sleep(POLL_SECONDS)


async def stop_gmail_poller():
    """Free the leases on shutdown so a reloaded worker polls at once instead of waiting them out."""
    for t in (_poller["task"], _poller.get("sheets")):
        if t:
            t.cancel()
    await db.locks.delete_many({"key": {"$in": [LEASE_KEY, SHEETS_LEASE]}, "owner": _poller["owner"]})


SHEETS_LEASE = "sheet_sync"
SHEETS_SECONDS = 30


async def sheet_poller():
    """Sync connected Google Sheets every 30 s (replaces the browser's POST /api/import/sync-all)."""
    from import_api import sync_all
    while True:
        try:
            conn = await get_conn()
            if conn and not conn.get("expired") and await take_lease(SHEETS_LEASE):
                await sync_all()
        except Exception:  # noqa: BLE001
            logger.exception("Sheet sync failed")
        await asyncio.sleep(SHEETS_SECONDS)


def start_gmail_poller():
    if _poller["task"] is None or _poller["task"].done():
        _poller["task"] = asyncio.create_task(gmail_poller())
    if _poller.get("sheets") is None or _poller["sheets"].done():
        _poller["sheets"] = asyncio.create_task(sheet_poller())


async def blocked_address(addr):
    addr = (addr or "").strip().lower()
    if not addr:
        return True
    for coll in ("prospects", "directory"):
        if await db[coll].find_one({"business_key": BKEY, "$or": [{"email": addr}, {"contact_email": addr}, {"contact": addr}]}):
            return True
    return False


def quote_html(q, accept_url, decline_url, per):
    btn = "display:inline-block;padding:12px 22px;border-radius:999px;font-weight:700;text-decoration:none;margin-right:8px"
    return (f'<table role="presentation" width="100%"><tr><td style="padding:24px;font-family:Arial,sans-serif;color:#111">'
            f'<p style="font-size:18px;margin:0 0 8px"><strong>{escape(q["price_text"])} {escape(per)}</strong>, pickup about {escape(q["pickup_label"])}.</p>'
            f'<p style="margin:0 0 18px">{escape(q["customer_line"])}</p>'
            f'<p><a href="{accept_url}" style="{btn};background:#141414;color:#F4F2EC;border:1px solid #141414">Accept</a>'
            f'<a href="{decline_url}" style="{btn};background:#F4F2EC;color:#141414;border:1px solid #141414">Decline</a></p>'
            f'<p style="font-size:12px;color:#777">Sent by Bayline Courier through Drivepast. We never ask for passwords or card details by email.</p>'
            f'</td></tr></table>')


async def send_in_thread(req, html, text):
    """Reply in the customer's Gmail thread; fall back to Emergent's managed email. Returns 'gmail', 'managed' or 'managed_fallback'."""
    g = req["gmail"]
    to = g["from_email"]
    if await blocked_address(to):
        raise PermissionError("That address belongs to a prospect or directory business, so Drivepast won't email it.")
    subject = g["subject"] if g["subject"].lower().startswith("re:") else f"Re: {g['subject']}"
    conn = await get_conn()
    if conn and not conn.get("expired") and GMAIL_SEND in (conn.get("scopes") or []):
        try:
            token = await access_token(conn)
            msg = EmailMessage()
            msg["From"] = formataddr((SENDER_NAME, conn["email"]))
            msg["To"], msg["Subject"] = to, subject
            if g.get("rfc_id"):
                msg["In-Reply-To"] = g["rfc_id"]
                msg["References"] = f"{g.get('references') or ''} {g['rfc_id']}".strip()
            msg.set_content(text)
            msg.add_alternative(html, subtype="html")
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            sent = await G.gmail("POST", "messages/send", token, json={"raw": raw, "threadId": g["thread_id"]})
            await db.gmail_sent.insert_one({"business_key": BKEY, "message_id": sent.get("id"), "thread_id": g["thread_id"], "at": time.time()})
            return "gmail"
        except Exception as e:  # noqa: BLE001
            logger.warning("Gmail send failed, using managed email: %s", type(e).__name__)
            via = "managed_fallback"
    else:
        via = "managed"
    await send_managed(to=to, subject=subject, html=html, reply_to=await last_email())
    return via


VIA_NOTE = {"gmail": "Sent from your Gmail in the same thread.", "managed": "Sent by Drivepast email.",
            "managed_fallback": "Sent by Drivepast email (Gmail didn't answer)."}


async def email_quote(req, q, per):
    base = await public_base()
    token = f"{q['key']}.{await sign(q['key'])}"
    html = quote_html(q, f"{base}/q/{token}?a=accept", f"{base}/q/{token}?a=decline", per)
    text = f"{q['price_text']} {per}, pickup about {q['pickup_label']}. {q['customer_line']}\nAccept: {base}/q/{token}?a=accept\nDecline: {base}/q/{token}?a=decline"
    via = await send_in_thread(req, html, text)
    await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"via": via, "email_note": VIA_NOTE[via]}})
    return via


async def email_cancelled(req):
    html = ('<table role="presentation" width="100%"><tr><td style="padding:24px;font-family:Arial,sans-serif;color:#111">'
            '<p>Change cancelled.</p><p style="font-size:12px;color:#777">Sent by Bayline Courier through Drivepast.</p></td></tr></table>')
    try:
        await send_in_thread(req, html, "Change cancelled.")
    except Exception as e:  # noqa: BLE001
        logger.warning("Couldn't email the cancellation: %s", type(e).__name__)


async def quote_from_token(token):
    key, _, sig = (token or "").partition(".")
    if not key or not sig or not hmac.compare_digest(sig, await sign(key)):
        return None
    return await db.quotes.find_one({"business_key": BKEY, "key": key}, {"_id": 0})


@router.get("/q/{token}")
async def public_quote(token: str):
    q = await quote_from_token(token)
    if not q:
        return JSONResponse(status_code=404, content={"valid": False, "message": INVALID})
    req = await db.requests.find_one({"business_key": BKEY, "key": q["request_key"]}, {"_id": 0, "job": 1})
    per = "for the run" if ((req or {}).get("job") or {}).get("frequency", {}).get("type") == "one_off" else "a visit"
    return {"valid": True, "open": q["status"] == "sent", "status": q["status"], "price_text": q.get("price_text"), "per": per,
            "pickup_label": q["pickup_label"], "customer_line": q["customer_line"], "unit_name": q["unit_name"],
            "message": None if q["status"] == "sent" else ANSWERED}


@router.post("/q/{token}/{action}")
async def public_answer(token: str, action: str):
    from phones_api import accept_quote, decline_quote
    if action not in ("accept", "decline"):
        return JSONResponse(status_code=404, content={"ok": False, "message": INVALID})
    async with answer_lock:
        q = await quote_from_token(token)
        if not q:
            return JSONResponse(status_code=404, content={"ok": False, "message": INVALID})
        if q["status"] != "sent":
            return {"ok": False, "answered": True, "message": ANSWERED}
        if action == "decline":
            await decline_quote(q)
            return {"ok": True, "status": "declined", "message": DECLINED}
        res = await accept_quote(q)
        if isinstance(res, JSONResponse):
            return {"ok": False, "status": "stale", "message": FILLED}
        return {"ok": True, "status": "accepted", "message": f"You're booked. {q['unit_name']} will be there around {q['pickup_label']}."}
