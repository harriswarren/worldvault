import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

POLICY_ADAPTER_URL = os.getenv("POLICY_ADAPTER_URL", "http://localhost:8002")
VAULT_API_URL = os.getenv("VAULT_API_URL", "http://localhost:8001")

TOOL_CATALOG = [
    {
        "name": "worldvault.profile.read",
        "description": "Read profile fields (name, company, role, contact info)",
        "input_schema": {
            "type": "object",
            "properties": {
                "fields": {"type": "array", "items": {"type": "string"}},
                "purpose": {"type": "string"},
            },
            "required": ["fields", "purpose"],
        },
        "price_usdc": 0.002,
    },
    {
        "name": "worldvault.prefs.read",
        "description": "Read user preferences (tone, style, timing)",
        "input_schema": {
            "type": "object",
            "properties": {
                "fields": {"type": "array", "items": {"type": "string"}},
                "purpose": {"type": "string"},
            },
            "required": ["fields", "purpose"],
        },
        "price_usdc": 0.001,
    },
    {
        "name": "worldvault.prefs.write",
        "description": "Update user preferences (HITL approval required)",
        "input_schema": {
            "type": "object",
            "properties": {
                "updates": {"type": "object"},
                "purpose": {"type": "string"},
            },
            "required": ["updates", "purpose"],
        },
        "price_usdc": 0.015,
        "requires_approval": True,
    },
    {
        "name": "worldvault.insights.read",
        "description": "Read behavioral insights (premium tier)",
        "input_schema": {
            "type": "object",
            "properties": {
                "fields": {"type": "array", "items": {"type": "string"}},
                "purpose": {"type": "string"},
            },
            "required": ["fields", "purpose"],
        },
        "price_usdc": 0.005,
    },
]


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]
    consent_token: str
    payment_proof: Optional[str] = None
    approval_id: Optional[str] = None


class ToolCallResponse(BaseModel):
    result: Dict[str, Any]
    receipt: Optional[Dict[str, Any]] = None


app = FastAPI(title="World Vault MCP Server", version="0.1.0")


def _tool_price(name: str) -> float:
    for tool in TOOL_CATALOG:
        if tool["name"] == name:
            return float(tool.get("price_usdc", 0.0))
    return 0.0


def _tool_definition() -> List[Dict[str, Any]]:
    return TOOL_CATALOG


def _scope_for_read(field: str) -> str:
    base = field.split(".")[-1]
    return f"profile:{base}.read" if field.startswith("profile.") else f"prefs:{base}.read"


def _scope_for_write(field: str) -> str:
    base = field.split(".")[-1]
    return f"prefs:{base}.write"


@app.get("/tools")
def list_tools() -> Dict[str, Any]:
    return {"tools": _tool_definition()}


@app.post("/tools/call", response_model=ToolCallResponse)
def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    if request.name == "worldvault.profile.read":
        return _handle_profile_read(request)
    if request.name == "worldvault.prefs.read":
        return _handle_prefs_read(request)
    if request.name == "worldvault.prefs.write":
        return _handle_prefs_write(request)
    if request.name == "worldvault.insights.read":
        return _handle_insights_read(request)
    raise HTTPException(status_code=404, detail="tool_not_found")


def _handle_profile_read(request: ToolCallRequest) -> ToolCallResponse:
    fields = request.arguments.get("fields", [])
    if not fields:
        raise HTTPException(status_code=400, detail="fields_required")

    resource = fields[0]
    scope = _scope_for_read(resource)
    price = _tool_price(request.name)

    policy_payload = {
        "consent_token": request.consent_token,
        "action": "read",
        "scope": scope,
        "resource": resource,
        "tool": request.name,
        "cost_usdc": price,
        "bytes": 0,
        "payment_proof": request.payment_proof,
        "approval_id": request.approval_id,
    }

    with httpx.Client() as client:
        policy_res = client.post(f"{POLICY_ADAPTER_URL}/policy/check", json=policy_payload)
    if policy_res.status_code == 402:
        raise HTTPException(status_code=402, detail=policy_res.json())
    if policy_res.status_code != 200:
        raise HTTPException(status_code=policy_res.status_code, detail=policy_res.text)

    decision = policy_res.json()
    if decision.get("decision") == "HOLD":
        return ToolCallResponse(result={"decision": "HOLD", "approval_id": decision.get("approval_id")})

    with httpx.Client() as client:
        vault_res = client.post(f"{VAULT_API_URL}/vault/read", json={"keys": fields})
    if vault_res.status_code != 200:
        raise HTTPException(status_code=vault_res.status_code, detail=vault_res.text)

    return ToolCallResponse(result=vault_res.json(), receipt=decision.get("receipt"))


def _handle_prefs_read(request: ToolCallRequest) -> ToolCallResponse:
    fields = request.arguments.get("fields", [])
    if not fields:
        raise HTTPException(status_code=400, detail="fields_required")

    resource = fields[0]
    scope = _scope_for_read(resource)
    price = _tool_price(request.name)

    policy_payload = {
        "consent_token": request.consent_token,
        "action": "read",
        "scope": scope,
        "resource": resource,
        "tool": request.name,
        "cost_usdc": price,
        "bytes": 0,
        "payment_proof": request.payment_proof,
        "approval_id": request.approval_id,
    }

    with httpx.Client() as client:
        policy_res = client.post(f"{POLICY_ADAPTER_URL}/policy/check", json=policy_payload)
    if policy_res.status_code == 402:
        raise HTTPException(status_code=402, detail=policy_res.json())
    if policy_res.status_code != 200:
        raise HTTPException(status_code=policy_res.status_code, detail=policy_res.text)

    decision = policy_res.json()
    if decision.get("decision") == "HOLD":
        return ToolCallResponse(result={"decision": "HOLD", "approval_id": decision.get("approval_id")})

    with httpx.Client() as client:
        vault_res = client.post(f"{VAULT_API_URL}/vault/read", json={"keys": fields})
    if vault_res.status_code != 200:
        raise HTTPException(status_code=vault_res.status_code, detail=vault_res.text)

    return ToolCallResponse(result=vault_res.json(), receipt=decision.get("receipt"))


def _handle_insights_read(request: ToolCallRequest) -> ToolCallResponse:
    fields = request.arguments.get("fields", [])
    if not fields:
        raise HTTPException(status_code=400, detail="fields_required")

    resource = fields[0]
    base = resource.split(".")[-1]
    scope = f"insights:{base}.read"
    price = _tool_price(request.name)

    policy_payload = {
        "consent_token": request.consent_token,
        "action": "read",
        "scope": scope,
        "resource": resource,
        "tool": request.name,
        "cost_usdc": price,
        "bytes": 0,
        "payment_proof": request.payment_proof,
        "approval_id": request.approval_id,
    }

    with httpx.Client() as client:
        policy_res = client.post(f"{POLICY_ADAPTER_URL}/policy/check", json=policy_payload)
    if policy_res.status_code == 402:
        raise HTTPException(status_code=402, detail=policy_res.json())
    if policy_res.status_code != 200:
        raise HTTPException(status_code=policy_res.status_code, detail=policy_res.text)

    decision = policy_res.json()
    if decision.get("decision") == "HOLD":
        return ToolCallResponse(result={"decision": "HOLD", "approval_id": decision.get("approval_id")})

    with httpx.Client() as client:
        vault_res = client.post(f"{VAULT_API_URL}/vault/read", json={"keys": fields})
    if vault_res.status_code != 200:
        raise HTTPException(status_code=vault_res.status_code, detail=vault_res.text)

    return ToolCallResponse(result=vault_res.json(), receipt=decision.get("receipt"))


def _handle_prefs_write(request: ToolCallRequest) -> ToolCallResponse:
    updates = request.arguments.get("updates")
    if not updates:
        raise HTTPException(status_code=400, detail="updates_required")

    first_key = next(iter(updates.keys()))
    scope = _scope_for_write(first_key)
    price = _tool_price(request.name)

    policy_payload = {
        "consent_token": request.consent_token,
        "action": "write",
        "scope": scope,
        "resource": first_key,
        "tool": request.name,
        "cost_usdc": price,
        "bytes": 0,
        "payment_proof": request.payment_proof,
        "require_approval": True,
        "approval_id": request.approval_id,
    }

    with httpx.Client() as client:
        policy_res = client.post(f"{POLICY_ADAPTER_URL}/policy/check", json=policy_payload)
    if policy_res.status_code == 402:
        raise HTTPException(status_code=402, detail=policy_res.json())
    if policy_res.status_code != 200:
        raise HTTPException(status_code=policy_res.status_code, detail=policy_res.text)

    decision = policy_res.json()
    if decision.get("decision") == "HOLD":
        return ToolCallResponse(result={"decision": "HOLD", "approval_id": decision.get("approval_id")})

    with httpx.Client() as client:
        vault_res = client.post(f"{VAULT_API_URL}/vault/write", json={"updates": updates})
    if vault_res.status_code != 200:
        raise HTTPException(status_code=vault_res.status_code, detail=vault_res.text)

    return ToolCallResponse(result=vault_res.json(), receipt=decision.get("receipt"))
