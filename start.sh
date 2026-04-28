#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Activate venv if it exists
if [ -f "$ROOT/.venv/bin/activate" ]; then
  source "$ROOT/.venv/bin/activate"
fi

echo "Starting Juno backend on :8001 ..."
python -m server.server --reload &
BACKEND_PID=$!

echo "Starting Juno frontend on :3000 ..."
cd "$ROOT/web" && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
