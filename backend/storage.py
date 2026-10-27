"""Emergent Object Storage for uploaded PDFs and photos."""
import asyncio
import os

import requests

APP = "drivepast"
_key = {"v": None}


def _url():
    base = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
    return base.rstrip("/") + "/objstore/api/v1/storage"


def _init(force=False):
    if _key["v"] and not force:
        return _key["v"]
    r = requests.post(f"{_url()}/init", json={"emergent_key": os.environ["EMERGENT_LLM_KEY"]}, timeout=30)
    r.raise_for_status()
    _key["v"] = r.json()["storage_key"]
    return _key["v"]


def _put(path, data, content_type):
    url = f"{_url()}/objects/{path}"
    r = requests.put(url, headers={"X-Storage-Key": _init(False), "Content-Type": content_type}, data=data, timeout=120)
    if r.status_code == 404:
        r = requests.put(url, headers={"X-Storage-Key": _init(True), "Content-Type": content_type}, data=data, timeout=120)
    r.raise_for_status()
    return r.json()


def _get(path):
    url = f"{_url()}/objects/{path}"
    r = requests.get(url, headers={"X-Storage-Key": _init(False)}, timeout=60)
    if r.status_code == 404:
        r = requests.get(url, headers={"X-Storage-Key": _init(True)}, timeout=60)
    r.raise_for_status()
    return r.content, r.headers.get("Content-Type", "application/octet-stream")


async def put_object(path, data, content_type):
    return await asyncio.to_thread(_put, f"{APP}/{path}", data, content_type)


async def get_object(path):
    return await asyncio.to_thread(_get, path)
