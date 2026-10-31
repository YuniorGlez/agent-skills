#!/usr/bin/env python3
"""CDP probe: abre la URL en pestaña nueva, captura errores de consola,
comprueba overlays que bloquean clics y prueba clics reales (cookies + calculadora)."""
import json
import sys
import time
import urllib.parse
import urllib.request

import websocket

PORT = 9222
BASE = f"http://localhost:{PORT}"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3058/"

req = urllib.request.Request(f"{BASE}/json/new?{urllib.parse.quote(URL, safe='')}", method="PUT")
with urllib.request.urlopen(req, timeout=10) as r:
    tab = json.loads(r.read())
ws_url = tab["webSocketDebuggerUrl"]
tab_id = tab["id"]

ws = websocket.create_connection(ws_url, timeout=30, origin="chrome-devtools://devtools")
mid = 0
events = []


def send(method, params=None):
    global mid
    mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == mid:
            return msg.get("result", {})
        events.append(msg)


send("Runtime.enable")
send("Page.enable")
send("Log.enable")
send("Network.enable")
send("Page.navigate", {"url": URL})
time.sleep(8)

probe = """
(() => {
  const out = {};
  const vw = innerWidth, vh = innerHeight;
  const center = document.elementFromPoint(vw/2, vh/2);
  out.center = center ? center.tagName + '.' + String(center.className||'').slice(0,80) : null;
  out.bigOverlays = [...document.querySelectorAll('*')].filter(e => {
    const r = e.getBoundingClientRect();
    return r.width >= vw*0.9 && r.height >= vh*0.9;
  }).slice(0,12).map(e => {
    const cs = getComputedStyle(e);
    return e.tagName + '.' + String(e.className||'').slice(0,50) + ' | pos=' + cs.position + ' z=' + cs.zIndex + ' pe=' + cs.pointerEvents;
  });
  out.fixed = [...document.querySelectorAll('*')].filter(e => getComputedStyle(e).position === 'fixed').slice(0,15).map(e => {
    const cs = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    return e.tagName + '.' + String(e.className||'').slice(0,50) + ' | z=' + cs.zIndex + ' rect=' + Math.round(r.width) + 'x' + Math.round(r.height) + ' pe=' + cs.pointerEvents;
  });
  out.h1 = document.querySelector('h1') ? document.querySelector('h1').innerText : null;
  out.ready = document.readyState;
  return out;
})()
"""
res = send("Runtime.evaluate", {"expression": probe, "returnByValue": True})
print("PROBE:", json.dumps(res.get("result", {}).get("value"), ensure_ascii=False, indent=1))

errs = []
for ev in events:
    m = ev.get("method")
    if m == "Network.responseReceived":
        resp = ev.get("params", {}).get("response", {})
        status = resp.get("status", 0)
        if status >= 400:
            errs.append(
                f"HTTP {status}: {resp.get('url', '')[:140]}"
            )
    elif m == "Network.loadingFailed":
        errs.append(
            "NETFAIL: " + str(ev.get("params", {}).get("errorText", ""))[:120]
        )
    elif m == "Runtime.exceptionThrown":
        d = ev.get("params", {}).get("exceptionDetails", {})
        desc = json.dumps(d.get("exception", {}).get("description", ""))[:300]
        errs.append("EXC: " + json.dumps(d.get("text", "")) + " " + desc)
    elif m == "Log.entryAdded":
        e = ev.get("params", {}).get("entry", {})
        if e.get("level") in ("error", "warning"):
            errs.append(e["level"].upper() + ": " + str(e.get("text", ""))[:300])
    elif m == "Runtime.consoleAPICalled" and ev.get("params", {}).get("type") == "error":
        args = ev.get("params", {}).get("args", [])
        errs.append("CONSOLE: " + json.dumps([a.get("value") for a in args])[:300])
print("ERRORS:", json.dumps(errs, ensure_ascii=False)[:1800] if errs else "ninguno")

click = """
(() => {
  const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Aceptar');
  if (!b) return 'no-accept-button';
  const r = b.getBoundingClientRect();
  const top = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);
  b.click();
  return 'clicked; localStorage=' + (localStorage.getItem('cookie-consent') || 'null') + '; topAtButton=' + (top ? top.tagName + '.' + String(top.className||'').slice(0,60) : 'none');
})()
"""
res = send("Runtime.evaluate", {"expression": click, "returnByValue": True})
print("ACCEPT:", res.get("result", {}).get("value"))
time.sleep(1.2)
banner = send(
    "Runtime.evaluate",
    {
        "expression": "(() => { const el = [...document.querySelectorAll('div')].find(e => { const r = e.getBoundingClientRect(); return r.top > innerHeight*0.5 && getComputedStyle(e).position === 'fixed' && r.height < 300; }); return el ? 'banner-sigue' : 'banner-oculto'; })()",
        "returnByValue": True,
    },
)
print("BANNER:", banner.get("result", {}).get("value"))

click2 = """
(() => {
  const b = [...document.querySelectorAll('button')].find(x => x.textContent.includes('Pro') && x.getAttribute('aria-pressed') !== null);
  if (!b) return 'no-pack-button';
  b.click();
  return 'clicked pack Pro; aria-pressed=' + b.getAttribute('aria-pressed');
})()
"""
res = send("Runtime.evaluate", {"expression": click2, "returnByValue": True})
print("PACKCLICK:", res.get("result", {}).get("value"))

ws.close()
try:
    urllib.request.urlopen(f"{BASE}/json/close/{tab_id}", timeout=5)
except Exception:
    pass
