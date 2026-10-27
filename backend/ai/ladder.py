"""The AI ladder (D-12): our model -> Emergent universal key (Claude Sonnet 5.5) -> no AI."""
import asyncio
import json
import os
import re
import time
import uuid
from collections import namedtuple
from datetime import datetime, timezone

import httpx
from pydantic import ValidationError

from ai.keyword import keyword_jobs
from ai.examples import examples_block
from ai.schema import READ_PROMPT, SCHEMA, RecordRequest
from agent_usage import take_call
from core import BKEY, db

TIMEOUT = 20
READ_BUDGET = float(os.environ.get("AGENT_TIMEOUT_SECONDS") or 15)  # whole reader call, both attempts
MODELS = {
    "claude-haiku-4-5": ("anthropic", "claude-haiku-4-5-20251001", "Claude Haiku 4.5"),
    "claude-sonnet-5-5": ("anthropic", "claude-sonnet-5-5", "Claude Sonnet 5.5"),
    "gpt-5-5": ("openai", "gpt-5.5", "GPT-5.5"),
    "gemini-3-flash": ("gemini", "gemini-3-flash-preview", "Gemini 3 Flash"),
}
DEFAULTS = {"mode": "auto", "reading_model": "claude-haiku-4-5", "reading_examples": 5, "assistant_model": "claude-sonnet-5-5"}
STUB_PATH = "/api/dev/stub-llm"


def is_stub(cfg):
    return STUB_PATH in (cfg.get("base_url") or "")


def is_openai(cfg):
    return "api.openai.com" in (cfg.get("base_url") or "").lower()


def is_reasoning_model(model):
    return bool(re.match(r"^(gpt-5|gpt-6|o\d)", (model or "").strip().lower()))


def ours_label(cfg):
    return "OpenAI (your key)" if is_openai(cfg) else "Our model"


def ours_tag(cfg):
    if is_stub(cfg):
        return "test stand-in"
    return f"OpenAI (your key) · {cfg['model']}" if is_openai(cfg) else "our model"


def model_name(key):
    return MODELS.get(key, MODELS[DEFAULTS["reading_model"]])[2]
THINK = re.compile(r"<think>.*?</think>", re.S | re.I)


class NoAnswer(Exception):
    pass


async def get_config():
    doc = await db.ai_config.find_one({"business_key": BKEY}, {"_id": 0}) or {}
    return {**DEFAULTS, **{k: v for k, v in doc.items() if v is not None}}


def configured(cfg):
    return bool((cfg.get("base_url") or "").strip() and (cfg.get("model") or "").strip())


def strip_think(text):
    text = THINK.sub("", text or "")
    return text.split("</think>")[-1].strip()


def parse_json(text):
    text = strip_think(text)
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < a:
        raise ValueError("no JSON object")
    return json.loads(text[a:b + 1])


def chat_url(base):
    base, _, query = base.strip().partition("?")
    base = base.rstrip("/")
    if not base.endswith("/chat/completions"):
        base = (base[:-3] if base.endswith("/v1") else base) + "/v1/chat/completions"
    return f"{base}?{query}" if query else base


def env_cfg():
    """The Task 1 assistant model (AGENT_*), used to read requests with reasoning 'low'."""
    base, key = os.environ.get("AGENT_API_BASE"), os.environ.get("AGENT_API_KEY")
    if not (base and key):
        return None
    return {"base_url": base, "model": os.environ.get("AGENT_MODEL") or "gpt-6-luna", "secret": key, "reasoning": "low", "env": True}


def ours_body(cfg, messages, json_schema):
    body = {"model": cfg["model"], "messages": messages, "stream": False}
    if not is_openai(cfg) and not cfg.get("env"):
        body["chat_template_kwargs"] = {"enable_thinking": False}
    if is_reasoning_model(cfg["model"]):
        body["reasoning_effort"] = cfg.get("reasoning") or "minimal"
    else:
        body["temperature"] = 0
    if json_schema:
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "record_request", "schema": json_schema}}
    return body


def drop_rejected(body, status, err):
    """After an error reply, remove the one field the server most likely refused. Returns False if nothing is left to try."""
    err = (err or "").lower()
    if status == 400:
        for field, words in (("chat_template_kwargs", ("chat_template_kwargs", "unrecognized", "unknown parameter", "extra")),
                             ("temperature", ("temperature",)), ("reasoning_effort", ("reasoning_effort", "reasoning"))):
            if field in body and any(w in err for w in words):
                body.pop(field)
                return True
    if "response_format" in body and status in (400, 404, 415, 422, 500, 501):
        body.pop("response_format")
        return True
    if "chat_template_kwargs" in body and status in (400, 422):
        body.pop("chat_template_kwargs")
        return True
    return False


async def call_ours(cfg, messages, json_schema=None, timeout=TIMEOUT):
    """One HTTP call to our model. Returns the reply text with any <think> block removed."""
    body = ours_body(cfg, messages, json_schema)
    headers = {"Content-Type": "application/json"}
    if cfg.get("secret"):
        headers["Authorization"] = f"Bearer {cfg['secret']}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(chat_url(cfg["base_url"]), json=body, headers=headers)
        for _ in range(4):
            if r.status_code < 400 or not drop_rejected(body, r.status_code, r.text):
                break
            r = await client.post(chat_url(cfg["base_url"]), json=body, headers=headers)
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
    return strip_think(msg.get("content") or "")


async def call_backup(system, text, image_b64=None, model_key=None):
    from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage
    provider, model, _ = MODELS.get(model_key, MODELS[DEFAULTS["reading_model"]])
    chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"read-{uuid.uuid4().hex}",
                   system_message=system).with_model(provider, model)
    msg = UserMessage(text=text, file_contents=[ImageContent(image_base64=image_b64)] if image_b64 else None)
    return strip_think(await chat.send_message(msg))


async def record(level, model, started, label=None, stub=False, cfg=None):
    tag = (ours_tag(cfg) if cfg else ("test stand-in" if stub else "our model")) if level == 1 else "backup"
    meta = {"level": level, "tag": tag, "model": model,
            "label": "Test stand-in" if stub and level == 1 else (label or {1: ours_label(cfg or {}), 2: "Built-in key", 3: "No AI"}[level]),
            "seconds": round(time.perf_counter() - started, 1), "at": datetime.now(timezone.utc).isoformat()}
    await db.ai_status.update_one({"business_key": BKEY}, {"$set": {**meta, "business_key": BKEY}}, upsert=True)
    return meta


def _user_content(text, image_b64):
    if not image_b64:
        return f"Request:\n<<<\n{text}\n>>>"
    return [{"type": "text", "text": "Read the request in this photo." + (f"\nText we already have: {text}" if text else "")},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]


def read_system(n_examples):
    return READ_PROMPT.replace("{schema}", json.dumps(SCHEMA)) + examples_block(n_examples)


def validate_jobs(obj):
    jobs = obj.get("jobs") if isinstance(obj, dict) and "jobs" in obj else [obj]
    out = [RecordRequest.model_validate(j).model_dump() for j in jobs or []]
    if not out:
        raise ValueError("no jobs")
    return out


async def _ours_read(cfg, text, image_b64):
    messages = [{"role": "system", "content": read_system(cfg["reading_examples"])},
                {"role": "user", "content": _user_content(text, image_b64)}]
    for _ in range(2):
        try:
            return validate_jobs(parse_json(await call_ours(cfg, messages, SCHEMA)))
        except (ValueError, ValidationError):
            continue
    raise NoAnswer("invalid output")


async def _backup_read(cfg, text, image_b64):
    user = "Read the request in this photo." if image_b64 and not text else f"Request:\n<<<\n{text}\n>>>"
    for _ in range(2):
        try:
            return validate_jobs(parse_json(await call_backup(read_system(cfg["reading_examples"]), user, image_b64, cfg["reading_model"])))
        except (ValueError, ValidationError):
            continue
    raise NoAnswer("invalid output")


async def read_request(text, sender="", image_b64=None, allow_keyword=True):
    """Read a request into record_request fields. Returns (fields, meta). Raises NoAnswer if nothing can read it."""
    cfg = await get_config()
    mode = cfg.get("mode", "auto")
    started = time.perf_counter()
    env = env_cfg()
    if mode != "none" and env and await take_call():
        return await _env_read(cfg, env, _ReadIn(text, sender, image_b64, allow_keyword), started)
    got = await _model_levels(cfg, mode, text, image_b64, started)
    if got:
        return got
    if not allow_keyword or not text.strip():
        raise NoAnswer("no level could read it")
    return await _keyword_read(text, sender, started)


async def _keyword_read(text, sender, started):
    return keyword_jobs(text, sender), await record(3, "No AI (keyword reader)", started, "No AI (keyword reader)")


_ReadIn = namedtuple("_ReadIn", "text sender image_b64 allow_keyword")


async def _env_read(cfg, env, req, started):
    try:
        out = await asyncio.wait_for(_ours_read({**cfg, **env}, req.text, req.image_b64), READ_BUDGET)
        return out, await record(1, env["model"], started, label="Assistant model")
    except Exception as exc:
        logger_safe("assistant model", exc)
    # Stage safety: one ~15 s budget for the reader, then the no-AI path at once (no further model levels).
    if req.allow_keyword and req.text.strip():
        return await _keyword_read(req.text, req.sender, started)
    raise NoAnswer("assistant model could not read it")


async def _model_levels(cfg, mode, text, image_b64, started):
    """Our configured model, then the universal-key backup. None when neither answered."""
    if mode == "auto" and configured(cfg):
        try:
            out = await asyncio.wait_for(_ours_read(cfg, text, image_b64), TIMEOUT)
            return out, await record(1, cfg["model"], started, stub=is_stub(cfg), cfg=cfg)
        except Exception as exc:
            logger_safe("our model", exc)
    if mode != "none" and os.environ.get("EMERGENT_LLM_KEY"):
        try:
            out = await asyncio.wait_for(_backup_read(cfg, text, image_b64), 25)
            return out, await record(2, model_name(cfg["reading_model"]), started)
        except Exception as exc:
            logger_safe("backup", exc)
    return None


async def write_text(system, prompt, check):
    """Short AI-written text. Returns (text or None, meta). None means use the fixed template."""
    cfg = await get_config()
    mode = cfg.get("mode", "auto")
    started = time.perf_counter()
    if mode == "auto" and configured(cfg):
        try:
            msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
            for _ in range(2):
                out = (await asyncio.wait_for(call_ours(cfg, msgs), TIMEOUT)).strip().strip('"')
                if check(out):
                    return out, await record(1, cfg["model"], started, stub=is_stub(cfg), cfg=cfg)
        except Exception as exc:
            logger_safe("our model", exc)
    if mode != "none" and os.environ.get("EMERGENT_LLM_KEY"):
        try:
            for _ in range(2):
                out = (await asyncio.wait_for(call_backup(system, prompt, None, cfg["reading_model"]), 25)).strip().strip('"')
                if check(out):
                    return out, await record(2, model_name(cfg["reading_model"]), started)
        except Exception as exc:
            logger_safe("backup", exc)
    return None, await record(3, "No AI (fixed templates)", started, "No AI (fixed templates)")


def logger_safe(level, exc):
    import logging
    logging.getLogger("drivepast.ai").info("AI level %s dropped: %s", level, type(exc).__name__)


async def test_connection(cfg):
    if not configured(cfg):
        return {"ok": False, "message": "Add the address and model name first."}
    if not re.match(r"^https?://", cfg["base_url"].strip()):
        return {"ok": False, "message": "That address doesn't look right. Start it with http:// or https://"}
    started = time.perf_counter()
    try:
        await asyncio.wait_for(call_ours(cfg, [{"role": "user", "content": "Reply with the word OK."}]), TIMEOUT)
    except (asyncio.TimeoutError, httpx.TimeoutException):
        return {"ok": False, "message": "Couldn't reach your model: no answer within 20 seconds"}
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if is_openai(cfg) and code in (401, 403):
            return {"ok": False, "message": "OpenAI turned the key away. Check the key."}
        if is_openai(cfg) and code == 429:
            return {"ok": False, "message": "OpenAI says the key is out of credit or rate-limited."}
        if code in (401, 403):
            return {"ok": False, "message": "Your model turned us away. Check the shared secret."}
        if code == 404:
            return {"ok": False, "message": "Something answered, but not at /v1/chat/completions. Check the address."}
        return {"ok": False, "message": f"Your model answered with an error (HTTP {code})."}
    except httpx.HTTPError:
        return {"ok": False, "message": "Couldn't reach your model: nothing answered at that address"}
    except Exception:
        return {"ok": False, "message": "Couldn't read your model's answer. Check that it speaks the OpenAI chat format."}
    secs = time.perf_counter() - started
    return {"ok": True, "message": f"Connected · answered in {secs:.1f} s", "model": cfg["model"], "seconds": round(secs, 1)}
