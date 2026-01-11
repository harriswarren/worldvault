#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

python - <<'PY'
import json
import os
import sys
import urllib.request


def req(method: str, url: str, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8")


def main():
    for url in [
        "http://localhost:8001/health",
        "http://localhost:8002/health",
        "http://localhost:8003/tools",
    ]:
        status, text = req("GET", url)
        print(url, status)

    issue_body = {
        "sub": "did:wv:user:demo",
        "act": "did:wv:agent:demo",
        "scp": ["profile:name.read", "prefs:outreach_tone.write"],
        "res": ["profile.name", "prefs.outreach_tone"],
        "purpose": "hackathon_demo",
        "limits": {"max_reads": 30, "max_writes": 5, "rate_per_min": 10, "bytes_cap": 65536},
        "ttl_seconds": 600,
    }
    status, text = req("POST", "http://localhost:8001/consent/issue", issue_body)
    if status != 200:
        print("consent issue failed", status, text)
        sys.exit(1)
    token = json.loads(text)["token"]
    print("Issued consent token (len)", len(token))

    call_body = {
        "name": "worldvault.profile.read",
        "arguments": {"fields": ["profile.name"], "purpose": "hackathon_demo"},
        "consent_token": token,
    }

    # First call should 402
    try:
        status, text = req("POST", "http://localhost:8003/tools/call", call_body)
        print("Unexpected non-402", status, text[:200])
    except Exception as e:
        # urllib raises on non-2xx; redo with basic error handling
        import urllib.error
        if isinstance(e, urllib.error.HTTPError):
            status = e.code
            body = e.read().decode("utf-8")
            print("MCP call status", status)
            if status != 402:
                print(body[:500])
                raise
        else:
            raise

    # Retry with proof
    call_body["payment_proof"] = "nevermined_sandbox_proof_demo_1"
    status, text = req("POST", "http://localhost:8003/tools/call", call_body)
    print("Paid retry status", status)
    print(text[:300])

    # Apify enrichment
    status, text = req("POST", "http://localhost:9011/start_task", {"lead_names": ["Avery", "Jordan"], "notes": "demo"})
    print("Lead enrichment", status)
    print(text[:300])

    status, text = req("GET", "http://localhost:8002/audit/export.jsonl")
    print("Audit export", status)
    print(text.splitlines()[-1][:300] if text else "(empty)")


if __name__ == "__main__":
    main()
PY
