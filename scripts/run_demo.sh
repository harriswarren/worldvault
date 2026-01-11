#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/.demo_logs"
PID_DIR="$ROOT_DIR/.demo_pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

wait_http() {
  local url="$1"
  local name="$2"
  local retries="${3:-50}"

  for i in $(seq 1 "$retries"); do
    if python - <<PY >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("$url", timeout=1).read()
PY
    then
      echo "  $name ready: $url"
      return 0
    fi
    sleep 0.2
  done

  echo "  ERROR: $name not reachable: $url"
  return 1
}

start_service() {
  local name="$1"
  local cwd="$2"
  local cmd="$3"
  local log_file="$LOG_DIR/${name}.log"
  local pid_file="$PID_DIR/${name}.pid"

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$name already running (pid $(cat "$pid_file"))"
    return 0
  fi

  echo "Starting $name..."
  (cd "$cwd" && nohup bash -lc "$cmd" >"$log_file" 2>&1 & echo $! >"$pid_file")
  sleep 0.5
  echo "  log: $log_file"
}

ensure_venv_and_deps() {
  local cwd="$1"
  local req_file="$2"

  if [[ ! -d "$cwd/.venv" ]]; then
    (cd "$cwd" && python -m venv .venv)
  fi
  (cd "$cwd" && bash -lc "source .venv/bin/activate && python -m pip install --upgrade pip >/dev/null && pip install -r $req_file")
}

echo "== WorldVault demo: starting =="

if [[ -z "${JWT_ED25519_PRIVATE_KEY_B64:-}" || -z "${JWT_ED25519_PUBLIC_KEY_B64:-}" ]]; then
  echo "WARNING: JWT_ED25519_* keys not set. Vault will generate a key each boot and Policy Adapter may not verify signatures."
fi

if [[ -z "${APIFY_TOKEN:-}" || -z "${APIFY_TASK_ID_ENRICH:-}" ]]; then
  echo "WARNING: APIFY_TOKEN or APIFY_TASK_ID_ENRICH not set. Lead enrichment will fall back to stub data."
fi

# Postgres (optional for this scaffold)
if command -v docker >/dev/null 2>&1; then
  (cd "$ROOT_DIR" && docker compose -f infra/docker-compose.yml up -d)
else
  echo "docker not found; skipping Postgres startup (ok for current in-memory demo)."
fi

# Python deps (one-time-ish)
ensure_venv_and_deps "$ROOT_DIR/services/vault_api" "requirements.txt"
ensure_venv_and_deps "$ROOT_DIR/services/policy_adapter" "requirements.txt"
ensure_venv_and_deps "$ROOT_DIR/services/mcp_worldvault" "requirements.txt"
ensure_venv_and_deps "$ROOT_DIR/services/a2a_agents/lead_enrichment" "requirements.txt"
ensure_venv_and_deps "$ROOT_DIR/services/a2a_agents/subject_optimizer" "requirements.txt"

# Start servers
start_service "vault_api" "$ROOT_DIR/services/vault_api" "source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8001"
start_service "policy_adapter" "$ROOT_DIR/services/policy_adapter" "source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8002"
start_service "mcp_worldvault" "$ROOT_DIR/services/mcp_worldvault" "source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8003"
start_service "a2a_lead_enrichment" "$ROOT_DIR/services/a2a_agents/lead_enrichment" "source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 9011"
start_service "a2a_subject_optimizer" "$ROOT_DIR/services/a2a_agents/subject_optimizer" "source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 9012"

echo "== Waiting for services =="
wait_http "http://localhost:8001/health" "Vault API"
wait_http "http://localhost:8002/health" "Policy Adapter"
wait_http "http://localhost:8003/tools" "MCP Server"
wait_http "http://localhost:9011/docs" "Lead Enrichment"
wait_http "http://localhost:9012/docs" "Subject Optimizer"

echo "== Started. Quick checks =="
echo "  Vault API:        http://localhost:8001/health"
echo "  Policy Adapter:   http://localhost:8002/health"
echo "  MCP Server:       http://localhost:8003/tools"
echo "  Lead Enrichment:  http://localhost:9011/docs"
echo "  Subject Optimizer:http://localhost:9012/docs"

echo "== Done =="
