#!/bin/bash
# Auditoría axe-core (agent-browser) de TODAS las rutas, con login opcional, y resumen por ruta.
# Deja un JSON por ruta en el directorio de salida: es la prueba del antes y del después.
#
# Uso:
#   BASE=http://localhost:3000 OUT=/tmp/a11y \
#   LOGIN_PATH=/login A11Y_USER=tu@email A11Y_PASS=clave \
#   RUTAS="/ /login /mapa /glosario" bash scripts/audit-axe.sh
#
# Sin A11Y_USER/A11Y_PASS solo audita páginas públicas. Comprueba en cada ruta que sigues
# autenticado (LANDMARK, por defecto «aside») o estarás auditando el login creyendo que auditas la app.
set -u
BASE=${BASE:-http://localhost:3000}
OUT=${OUT:-/tmp/a11y}
LOGIN_PATH=${LOGIN_PATH:-/login}
A11Y_USER=${A11Y_USER:-}
A11Y_PASS=${A11Y_PASS:-}
LANDMARK=${LANDMARK:-aside}
RUTAS=${RUTAS:-/}
mkdir -p "$OUT"
agent-browser close --all >/dev/null 2>&1
sleep 2

if [ -n "$A11Y_USER" ] && [ -n "$A11Y_PASS" ]; then
  agent-browser open "$BASE$LOGIN_PATH" >/dev/null 2>&1
  for i in 1 2 3 4 5; do
    sleep 3
    # El fetch tiene que ocurrir con la página ya cargada: si no, devuelve ERR (no 200) y la tanda sale pública.
    code=$(agent-browser eval "fetch('$LOGIN_PATH',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:'$A11Y_USER',password:'$A11Y_PASS'})}).then(r=>r.status).catch(()=>'ERR')" 2>&1 | tail -1 | tr -d '"')
    echo "login intento $i -> $code"
    [ "$code" = "200" ] && break
  done
fi

for p in $RUTAS; do
  name=$(echo "$p" | tr '/' '_'); name="${name:-home}"
  agent-browser open "$BASE$p" >/dev/null 2>&1
  sleep 1
  estado=$(agent-browser eval "document.querySelector('$LANDMARK') ? 'APP' : 'PUBLICA'" 2>&1 | tail -1 | tr -d '"')
  agent-browser a11y "$BASE$p" --tags wcag2a,wcag2aa --json > "$OUT/$name.json" 2>/dev/null
  echo "$p ($estado)"
done
agent-browser close --all >/dev/null 2>&1

python3 - "$OUT" <<'EOF'
import json, sys, glob, os
d = sys.argv[1]
total = 0
for f in sorted(glob.glob(os.path.join(d, "*.json"))):
    try: data = json.load(open(f)).get("data", {})
    except Exception as e: print(f"{os.path.basename(f)}: ERROR {e}"); continue
    v = data.get("violations", []); inc = data.get("incomplete", [])
    total += len(v)
    print(f"\n=== {os.path.basename(f)}  violations={len(v)} passes={data.get('counts',{}).get('passes')} incomplete={len(inc)}")
    for x in v:
        print(f"  VIOLACION [{x.get('impact')}] {x['id']} ({len(x['nodes'])} nodos)")
        for n in x["nodes"][:3]:
            print("      ", n["target"], (n.get("failureSummary") or "").split("\n")[0][:110])
    for x in inc:
        print(f"  (revisar: axe no lo puede medir) {x['id']} ({len(x['nodes'])} nodos)")
print(f"\nTOTAL violaciones: {total}")
sys.exit(1 if total else 0)
EOF
