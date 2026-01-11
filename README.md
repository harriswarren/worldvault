# World Vault Hackathon Scaffold

This repo contains a runnable scaffold for the World Vault demo: a consented memory vault with paid MCP tools, 402 payment loops, A2A async agents, and a CrewAI Flow orchestrator.

## Structure
- `apps/ui_streamlit`: Streamlit UI (consent, approvals, revocation, audit)
- `apps/orchestrator`: CrewAI Flow skeleton
- `services/vault_api`: FastAPI Vault API (consent, JWKS, vault read/write)
- `services/policy_adapter`: FastAPI Policy Adapter (authz, 402, approvals, audit)
- `services/mcp_worldvault`: MCP tool server stub
- `services/a2a_agents`: A2A agent stubs
- `infra`: Docker compose for Postgres

## Quick start
1) Copy env file and edit values:

```
cp .env.example .env
```

2) Start Postgres:

```
docker compose -f infra/docker-compose.yml up -d
```

3) Run services in separate shells:

```
# Vault API
cd services/vault_api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Policy Adapter
cd services/policy_adapter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Streamlit UI
cd apps/ui_streamlit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Notes:
- The MCP server and CrewAI Flow are stubs for now, ready for full integration.
- This scaffold uses in-memory stores for demo flow; wire to Postgres when ready.
