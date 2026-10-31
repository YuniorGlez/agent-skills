#!/usr/bin/env bash
# scan_repo_risks.sh — escaneo SOLO-LECTURA de patrones de riesgo en repos clonados.
# Uso: scan_repo_risks.sh <dir1> [dir2 ...]
# Cada match es un CANDIDATO: verificar SIEMPRE el contexto antes de declarar
# riesgo (falsos positivos comunes: "searchModelType" para chmod, fixtures de
# test con sk- falsos, base64 de imágenes, exec de git local, telemetría
# legítima en un EDR). NO ejecutar nada de lo que se encuentre.
set -u

PATTERNS=(
  'curl.*sh'
  'wget.*sh'
  'eval\('
  'exec\('
  'os\.system'
  'base64'
  'sk-[a-zA-Z0-9]'
  'api[_-]?key'
  'AKIA[0-9A-Z]'
  'ghp_[a-zA-Z0-9]'
  'posthog'
  'segment'
  'analytics'
  'sentry'
  'chmod'
  'subprocess'
  'telemetry'
)
EXTS=(--include='*.py' --include='*.sh' --include='*.js' --include='*.ts'
      --include='*.tsx' --include='*.go' --include='*.java' --include='*.rs'
      --include='*.json' --include='*.yml' --include='*.yaml' --include='*.toml'
      --include='Makefile' --include='Taskfile*' --include='Dockerfile' --include='*.md')
EXCLUDE=(--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist
         --exclude-dir=build --exclude-dir=target --exclude-dir=.venv --exclude-dir=venv)

for dir in "$@"; do
  [ -d "$dir" ] || { echo "SKIP $dir (no es directorio)"; continue; }
  echo "===== $dir ====="
  for p in "${PATTERNS[@]}"; do
    hits=$(grep -rInE "${EXCLUDE[@]}" "${EXTS[@]}" "$p" "$dir" 2>/dev/null | head -12)
    if [ -n "$hits" ]; then
      echo "--- [$p]"
      echo "$hits"
    fi
  done
done
echo "DONE — cada match es CANDIDATO: verificar contexto antes de declarar riesgo."
