# World Vault Build Runbook (Codex-ready)

This runbook is the concrete, step-by-step setup and build plan for the full 9-item hackathon scope.

## 1. Tooling context (what each tool is doing)

### CrewAI Flows (orchestration)
- You will implement the demo as a **CrewAI Flow**, which models your workflow as explicit steps with state (budgets, consent token, tool catalog, results).
- Key idea: a Flow makes it easy to show deterministic multi-step reasoning and to branch on policy outcomes (ALLOW, HOLD, BLOCK).

### MCP (Model Context Protocol)
- MCP provides the **tool discovery and invocation** layer.
- You will expose your paid capabilities (memory read, prefs write, enrichment, optimization) as **MCP tools** with JSON schema inputs.

### Nevermined (payments + monetization + proxy)
- Nevermined is used to create **monetizable services and pricing plans**, and to enforce payment in front of your endpoints using a proxy or SDK.
- You will map each paid MCP tool to a Nevermined plan id and require payment proof.

### x402 (HTTP 402 payments semantics)
- x402 uses HTTP 402 Payment Required as an on-the-wire flow:
  - server returns 402 + payment requirements
  - client pays
  - client retries with proof of payment
- You will implement this pattern on your Policy Adapter and show it once in the demo.

### Apify (real-world enrichment)
- Apify runs Actors and Tasks via API, producing structured datasets.
- In the demo, it powers lead enrichment in a paid, metered step.

### Cline CLI (scaffold a tool server)
- You will run one scripted Cline CLI command to scaffold a new MCP tool or extend your MCP server.
- This is a visible proof you used Cline in development.

### A2A Async + AP2 (agent-to-agent parallelism and payments)
- A2A is used to send two async tasks in parallel.
- AP2 is used to represent the agent payments handshake (receipt metadata). If AP2 tooling is early, treat it as an interop layer and keep the demo minimal.

## 2. Accounts, keys, and prerequisites

### 2.1 Local prerequisites
- Python 3.10+
- Node.js 18+
- Docker Desktop
- Postgres 15+

### 2.2 Accounts and secrets
Create and store:
- OPENAI_API_KEY
- APIFY_TOKEN
- NEVERMINED_API_KEY (from Nevermined App)
- NEVERMINED_ENV (eg: staging or production base URL)
- x402 wallet configuration (depends on the x402 library you choose)

## 3. Repo scaffold

Create a monorepo:

```
world-vault/
  apps/
    ui_streamlit/
    orchestrator/
  services/
    vault_api/
    policy_adapter/
    mcp_worldvault/
    a2a_agents/
      lead_enrichment/
      subject_optimizer/
  infra/
    docker-compose.yml
  packages/
    sdk_node/
```

## 4. Environment variables

Create `.env` at repo root:

```
# Core
POSTGRES_URL=postgresql://worldvault:worldvault@localhost:5432/worldvault
JWT_ISSUER_DID=did:wv:issuer:main
JWT_AUDIENCE=memmachine-policy-adapter

# Nevermined
NEVERMINED_API_KEY=...
NEVERMINED_BASE_URL=...
NVM_SERVICE_ID_POLICY_ADAPTER=...
NVM_PLAN_ID_PROFILE_READ=...
NVM_PLAN_ID_PREFS_WRITE=...
NVM_PLAN_ID_APIFY_ENRICH=...

# x402
X402_ENABLED=true
X402_RECEIVER_ADDRESS=...
X402_CHAIN=base
X402_ASSET=USDC

# Apify
APIFY_TOKEN=...
APIFY_TASK_ID_ENRICH=...

# A2A
A2A_BASE_URL=http://localhost:9010

# UI
STREAMLIT_SERVER_PORT=8501
```

## 5. Docker compose (minimal)

`infra/docker-compose.yml`

```
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: worldvault
      POSTGRES_PASSWORD: worldvault
      POSTGRES_DB: worldvault
    ports:
      - "5432:5432"
```

Start it:

```
docker compose -f infra/docker-compose.yml up -d
```

## 6. Implement the 9 required items

## Item 1. Consent issuer + JWKS (Vault API)

### 6.1.1 Tech choice
Use FastAPI (Python) for speed.

### 6.1.2 Endpoints
- POST /consent/issue
- GET /.well-known/jwks.json
- POST /revoke
- POST /vault/read
- POST /vault/write

### 6.1.3 Token signing approach (hackathon)
- Use Ed25519 (preferred) or ES256.
- Store private key in env var for demo.
- Publish public key via JWKS.

## Item 2. Policy Adapter (authZ + meter + charge + audit)

### 6.2.1 Responsibilities
- Verify JWT signature against JWKS
- Validate aud, exp, iat
- Check scopes and resources
- Enforce limits
- Check revocation table
- If payment missing, respond 402 with requirements
- Log audit events

### 6.2.2 Decision outcomes
- ALLOW: proceed
- HOLD: create approval record, return approval_id
- BLOCK: return error

## Item 3. Metering + receipts
- Every allowed action writes `audit_events` with:
  - scope, resource, decision
  - cost_usdc and payment_ref
- Export JSONL at /audit/export.jsonl

## Item 4. Nevermined plans and enforcement
1. Create services for policy adapter and MCP server.
2. Create plans per tool.
3. Map tool name -> plan id.
4. Enforce plan id on each request (proxy or SDK).

## Item 5. x402 402 loop
- When payment is required, return HTTP 402.
- Include a machine-readable payload describing:
  - receiver, asset, amount
  - memo: tool name + jti + request id

Client behavior:
- Detect 402
- Pay automatically
- Retry with proof header

## Item 6. MCP server exposing paid tools
Expose:
- worldvault.profile.read
- worldvault.prefs.write

Each tool implementation:
- Calls Policy Adapter /policy/check
- If payment required, runs pay loop
- Calls Vault API read or write
- Returns data + receipt

## Item 7. CrewAI Flow orchestration
Flow steps:
1. discover tools via MCP
2. ensure consent token exists
3. call paid profile.read
4. run A2A async parallel tasks
5. draft outreach
6. request prefs.write (likely HOLD)
7. wait for approval
8. finalize and export audit

## Item 8. A2A async parallel paid calls
Create two simple A2A agents:
- lead_enrichment: calls Apify paid tool
- subject_optimizer: uses an LLM or a simple heuristic, but still metered

Dispatch both in parallel:
- start_task() returns task_id
- poll_task(task_id) returns status and result

## Item 9. Streamlit UI (HITL)
Pages:
- Issue consent token
- Approval queue (approve/deny)
- Revoke token
- View audit log and receipts

## 7. Apify integration (concrete API calls)

Option A: async run
- POST /v2/actor-tasks/:taskId/runs
- Read defaultDatasetId, then fetch dataset items

Option B: sync run (timeout <= 300 seconds)
- GET /v2/actor-tasks/:taskId/run-sync-get-dataset-items

## 8. Cline CLI proof step
Pick one reproducible command:
- scaffold MCP server
- add a new tool definition
- generate a client wrapper

Save terminal output as a demo artifact.

## 9. Demo validation checklist
- Payment-required shown at least once
- Two paid tools invoked
- One HITL approval shown
- Revocation shown and then blocked access shown
- Audit export produced and opened

