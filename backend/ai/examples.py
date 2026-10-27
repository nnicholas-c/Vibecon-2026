"""A fixed set of 5 synthetic examples for the reading prompt (from the synthetic templates)."""
import json
from functools import lru_cache

EXAMPLES = [
    ("Hi, this is Ana from Piedmont Ave Lab. Can you pick up at our lab every weekday at 4pm and drop at Emeryville Central Lab? Thanks, Ana", "Ana at Piedmont Ave Lab"),
    ("need a same day pickup at 2000 University Ave Berkeley around 3, deliver to 1400 Powell St Emeryville. 3 boxes", ""),
    ("Fwd: PO 812\nFrom: office@claystreetlaw.example\nPURCHASE ORDER 812\nPickup: Clay Street Law Group\nDeliver to: Fallon Street Courthouse\nSchedule: Tuesdays and Thursdays at 10am", ""),
    ("[9/14, 9:12 AM] Leo: can u grab a box from Third Street Print tomorrow at 1pm\n[9/14, 9:13 AM] Leo: to Montgomery Partners pls", ""),
    ("Hi! Two things:\n1) Today at 11am pick up at Elmwood Pharmacy and deliver to Ashby Medical Center.\n2) Every weekday at 3pm pick up at Temescal Diagnostics Lab and deliver to Piedmont Ave Lab.\nThanks, Priya", ""),
]


@lru_cache(maxsize=2)
def examples_block(n):
    if not n:
        return ""
    from ai.keyword import keyword_jobs
    lines = ["", "", "Examples (request, then the JSON you reply with):"]
    for text, sender in EXAMPLES[:n]:
        jobs = keyword_jobs(text, sender)
        lines.append(f"Request:\n<<<\n{text}\n>>>\nJSON: {json.dumps({'jobs': jobs}, separators=(',', ':'))}")
    return "\n\n".join(lines)
