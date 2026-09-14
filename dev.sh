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

# Instala ffmpeg y deno si faltan (ADR-0020): no corta el arranque si el instalador falla,
# solo avisa. La app funciona igual; lo que se pierde es la descarga de video de YouTube.
sh "$ROOT/scripts/install-deps.sh" || printf '%s\n' "Aviso: no se pudieron instalar todas las dependencias de video (ver docs/troubleshooting.md)." >&2

# El instalador de Deno lo deja en ~/.deno/bin, que puede no estar en el PATH todavía.
[ -d "$HOME/.deno/bin" ] && PATH="$HOME/.deno/bin:$PATH"
export PATH

# Siempre, como uv sync: después de un pull con dependencias nuevas, node_modules queda viejo.
npm --prefix frontend install

uv sync

# Matar procesos existentes en el puerto antes de levantar
PORT="${COINDOOR_PORT:-8765}"
EXISTING_PIDS=$(lsof -ti :"$PORT" 2>/dev/null || true)
if [ -n "$EXISTING_PIDS" ]; then
  printf '%s\n' "Bajando procesos en :$PORT (PIDs $EXISTING_PIDS)…"
  echo "$EXISTING_PIDS" | xargs kill -9 2>/dev/null || true
  sleep 1
fi

uv run uvicorn backend.main:app --host 127.0.0.1 --port "$PORT" --reload &
BACKEND_PID=$!

npm run dev &
FRONTEND_PID=$!

printf '%s\n' 'COINDOOR levantado:'
printf '%s\n' 'Frontend: http://127.0.0.1:5173'
printf '%s\n' 'API docs: http://127.0.0.1:8765/api/docs'
printf '%s\n' 'Cortar: Ctrl+C'

wait "$BACKEND_PID" "$FRONTEND_PID"
