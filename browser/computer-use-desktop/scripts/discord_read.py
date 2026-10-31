#!/usr/bin/env python3
"""Navega y lee canales de Discord de escritorio con agent-desktop (solo lectura).

Uso:
  python3 discord_read.py list                 # canales visibles
  python3 discord_read.py read "<canal>" [n]   # abre el canal y lee los últimos n mensajes
  python3 discord_read.py tour a,b,c           # recorre varios canales y resume

Los mensajes salen del `description` de cada `article`, que Discord ya compone como
"autor Etiqueta… , texto , fecha". No se pulsa nada más y no se envía nada.
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
FORBIDDEN = ("ventas-y-cuentas",)


def run(*args, timeout=90):
    p = subprocess.run([BIN, *args], capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": {"code": "PARSE", "message": (p.stdout or p.stderr)[:160]}}


def walk(node):
    if isinstance(node, dict):
        yield node
        for c in node.get("children") or []:
            yield from walk(c)


def snap():
    return run("snapshot", "--app", APP, "-i", "--compact", "--timeout-ms", "30000")


def channels(env):
    out = []
    for n in walk((env.get("data") or {}).get("tree")):
        name = str(n.get("name") or "")
        if n.get("role") == "link" and "(canal de texto)" in name:
            out.append({
                "nombre": name.split(" (canal de texto)")[0],
                "estado": "privado" if "Canal privado" in name else "abierto",
                "ref": n.get("ref_id"),
            })
    return out


def posts(env):
    rows = []
    for n in walk((env.get("data") or {}).get("tree")):
        if n.get("role") != "article":
            continue
        raw = str(n.get("description") or n.get("name") or "").strip()
        if not raw:
            continue
        parts = [p.strip() for p in raw.split(" , ")]
        # el último trozo suele ser la fecha; el primero, autor + etiquetas
        fecha = parts[-1] if parts and any(ch.isdigit() for ch in parts[-1]) else ""
        cuerpo = " , ".join(parts[1:-1]) if fecha else " , ".join(parts[1:])
        rows.append({"autor": parts[0] if parts else "", "texto": cuerpo, "fecha": fecha})
    return rows


def goto(nombre, env=None):
    env = env or snap()
    if not env.get("ok"):
        return None, f"captura falló: {env.get('error', {}).get('code')}"
    hit = next((c for c in channels(env) if nombre.lower() in c["nombre"].lower()), None)
    if not hit:
        return None, "canal no encontrado"
    if any(f in hit["nombre"].lower() for f in FORBIDDEN):
        return None, "canal excluido por regla del operador"
    cl = run("click", hit["ref"])
    time.sleep(2)
    env2 = snap()
    return env2, f"{hit['nombre']} ({hit['estado']}) click={cl.get('ok')}"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    env = snap()
    if not env.get("ok"):
        print("no puedo capturar Discord:", env.get("error", {}).get("code"))
        return 1

    if cmd == "list":
        for c in channels(env):
            print(f"  [{c['estado']:8}] {c['nombre']}")
        return 0

    if cmd == "read":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        env2, info = goto(sys.argv[2], env)
        if not env2:
            print(info)
            return 1
        print("abierto:", info, "| refs:", env2["data"].get("ref_count"))
        rows = posts(env2)
        print(f"{len(rows)} mensajes en pantalla; últimos {min(n, len(rows))}:")
        for r in rows[-n:]:
            print(f"  [{r['fecha']}] {r['autor'][:28]:30} {r['texto'][:120]}")
        json.dump(rows, open(os.path.join(OUT, "discord_last.json"), "w"), ensure_ascii=False, indent=1)
        return 0

    if cmd == "tour":
        for nombre in sys.argv[2].split(","):
            env2, info = goto(nombre.strip(), env)
            if not env2:
                print(f"{nombre}: {info}")
                continue
            rows = posts(env2)
            print(f"{info} → {len(rows)} mensajes; último: {rows[-1]['texto'][:90] if rows else '—'}")
            env = env2
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
