#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.demo_pids"

DEMO_PORTS=(8001 8002 8003 9011 9012)

if [[ ! -d "$PID_DIR" ]]; then
  echo "No pid dir found ($PID_DIR). Nothing to stop."
  exit 0
fi

stop_pid_file() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 0
  fi
  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $(basename "$pid_file" .pid) (pid $pid)"
    kill "$pid" || true
  fi
  rm -f "$pid_file"
}

for f in "$PID_DIR"/*.pid; do
  stop_pid_file "$f"
done

# Clean up any orphaned listeners (uvicorn can spawn child processes)
for port in "${DEMO_PORTS[@]}"; do
  pids="$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Stopping listeners on port $port: $pids"
    kill $pids 2>/dev/null || true
  fi
done

echo "Stopped demo processes. Postgres is still running (docker compose)."
