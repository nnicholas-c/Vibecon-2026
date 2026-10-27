"""Mocked OpenAI checks for the "Our model" slot: request shape, 400 retries, error wording, labels. No real key needed."""
import asyncio
import json

import httpx

from ai import ladder

SCHEMA = {"type": "object", "properties": {"pickup": {"type": "string"}}}


def run(handler, cfg, schema=None):
    seen = []

    def wrapped(request):
        body = json.loads(request.content)
        seen.append(body)
        return handler(body, len(seen))

    real = httpx.AsyncClient

    class Fake(real):
        def __init__(self, *a, **k):
            super().__init__(*a, transport=httpx.MockTransport(wrapped), **{x: y for x, y in k.items() if x != "transport"})

    ladder.httpx.AsyncClient = Fake
    try:
        out = asyncio.run(ladder.call_ours(cfg, [{"role": "user", "content": "hi"}], schema))
    finally:
        ladder.httpx.AsyncClient = real
    return out, seen


def ok(text="OK"):
    return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": text}}]})


OPENAI = {"base_url": "https://api.openai.com/v1", "model": "gpt-5-nano", "secret": "sk-test"}

# 1. OpenAI + gpt-5 family: no vLLM extra, no temperature, reasoning_effort minimal, json_schema kept.
out, seen = run(lambda b, n: ok(), OPENAI, SCHEMA)
b = seen[0]
assert "chat_template_kwargs" not in b and "temperature" not in b and b["reasoning_effort"] == "minimal"
assert b["response_format"]["type"] == "json_schema" and len(seen) == 1
print("1 ok: openai gpt-5-nano body", sorted(b))

# 2. Older OpenAI model: temperature 0 sent; a 400 naming temperature retries without it.
def temp_400(b, n):
    if "temperature" in b:
        return httpx.Response(400, json={"error": {"message": "Unsupported value: 'temperature' does not support 0 with this model.", "param": "temperature"}})
    return ok()
out, seen = run(temp_400, {**OPENAI, "model": "gpt-4.1-mini"}, SCHEMA)
assert seen[0]["temperature"] == 0 and "temperature" not in seen[1] and "response_format" in seen[1] and out == "OK"
print("2 ok: temperature 400 -> retried without temperature, kept json_schema")

# 3. Non-OpenAI host that rejects the vLLM extra: dropped and retried.
def extra_400(b, n):
    if "chat_template_kwargs" in b:
        return httpx.Response(400, json={"error": {"message": "Unrecognized request argument supplied: chat_template_kwargs"}})
    return ok()
out, seen = run(extra_400, {"base_url": "https://my-model.example.com", "model": "qwen3-8b"}, SCHEMA)
assert "chat_template_kwargs" in seen[0] and "chat_template_kwargs" not in seen[1] and out == "OK"
print("3 ok: extra-field 400 -> retried without chat_template_kwargs")

# 4. Schema refused: falls back to JSON-only (no response_format).
def schema_400(b, n):
    if "response_format" in b:
        return httpx.Response(400, json={"error": {"message": "Invalid schema for response_format"}})
    return ok("{}")
out, seen = run(schema_400, OPENAI, SCHEMA)
assert "response_format" in seen[0] and "response_format" not in seen[-1]
print("4 ok: schema refused -> JSON-only fallback")

# 5. Error wording for OpenAI 401 / 429 in Test connection.
for code, want in ((401, "OpenAI turned the key away. Check the key."), (429, "OpenAI says the key is out of credit or rate-limited.")):
    real = httpx.AsyncClient

    class Fake(real):
        def __init__(self, *a, code=code, **k):
            super().__init__(*a, transport=httpx.MockTransport(lambda r: httpx.Response(code, json={"error": {"message": "x"}})), **{x: y for x, y in k.items() if x != "transport"})

    ladder.httpx.AsyncClient = Fake
    try:
        res = asyncio.run(ladder.test_connection(OPENAI))
    finally:
        ladder.httpx.AsyncClient = real
    assert res["message"] == want, res
    print(f"5 ok: HTTP {code} -> {res['message']}")

# 6. Labels.
assert ladder.ours_label(OPENAI) == "OpenAI (your key)" and ladder.ours_tag(OPENAI) == "OpenAI (your key) · gpt-5-nano"
assert ladder.ours_tag({"base_url": "https://x.example.com", "model": "m"}) == "our model"
assert ladder.ours_tag({"base_url": "http://localhost:8001/api/dev/stub-llm", "model": "m"}) == "test stand-in"
print("6 ok: labels")
print("ALL OPENAI MOCK CHECKS PASSED")
