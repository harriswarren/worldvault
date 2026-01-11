# World Vault Commerce Memory (Hackathon Build Pack)

This doc is written to be pasted into a coding agent (Codex) to implement an end-to-end demo: a user-owned memory vault where agents discover paid MCP tools, obtain short-lived consent, pay inline via Nevermined and x402 semantics, run parallel A2A async steps, and export auditable receipts.

## 0. What you are building (MVP)
A working demo with:
1. **Consent UI (HITL):** user issues and revokes consent; approves risky actions.
2. **Consent issuer + JWKS:** short-lived signed tokens with scopes, resources, TTL, limits.
3. **Policy adapter:** validates consent, enforces scope, checks revocation, meters, charges, logs.
4. **Paid MCP tools:** at least two paid tools behind monetization enforcement.
5. **Agent-to-agent payments:** orchestrator agent calls another paid agent mid-flow.
6. **A2A async:** parallel paid calls with task management and completion callbacks.
7. **Apify integration:** real-world enrichment step.
8. **Cline CLI integration:** scaffold or extend MCP server during the demo.
9. **CrewAI Flows:** orchestrate the whole workflow as a Flow, not just a Crew.

## 1. Product Requirements (PRD)

### 1.1 Goals
- Portable, revocable AI memory demo that feels real.
- Payments are inside the reasoning loop, not a manual checkout.
- MCP discovery + paid tools + agent-to-agent commerce are undeniable in the demo.
- Exportable audit log proves what happened.

### 1.2 Non-goals
- Health data
- Full DID resolution pipeline
- Production HSMs or full verifiable credentials
- Full subscription billing

### 1.3 Users
- End user: wants personalization without lock-in, wants revoke.
- Agent developer: wants to buy memory reads safely and cheaply.
- Tool developer: wants to monetize a tool without building billing infra.
- Judges: want proof fast.

### 1.4 User stories
- Issue short-lived consent to a specific agent for specific fields.
- Revoke consent and force cache purge.
- Agent discovers paid tools via MCP.
- Agent hits 402 payment required, pays, retries, continues.
- Agent runs A2A async parallel calls within a budget.
- Risky write is held for human approval.
- Export audit and receipts.

### 1.5 Acceptance criteria
- 2+ monetizable tools and 2+ payment plans used.
- 1+ agent pays another agent mid-flow.
- 1+ revoke shown, then blocked access shown.
- Audit export contains consent issue, paid read, paid write attempt, approval decision, revoke, block.

## 2. System design

### 2.1 Components
- **Streamlit UI:** consent issuance, approvals queue, revoke, audit viewer.
- **Vault API:** consent issuer, JWKS endpoint, encrypted store, revoke trigger.
- **Policy Adapter:** authorization + metering + payment enforcement + audit logging.
- **MCP server:** exposes paid tools for reads/writes.
- **Paid agents (A2A):** lead enrichment, subject optimizer.
- **Orchestrator (CrewAI Flow):** chooses tools, budgets, and runs the workflow.

### 2.2 Token model (JWT)
Header:
- alg: EdDSA or ES256
- kid: key id

Payload:
- iss: vault issuer DID
- sub: user DID
- act: agent DID
- aud: policy-adapter
- scp: scope list
- res: resource allowlist
- purpose
- limits: {max_reads, max_writes, rate_per_min, bytes_cap}
- jti, iat, nbf, exp

### 2.3 Data model (Postgres)
Tables:
- vault_items(user_did, key, ciphertext, version, timestamps)
- consent_tokens(jti, user_did, agent_did, scopes, resources, expires_at, revoked_at)
- audit_events(ts, type, decision, scope, resource, cost_usdc, payment_ref, details)
- approvals(status, request, decision_ts)
- revocations(idempotency_key, jti, ts)

### 2.4 APIs

Vault:
- POST /consent/issue
- GET /.well-known/jwks.json
- POST /revoke
- POST /vault/read
- POST /vault/write

Revocation webhook:
- POST /webhooks/revocation

Policy adapter:
- POST /policy/check
- POST /policy/approve
- GET /audit/export.jsonl

### 2.5 Paid MCP tools
- worldvault.profile.read(fields, purpose, consent_token)
- worldvault.prefs.write(updates, purpose, consent_token)

### 2.6 Pricing plan suggestions
- profile read: per request $0.002
- prefs write: per write $0.010 (HITL)
- apify enrich: per request $0.020
- subject optimize: per token $0.005

Budget policy:
- workflow cap $0.25
- hold any single call > $0.05

## 3. Implementation checklist (the 9 items)
1. Consent issuer + JWKS
2. Policy adapter with token validation and revocation check
3. Metering + receipts
4. Nevermined plan registration and enforcement path
5. x402 style 402 payment-required loop
6. MCP server advertising paid tools
7. CrewAI Flow orchestration with state and budgets
8. A2A async parallel paid calls
9. Streamlit HITL UI (consent + approvals + revoke + audit)

## 4. Demo script (2 minutes)
1. Issue consent in UI (show token preview)
2. Run orchestrator flow
3. Show payment-required then auto-pay then success
4. Show A2A async parallel completion
5. Show a held write and approve in UI
6. Revoke token
7. Re-run read and show blocked
8. Export audit JSONL and open it

