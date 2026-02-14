#!/usr/bin/env bash
# Start FastAPI backend (port 8000) and React frontend (Vite) with one command.
# From repo root: ./scripts/run_dev.sh   or   bash scripts/run_dev.sh
# Ctrl+C stops both.

set -e
cd "$(dirname "$0")/.."

BACKEND_PORT=8000
if command -v lsof &>/dev/null; then
  if lsof -i ":$BACKEND_PORT" -sTCP:LISTEN -t &>/dev/null; then
    echo "Port $BACKEND_PORT already in use (backend may be running). Starting frontend only."
    echo "To run both, stop the process on port $BACKEND_PORT first."
    exec bash -c "cd frontend && npm run dev"
    exit 0
  fi
fi

echo "Starting backend (uvicorn) on port $BACKEND_PORT..."
uvicorn api.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!

cleanup() {
  trap - INT TERM EXIT
  echo "Stopping backend (PID $BACKEND_PID)..."
  kill "$BACKEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM EXIT

echo "Starting frontend (Vite)..."
cd frontend && npm run dev
