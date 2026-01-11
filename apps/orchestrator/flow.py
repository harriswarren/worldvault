from __future__ import annotations

import asyncio
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


MCP_URL = "http://localhost:8003"
POLICY_ADAPTER_URL = "http://localhost:8002"
LEAD_AGENT_URL = "http://localhost:9011"
SUBJECT_AGENT_URL = "http://localhost:9012"


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

    @start()
    def discover_tools(self) -> None:
        with httpx.Client() as client:
            response = client.get(f"{MCP_URL}/tools")
            response.raise_for_status()
            self.state.tool_catalog = response.json().get("tools", [])

    @step()
    def paid_profile_read(self) -> None:
        if not self.state.consent_token:
            return
        payload = {
            "name": "worldvault.profile.read",
            "arguments": {"fields": ["profile.name"], "purpose": "outreach_personalization"},
            "consent_token": self.state.consent_token,
        }
        with httpx.Client() as client:
            response = client.post(f"{MCP_URL}/tools/call", json=payload)
            response.raise_for_status()
            self.state.results["profile"] = response.json()

    @step()
    def run_parallel_agents(self) -> None:
        asyncio.run(self._run_parallel_agents())

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
        if not self.state.consent_token:
            return
        payload = {
            "name": "worldvault.prefs.write",
            "arguments": {
                "updates": {"prefs.outreach_tone": "direct, friendly, concise"},
                "purpose": "outreach_personalization",
            },
            "consent_token": self.state.consent_token,
        }
        with httpx.Client() as client:
            response = client.post(f"{MCP_URL}/tools/call", json=payload)
            response.raise_for_status()
            self.state.results["prefs_write"] = response.json()


if __name__ == "__main__":
    flow = WorldVaultFlow()
    if hasattr(flow, "kickoff"):
        flow.kickoff()
    else:
        flow.discover_tools()
        flow.paid_profile_read()
        flow.run_parallel_agents()
        flow.request_prefs_write()
