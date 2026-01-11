# World Vault Hackathon Demo Script
**Duration:** 2-3 minutes (150 seconds)
**Focus:** AI/Agent Integration + Technical Innovation for Privacy-Conscious Users

---

## Setup Checklist

Before recording:
- [ ] All services running: `./scripts/run_demo.sh`
- [ ] Streamlit UI open: `http://localhost:8501`
- [ ] Terminal ready: `cd apps/orchestrator && python flow.py`
- [ ] Screen split: Streamlit (40% left) | Terminal (60% right)
- [ ] Terminal: JetBrains Mono 16pt, dark theme
- [ ] Browser: Hide chrome, 110% zoom

---

## Scene-by-Scene Script

### [0:00-0:15] HOOK: The Problem (15 seconds)

**Visual:** Static slide with text overlay

**Narration:**
> "AI agents are everywhere now - writing emails, enriching leads, personalizing outreach. But your personal data is trapped in walled gardens. You can't control who accesses it, you can't revoke access instantly, and you definitely aren't getting paid for it. Until now."

**On-Screen Text:**
- "Your Data. Locked Away. Unmonetized."

---

### [0:15-0:40] ACT 1: Issue Consent - User Takes Control (25 seconds)

**Visual:** Streamlit "Issue Consent" tab (pre-filled)

**Actions:**
1. Switch to Streamlit browser
2. Navigate to "Issue Consent" tab
3. Scroll through form showing:
   - User DID: `did:wv:user:alex_rivera_0x4f2a`
   - Agent DID: `did:cobra:agent:sales_autopilot_v2`
   - Scopes with pricing:
     - `profile:name.read ($0.002)`
     - `profile:company.read ($0.002)`
     - `prefs:outreach_tone.read ($0.001)`
     - `prefs:writing_style.read ($0.001)`
     - `prefs:outreach_tone.write ($0.015)` - HITL approval
   - Limits: 50 reads, 3 writes, 20/min rate
   - TTL: 10 minutes
4. Highlight JWT preview at bottom (expand briefly)

**Narration:**
> "Meet Alex, a sales director. She's granting her AI sales assistant temporary access to her profile and preferences - scoped exactly to what's needed, priced per-operation, with strict limits. This isn't OAuth - it's a cryptographically signed Ed25519 JWT with embedded pricing and consent."

**On-Screen:**
- Flash: "Token issued: ctok_a7f39c2e" (if functional, otherwise show preview)

---

### [0:40-0:70] ACT 2: 402 Payment Loop (30 seconds)

**Visual:** Split-screen (Terminal left, Architecture diagram overlay right)

**Actions:**
1. Switch to terminal pane
2. Run: `python flow.py`
3. Watch color-coded logs appear:
   - Blue: `[FLOW] Step 1/5: Discovering MCP tools...`
   - Green: `✓ Token issued: ctok_...`
   - Tool discovery with prices
   - Blue: `[FLOW] Step 2/5: Reading Alex's profile...`
   - Red: `✗ HTTP 402 Payment Required`
   - Yellow: `[PAYMENT] Nevermined payment proof generated`
   - Green: `✓ PAID & ALLOWED`

**Narration:**
> "The orchestrator discovers paid MCP tools, attempts a read, hits a 402 Payment Required, auto-pays via USDC through Nevermined's x402 protocol, and retries - all in the reasoning loop. No checkout pages. No subscriptions. Just pay-per-use, inline payments."

**On-Screen:**
- Optional: Architecture diagram overlay (0:45-0:55) showing payment flow with animated arrows

---

### [0:70-0:95] ACT 3: Parallel Agent Execution (25 seconds)

**Visual:** Terminal continues (full screen)

**Actions:**
1. Watch terminal logs:
   - Blue: `[FLOW] Step 3/5: Parallel A2A agents executing...`
   - Yellow: `[AGENT 1] Lead Enrichment (Apify)`
   - Yellow: `[AGENT 2] Subject Optimizer`
   - Green: `⚡ Both agents completed in 2.3s`
   - Green: `✓ Lead Enrichment: 3 profiles enriched`
   - Green: `✓ Subject Optimizer: "Quick intro from Alex at TechFlow"`
   - Blue: `Budget used: $0.030 / $0.250`

**Narration:**
> "Now it gets interesting. The orchestrator spins up two paid A2A agents in parallel - one calls Apify for real-world lead enrichment, the other optimizes email subjects using Alex's tone preferences. Agent-to-agent commerce, async execution, all within a $0.25 budget cap."

**On-Screen:**
- Flash: "Budget used: $0.030 / $0.250" (post-production overlay)

---

### [0:95-0:115] ACT 4: Human-in-the-Loop Approval (20 seconds)

**Visual:** Split-screen (Terminal left, Streamlit right)

**Actions:**
1. Terminal shows:
   - Blue: `[FLOW] Step 4/5: Writing updated preferences...`
   - Orange: `⚠ HOLD - Requires human approval`
   - Orange: `[WAITING] Human approval pending...`
2. Switch to Streamlit "Approvals Queue" tab
3. Show approval card:
   - Request: `appr_b8f2`
   - Tool: `worldvault.prefs.write`
   - Change: `outreach_tone → "direct, warm, data-driven"`
   - Cost: `$0.015`
4. Click **APPROVE** button
5. Switch back to terminal:
   - Green: `✓ APPROVED by user`
   - Green: `✓ Write completed`

**Narration:**
> "Risky writes trigger human-in-the-loop approval. Alex sees exactly what's changing, the cost, and who's requesting it. She approves in the UI, and the orchestrator continues. Total transparency, total control."

---

### [0:115-0:140] ACT 5: Instant Revocation (25 seconds)

**Visual:** Streamlit "Revocation" tab

**Actions:**
1. Switch to Streamlit "Revocation" tab
2. Show active token card details
3. Click big red **REVOKE TOKEN** button
4. Show webhook payload preview (JSON animation)
5. Show cache purge checklist:
   - ✓ Invalidate sessions
   - ✓ Purge cached pointers
   - ✓ Log audit event
   - ✓ Block future calls
6. Optional: Terminal shows re-attempt → BLOCKED

**Narration:**
> "Alex decides she's done. One click, instant revocation. The vault broadcasts to all policy adapters, purges caches, and blocks any future access. The agent tries to read again - denied instantly. No grace periods, no delayed propagation. Immediate control."

---

### [0:140-0:150] ACT 6: Audit Trail & Impact (10 seconds)

**Visual:** Streamlit "Audit Trail" tab

**Actions:**
1. Switch to "Audit Trail" tab
2. Show summary stats KPI boxes:
   - Total Operations: 12
   - Total Revenue: $0.047 (green)
   - Control Events: 2
3. Scroll through event table:
   - `consent_issued` (OK)
   - `read` (PAID)
   - `read` (PAID)
   - `write` (HOLD → APPROVED)
   - `consent_revoked` (BLOCKED)
4. Hover over "Export JSONL" button

**Narration:**
> "Every action is auditable. Every payment is tracked. Alex earned $0.047 from her data, kept complete control, and the agent got exactly what it needed. This is the future: user-owned memory, consented commerce, cryptographic trust."

**On-Screen:**
- Fade to closing slide: "World Vault - Your Data. Your Rules. Your Revenue."
- Tech stack: "Built with: Ed25519 JWT • x402 Protocol • MCP • CrewAI • Nevermined • Apify"

---

## Post-Recording Checklist

Video editing:
- [ ] Add intro slide (0:00-0:05): World Vault logo + hackathon name
- [ ] Add architecture diagram overlay (0:45-0:55)
- [ ] Add budget counter overlay (0:90-0:95)
- [ ] Add summary stats overlay (0:140-0:145)
- [ ] Add closing slide with tagline + tech stack
- [ ] Add subtle background music (non-distracting)
- [ ] Add captions/subtitles for accessibility
- [ ] Export: 1080p60fps, H.264, high bitrate

---

## Key Talking Points (Reference)

### Technical Innovation
1. **Ed25519 JWT with embedded pricing** - Not just OAuth, cryptographic consent with economics baked in
2. **x402 HTTP Payment Protocol** - USDC payments in the reasoning loop, no checkout flow
3. **MCP tool monetization** - Tool developers monetize without billing infrastructure
4. **Instant revocation** - No grace periods, immediate cache purge across services
5. **A2A commerce** - Agents paying other agents with receipts and audit trails

### Privacy & Control
1. **Granular consent** - Per-field, per-scope, per-operation pricing
2. **HITL for risky ops** - Human approval for sensitive writes
3. **Complete audit trail** - Every operation logged immutably
4. **User revenue** - Data owners get paid for access ($0.047 in demo)

### Architecture
1. **Policy adapter as trust layer** - Single enforcement point for authz + metering
2. **Consent tokens as bearer credentials** - Portable, revocable, time/scope limited
3. **Parallel orchestration** - CrewAI coordinates multiple paid agents within budget
4. **Real-world integrations** - Apify (data), Nevermined (payments), MCP (tools)

---

## Backup Commands

If services aren't running:
```bash
cd /Users/home/dev/worldvault
./scripts/run_demo.sh
```

If orchestrator needs manual run:
```bash
cd apps/orchestrator
python flow.py
```

If Streamlit needs restart:
```bash
streamlit run apps/ui_streamlit/app.py --server.port 8501
```

---

## Success Criteria

✅ Demo runs end-to-end without errors
✅ All 5 services healthy (8001, 8002, 8003, 9011, 9012)
✅ 402 payment loop completes with payment proof
✅ HITL approval shows in UI
✅ Revocation blocks subsequent access
✅ Audit trail shows all events
✅ Terminal logs are color-coded and readable
✅ Video under 3 minutes and tells compelling story
✅ Architecture and impact are clear to judges

---

**Good luck! You're going to win this! 🏆**
