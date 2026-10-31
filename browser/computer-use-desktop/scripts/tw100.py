#!/usr/bin/env python3
"""Lee N posts del muro de X en la app Twitter.app usando SOLO agent-desktop.

Uso: python3 tw100.py [objetivo] [max_iter]
Deja los posts en out/tw_posts.json y un resumen por stdout.
"""
import json
import os
import subprocess
import sys
import time

BIN = os.path.expanduser("~/.bun/bin/agent-desktop")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
APP = "Twitter"
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 100
MAX_ITER = int(sys.argv[2]) if len(sys.argv) > 2 else 40


def run(*args, timeout=90):
    p = subprocess.run([BIN, *args], capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": {"code": "PARSE", "message": (p.stdout or p.stderr)[:200]}}


def walk(node, acc):
    if isinstance(node, dict):
        acc.append(node)
        for child in node.get("children") or []:
            walk(child, acc)


def flat(env):
    acc = []
    walk((env.get("data") or {}).get("tree"), acc)
    return acc


def extract(env):
    """Devuelve lista de posts {autor, handle, tiempo, texto} de los articles visibles."""
    nodes = flat(env)
    arts = [n for n in nodes if n.get("role") == "article"]
    posts = []
    for art in arts:
        sub = []
        walk(art, sub)
        links = [n for n in sub if n.get("role") == "link"]
        texts = [n for n in sub if n.get("role") == "statictext" and (n.get("value") or n.get("name"))]
        author = links[0].get("name", "").split("\n")[0] if links else ""
        handle = next((l.get("name") for l in links if str(l.get("name", "")).startswith("@")), "")
        when = next((l.get("description") for l in links if str(l.get("description", "")).startswith("Hace")), "")
        body = max((t.get("value") or t.get("name") or "" for t in texts), key=len, default="")
        if body:
            posts.append({"autor": author, "handle": handle, "cuando": when, "texto": body})
    return posts


def main():
    seen = {}
    order = []
    stats = {"iteraciones": 0, "snapshots_bytes": 0, "errores": 0, "t0": time.time()}
    env = run("snapshot", "--app", APP, "--compact", "--timeout-ms", "30000")
    if not env.get("ok"):
        print("no puedo capturar la app:", env.get("error", {}).get("code"))
        return 1
    scroll_ref = next((n.get("ref_id") for n in flat(env) if n.get("role") == "scrollarea"), None)
    if not scroll_ref:
        print("no encuentro scrollarea")
        return 1
    print(f"scrollarea = {scroll_ref}")

    for it in range(MAX_ITER):
        stats["iteraciones"] = it + 1
        stats["snapshots_bytes"] += len(json.dumps(env, ensure_ascii=False))
        new = 0
        for p in extract(env):
            key = (p["handle"], p["texto"][:140])
            if key not in seen:
                seen[key] = p
                order.append(p)
                new += 1
        print(f"  iter {it+1:2d}: articles={len(extract(env)):2d} nuevos={new:2d} total={len(order):3d} "
              f"({time.time()-stats['t0']:.0f}s)")
        if len(order) >= TARGET:
            break
        sc = run("scroll", scroll_ref, "--direction", "down", "--amount", "8")
        if not sc.get("ok"):
            stats["errores"] += 1
            print("   scroll falló:", sc.get("error", {}).get("code"))
            time.sleep(1.5)
        time.sleep(1.8)
        env = run("snapshot", "--app", APP, "--compact", "--timeout-ms", "30000")
        if not env.get("ok"):
            stats["errores"] += 1
            print("   snapshot falló:", env.get("error", {}).get("code"))
            break

    stats["posts"] = len(order)
    stats["segundos"] = round(time.time() - stats["t0"], 1)
    stats["mb_leidos"] = round(stats["snapshots_bytes"] / 1e6, 2)
    json.dump({"stats": stats, "posts": order[:TARGET]}, open(os.path.join(OUT, "tw_posts.json"), "w"),
              ensure_ascii=False, indent=1)
    print("\nresumen:", json.dumps(stats, ensure_ascii=False))
    print(f"guardados {min(len(order), TARGET)} posts en out/tw_posts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
