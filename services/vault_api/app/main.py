import base64
import os
import time
import uuid
from typing import Dict, List, Optional

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ISSUER_DID = os.getenv("JWT_ISSUER_DID", "did:wv:issuer:main")
AUDIENCE = os.getenv("JWT_AUDIENCE", "memmachine-policy-adapter")
JWKS_KID = os.getenv("JWKS_KID", "wv_jwks_1")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _load_signing_key() -> ed25519.Ed25519PrivateKey:
    key_b64 = os.getenv("JWT_ED25519_PRIVATE_KEY_B64")
    if key_b64:
        return ed25519.Ed25519PrivateKey.from_private_bytes(_b64url_decode(key_b64))
    return ed25519.Ed25519PrivateKey.generate()


def _build_jwks(public_key: ed25519.Ed25519PublicKey) -> Dict[str, List[Dict[str, str]]]:
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {
        "keys": [
            {
                "kty": "OKP",
                "crv": "Ed25519",
                "x": _b64url_encode(public_bytes),
                "kid": JWKS_KID,
                "alg": "EdDSA",
                "use": "sig",
            }
        ]
    }


class ConsentLimits(BaseModel):
    max_reads: int = 30
    max_writes: int = 5
    rate_per_min: int = 10
    bytes_cap: int = 65536


class ConsentIssueRequest(BaseModel):
    sub: str
    act: str
    scp: List[str]
    res: List[str]
    purpose: str
    limits: ConsentLimits
    ttl_seconds: int = Field(600, ge=60, le=3600)


class ConsentIssueResponse(BaseModel):
    token: str
    jti: str
    expires_at: int
    payload: Dict[str, object]


class RevokeRequest(BaseModel):
    jti: str
    reason: Optional[str] = "user_revoked"
    idempotency_key: Optional[str] = None


class VaultReadRequest(BaseModel):
    keys: List[str]


class VaultWriteRequest(BaseModel):
    updates: Dict[str, str]


class VaultReadResponse(BaseModel):
    values: Dict[str, Optional[str]]


class VaultWriteResponse(BaseModel):
    updated_keys: List[str]


app = FastAPI(title="World Vault API", version="0.1.0")

signing_key = _load_signing_key()
public_key = signing_key.public_key()
app.state.signing_key = signing_key
app.state.jwks = _build_jwks(public_key)

# Demo in-memory stores
app.state.consents = {}
app.state.revoked = set()
app.state.vault_data = {
    "profile.name": "Hayes",
    "prefs.outreach_tone": "direct, friendly, concise",
    "prefs.writing_style": "no emojis, no long dashes",
}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/consent/issue", response_model=ConsentIssueResponse)
def issue_consent(request: ConsentIssueRequest) -> ConsentIssueResponse:
    now = int(time.time())
    jti = f"ctok_{uuid.uuid4().hex[:8]}"
    payload = {
        "iss": ISSUER_DID,
        "sub": request.sub,
        "act": request.act,
        "aud": AUDIENCE,
        "scp": request.scp,
        "res": request.res,
        "purpose": request.purpose,
        "limits": request.limits.model_dump(),
        "jti": jti,
        "iat": now,
        "nbf": now,
        "exp": now + request.ttl_seconds,
    }
    token = jwt.encode(
        payload,
        app.state.signing_key,
        algorithm="EdDSA",
        headers={"kid": JWKS_KID, "typ": "JWT"},
    )
    app.state.consents[jti] = payload
    return ConsentIssueResponse(token=token, jti=jti, expires_at=payload["exp"], payload=payload)


@app.get("/.well-known/jwks.json")
def jwks() -> Dict[str, List[Dict[str, str]]]:
    return app.state.jwks


@app.post("/revoke")
def revoke(request: RevokeRequest) -> Dict[str, str]:
    if request.jti not in app.state.consents:
        raise HTTPException(status_code=404, detail="unknown token")
    app.state.revoked.add(request.jti)
    return {"status": "revoked", "jti": request.jti}


@app.post("/vault/read", response_model=VaultReadResponse)
def vault_read(request: VaultReadRequest) -> VaultReadResponse:
    values = {key: app.state.vault_data.get(key) for key in request.keys}
    return VaultReadResponse(values=values)


@app.post("/vault/write", response_model=VaultWriteResponse)
def vault_write(request: VaultWriteRequest) -> VaultWriteResponse:
    app.state.vault_data.update(request.updates)
    return VaultWriteResponse(updated_keys=list(request.updates.keys()))
