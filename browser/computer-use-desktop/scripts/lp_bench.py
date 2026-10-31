#!/usr/bin/env python3
"""Benchmark Lightpanda vs Chrome headless: tiempo, memoria y contenido por URL."""
import json
import os
import re
import subprocess
import sys
import time

LP = os.path.expanduser("./artifacts/lightpanda")
URLS = [
    ("example", "https://example.com"),
    ("hn", "https://news.ycombinator.com"),
    ("the agency", "https://the agency.com"),
    ("informe", "https://example.com/"),
    ("booking", "https://www.booking.com"),
    ("linkedin", "https://www.linkedin.com/"),
    ("x", "https://x.com/lightpanda_io"),
]

MAX_RSS = re.compile(r"^\s*(\d+)\s+maximum resident set size", re.M)


def run(cmd, timeout=90):
    t0 = time.time()
    try:
        p = subprocess.run(["/usr/bin/time", "-l"] + cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "TIMEOUT", "secs": round(time.time() - t0, 2)}
    secs = time.time() - t0
    err = p.stderr.decode(errors="replace")
    m = MAX_RSS.search(err)
    rss = int(m.group(1)) if m else None
    return {
        "ok": p.returncode == 0,
        "code": p.returncode,
        "secs": round(secs, 2),
        "rss_mb": round(rss / 1048576, 1) if rss else None,
        "bytes": len(p.stdout),
        "head": p.stdout[:160].decode(errors="replace").replace("\n", " "),
        "err": err.strip().split("\n")[-1][:140] if err.strip() else "",
    }


engine = sys.argv[1] if len(sys.argv) > 1 else "lightpanda"
CHROME = os.environ.get("CHROME_BIN", "")

rows = []
for label, url in URLS:
    if engine == "lightpanda":
        r = run([LP, "fetch", url, "--dump", "markdown"], timeout=90)
    else:
        if not CHROME:
            print("falta CHROME_BIN")
            sys.exit(2)
        r = run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=8000",
                 "--dump-dom", url], timeout=120)
    r.update({"engine": engine, "site": label, "url": url})
    rows.append(r)
    print(f"{label:10} {r.get('secs'):>6}s  rss={r.get('rss_mb')}MB  bytes={r.get('bytes'):>7}  "
          f"{'ok' if r.get('ok') else 'FALLO ' + str(r.get('code'))}  {r.get('err','')[:60]}")

out = os.path.expanduser(f"./artifacts/bench_{engine}.json")
json.dump(rows, open(out, "w"), ensure_ascii=False, indent=1)
print("guardado:", out)
