#!/usr/bin/env python3
"""Captura request headers + body 403 de chunks JS en el túnel."""
import json
import time
import urllib.parse
import urllib.request

import websocket

PORT = 9222
BASE = f"http://localhost:{PORT}"
URL = "https://tions-becomes-affecting-zus.trycloudflare.com/"

req = urllib.request.Request(f"{BASE}/json/new?{urllib.parse.quote(URL, safe='')}", method="PUT")
with urllib.request.urlopen(req, timeout=10) as r:
    tab = json.loads(r.read())
ws_url = tab["webSocketDebuggerUrl"]
tab_id = tab["id"]

ws = websocket.create_connection(ws_url, timeout=30, origin="chrome-devtools://devtools")
mid = 0
events = []
req_headers = {}
req_ids = {}


def send(method, params=None):
    global mid
    mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == mid:
            return msg.get("result", {})
        events.append(msg)


send("Network.enable")
send("Page.enable")
send("Page.navigate", {"url": URL})
time.sleep(8)
# drenar buffer: un comando extra fuerza leer todos los eventos pendientes
send("Runtime.evaluate", {"expression": "1+1", "returnByValue": True})

for ev in events:
    p = ev.get("params", {})
    m = ev.get("method")
    if m == "Network.requestWillBeSent":
        if "static/chunks" in p.get("request", {}).get("url", ""):
            req_headers[p.get("requestId")] = p.get("request", {}).get("headers", {})
            req_ids[p.get("requestId")] = p.get("request", {}).get("url", "")[:120]
    elif m == "Network.responseReceived":
        rid = p.get("requestId")
        if rid in req_headers and p.get("response", {}).get("status", 0) >= 400:
            status = p.get("response", {}).get("status")
            url = req_ids.get(rid, "?")
            print(f"=== 403 en: {url}")
            hdrs = req_headers[rid]
            interesting = {k: v for k, v in hdrs.items() if k.lower() in (
                "accept", "accept-encoding", "cache-control", "if-none-match",
                "if-modified-since", "referer", "sec-fetch-dest", "sec-fetch-mode",
                "sec-fetch-site", "pragma", "cookie", "user-agent", "origin",
            )}
            print("REQUEST HEADERS:", json.dumps(interesting, indent=1))
            # intentar leer el body de la respuesta
            try:
                body = send("Network.getResponseBody", {"requestId": rid})
                print("RESPONSE BODY:", json.dumps(body.get("body", ""))[:600])
            except Exception as e:
                print("body no disponible:", str(e)[:120])

ws.close()
try:
    urllib.request.urlopen(f"{BASE}/json/close/{tab_id}", timeout=5)
except Exception:
    pass
