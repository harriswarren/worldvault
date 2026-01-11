import base64
import json
import os
import time
import uuid
from typing import Dict, List, Literal, Optional

import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

AUDIENCE = os.getenv("JWT_AUDIENCE", "memmachine-policy-adapter")
RECEIVER_ADDRESS = os.getenv("X402_RECEIVER_ADDRESS", "")
X402_ASSET = os.getenv("X402_ASSET", "USDC")
HOLD_THRESHOLD = float(os.getenv("HOLD_THRESHOLD", "0.05"))


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _load_public_key() -> Optional[ed25519.Ed25519PublicKey]:
    key_b64 = os.getenv("JWT_ED25519_PUBLIC_KEY_B64")
    if not key_b64:
        return None
    return ed25519.Ed25519PublicKey.from_public_bytes(_b64url_decode(key_b64))


class PolicyCheckRequest(BaseModel):
    consent_token: str
    action: Literal["read", "write"]
    scope: str
    resource: str
    tool: str
    cost_usdc: float = 0.0
    bytes: int = 0
    require_approval: bool = False
    payment_proof: Optional[str] = None
    approval_id: Optional[str] = None


class PolicyDecisionResponse(BaseModel):
    decision: Literal["ALLOW", "HOLD", "BLOCK"]
    reason: Optional[str] = None
    approval_id: Optional[str] = None
    receipt: Optional[Dict[str, object]] = None


class ApprovalDecisionRequest(BaseModel):
    approval_id: str
    decision: Literal["APPROVE", "DENY"]


class RevocationEvent(BaseModel):
    event_type: Literal["CONSENT_REVOKED", "SCOPE_REVOKED"]
    subject_did: str
    agent_did: str
    jti: str
    scopes: List[str]
    resources: List[str]
    reason: Optional[str] = None
    idempotency_key: Optional[str] = None


class AuditEvent(BaseModel):
    ts: int
    event_type: str
    user_did: Optional[str]
    agent_did: Optional[str]
    jti: Optional[str]
    scope: Optional[str]
    resource: Optional[str]
    decision: str
    cost_usdc: float
    payment_ref: Optional[str]
    details: Dict[str, object]


app = FastAPI(title="World Vault Policy Adapter", version="0.1.0")
public_key = _load_public_key()

# Demo in-memory stores
app.state.revoked = set()
app.state.approvals = {}
app.state.usage = {}
app.state.audit_events = []


def _decode_token(token: str) -> Dict[str, object]:
    if public_key is None:
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True, "verify_aud": False},
        )
    return jwt.decode(token, public_key, algorithms=["EdDSA"], audience=AUDIENCE)


def _record_audit(event: AuditEvent) -> None:
    app.state.audit_events.append(event.model_dump())


def _ensure_limits(payload: Dict[str, object], action: str, bytes_used: int) -> Optional[str]:
    limits = payload.get("limits") or {}
    jti = payload.get("jti")
    if not jti:
        return "missing_jti"

    usage = app.state.usage.setdefault(jti, {"reads": 0, "writes": 0, "bytes": 0})
    usage["bytes"] += bytes_used
    if usage["bytes"] > int(limits.get("bytes_cap", 65536)):
        return "bytes_cap_exceeded"

    if action == "read":
        usage["reads"] += 1
        if usage["reads"] > int(limits.get("max_reads", 30)):
            return "read_limit_exceeded"
    if action == "write":
        usage["writes"] += 1
        if usage["writes"] > int(limits.get("max_writes", 5)):
            return "write_limit_exceeded"
    return None


def _payment_required_response(tool: str, amount: float) -> None:
    raise HTTPException(
        status_code=402,
        detail={
            "error": "payment_required",
            "requirements": {
                "receiver": RECEIVER_ADDRESS,
                "asset": X402_ASSET,
                "amount": amount,
                "memo": f"{tool}:{uuid.uuid4().hex[:8]}",
            },
        },
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/policy/check", response_model=PolicyDecisionResponse)
def policy_check(request: PolicyCheckRequest) -> PolicyDecisionResponse:
    try:
        payload = _decode_token(request.consent_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"invalid_token: {exc}") from exc

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="missing_jti")
    if jti in app.state.revoked:
        return PolicyDecisionResponse(decision="BLOCK", reason="revoked")

    scopes = set(payload.get("scp") or [])
    resources = set(payload.get("res") or [])
    if request.scope not in scopes:
        return PolicyDecisionResponse(decision="BLOCK", reason="scope_denied")
    if request.resource not in resources:
        return PolicyDecisionResponse(decision="BLOCK", reason="resource_denied")

    limit_error = _ensure_limits(payload, request.action, request.bytes)
    if limit_error:
        return PolicyDecisionResponse(decision="BLOCK", reason=limit_error)

    approval_status: Optional[str] = None
    if request.approval_id:
        approval = app.state.approvals.get(request.approval_id)
        if not approval:
            return PolicyDecisionResponse(decision="BLOCK", reason="approval_not_found")
        approval_status = approval.get("status")
        if approval_status == "DENY":
            return PolicyDecisionResponse(decision="BLOCK", reason="approval_denied")
        if approval_status != "APPROVE":
            return PolicyDecisionResponse(decision="HOLD", approval_id=request.approval_id)

    if (request.require_approval or request.cost_usdc > HOLD_THRESHOLD) and approval_status != "APPROVE":
        approval_id = f"appr_{uuid.uuid4().hex[:8]}"
        app.state.approvals[approval_id] = {"status": "PENDING", "request": request.model_dump()}
        _record_audit(
            AuditEvent(
                ts=int(time.time()),
                event_type="policy_check",
                user_did=payload.get("sub"),
                agent_did=payload.get("act"),
                jti=jti,
                scope=request.scope,
                resource=request.resource,
                decision="HOLD",
                cost_usdc=request.cost_usdc,
                payment_ref=None,
                details={"approval_id": approval_id, "tool": request.tool},
            )
        )
        return PolicyDecisionResponse(decision="HOLD", approval_id=approval_id)

    if request.cost_usdc > 0 and not request.payment_proof:
        _payment_required_response(request.tool, request.cost_usdc)

    receipt = {
        "tool": request.tool,
        "amount": request.cost_usdc,
        "asset": X402_ASSET,
        "payment_ref": request.payment_proof,
    }
    _record_audit(
        AuditEvent(
            ts=int(time.time()),
            event_type="policy_check",
            user_did=payload.get("sub"),
            agent_did=payload.get("act"),
            jti=jti,
            scope=request.scope,
            resource=request.resource,
            decision="ALLOW",
            cost_usdc=request.cost_usdc,
            payment_ref=request.payment_proof,
            details={"tool": request.tool},
        )
    )
    return PolicyDecisionResponse(decision="ALLOW", receipt=receipt)


@app.post("/policy/approve")
def policy_approve(request: ApprovalDecisionRequest) -> Dict[str, str]:
    approval = app.state.approvals.get(request.approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="approval_not_found")
    approval["status"] = request.decision
    try:
        original = approval.get("request") or {}
        _record_audit(
            AuditEvent(
                ts=int(time.time()),
                event_type="approval_decision",
                user_did=None,
                agent_did=None,
                jti=None,
                scope=original.get("scope"),
                resource=original.get("resource"),
                decision=request.decision,
                cost_usdc=float(original.get("cost_usdc") or 0.0),
                payment_ref=original.get("payment_proof"),
                details={"approval_id": request.approval_id},
            )
        )
    except Exception:
        pass
    return {"status": approval["status"], "approval_id": request.approval_id}


@app.get("/audit/export.jsonl")
def audit_export() -> PlainTextResponse:
    lines = [json.dumps(event) for event in app.state.audit_events]
    return PlainTextResponse("\n".join(lines))


@app.post("/webhooks/revocation")
def revocation_webhook(event: RevocationEvent) -> Dict[str, str]:
    app.state.revoked.add(event.jti)
    _record_audit(
        AuditEvent(
            ts=int(time.time()),
            event_type="revocation",
            user_did=event.subject_did,
            agent_did=event.agent_did,
            jti=event.jti,
            scope=None,
            resource=None,
            decision="BLOCK",
            cost_usdc=0.0,
            payment_ref=None,
            details={"event_type": event.event_type, "reason": event.reason},
        )
    )
    return {"status": "revoked", "jti": event.jti}
