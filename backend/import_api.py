"""Spreadsheet import: Google Sheet (via Google sign-in) or CSV upload (Emergent Object Storage) -> Inbox requests."""
import asyncio
import csv
import hashlib
import io
import json
import logging
import re
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from core import BKEY, db
from phones_api import fail

router = APIRouter(prefix="/api")
logger = logging.getLogger("drivepast.import")
READ_FAIL = "We couldn't read that sheet. Check the link or the file."
FIELDS = [("customer", "Customer"), ("contact", "Email or phone"), ("pickup", "Pickup address"), ("dropoff", "Drop-off address"),
          ("when", "Date or days"), ("pickup_time", "Pickup time"), ("deadline", "Deliver by"), ("notes", "Notes")]
KEYWORDS = {
    "customer": ["customer", "company", "client", "business", "name", "sender"],
    "contact": ["email", "phone", "contact", "mobile"],
    "pickup": ["pickup address", "pick up address", "pickup", "pick up", "from", "origin", "collect"],
    "dropoff": ["drop off", "dropoff", "drop-off", "deliver to", "destination", "delivery address", "to"],
    "when": ["date", "day", "days", "frequency", "schedule", "when", "recurring"],
    "pickup_time": ["pickup time", "pick up time", "ready time", "time", "ready"],
    "deadline": ["deliver by", "deadline", "due", "by"],
    "notes": ["notes", "note", "comments", "comment", "details", "items", "boxes", "instructions"],
}
sem = asyncio.Semaphore(3)


class ReadFail(Exception):
    pass


def norm(h):
    return re.sub(r"[^a-z0-9]+", " ", (h or "").lower()).strip()


def keyword_match(headers):
    scored = []
    for hi, h in enumerate(headers):
        n = f" {norm(h)} "
        for f, kws in KEYWORDS.items():
            best = max((len(k) for k in kws if f" {norm(k)} " in n), default=0)
            if best:
                scored.append((best, hi, f))
    out, used = {}, set()
    for _, hi, f in sorted(scored, key=lambda x: -x[0]):
        if f not in out and hi not in used:
            out[f] = headers[hi]
            used.add(hi)
    return out


async def ai_match(headers, rows):
    from ai.ladder import call_backup, parse_json
    system = ("Match spreadsheet columns to courier request fields. Reply with JSON only: an object whose keys are field ids "
              f"from {json.dumps([f for f, _ in FIELDS])} and whose values are exact column headers from the sheet, or null.")
    text = json.dumps({"fields": dict(FIELDS), "headers": headers, "sample_rows": rows[:3]})
    got = parse_json(await asyncio.wait_for(call_backup(system, text), 25))
    return {f: got[f] for f, _ in FIELDS if got.get(f) in headers}


def to_rows(values):
    values = [[(c or "").strip() for c in r] for r in values if any((c or "").strip() for c in r)]
    if len(values) < 1:
        raise ReadFail()
    headers = [h or f"Column {i + 1}" for i, h in enumerate(values[0])]
    return headers, [{h: (r[i] if i < len(r) else "") for i, h in enumerate(headers)} for r in values[1:]]


def sheet_id(url):
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url or "") or re.fullmatch(r"\s*([a-zA-Z0-9_-]{25,})\s*", url or "")
    if not m:
        raise ReadFail()
    return m.group(1)


async def fetch_sheet(sid):
    from google_api import Expired, access_token, get_conn
    conn = await get_conn()
    if not conn:
        raise ReadFail()
    try:
        token = await access_token(conn)
    except Expired as e:
        raise ReadFail() from e
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/A1:Z1000", headers={"Authorization": f"Bearer {token}"})
        meta = await c.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}?fields=properties.title", headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        logger.info("Sheet read failed %s: %s", r.status_code, r.text[:200])
        raise ReadFail()
    title = meta.json().get("properties", {}).get("title") if meta.status_code == 200 else None
    return to_rows(r.json().get("values") or []), title or "Google Sheet"


async def fetch_csv(path):
    from storage import get_object
    data, _ = await get_object(path)
    return parse_csv(data)


def parse_csv(data):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    return to_rows(list(csv.reader(io.StringIO(text))))


async def load_rows(src):
    if src["kind"] == "sheet":
        (headers, rows), _ = await fetch_sheet(src["sheet_id"])
    else:
        headers, rows = await fetch_csv(src["storage_path"])
    return headers, rows


def row_hash(row):
    return hashlib.sha1("|".join(f"{k}={v}" for k, v in sorted(row.items())).encode()).hexdigest()


def row_text(row, m):
    g = lambda f: (row.get(m.get(f) or "") or "").strip()  # noqa: E731
    parts = []
    if g("pickup"):
        parts.append(f"Pickup at {g('pickup')}" + (f" {g('when')}" if g("when") else "") + (f" at {g('pickup_time')}" if g("pickup_time") else "") + ".")
    if g("dropoff"):
        parts.append(f"Deliver to {g('dropoff')}" + (f" by {g('deadline')}" if g("deadline") else "") + ".")
    if g("notes"):
        parts.append(g("notes"))
    if g("customer"):
        parts.append(f"Thanks, {g('customer')}")
    return " ".join(parts)


def view(src, headers=None, rows=None):
    out = {k: src.get(k) for k in ("key", "kind", "name", "mapping", "mapped_by", "connected", "last_sync", "last_line")}
    out["imported_count"] = len(src.get("imported") or [])
    if headers is not None:
        out.update(headers=headers, sample=rows[:3], row_count=len(rows))
    out["fields"] = [{"id": f, "label": label} for f, label in FIELDS]
    return out


async def start_source(kind, name, extra, headers, rows):
    try:
        mapping, by = await ai_match(headers, rows), "ai"
        if not mapping:
            raise ValueError("empty match")
    except Exception as exc:  # noqa: BLE001
        logger.info("AI column match failed, using keywords: %s", exc)
        mapping, by = keyword_match(headers), "keywords"
    src = {"business_key": BKEY, "key": f"imp-{uuid.uuid4().hex[:8]}", "kind": kind, "name": name, **extra, "headers": headers,
           "mapping": mapping, "mapped_by": by, "connected": False, "imported": [], "created_at": datetime.now(timezone.utc).isoformat()}
    await db.import_sources.insert_one(dict(src))
    return view(src, headers, rows)


async def read_bg(keys):
    from inbox_api import read_one

    async def one(k):
        async with sem:
            try:
                await read_one(await db.requests.find_one({"business_key": BKEY, "key": k}))
            except Exception:  # noqa: BLE001
                logger.exception("Reading imported %s failed", k)
    await asyncio.gather(*(one(k) for k in keys))


async def sync(src):
    from inbox_api import new_request
    headers, rows = await load_rows(src)
    seen, m = set(src.get("imported") or []), src["mapping"] or {}
    new_keys, skipped, added = [], 0, []
    for row in rows:
        h = row_hash(row)
        if h in seen:
            skipped += 1
            continue
        text = row_text(row, m)
        seen.add(h)
        added.append(h)
        if not text:
            continue
        customer = (row.get(m.get("customer") or "") or "").strip() or f"{src['name']} row"
        r = await new_request(src["kind"], text, customer, (row.get(m.get("contact") or "") or "").strip() or None)
        new_keys.append(r["key"])
    line = f"Imported {len(new_keys)} new, skipped {skipped} already imported"
    await db.import_sources.update_one({"key": src["key"]}, {"$push": {"imported": {"$each": added}},
                                                            "$set": {"last_sync": datetime.now(timezone.utc).isoformat(), "last_line": line}})
    if new_keys:
        asyncio.create_task(read_bg(new_keys))
    return {"ok": True, "imported": len(new_keys), "skipped": skipped, "line": line, "request_keys": new_keys}


class SheetIn(BaseModel):
    url: str


class ConfirmIn(BaseModel):
    mapping: dict


@router.get("/import/sources")
async def sources():
    from google_api import get_conn
    conn = await get_conn()
    sheets = await db.import_sources.count_documents({"business_key": BKEY, "connected": True, "kind": "sheet"})
    run = await db.import_runs.find_one({"business_key": BKEY}, {"_id": 0, "business_key": 0}) if sheets else None
    return {"sources": [view(s) async for s in db.import_sources.find({"business_key": BKEY, "connected": True}).sort("created_at", -1)],
            "google": bool(conn and not conn.get("expired")), "fields": [{"id": f, "label": label} for f, label in FIELDS],
            "sheet_connected": bool(sheets), "last_auto_sync": run}


@router.post("/import/sheet")
async def import_sheet(body: SheetIn):
    try:
        sid = sheet_id(body.url)
        (headers, rows), title = await fetch_sheet(sid)
    except (ReadFail, httpx.HTTPError):
        return fail(422, READ_FAIL)
    return await start_source("sheet", title, {"sheet_id": sid}, headers, rows)


@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...)):
    from storage import put_object
    data = await file.read()
    if not data or len(data) > 2_000_000:
        return fail(422, READ_FAIL)
    try:
        headers, rows = parse_csv(data)
    except (ReadFail, csv.Error):
        return fail(422, READ_FAIL)
    try:
        res = await put_object(f"imports/{BKEY}/{uuid.uuid4()}.csv", data, "text/csv")
    except Exception:  # noqa: BLE001
        logger.exception("CSV upload to storage failed")
        return fail(502, "We couldn't store that file. Try again.")
    return await start_source("csv", file.filename or "CSV file", {"storage_path": res["path"], "size": res.get("size")}, headers, rows)


async def get_src(key):
    return await db.import_sources.find_one({"business_key": BKEY, "key": key})


@router.post("/import/{key}/confirm")
async def confirm(key: str, body: ConfirmIn):
    src = await get_src(key)
    if not src:
        return fail(404, "That import is gone. Load the sheet again.")
    mapping = {f: h for f, h in body.mapping.items() if f in dict(FIELDS) and h in src["headers"]}
    if not mapping.get("pickup"):
        return fail(422, "Pick the column that holds the pickup address.")
    await db.import_sources.update_one({"_id": src["_id"]}, {"$set": {"mapping": mapping, "connected": True}})
    try:
        return await sync({**src, "mapping": mapping})
    except (ReadFail, httpx.HTTPError):
        return fail(422, READ_FAIL)


@router.post("/import/{key}/sync")
async def sync_one(key: str):
    src = await get_src(key)
    if not src or not src.get("connected"):
        return fail(404, "That import is gone. Load the sheet again.")
    try:
        return await sync(src)
    except Exception:  # noqa: BLE001
        return fail(422, READ_FAIL)


@router.post("/import/sync-all")
async def sync_all():
    created, skipped, error, n = 0, 0, None, 0
    async for src in db.import_sources.find({"business_key": BKEY, "connected": True, "kind": "sheet"}):
        n += 1
        try:
            res = await sync(src)
            created, skipped = created + res["imported"], skipped + res["skipped"]
        except Exception:  # noqa: BLE001
            logger.info("Sheet sync failed for %s", src["key"])
            error = READ_FAIL
    if n:
        await db.import_runs.update_one({"business_key": BKEY}, {"$set": {
            "at": datetime.now(timezone.utc).isoformat(), "created": created, "skipped": skipped, "error": error}}, upsert=True)
    return {"ok": True, "created": created}
