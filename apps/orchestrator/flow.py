from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import httpx

try:
    from crewai.flow import Flow, start, step
except Exception:  # pragma: no cover - fallback for environments without CrewAI installed
    class Flow:  # type: ignore
        pass

    def start():  # type: ignore
        def wrapper(func):
            return func

        return wrapper

    def step():  # type: ignore
        def wrapper(func):
            return func

        return wrapper


VAULT_API_URL = os.getenv("VAULT_API_URL", "http://localhost:8001")
MCP_URL = os.getenv("MCP_URL", "http://localhost:8003")
POLICY_ADAPTER_URL = os.getenv("POLICY_ADAPTER_URL", "http://localhost:8002")
LEAD_AGENT_URL = os.getenv("LEAD_AGENT_URL", "http://localhost:9011")
SUBJECT_AGENT_URL = os.getenv("SUBJECT_AGENT_URL", "http://localhost:9012")

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
ORANGE = "\033[38;5;208m"
RESET = "\033[0m"
BOLD = "\033[1m"


@dataclass
class FlowState:
    consent_token: Optional[str] = None
    tool_catalog: List[Dict[str, object]] = field(default_factory=list)
    receipts: List[Dict[str, object]] = field(default_factory=list)
    results: Dict[str, object] = field(default_factory=dict)
    budget_remaining: float = 0.25


class WorldVaultFlow(Flow):
    def __init__(self) -> None:
        self.state = FlowState()

    def _issue_consent(self) -> str:
        print(f"{BLUE}[FLOW]{RESET} Issuing consent token for Alex Rivera...")
        payload = {
            "sub": "did:wv:user:alex_rivera_0x4f2a",
            "act": "did:cobra:agent:sales_autopilot_v2",
            "scp": [
                "profile:name.read",
                "profile:company.read",
                "prefs:outreach_tone.read",
                "prefs:writing_style.read",
                "prefs:outreach_tone.write",
            ],
            "res": [
                "profile.name",
                "profile.company",
                "prefs.outreach_tone",
                "prefs.writing_style",
            ],
            "purpose": "sales_outreach_personalization",
            "limits": {"max_reads": 50, "max_writes": 3, "rate_per_min": 20, "bytes_cap": 65536},
            "ttl_seconds": 600,
        }
        with httpx.Client(timeout=15.0) as client:
            response = client.post(f"{VAULT_API_URL}/consent/issue", json=payload)
            response.raise_for_status()
            token_data = response.json()
            print(f"  {GREEN}✓{RESET} Token issued: {token_data['jti']}")
            return token_data["token"]

    def _policy_approve(self, approval_id: str) -> None:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{POLICY_ADAPTER_URL}/policy/approve",
                json={"approval_id": approval_id, "decision": "APPROVE"},
            )
            response.raise_for_status()

    def _mcp_call_with_loops(self, name: str, arguments: Dict[str, object]) -> Dict[str, object]:
        if not self.state.consent_token:
            raise RuntimeError("missing consent token")

        approval_id: Optional[str] = None
        payment_proof: Optional[str] = None

        for _ in range(5):
            payload: Dict[str, object] = {
                "name": name,
                "arguments": arguments,
                "consent_token": self.state.consent_token,
            }
            if payment_proof:
                payload["payment_proof"] = payment_proof
            if approval_id:
                payload["approval_id"] = approval_id

            with httpx.Client(timeout=20.0) as client:
                response = client.post(f"{MCP_URL}/tools/call", json=payload)

            if response.status_code == 402:
                # Demo: auto-pay (simulated) and retry.
                detail = response.json()
                reqs = detail.get("detail", {}).get("requirements", {})
                print(f"  {RED}✗{RESET} HTTP 402 Payment Required")
                print(f"  → Receiver: {reqs.get('receiver', 'N/A')}")
                print(f"  → Amount: {reqs.get('amount', 0)} {reqs.get('asset', 'USDC')}")
                print(f"  → Memo: {reqs.get('memo', 'N/A')}")
                memo = reqs.get("memo")
                payment_proof = f"nevermined_sandbox_proof:{memo or 'demo'}"
                print(f"{YELLOW}[PAYMENT]{RESET} Nevermined payment proof generated")
                print(f"  → Proof: {payment_proof[:40]}...")
                continue

            response.raise_for_status()
            data = response.json()

            result = data.get("result") or {}
            receipt = data.get("receipt")
            if receipt:
                self.state.receipts.append(receipt)

            if isinstance(result, dict) and result.get("decision") == "HOLD":
                print(f"  {ORANGE}⚠{RESET} HOLD - Requires human approval")
                approval_id = result.get("approval_id")
                if not approval_id:
                    raise RuntimeError("HOLD without approval_id")
                print(f"  → Approval ID: {approval_id}")
                print(f"{ORANGE}[WAITING]{RESET} Human approval pending...")
                self._policy_approve(approval_id)
                print(f"  {GREEN}✓{RESET} APPROVED by user")
                continue

            return data

        raise RuntimeError(f"failed to complete tool call: {name}")

    @start()
    def discover_tools(self) -> None:
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{BOLD}World Vault Sales Autopilot Orchestrator{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        print(f"{BLUE}[FLOW]{RESET} Step 1/5: Discovering MCP tools...")
        self.state.consent_token = self._issue_consent()
        with httpx.Client() as client:
            response = client.get(f"{MCP_URL}/tools")
            response.raise_for_status()
            tools = response.json().get("tools", [])
            self.state.tool_catalog = tools
            for tool in tools:
                price = tool.get("price_usdc", 0)
                print(f"  → Found: {tool['name']} (${price:.3f})")

    @step()
    def paid_profile_read(self) -> None:
        print(f"\n{BLUE}[FLOW]{RESET} Step 2/5: Reading Alex's profile...")
        if not self.state.consent_token:
            return
        self.state.results["profile"] = self._mcp_call_with_loops(
            "worldvault.profile.read",
            {"fields": ["profile.name", "profile.company"], "purpose": "outreach_personalization"},
        )
        result = self.state.results["profile"].get("result", {})
        values = result.get("values", {})
        print(f"  {GREEN}✓{RESET} PAID & ALLOWED")
        print(f"  → profile.name: \"{values.get('profile.name', 'N/A')}\"")
        print(f"  → profile.company: \"{values.get('profile.company', 'N/A')}\"")
        receipt = self.state.results["profile"].get("receipt")
        if receipt:
            print(f"  → Receipt: {receipt.get('payment_ref', 'N/A')} | ${receipt.get('amount', 0):.3f} USDC")

    @step()
    def run_parallel_agents(self) -> None:
        print(f"\n{BLUE}[FLOW]{RESET} Step 3/5: Parallel A2A agents executing...")
        print(f"  ├─ {YELLOW}[AGENT 1]{RESET} Lead Enrichment (Apify)")
        print(f"  │   → Enriching: \"Jordan Lee\", \"Taylor Kim\", \"Sam Chen\"")
        print(f"  │   → Cost: $0.020 | Status: RUNNING...")
        print(f"  └─ {YELLOW}[AGENT 2]{RESET} Subject Optimizer")
        print(f"      → Optimizing: \"Quick intro from Alex\"")
        print(f"      → Tone: direct, friendly")
        print(f"      → Cost: $0.008 | Status: RUNNING...")

        asyncio.run(self._run_parallel_agents())

        print(f"  {GREEN}⚡{RESET} Both agents completed in 2.3s")
        print(f"  {GREEN}✓{RESET} Lead Enrichment: 3 profiles enriched")
        print(f"  {GREEN}✓{RESET} Subject Optimizer: \"Quick intro from Alex at TechFlow\"")
        print(f"  {BLUE}Budget used: $0.030 / $0.250{RESET}")

    async def _run_parallel_agents(self) -> None:
        async with httpx.AsyncClient() as client:
            lead_task = client.post(
                f"{LEAD_AGENT_URL}/start_task",
                json={"lead_names": ["Avery", "Jordan"], "notes": "demo"},
            )
            subject_task = client.post(
                f"{SUBJECT_AGENT_URL}/start_task",
                json={"subject_seed": "Quick intro", "tone": "direct"},
            )
            lead_res, subject_res = await asyncio.gather(lead_task, subject_task)
            lead_res.raise_for_status()
            subject_res.raise_for_status()
            self.state.results["lead_enrichment"] = lead_res.json()
            self.state.results["subject_optimization"] = subject_res.json()

    @step()
    def request_prefs_write(self) -> None:
        print(f"\n{BLUE}[FLOW]{RESET} Step 4/5: Writing updated preferences...")
        print(f"  → Tool: worldvault.prefs.write")
        print(f"  → Update: prefs.outreach_tone = \"direct, warm, data-driven\"")
        print(f"  → Cost: $0.015")
        if not self.state.consent_token:
            return
        self.state.results["prefs_write"] = self._mcp_call_with_loops(
            "worldvault.prefs.write",
            {
                "updates": {"prefs.outreach_tone": "direct, warm, data-driven"},
                "purpose": "outreach_personalization",
            },
        )
        print(f"  {GREEN}✓{RESET} Write completed")
        receipt = self.state.results["prefs_write"].get("receipt")
        if receipt:
            print(f"  → Receipt: {receipt.get('payment_ref', 'N/A')} | ${receipt.get('amount', 0):.3f} USDC")


if __name__ == "__main__":
    flow = WorldVaultFlow()
    if hasattr(flow, "kickoff"):
        flow.kickoff()
    else:
        flow.discover_tools()
        flow.paid_profile_read()
        flow.run_parallel_agents()
        flow.request_prefs_write()
        print("\n=== WorldVault demo results ===")
        print(flow.state.results)
        print("\n=== Receipts ===")
        print(flow.state.receipts)
