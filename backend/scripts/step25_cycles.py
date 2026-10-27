"""Import-cycle check over backend app modules (top-level AND function-level imports) + import each module alone."""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path("/app/backend")
SKIP = {"tests", "e1_tests", "scripts", "__pycache__"}
mods = {}
for p in ROOT.rglob("*.py"):
    rel = p.relative_to(ROOT)
    if SKIP & set(rel.parts):
        continue
    name = ".".join(rel.with_suffix("").parts).removesuffix(".__init__")
    mods[name] = p


def deps(p, me, top_only=False):
    out = set()
    tree = ast.parse(p.read_text())
    for n in (tree.body if top_only else ast.walk(tree)):
        names = [a.name for a in n.names] if isinstance(n, ast.Import) else []
        if isinstance(n, ast.ImportFrom) and n.module and not n.level:
            names = [n.module] + [f"{n.module}.{a.name}" for a in n.names]
        out |= {x for x in names if x in mods and x != me}
    return out


graph = {m: deps(p, m, "--top" in sys.argv) for m, p in mods.items()}
idx, low, stack, on, sccs, c = {}, {}, [], set(), [], [0]


def strong(v):
    idx[v] = low[v] = c[0]
    c[0] += 1
    stack.append(v)
    on.add(v)
    for w in graph[v]:
        if w not in idx:
            strong(w)
            low[v] = min(low[v], low[w])
        elif w in on:
            low[v] = min(low[v], idx[w])
    if low[v] == idx[v]:
        comp = []
        while True:
            w = stack.pop()
            on.discard(w)
            comp.append(w)
            if w == v:
                break
        if len(comp) > 1:
            sccs.append(sorted(comp))


sys.setrecursionlimit(5000)
for m in graph:
    if m not in idx:
        strong(m)
print("modules:", len(mods), "| import cycles", "(top-level imports only):" if "--top" in sys.argv else "(incl. function-level imports):", len(sccs))
for s in sccs:
    print("  cycle group:", " , ".join(s))
bad = []
for m in sorted(mods):
    r = subprocess.run([sys.executable, "-c", f"import {m}"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        bad.append((m, r.stderr.strip().splitlines()[-1]))
print("imported alone OK:", len(mods) - len(bad), "/", len(mods))
for m, e in bad:
    print("  FAIL", m, e)
