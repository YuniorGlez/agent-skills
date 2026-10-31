#!/bin/bash
# Lanza Chrome con remote debugging y perfil dedicado para Hermes (tl;dv + web tasks).
# Uso: launch_chrome_cdp.sh [url]
# El perfil se guarda en ~/.hermes/chrome-cdp/ -> la sesión de tl;dv persiste entre lanzamientos.
set -e

PROFILE="$HOME/.hermes/chrome-cdp"
PORT="${CDP_PORT:-9222}"
URL="${1:-https://tldv.io/app/meetings}"

# Si ya hay un Chrome en el puerto, no duplicar
if curl -s "http://localhost:$PORT/json/version" >/dev/null 2>&1; then
  echo "Chrome CDP ya activo en :$PORT"
  # Abrir pestaña con la URL pedida
  curl -s "http://localhost:$PORT/json/new?$URL" >/dev/null 2>&1 || true
  exit 0
fi

mkdir -p "$PROFILE"
echo "Lanzando Chrome CDP en :$PORT con perfil $PROFILE ..."
nohup "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins="*" \
  --user-data-dir="$PROFILE" \
  --no-first-run \
  --no-default-browser-check \
  --disable-features=Translate \
  --window-size=1440,900 \
  "$URL" >/tmp/chrome-cdp.log 2>&1 &

# Esperar a que el puerto responda (máx 15s)
for i in $(seq 1 15); do
  if curl -s "http://localhost:$PORT/json/version" >/dev/null 2>&1; then
    echo "Chrome CDP listo tras ${i}s: $(curl -s http://localhost:$PORT/json/version | /opt/homebrew/bin/python3.9 -c 'import sys,json;print(json.load(sys.stdin)["Browser"])' 2>/dev/null || echo ok)"
    exit 0
  fi
  sleep 1
done
echo "ERROR: Chrome CDP no respondió en :$PORT" >&2
exit 1
