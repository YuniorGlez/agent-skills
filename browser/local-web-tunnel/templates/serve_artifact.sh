#!/bin/bash
# Servir un artefacto web local + túnel trycloudflare persistente (launchd).
# Copiar y ajustar DIR y PORT. Ver skill local-web-tunnel (pitfalls: PATH de
# launchd es mínimo → rutas absolutas; el job debe quedarse vivo con el loop).
DIR="/ruta/al/artefacto"
PORT=8085
PYTHON=/usr/bin/python3
CLOUDFLARED=/opt/homebrew/bin/cloudflared
LOG_DIR="$HOME/.hermes/logs"
LOG="$LOG_DIR/tunnel.log"
mkdir -p "$LOG_DIR"

# 1) HTTP server estático (solo localhost)
if ! lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  cd "$DIR" || exit 1
  nohup "$PYTHON" -m http.server "$PORT" --bind 127.0.0.1 >>"$LOG_DIR/http.log" 2>&1 &
fi

# 2) Túnel trycloudflare (URL pública; el hostname queda en el log)
if ! pgrep -f "cloudflared tunnel --url http://127.0.0.1:$PORT" >/dev/null 2>&1; then
  nohup "$CLOUDFLARED" tunnel --url "http://127.0.0.1:$PORT" >>"$LOG" 2>&1 &
fi

# Mantener el job vivo (launchd KeepAlive + hijos en background)
while true; do
  sleep 30
done
