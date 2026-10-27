"""Inbox: read requests through the AI ladder, check problems, price options, ask the customer, decline."""
import asyncio
import time
import base64
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from activity import log
from engine.pricing import money_text
from ai import ladder
from core import BKEY, db, ensure_matrix, get_business
from engine import matrix
from engine_api import price_job, refresh_for_rules
from reading.build import build, numbers_ok, question_template
from reading.locate import resolve
from storage import get_object, put_object

router = APIRouter(prefix="/api")
logger = logging.getLogger("drivepast.inbox")
PACIFIC = ZoneInfo("America/Los_Angeles")
READ_FAIL = "Couldn't read that right now. Try again."
PHOTO_FAIL = "Couldn't read the photo. Type what it says."
STATUS = {"new": "New", "reading": "Reading", "needs_info": "Needs info", "priced": "Priced", "quoted": "Quoted", "accepted": "Booked", "declined": "Declined", "needs_attention": "Needs attention"}
OPEN = {"$nin": ["quoted", "accepted", "declined"]}
SEEDED_COUNT = 14


def fail(status, message, **extra):
    return JSONResponse(status_code=status, content={"detail": {"message": message, **extra}})


BOOKED_BY = {"auto": "Booked automatically", "customer": "Accepted by customer"}


def api_status(s):
    return "booked" if s == "accepted" else s


def list_row(r):
    return {"key": r["key"], "number": r["number"], "source": r["source"], "sender": r["sender"],
            "summary": r.get("summary") or r.get("raw_text", "")[:120], "status": api_status(r["status"]),
            "status_label": STATUS.get(r["status"], r["status"]), "needs_clarification": r.get("needs_clarification", False),
            "ai_tag": (r.get("ai") or {}).get("tag"), "received_at": r.get("received_at"), "read": bool(r.get("details")),
            "group": r.get("group"), "booked_seconds": r.get("booked_seconds") if r["status"] == "accepted" else None,
            "booked_by": BOOKED_BY.get(r.get("booked_by")) if r["status"] == "accepted" else None, "auto_sent": bool(r.get("auto_sent"))}


def detail_view(r):
    out = {k: v for k, v in r.items() if k not in ("_id", "parsed", "stop_sig", "business_key")}
    out["status_label"] = STATUS.get(r["status"], r["status"])
    out["status"] = api_status(r["status"])
    if r["status"] != "accepted":
        out["booked_seconds"] = None
    out["booked_by"] = BOOKED_BY.get(r.get("booked_by")) if r["status"] == "accepted" else None
    if r.get("file"):
        out["file"] = {k: r["file"][k] for k in ("name", "content_type", "size")} | {"url": f"/api/inbox/{r['key']}/file"}
    return out


async def get_req(key):
    r = await db.requests.find_one({"business_key": BKEY, "key": key})
    if not r:
        raise HTTPException(404, "We couldn't find that request.")
    return r


async def parse_and_locate(r, image_b64=None):
    text = r.get("raw_text") or ""
    jobs, meta = await ladder.read_request(text, r.get("sender", ""), image_b64, allow_keyword=not image_b64 or bool(text))
    return [(rec, [(loc, await resolve(loc)) for loc in rec["locations"]]) for rec in jobs], meta


async def earlier_docs(exclude_key):
    q = {"business_key": BKEY, "stop_sig": {"$exists": True}, "key": {"$ne": exclude_key}}
    proj = {"key": 1, "number": 1, "sender_contact": 1, "received_at": 1, "stop_sig": 1, "seeded": 1, "parent_key": 1}
    return [d async for d in db.requests.find(q, proj)]


async def linked_part(r, part):
    q = {"business_key": BKEY, "parent_key": r["key"], "part": part}
    child = await db.requests.find_one(q)
    if child:
        return child
    child = await new_request(r["source"], r.get("raw_text", ""), r["sender"], r.get("sender_contact"), r.get("file"))
    await db.requests.update_one({"_id": child["_id"]}, {"$set": {"parent_key": r["key"], "part": part, "received_at": r["received_at"], "gmail": r.get("gmail")}})
    return await db.requests.find_one({"_id": child["_id"]})


async def finish_read(r, jobs, meta, biz, earlier, auto=True):
    """Store the first job on this request; extra jobs become linked requests ("2 of 2")."""
    n = len(jobs)
    group = {"parent": r["key"], "part": 1, "of": n, "keys": [r["key"]]} if n > 1 else None
    parts = [r] + [await linked_part(r, i) for i in range(2, n + 1)]
    if group:
        group["keys"] = [p["key"] for p in parts]
    done = []
    for i, (p, (rec, locs)) in enumerate(zip(parts, jobs), start=1):
        g = {**group, "part": i} if group else None
        out = await finish_one(p, rec, meta, locs, biz, earlier + done, g, auto)
        done.append(out)
    return done[0]


async def finish_one(r, rec, meta, locs, biz, earlier, group, auto=True):
    s = biz.settings.model_dump()
    await ensure_matrix(s)
    fields = build(r, rec, [(loc, p) for loc, p in locs], biz.demo_date, matrix.make_travel(s), earlier)
    fields.update(parsed=rec, ai=meta, read_at=datetime.now(PACIFIC).isoformat(), read_error=None, question=None, group=group)
    fields["options"] = None
    if fields["job"]:
        res = await price_job(fields["job"], biz, None, r["key"])
        fields["options"] = res["options"]
    if r["status"] in ("quoted", "accepted", "declined"):
        fields["status"] = r["status"]
    await db.requests.update_one({"_id": r["_id"]}, {"$set": fields})
    await log("assistant", f"Read request #{r['number']} from {r.get('sender') or 'a customer'}.", "read")
    done = {**r, **fields}
    if auto and biz.settings.auto_send_cheapest and fields["options"] and done["status"] == "priced":
        from phones_api import send_quote
        cheap = next((c for c in fields["options"]["cards"] if "Cheapest" in c["labels"]), None)
        floor = s["floor_one_off"] if fields["job"]["frequency"]["type"] == "one_off" else s["floor_recurring"]
        if cheap and not cheap.get("loses_money") and cheap["price"] >= floor - 1e-9:
            res = await send_quote(done, cheap["option_id"], auto=True)
            if isinstance(res, dict):
                done["status"] = "quoted"
                commit_at = (datetime.now(timezone.utc) + timedelta(seconds=AUTO_WAIT_SECONDS)).isoformat()
                await db.quotes.update_one({"business_key": BKEY, "key": res["key"]}, {"$set": {"commit_at": commit_at}})
                await db.requests.update_one({"_id": r["_id"]}, {"$set": {"auto_sent": True}})
                await log("auto", f"Auto-sent within your rules: {cheap['unit_name']} at {money_text(cheap['price'])} to {r.get('sender') or 'the customer'}.", "auto_sent")
                later(auto_commit_later(res["key"]))
    return done


AUTO_WAIT_SECONDS = 5


def later(coro):
    task = asyncio.create_task(coro)
    BG.add(task)
    task.add_done_callback(BG.discard)
    return task


async def _still_committable(quote_key):
    q = await db.quotes.find_one({"business_key": BKEY, "key": quote_key}, {"_id": 0, "status": 1, "request_key": 1, "option_id": 1})
    if not q or q.get("status") != "sent":
        return False
    req = await db.requests.find_one({"business_key": BKEY, "key": q["request_key"]}, {"_id": 0, "options": 1})
    opts = (req or {}).get("options") or {}
    return any(o.get("option_id") == q["option_id"] for o in (opts.get("cards") or []) + (opts.get("others") or []))


async def auto_commit_later(quote_key):
    """Auto-send: wait up to 5 s for the customer page's Accept, then commit (books once: accept_once holds the quote lock)."""
    from phones_api import accept_once
    await asyncio.sleep(AUTO_WAIT_SECONDS)
    try:
        if not await _still_committable(quote_key):
            logger.info("Auto-commit of %s skipped: quote or option is gone, or the quote isn't sent any more", quote_key)
            return
        res = await accept_once(quote_key, auto=True, by="auto")
        if isinstance(res, dict):
            q = await db.quotes.find_one({"business_key": BKEY, "key": quote_key}, {"_id": 0, "customer": 1, "unit_name": 1, "price": 1})
            await log("auto", f"Auto-sent within your rules: booked {q.get('customer') or 'the customer'} on {q['unit_name']} at {money_text(q['price'])}.", "auto_sent")
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        logger.info("Auto-commit of %s skipped: %s", quote_key, exc.detail)
    except Exception:  # noqa: BLE001
        logger.exception("Auto-commit of %s failed", quote_key)


async def read_bg(r, image_b64=None):
    """Parse on ingest: status 'reading' now, the read-and-price pipeline in the background."""
    await db.requests.update_one({"_id": r["_id"]}, {"$set": {"status": "reading", "read_error": None}})

    async def run():
        try:
            await read_one(await db.requests.find_one({"_id": r["_id"]}), image_b64)
        except asyncio.TimeoutError:
            logger.warning("Reading %s hit the %ss cap", r["key"], PARSE_CAP_SECONDS)
            await db.requests.update_one({"_id": r["_id"], "status": "reading"}, {"$set": {"status": "needs_info", "read_error": SLOW_READ}})
        except Exception:  # noqa: BLE001
            logger.exception("Background read of %s failed", r["key"])
            await db.requests.update_one({"_id": r["_id"], "status": "reading"}, {"$set": {"status": "new", "read_error": READ_FAIL}})
    task = asyncio.create_task(run())
    BG.add(task)
    task.add_done_callback(BG.discard)
    return task


BG = set()
RECLAIM_AFTER_S = 60
RESUME_TRIES = 3


async def resume_stuck_reads():
    """Startup: re-read requests a restart left in "reading" (the background task died with the process). Once each, no quote yet."""
    quoted = set(await db.quotes.distinct("request_key", {"business_key": BKEY}))
    async for r in db.requests.find({"business_key": BKEY, "status": "reading"}, {"_id": 1, "key": 1}):
        if r["key"] in quoted:
            continue
        # Atomic claim, so a second worker starting at the same time can't read (and quote) it twice.
        # A claim older than RECLAIM_AFTER_S (another restart mid-read) can be taken again, up to RESUME_TRIES times.
        now = time.time()
        claimed = await db.requests.find_one_and_update(
            {"_id": r["_id"], "status": "reading",
             "$or": [{"resumed_at": {"$exists": False}}, {"resumed_at": {"$lt": now - RECLAIM_AFTER_S}}]},
            {"$set": {"resumed_at": now}, "$inc": {"resume_tries": 1}}, return_document=True)
        if not claimed:
            continue
        if claimed.get("resume_tries", 1) > RESUME_TRIES:
            logger.warning("Gave up re-reading %s after %s restarts", r["key"], RESUME_TRIES)
            await db.requests.update_one({"_id": r["_id"], "status": "reading"}, {"$set": {"status": "needs_info", "read_error": SLOW_READ}})
            continue
        logger.info("Re-reading %s, left in 'reading' by a restart", r["key"])
        await read_bg(r)


async def read_seeded_bg():
    await db.requests.update_many({"business_key": BKEY, "seeded": {"$ne": False}, "number": {"$lte": SEEDED_COUNT}, "status": "new"},
                                  {"$set": {"status": "reading"}})
    task = asyncio.create_task(inbox_read_all())
    BG.add(task)
    task.add_done_callback(BG.discard)


PARSE_CAP_SECONDS = 18  # read + geocode; pricing after it takes well under a second, so ~20 s total
SLOW_READ = "We couldn't finish reading this in time. Check the pickup and drop-off addresses, then tap Re-read."


async def read_one(r, image_b64=None):
    biz = await get_business()
    jobs, meta = await asyncio.wait_for(parse_and_locate(r, image_b64), PARSE_CAP_SECONDS)
    return await finish_read(r, jobs, meta, biz, await earlier_docs(r["key"]))


async def read_or_fail(r, image_b64=None):
    try:
        return detail_view(await read_one(r, image_b64))
    except ladder.NoAnswer:
        if image_b64:
            await db.requests.update_one({"_id": r["_id"]}, {"$set": {"read_error": PHOTO_FAIL}})
            return detail_view({**r, "read_error": PHOTO_FAIL})
        return fail(503, READ_FAIL, retry=True)
    except Exception:
        logger.exception("Reading %s failed", r["key"])
        return fail(503, READ_FAIL, retry=True)


@router.get("/inbox")
async def inbox_list():
    rows = [list_row(r) async for r in db.requests.find({"business_key": BKEY}).sort("number", 1)]
    return {"requests": rows, "open_count": sum(1 for r in rows if r["status"] not in ("quoted", "accepted", "declined"))}


@router.get("/inbox/{key}")
async def inbox_detail(key: str):
    out = detail_view(await refresh_for_rules(await get_req(key)))
    q = await db.quotes.find_one({"business_key": BKEY, "request_key": key, "status": {"$ne": "replaced"}},
                                 {"_id": 0, "business_key": 0}, sort=[("created_at", -1)])
    out["quote"] = q
    return out


@router.post("/inbox/{key}/read")
async def inbox_read(key: str):
    r = await get_req(key)
    image = None
    if r.get("file") and r["source"] == "photo":
        data, _ = await get_object(r["file"]["path"])
        image = base64.b64encode(data).decode()
    return await read_or_fail(r, image)


@router.post("/inbox/read-all")
async def inbox_read_all():
    biz = await get_business()
    seeded = [r async for r in db.requests.find({"business_key": BKEY, "seeded": {"$ne": False}, "parent_key": {"$exists": False},
                                                   "number": {"$lte": SEEDED_COUNT}}).sort("number", 1)]
    parsed = await asyncio.gather(*[parse_and_locate(r) for r in seeded], return_exceptions=True)
    earlier = [d for d in await earlier_docs(None) if d.get("seeded") is False and not d.get("parent_key")]
    out = []
    for r, p in zip(seeded, parsed):
        if isinstance(p, Exception):
            await db.requests.update_one({"_id": r["_id"], "status": "reading"}, {"$set": {"status": "new", "read_error": READ_FAIL}})
            out.append({"key": r["key"], "number": r["number"], "ok": False, "message": READ_FAIL})
            continue
        done = await finish_read(r, p[0], p[1], biz, earlier, auto=False)
        earlier.append(done)
        out.append({"key": r["key"], "number": r["number"], "ok": True, "status": done["status"], "ai_tag": done["ai"]["tag"],
                    "parts": (done.get("group") or {}).get("of", 1)})
    return {"results": out}


@router.post("/inbox/{key}/ask-vans")
async def inbox_ask_vans(key: str):
    r = await get_req(key)
    if not r.get("details"):
        res = await read_or_fail(r)
        if isinstance(res, JSONResponse):
            return res
        r = await get_req(key)
    if r.get("job_status") != "ready":
        reason = r.get("job_reason") or "This request can't be priced yet."
        return {"priceable": False, "reason": f"Can't price yet: {reason[0].lower()}{reason[1:]}"}
    res = await price_job(r["job"], await get_business(), None, key)
    upd = {"options": res["options"]}
    if not r.get("problems") and r["status"] in ("new", "needs_info", "priced"):
        upd["status"] = "priced"
    await db.requests.update_one({"_id": r["_id"]}, {"$set": upd})
    return {"priceable": True, "options": res["options"], "ms": res["ms"], "status": upd.get("status", r["status"])}


@router.post("/inbox/{key}/ask-customer")
async def inbox_ask_customer(key: str):
    r = await get_req(key)
    if not r.get("details"):
        res = await read_or_fail(r)
        if isinstance(res, JSONResponse):
            return res
        r = await get_req(key)
    problems = r.get("problems") or []
    if not problems:
        return {"question": None, "message": "Nothing needs asking. This request has no problems."}
    cust = next((d["value"] for d in r["details"] if d["key"] == "customer"), "") or ""
    first = cust.split(",")[0].split(" ")[0] if cust and not cust.lower().startswith(("unknown", "photo")) else ""
    template = question_template(problems[0], first)
    system = ("You write one short, friendly text message from a courier dispatcher to a customer, asking one clear question. "
              "Use only the facts given. Never add numbers, prices, times or addresses that aren't in the facts. "
              "Reply with the message only.")
    prompt = f"Customer first name: {first or 'unknown'}\nThe problem: {problems[0]['text']}\nA plain draft to improve: {template}"
    text, meta = await ladder.write_text(system, prompt, lambda t: numbers_ok(t, problems[0]["text"] + " " + template))
    q = {"text": text or template, "tag": meta["tag"], "level": meta["level"]}
    await db.requests.update_one({"_id": r["_id"]}, {"$set": {"question": q}})
    return {"question": q}


@router.post("/inbox/{key}/decline")
async def inbox_decline(key: str):
    r = await get_req(key)
    await db.requests.update_one({"_id": r["_id"]}, {"$set": {"status": "declined"}})
    await log("owner", f"Declined request #{r['number']} from {r.get('sender') or 'a customer'}.", "decline")
    return {"ok": True, "status": "declined", "status_label": "Declined"}


async def new_request(source, text, sender, contact, file=None):
    last = await db.requests.find_one({"business_key": BKEY}, sort=[("number", -1)])
    n = (last["number"] if last else 0) + 1
    doc = {"key": f"req-{n:02d}", "business_key": BKEY, "number": n, "source": source, "sender": sender,
           "sender_contact": contact, "raw_text": text, "file": file, "received_at": datetime.now(PACIFIC).isoformat(),
           "parsed": None, "problems": [], "status": "new", "seeded": False, "job_status": "cant_price",
           "job": None, "job_reason": "Not read yet.", "job_summary": None}
    await db.requests.insert_one(doc)
    return await db.requests.find_one({"key": doc["key"], "business_key": BKEY})


class PasteIn(BaseModel):
    text: str
    source: str = "email"
    sender: Optional[str] = None


async def after_read(res):
    if isinstance(res, dict) and res.get("details") and res.get("sender") in ("Pasted request", "Uploaded PDF", "Uploaded photo"):
        cust = next((d["value"] for d in res["details"] if d["key"] == "customer"), None)
        if cust:
            await db.requests.update_one({"business_key": BKEY, "key": res["key"]}, {"$set": {"sender": cust}})
            res["sender"] = cust
    return res


@router.post("/inbox")
async def inbox_add(body: PasteIn):
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Paste the request text first.")
    if len(text) > 5000:
        raise HTTPException(422, "That's too long. Keep it under 5,000 characters.")
    if body.source not in ("email", "text", "voicemail"):
        raise HTTPException(422, "Pick email, text or voicemail.")
    r = await new_request(body.source, text, (body.sender or "").strip() or "Pasted request", None)
    await read_bg(r)
    return detail_view(await get_req(r["key"]))


class IncomingText(BaseModel):
    from_number: str
    text: str


@router.post("/inbox/incoming-text")
async def inbox_incoming_text(body: IncomingText):
    if not body.text.strip():
        raise HTTPException(422, "The text is empty.")
    r = await new_request("text", body.text.strip(), body.from_number.strip(), body.from_number.strip())
    return await read_or_fail(r)


@router.post("/inbox/upload")
async def inbox_upload(file: UploadFile = File(...), kind: str = Form(...)):
    data = await file.read()
    if kind not in ("pdf", "photo"):
        raise HTTPException(422, "Upload a PDF or a photo.")
    if not data or len(data) > 10 * 1024 * 1024:
        raise HTTPException(422, "The file needs to be under 10 MB.")
    ctype = file.content_type or ("application/pdf" if kind == "pdf" else "image/jpeg")
    if kind == "pdf" and not (ctype == "application/pdf" or data[:4] == b"%PDF"):
        raise HTTPException(422, "That file isn't a PDF.")
    if kind == "photo" and not ctype.startswith("image/"):
        raise HTTPException(422, "That file isn't a photo. Use a JPG, PNG or WEBP.")
    text = ""
    if kind == "pdf":
        try:
            from pypdf import PdfReader
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages).strip()
        except Exception:
            raise HTTPException(422, "We couldn't open that PDF.")
        if not text:
            raise HTTPException(422, "That PDF has no text we can read. Paste what it says instead.")
    ext = "pdf" if kind == "pdf" else (ctype.split("/")[-1].replace("jpeg", "jpg") or "jpg")
    try:
        stored = await put_object(f"uploads/{uuid.uuid4().hex}.{ext}", data, ctype)
    except Exception:
        logger.exception("Upload to storage failed")
        raise HTTPException(503, "Couldn't save the file right now. Try again.")
    meta = {"path": stored["path"], "name": file.filename or f"upload.{ext}", "content_type": ctype, "size": len(data)}
    r = await new_request(kind, text, "Uploaded PDF" if kind == "pdf" else "Uploaded photo", None, meta)
    image = base64.b64encode(data).decode() if kind == "photo" else None
    return await after_read(await read_or_fail(r, image))


@router.get("/inbox/{key}/file")
async def inbox_file(key: str):
    r = await get_req(key)
    if not r.get("file"):
        raise HTTPException(404, "This request has no file.")
    data, _ = await get_object(r["file"]["path"])
    return Response(content=data, media_type=r["file"]["content_type"])
