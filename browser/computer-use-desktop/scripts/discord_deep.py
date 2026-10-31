#!/usr/bin/env python3
"""Lee el historial de un canal de Discord hacia arriba con scroll-to sobre el primer mensaje.

Uso: python3 discord_deep.py "<canal>" [iteraciones]

Mecanismo: en Discord el contenedor de mensajes NO expone la acción Scroll (ACTION_NOT_SUPPORTED),
pero `scroll-to` sobre el primer `article` visible sí desplaza el list y dispara la carga de historial.
"""
import json
import os
import subprocess
import sys
import time

BIN = os.path.expanduser("~/.bun/bin/agent-desktop")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
APP = "Discord"


def run(*args, timeout=90):
    p = subprocess.run([BIN, *args], capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": {"code": "PARSE"}}


def walk(n):
    if isinstance(n, dict):
        yield n
        for c in n.get("children") or []:
            yield from walk(c)


def snap():
    return run("snapshot", "--app", APP, "-i", "--compact", "--timeout-ms", "30000")


def arts(env):
    return [n for n in walk((env.get("data") or {}).get("tree")) if n.get("role") == "article"]


def texts(env):
    out = []
    for n in arts(env):
        raw = str(n.get("description") or n.get("name") or "").strip()
        if raw:
            out.append(raw)
    return out


def channels(env):
    for n in walk((env.get("data") or {}).get("tree")):
        name = str(n.get("name") or "")
        if n.get("role") == "link" and "(canal de texto)" in name:
            yield name.split(" (canal de texto)")[0], n.get("ref_id")


nombre = sys.argv[1]
iters = int(sys.argv[2]) if len(sys.argv) > 2 else 6

env = snap()
hit = next(((c, r) for c, r in channels(env) if nombre.lower() in c.lower()), None)
if not hit:
    print("canal no encontrado")
    raise SystemExit(1)
print("click en", hit[0], run("click", hit[1]).get("ok"))
time.sleep(2)
env = snap()

seen, order = set(), []
t0 = time.time()
for i in range(iters):
    nuevos = 0
    for p in texts(env):
        if p not in seen:
            seen.add(p)
            order.append(p)
            nuevos += 1
    print(f"  iter {i+1}: articles={len(arts(env)):3d} nuevos={nuevos:3d} total={len(order):4d} ({time.time()-t0:.0f}s)")
    first = arts(env)
    if not first:
        break
    st = run("scroll-to", first[0].get("ref_id"))
    if not st.get("ok"):
        print("   scroll-to:", st.get("error", {}).get("code"))
        break
    time.sleep(1.6)
    env = snap()
    if not env.get("ok"):
        break

print(f"\n{len(order)} mensajes únicos en #{hit[0]} ({time.time()-t0:.0f}s):")
for p in order[:25]:
    print("  ·", p[:170])
json.dump(order, open(os.path.join(OUT, "discord_deep.json"), "w"), ensure_ascii=False, indent=1)
