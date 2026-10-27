"""Step 25 snapshot: keyword reader on 57 sample texts + options for Maya/Dana/Gilman/Grand Ave. Usage: step25_snapshot.py out.json"""
import ast
import glob
import json
import subprocess
import sys

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402

load_dotenv("/app/backend/.env")
from ai.keyword import keyword_jobs, keyword_read, read_frequency, read_time  # noqa: E402


def corpus():
    seen = []
    for f in sorted(glob.glob("/app/backend/seed/*.py") + glob.glob("/app/backend/live_api.py") + glob.glob("/app/backend/scripts/step*.py")):
        for node in ast.walk(ast.parse(open(f).read())):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                if 30 < len(s) < 600 and any(w in s.lower() for w in ("pick", "drop", "deliver")) and s not in seen:
                    seen.append(s)
    return seen[:57]


texts = json.load(open('/app/backend/scripts/step25_texts.json'))
kw = [{"text": t, "time": repr(read_time(t)), "freq": repr(read_frequency(t)), "read": repr(keyword_read(t, "")),
       "jobs": repr(keyword_jobs(t, ""))} for t in texts]
opts = json.load(open(subprocess.run([sys.executable, "/app/backend/scripts/step21_snapshot.py", "/tmp/s25_opts.json"],
                                     check=True, capture_output=True) and "/tmp/s25_opts.json"))
import requests  # noqa: E402
import time  # noqa: E402
from live_api import DEMO_EMAIL, FIRE_TEXT  # noqa: E402
sys.path.insert(0, "/app/backend/scripts")
API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
requests.put(f"{API}/settings", json={"auto_send_cheapest": False})
k = requests.post(f"{API}/inbox", json={"text": FIRE_TEXT, "source": "email", "sender": f"{DEMO_EMAIL[0]} <{DEMO_EMAIL[1]}>"}, timeout=30).json()
k = k.get("key") or k.get("request", {}).get("key")
d = {}
for _ in range(30):
    d = requests.get(f"{API}/inbox/{k}").json()
    if d.get("status") not in ("reading", "new"):
        break
    time.sleep(1)
requests.put(f"{API}/settings", json={"auto_send_cheapest": True})
VOL = {"option_id", "created_at", "updated_at", "key", "request_key", "source_key", "ts", "at"}
opts["Dana"] = [{k2: v for k2, v in sorted(c.items()) if k2 not in VOL} for c in (d.get("options") or {}).get("cards", []) + (d.get("options") or {}).get("others", [])]
json.dump({"n_texts": len(texts), "keyword": kw, "options": opts}, open(sys.argv[1], "w"), indent=1, sort_keys=True)
print("texts", len(texts))
