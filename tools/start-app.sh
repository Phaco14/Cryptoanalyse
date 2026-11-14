#!/usr/bin/env bash
# One-command launcher: starts the API (:3000) and the dashboard (:3001), waits
# until both answer, opens the browser, and stops both on Ctrl+C.
set -euo pipefail
cd "$(dirname "$0")/.."

export PATH="$HOME/.local/node/bin:$HOME/.bun/bin:$PATH"

API_URL="http://127.0.0.1:3000"
WEB_URL="http://localhost:3001"
NODE_BIN="$(command -v node || true)"

port_open() {
  (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null || return 1
  exec 3>&- 3<&- 2>/dev/null || true
  return 0
}

wait_port() {
  local port="$1" label="$2" i
  for i in $(seq 1 120); do
    if port_open "$port"; then
      echo "[OK] $label prêt (port $port)"
      return 0
    fi
    sleep 1
  done
  echo "[ERREUR] $label n'a pas démarré sur le port $port" >&2
  return 1
}

cleanup() {
  echo ""
  echo "[..] Arrêt de l'application"
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${WEB_PID:-}" ]] && kill "$WEB_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

if port_open 3000; then
  echo "[OK] API déjà en cours (port 3000)"
else
  echo "[..] Démarrage de l'API"
  uv run --package api-app uvicorn api.main:app --port 3000 &
  API_PID=$!
fi

wait_port 3000 "API"

if port_open 3001; then
  echo "[OK] Dashboard déjà en cours (port 3001)"
else
  echo "[..] Démarrage du dashboard"
  if [[ -z "$NODE_BIN" ]]; then
    echo "[ERREUR] Node introuvable. Installe-le :" >&2
    echo "  cd /tmp && curl -fsSL -o node.tar.xz https://nodejs.org/dist/v22.20.0/node-v22.20.0-linux-x64.tar.xz && mkdir -p ~/.local/node && tar -xJf node.tar.xz -C ~/.local/node --strip-components=1" >&2
    exit 1
  fi
  (cd apps/web && exec "$NODE_BIN" ../../node_modules/vite/bin/vite.js dev --port 3001) &
  WEB_PID=$!
fi

wait_port 3001 "Dashboard"

echo ""
echo "============================================================"
echo "  Cryptoanalyse est disponible : $WEB_URL"
echo "  Laisse cette fenêtre ouverte ; CTRL+C pour tout arrêter."
echo "============================================================"
echo ""
explorer.exe "$WEB_URL" 2>/dev/null || true

wait
