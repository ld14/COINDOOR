#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf '%s\n' "Falta '$1'. Instalalo y volvé a ejecutar este script." >&2
    exit 1
  fi
}

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}

trap cleanup INT TERM EXIT

need uv
need npm

if [ ! -d frontend/node_modules ]; then
  npm install
fi

uv sync

uv run uvicorn backend.main:app --host 127.0.0.1 --port "${COINDOOR_PORT:-8765}" --reload &
BACKEND_PID=$!

npm run dev &
FRONTEND_PID=$!

printf '%s\n' 'COINDOOR levantado:'
printf '%s\n' 'Frontend: http://127.0.0.1:5173'
printf '%s\n' 'API docs: http://127.0.0.1:8765/api/docs'
printf '%s\n' 'Cortar: Ctrl+C'

wait "$BACKEND_PID" "$FRONTEND_PID"
