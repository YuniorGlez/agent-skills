---
name: local-web-tunnel
description: "Expose local web artifacts publicly: cloudflared + launchd."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [tunnel, cloudflared, trycloudflare, launchd, mobile, http-server]
---

# Artefacto web local → túnel público persistente (cloudflared + launchd)

## When to Use
el operador necesita ver un artefacto web local (dashboard HTML, demo, landing) desde el móvil — p.ej. el navegador interno de Orca, donde no puede tocar ni refrescar HTML — o compartir un demo por Discord/WhatsApp. Patrón de casa: HTTP local + túnel trycloudflare (sin login, gratis) + agente launchd para que sobreviva a la sesión de Hermes y a reinicios del Mac (vuelve al hacer login).

## Pasos
1. Comprobar `which cloudflared` (brew: /opt/homebrew/bin/cloudflared) y elegir un puerto libre: `lsof -i :8085 -sTCP:LISTEN`.
2. Servir el artefacto SOLO en localhost: `python3 -m http.server PORT --bind 127.0.0.1` desde su directorio. El puerto no se expone a la LAN; lo único público es el túnel.
3. Túnel: `cloudflared tunnel --url http://127.0.0.1:PORT` — la URL trycloudflare aparece en stdout/log en ~5-10s. Extraerla con `grep -o "https://[a-z0-9-]*\.trycloudflare\.com" <log>`.
4. Persistencia: agente launchd con KeepAlive + wrapper idempotente (plantillas en `templates/`). Arrancar con `launchctl load -w ~/Library/LaunchAgents/<label>.plist`; parar con `launchctl unload` (matar cloudflared/http.server a mano si quedan).
5. Verificar SIEMPRE con curl: 200 en `http://127.0.0.1:PORT/index.html` y 200 en la URL pública. Confirmar con `launchctl list | grep <label>` (PID vivo).

## Acceso privado desde el móvil: `tailscale serve` (preferido si hay tailnet)

`trycloudflare` publica al mundo entero y la URL cambia en cada relanzamiento. Si el artefacto
es algo con poder real (un harness de agentes que ejecuta bash, un panel de administración),
lo correcto es **el tailnet**: WireGuard cifrado, URL fija, cero exposición a Internet.

```bash
tailscale up                                            # si está 'Stopped' (el CLI habla con la app GUI)
tailscale serve --bg --http=80 3080                     # http://<host>.<tailnet>.ts.net -> 127.0.0.1:3080
tailscale serve --bg --http=80 --set-path /login 3081   # ruta extra en el mismo host
tailscale serve status                                   # debe decir "(tailnet only)"; `funnel` = público, NO
tailscale ip -4                                          # probar: curl -H "Host: <host>.<tailnet>.ts.net" http://<ip>/
```

Pitfalls medidos (Tailscale 1.96.2, macOS, GUI app):

- **`--set-path` sin `--http=<puerto>` explícito se cuelga en silencio** (ni error ni salida;
  muere por timeout a los 180 s). Con `--http=80 --set-path /login` funciona a la primera.
- **Fence de Host**: servidores con defensa anti-rebinding (dsh, p.ej.) exigen
  `--trusted-host <host>.<tailnet>.ts.net` y opcionalmente `--public-url http://<host>.<tailnet>.ts.net`.
  Sin eso el UI carga pero `/api` devuelve 401/403.
- **HTTPS no viene de serie**: `tailscale cert` responde `500 your Tailscale account does not support
  getting TLS certs` hasta habilitar *HTTPS Certificates* en `login.tailscale.com/admin/dns`. Sobre http
  todo funciona (el cifrado lo pone WireGuard) pero el manifest PWA no instala del todo: iOS acepta
  "Añadir a pantalla de inicio", sin service worker ni fullscreen.
- Los peers se listan con `tailscale status`; un móvil "offline, last seen 209d ago" sigue registrado:
  basta encender la app, no hay que reinstalar ni reautenticar.

## Token de un solo uso por proceso → redirector estable `/login`

Cuando el servidor imprime un token al arrancar (`dsh web: http://…/?token=…`) y lo acuña de nuevo
en **cada** reinicio, el enlace que mandas al móvil caduca al primer crash. La cookie de sesión de dsh
sí sobrevive (se firma con una credencial persistida en su credential store; 30 días), pero un
dispositivo nuevo necesita un token vivo. Patrón que lo arregla:

1. Un wrapper que **captura el token del stdout** mientras el servidor corre (pipe + `sed`), y lo deja
   en `~/.hermes/dsh/token` (600). Con `exec` no puedes leer la salida; el pipe mantiene vivo el job.
2. Un redirector de 20 líneas (`http.server` en 127.0.0.1:3081) que responde 302 a `/?token=<fichero>`.
3. Publicarlo con `--set-path /login` y dar al usuario **solo** `http://<host>.<tailnet>.ts.net/login`.
4. launchd: dos agentes `KeepAlive` (servidor y redirector). El wrapper **re-registra ambas rutas de
   `tailscale serve` en cada arranque**; si no, un reset del serve deja la raíz viva y `/login` muerto.

Verificación que vale (no `curl` a pelo): Playwright con contexto limpio → `goto /login` → 200, título
correcto, y la recarga en `/` sigue autenticada; luego `kill` del proceso, esperar el relanzado de
launchd y repetir: el token cambia, la URL no.

Ficheros reales (caso dsh): `scripts/serve_dsh_web.sh`,
`scripts/dsh_login_redirect.py`, los plist de launchd del servidor y del redirector.

## Pitfalls (aprendidos con com.la agencia.dashboard-tunnel, 14-ago-2026)
- **PATH mínimo de launchd**: los LaunchAgents corren con PATH `/usr/bin:/bin:/usr/sbin:/sbin` → `cloudflared` (brew) NO se encuentra. Doble fix: rutas absolutas dentro del wrapper (PYTHON=/usr/bin/python3, CLOUDFLARED=/opt/homebrew/bin/cloudflared) + `<key>EnvironmentVariables</key><dict>PATH=/opt/homebrew/bin:...` en el plist.
- **El job debe quedarse VIVO**: si el wrapper hace `exit 0`, launchd con KeepAlive lo relanza en bucle y los hijos en background (nohup &) se matan o degradan (síntoma: `launchctl list` muestra PID `-`, logs vacíos, nada escucha). Terminar el wrapper con `while true; do sleep 30; done`.
- **URL efímera**: trycloudflare genera un hostname NUEVO si cloudflared se relanza (crash o reinicio del Mac). La URL activa queda siempre en el log del wrapper; avisar al usuario de que puede cambiar y cómo recuperarla.
- **Idempotencia**: antes de lanzar, comprobar `lsof -i :PORT` y `pgrep -f "cloudflared tunnel --url http://127.0.0.1:PORT"` — los relanzamientos de KeepAlive no deben duplicar procesos.
- **Móvil**: si el artefacto tiene auto-refresh (setInterval + location.reload()), funciona en el móvil sin interacción — clave cuando el navegador del usuario (Orca) no recarga a mano.
- Ficheros de casos reales: `~/.hermes/scripts/serve_dashboard.sh` + `~/Library/LaunchAgents/com.la agencia.dashboard-tunnel.plist` (dashboard sprint 30d, :8085) y `~/.hermes/scripts/serve_operator_dashboard.sh` + `~/Library/LaunchAgents/com.la agencia.operator-dashboard-tunnel.plist` (dashboard operador la agencia, :8090, servido desde `~/.hermes/reports/operator_dashboard/`).

## Plantillas
- `templates/serve_artifact.sh` — wrapper genérico (http.server + cloudflared + loop, idempotente)
- `templates/tunnel-agent.plist` — plist launchd (KeepAlive + PATH)
