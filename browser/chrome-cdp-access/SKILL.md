---
name: chrome-cdp-access
description: "Use when you need to see/drive user's live Chrome via CDP."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [chrome, cdp, browser, macos, slack, apple-script]
    category: devops
    related_skills: [computer-use, agent-browser]
---

# Chrome CDP Access — read/drive the user's live Chrome

## When to Use

- User asks "can you see what I have open in my browser?" or wants you to read/drive THEIR tab (Slack, dashboards, logged-in apps — anything needing their session).
- You need page state, DOM, or console from a tab the user is actually viewing.
- NOT for general web automation — that goes to the headless browser tools.

User preference (11-ago-2026): when the user asks "can you see my browser tab?", do NOT default to computer_use screen-driving — the user explicitly doubts that path ("no creo que el camino adecuado sea usar computer use"). Prefer CDP/AppleScript direct access: more reliable, no window-visibility issues (cua-driver may not even see the Chrome window).

## Decision tree

1. **Read-only quick check (always works, zero setup):** AppleScript → URL + title of active tab.
2. **Full control (DOM, navigation, JS):** CDP on a SECOND Chrome instance with explicit `--user-data-dir`.

## 1. AppleScript quick check (no setup)

```applescript
osascript -e 'tell application "Google Chrome" to get {count of windows, URL of active tab of front window, title of active tab of front window}'
```

- All tabs: `tell application "Google Chrome" to get URL of every tab of every window`
- **Executing JS in the tab via AppleScript is BLOCKED by default** (error: "La ejecución de JavaScript mediante AppleScript está desactivada"). Needs a one-time user toggle: Chrome menu → Ver > Desarrollador > "Permitir JavaScript para eventos de Apple". Not settable via defaults/Preferences (no key present in profile Preferences).

## 2. Full CDP — the Chrome 136+ gotcha (CRITICAL)

### Chromium browsers that are not Chrome (Dia, Arc, Brave…)

Dia (`company.thebrowser.dia`, ArcCore over Chromium 156) **does not expose web accessibility**:
`agent-desktop` returns `Renderer did not enable accessibility activation`, even when relaunched with
`--force-renderer-accessibility` (verified 31-oct-2026). CDP does work and is the only reliable route:

```bash
# needs one browser restart; Dia restores all tabs
osascript -e 'tell application "Dia" to quit'
open -a Dia --args --remote-debugging-port=9222
curl -s http://localhost:9222/json/version        # {"Browser":"Chrome/156…","Protocol-Version":"1.3"}
curl -s http://localhost:9222/json/list | jq -r '.[] | select(.type=="page") | .title'
curl -s -X PUT "http://localhost:9222/json/new?https://www.linkedin.com/feed/"
curl -s http://localhost:9222/json/close/<id>     # close the tab you opened
```

- The scripts in this skill work unchanged: `node cdp_eval.js --match linkedin.com --js "…"`
  (override the port with `CDP_PORT`).
- `agent-desktop launch "Dia"` returns `AMBIGUOUS_TARGET`: ArcCore `Browser Helper` processes count as
  app instances. Open with `open -b company.thebrowser.dia`, then `list-windows --app Dia`.
- The `--remote-debugging-port` flag **stays active until the browser is closed**: tell the user when
  you finish (local port, but it should not stay open unnoticed).
- Quitting returns `error -128 User canceled` from AppleScript and still quits: check `pgrep -x Dia`.

**What not to do:** switch to Chrome for convenience when el operador asked for their own browser.
Their browser preference outranks the agent's comfort.

### The Chrome 136+ gotcha

**Chrome 136+ IGNORES `--remote-debugging-port` when using the default user-data-dir.** Verified on Chrome 151 (ago-2026): flag present in process args, but no listener on the port. Security change — the flag only works with an explicit `--user-data-dir`.

**Do NOT restart the user's Chrome with the flag**: the port won't open AND you disrupt their session. Instead run a SECOND Chrome instance on a COPY of their profile:

1. Tab backup + quit Chrome, wait for full exit:
   ```
   osascript -e 'tell application "Google Chrome" to get URL of every tab of every window' > ~/.hermes/chrome_tabs_backup_$(date +%Y%m%d_%H%M%S).txt
   osascript -e 'tell application "Google Chrome" to quit'
   for i in $(seq 1 25); do pgrep -x "Google Chrome" >/dev/null || break; sleep 1; done
   ```
2. Copy candidate profile(s) — caches excluded (copy while Chrome is CLOSED, sqlite locks):
   ```
   mkdir -p ~/.hermes/chrome-cdp
   rsync -a --exclude 'Cache/' --exclude 'Code Cache/' --exclude 'GPUCache/' --exclude 'Service Worker/CacheStorage' --exclude 'Service Worker/ScriptCache' <ProfileDir> ~/.hermes/chrome-cdp/
   cp "Local State" ~/.hermes/chrome-cdp/
   ```
3. Relaunch the user's normal Chrome: `open -a "Google Chrome"`
4. Launch the CDP instance (background, never exits) — **MUST include `--remote-allow-origins=*`** (see pitfall below; `launch_chrome_cdp.sh` ya lo incluye):
   ```
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --remote-allow-origins="*" --user-data-dir="$HOME/.hermes/chrome-cdp" --no-first-run --no-default-browser-check
   ```
5. Verify: `curl -s http://localhost:9222/json/version` and `curl -s http://localhost:9222/json/list` (tabs with titles + URLs).

The copied profile keeps cookies → the CDP instance is logged into the same services (Slack, etc.) and restores the user's open tabs. The user's real Chrome stays untouched.

## 3. Interacting via CDP

No Python websocket libs assumed — use Node 22+ (native WebSocket + fetch, zero deps):

```
node scripts/cdp_eval.js --match slack.com --navigate "https://app.slack.com/client/TEAM/CHANNEL" --js "document.title"
```

Finds the page tab whose URL contains `--match`, optionally navigates it, evaluates `--js`, prints the JSON value. Full usage in scripts/cdp_eval.js.

- **WebSocket 403 handshake "Rejected an incoming WebSocket connection... Use --remote-allow-origins" (Chrome 136+, verificado 13-ago-2026)**: si la instancia CDP se lanzó SIN `--remote-allow-origins=*`, TODA conexión websocket al puerto 9222 falla con 403 — incluso con `origin="chrome-devtools://devtools"` (Chrome 136+ rechaza también ese origin). curl a `/json/version` funciona (HTTP), el websocket no. Fix: matar la instancia (`kill $(lsof -ti:9222)`) y relanzarla con el flag (usar `scripts/launch_chrome_cdp.sh <url>`, que ya lo incluye; el perfil persiste).
- **Python websocket-client**: `websocket` module NO está en el python3 default (uv-managed 3.14). Usar `python3` (tiene websocket-client). Al conectar: `websocket.create_connection(ws_url, origin="chrome-devtools://devtools")` solo si la instancia tiene el flag.

## Diagnosticar "la web se ve pero nada es clickeable" (React sin hidratar)

Síntoma: el HTML renderiza perfecto (texto, estilos) pero ningún botón responde (ni cookies, ni calculadora). Casi siempre = **los chunks JS fallaron → React nunca hidrató**. Flujo de diagnóstico con CDP (probado 13-ago-2026, Next 16 dev por túnel trycloudflare):

1. Abrir pestaña nueva y probar clics + overlays con el probe:
   `python3 scripts/cdp_probe_click.py "<URL>"`
   → imprime: elementFromPoint del centro, overlays ≥90% viewport, elementos fixed, errores de consola/red (HTTP ≥400 + URLs), y resultado de click programático en botones (si `localStorage` no cambia tras click en "Aceptar", React NO está hidratado).
2. Si hay `HTTP 403` en `/_next/static/chunks/*.js` → protección anti-CSRF del dev server de Next contra el Origin del túnel → fix `allowedDevOrigins` (skill `la agencia-webapp-bootstrap`, pitfall tunnel).
3. Si hace falta el detalle de qué headers/quién responde el 403: `cdp_probe_403.py` (captura request headers del chunk + intenta body de la respuesta).
4. Para verificar scroll al cargar: navegar y leer `window.scrollY` a intervalos (debe quedarse en 0).

Los scripts viven en `scripts/cdp_probe_click.py` y `cdp_probe_403.py` (crean pestaña nueva, la cierran al terminar; no tocan las pestañas del usuario).

## Pitfalls

- **The user may be USING the CDP Chrome themselves** — it's a visible second browser on their screen. Ask before navigating/clicking/evaluating in it; if the user says stop (or is mid-task there), stop immediately and pivot to guiding them click-by-click instead (user correction 13-ago-2026: «no me toques más el chrome que lo estoy usando yo»). Read-only evals are lower risk but still visible — say what you're doing. Some users prefer doing the clicks themselves (login, org config): offer, don't assume.
- **`Network.getAllCookies` returns undefined/{} unless `Network.enable` was called on the tab first** (verified 13-ago-2026). Per-origin cookies are also readable via `document.cookie` from the page itself.
- **Logged-in SaaS tabs can 401 on their own API endpoints despite a valid UI session** — the UI session cookie is not the API token (e.g. Salesforce split-cookie model `sid`/`sid_Client` → `INVALID_SESSION_ID`). Read the error body (XML/JSON) to diagnose, then pivot to app-native auth (OAuth) instead of fetch variations. See the `salesforce-api-integration` skill.
- **The CDP instance is a SNAPSHOT, not a live mirror.** It does NOT follow the user's navigation — if they switch channels/tabs, re-navigate explicitly (ask the URL, or re-read /json/list for the current tab).
- **Two Chrome instances can't share the same profile dir** (SingletonLock). Always copy, never point at the live profile.
- The CDP Chrome shows the "controlled by automated software" bar and may appear in the Dock — tell the user; offer to kill it when done.
- Kill the CDP instance via `lsof -ti:9222` — never `pkill -f Chrome` (kills the user's real browser too).
- Slack URLs don't reveal channel names (`client/TEAM/CHANNELID`) — read the tab title for the name (e.g. "genelal (Canal) - la agencia - Slack").
- Profile detection: session files (Current Session/Last Session) are snappy-compressed (grep finds no URLs) and cookies are app-bound encrypted (sqlite COUNT returns nothing). Use Local State → profile.info_cache names (e.g. "la agencia.com") + AppleScript tab titles instead.
- cua-driver (computer_use) may not SEE the Chrome window at all (list_windows shows only other apps) — another reason to prefer CDP/AppleScript for browser tabs.
- **Profile picker on launch** ("¿Quién usa Chrome?" even though `Default/` exists): relaunch the CDP instance with `--profile-directory=Default` (Chrome 151 shows the picker when the user-data-dir contains several profile dirs). Verified 12-ago-2026.
- **cdp_eval.js evaluates synchronously**: a `--js` expression returning a Promise prints `{}` and `setTimeout`-based async JS doesn't wait. For fetch/await/waits write a one-off script using `Runtime.evaluate` + `awaitPromise:true` (pattern: `sales-navigator` skill scripts/cdp_fetch.js).
- **~64KB caps, two of them (verified Chrome 151)**: (1) `Runtime.evaluate` with `returnByValue` silently truncates strings > ~65536 chars — store the payload on `window.__x` and read it back in slices of ≤50000 chars (each slice under the cap); (2) the terminal's stdout also truncates at ~64KB when piping `node ... | python3` — have the script `fs.writeFileSync` the body to a temp file and read the file from Python. Symptom of either cap: JSON parse errors at column ~65xxx ("Unterminated string").
- **React/SPA inputs ignore synthetic events**: `el.value = x; el.dispatchEvent(new Event('input'))` does NOT trigger React autocompletes (e.g. LinkedIn location filter). Use CDP `Input.dispatchKeyEvent` per character or `Input.insertText` (helpers: `sales-navigator` skill scripts/cdp_ui.js).
- **No screenshot support** in cdp_eval.js: use a small one-off script with `Page.captureScreenshot` (`sales-navigator` skill scripts/cdp_shot.js) when DOM text and vision disagree.
- Driving LinkedIn Sales Navigator (searches, internal API, lead extraction): see the `sales-navigator` skill.

## Files

- scripts/cdp_eval.js — generic Node CDP client (find tab, navigate, eval JS)
- scripts/cdp_do.js — chained steps on one tab: `js:` / `insert:` (Input.insertText) / `key:` / `clickxy:` / `upload:` / `wait:` — needed for typeaheads and ProseMirror editors where synthetic events are ignored
- scripts/cdp_upload.js — intercepts the native file chooser (`Page.setInterceptFileChooserDialog`) and delivers a file; retries the click as real mouse input for user activation
- scripts/cdp_drop.js — `Input.dispatchDragEvent` (dragEnter → dragOver → drop) with `files`, for drop zones that never expose an `input[type=file]`
- scripts/cdp_probe_click.py — probe de clics/overlays/errores (pestaña nueva; ver sección diagnóstico)
- scripts/cdp_probe_403.py — captura headers + body de respuestas 4xx de recursos
- scripts/launch_chrome_cdp.sh — lanza/reutiliza el Chrome CDP con los flags correctos (incl. --remote-allow-origins=*)
- references/macos-live-chrome-cdp.md — worked example: exact commands, diagnosis, Slack message extraction
