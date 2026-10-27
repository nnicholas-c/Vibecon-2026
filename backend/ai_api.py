"""Our model settings, the AI mode, Test connection, and a test-only OpenAI-compatible stub."""
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai import ladder
from ai.keyword import keyword_jobs
from core import BKEY, db

router = APIRouter(prefix="/api")
MODES = {"auto": "Auto", "skip_ours": "Skip our model", "none": "No AI"}


def mask(secret):
    return "saved" if secret else ""


async def public_config():
    cfg = await ladder.get_config()
    status = await db.ai_status.find_one({"business_key": BKEY}, {"_id": 0, "business_key": 0})
    return {"base_url": cfg.get("base_url", ""), "model": cfg.get("model", ""), "secret_set": bool(cfg.get("secret")),
            "secret_masked": mask(cfg.get("secret")), "mode": cfg.get("mode", "auto"), "modes": MODES,
            "configured": ladder.configured(cfg), "last_test": cfg.get("last_test"), "last_answered": status,
            "reading_model": cfg["reading_model"], "reading_examples": cfg["reading_examples"],
            "assistant_model": cfg["assistant_model"], "models": {k: v[2] for k, v in ladder.MODELS.items()}}


class ConfigIn(BaseModel):
    base_url: Optional[str] = None
    model: Optional[str] = None
    secret: Optional[str] = None
    clear_secret: bool = False
    mode: Optional[str] = None
    reading_model: Optional[str] = None
    reading_examples: Optional[int] = None
    assistant_model: Optional[str] = None


@router.get("/ai/config")
async def ai_config():
    return await public_config()


@router.put("/ai/config")
async def ai_config_save(body: ConfigIn):
    upd, errors = {}, {}
    _text_fields(body, upd, errors)
    _choice_fields(body, upd, errors)
    if errors:
        return JSONResponse(status_code=422, content={"detail": {"message": "Some values need fixing.", "fields": errors}})
    if {"base_url", "model", "secret"} & upd.keys():
        upd["last_test"] = None
    await db.ai_config.update_one({"business_key": BKEY}, {"$set": {**upd, "business_key": BKEY}}, upsert=True)
    return await public_config()


def _text_fields(body, upd, errors):
    if body.base_url is not None:
        url = body.base_url.strip()
        if url and not re.match(r"^https?://[^\s]+$", url):
            errors["base_url"] = "Start the address with http:// or https://"
        upd["base_url"] = url
    if body.model is not None:
        upd["model"] = body.model.strip()[:200]
    if body.secret:
        upd["secret"] = body.secret.strip()[:500]
    if body.clear_secret:
        upd["secret"] = ""


def _choice_fields(body, upd, errors):
    if body.mode is not None:
        if body.mode not in MODES:
            errors["mode"] = "Pick Auto, Skip our model or No AI."
        upd["mode"] = body.mode
    for k in ("reading_model", "assistant_model"):
        v = getattr(body, k)
        if v is not None:
            if v not in ladder.MODELS:
                errors[k] = "Pick Claude Haiku 4.5, Claude Sonnet 5.5, GPT-5.5 or Gemini 3 Flash."
            upd[k] = v
    if body.reading_examples is not None:
        if body.reading_examples not in (0, 5):
            errors["reading_examples"] = "Pick 0 or 5 examples."
        upd["reading_examples"] = body.reading_examples


@router.post("/ai/test")
async def ai_test():
    cfg = await ladder.get_config()
    res = await ladder.test_connection(cfg)
    res["at"] = datetime.now(timezone.utc).isoformat()
    await db.ai_config.update_one({"business_key": BKEY}, {"$set": {"last_test": res, "business_key": BKEY}}, upsert=True)
    return res


@router.post("/dev/stub-llm/v1/chat/completions", include_in_schema=False)
async def stub_llm(request: Request, delay: float = 0, fail: int = 0):
    """TEST ONLY. Answers like an OpenAI-compatible server, wrapping replies in a <think> block."""
    if os.environ.get("DEV_STUB_ENABLED", "false").lower() != "true":
        raise HTTPException(404, "Not available.")
    if delay:
        await asyncio.sleep(min(delay, 60))
    if fail:
        raise HTTPException(500, "Stub model failure (test).")
    body = await request.json()
    msgs = body.get("messages") or []
    system = " ".join(m["content"] for m in msgs if m.get("role") == "system" and isinstance(m.get("content"), str))
    user = msgs[-1].get("content") if msgs else ""
    if isinstance(user, list):
        return JSONResponse(status_code=400, content={"error": {"message": "This model can't read images."}})
    if "record_request" in system:
        m = re.search(r"<<<\n(.*)\n>>>", user, re.S)
        reply = json.dumps({"jobs": keyword_jobs(m.group(1) if m else user)})
    elif "Reply with the word OK" in user:
        reply = "OK"
    else:
        draft = re.search(r"A plain draft to improve: (.*)", user, re.S)
        reply = draft.group(1).strip() if draft else "OK"
    return {"id": "stub-1", "object": "chat.completion", "model": body.get("model", "stub"),
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": f"<think>Stub model thinking.</think>{reply}"}}]}
