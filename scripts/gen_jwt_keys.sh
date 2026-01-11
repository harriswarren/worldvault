#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_DIR="$ROOT_DIR/services/vault_api"

# Ensure vault_api venv exists and has deps (cryptography) so keygen works reliably.
if [[ ! -d "$VAULT_DIR/.venv" ]]; then
  (cd "$VAULT_DIR" && python -m venv .venv)
fi

(cd "$VAULT_DIR" && bash -lc "source .venv/bin/activate && python -m pip install --upgrade pip >/dev/null && pip install -r requirements.txt >/dev/null")

(cd "$VAULT_DIR" && bash -lc "source .venv/bin/activate && python - <<'PY'
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

priv = ed25519.Ed25519PrivateKey.generate()
priv_bytes = priv.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption(),
)
pub_bytes = priv.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)

def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode('ascii').rstrip('=')

print('JWT_ED25519_PRIVATE_KEY_B64=' + b64u(priv_bytes))
print('JWT_ED25519_PUBLIC_KEY_B64=' + b64u(pub_bytes))
PY")
