from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "World-Vault-Logo.png"
ICON_PATH = ASSETS_DIR / "World-Vault-Icon.png"

st.set_page_config(
    page_title="World Vault",
    page_icon=str(ICON_PATH),
    layout="wide",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');
:root {
  --bg: #f6f4ee;
  --text: #101010;
  --muted: #5c5b55;
  --border: #dad6cc;
  --card: #fbfaf7;
  --accent: #111111;
  --accent-soft: #ece8df;
  --good: #1f7a4d;
  --warn: #b36b00;
  --bad: #a31224;
  --mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  --sans: 'IBM Plex Sans', 'Space Grotesk', 'Helvetica Neue', sans-serif;
  --title: 'Space Grotesk', 'IBM Plex Sans', 'Helvetica Neue', sans-serif;
}
html, body, .stApp {
  background: radial-gradient(900px 460px at 4% -10%, rgba(0,0,0,0.08), transparent 60%),
              radial-gradient(520px 320px at 95% 0%, rgba(0,0,0,0.05), transparent 60%),
              var(--bg);
  color: var(--text);
  font-family: var(--sans);
}
h1, h2, h3, h4 {
  font-family: var(--title);
  letter-spacing: -0.01em;
}
small, .muted {
  color: var(--muted);
}
code, pre {
  font-family: var(--mono);
}
section.main > div {
  padding-top: 20px;
}
div[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(255,255,255,0.6), rgba(255,255,255,0.1));
  border-right: 1px solid var(--border);
}
.wv-chip {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  color: var(--muted);
  background: #ffffff;
  gap: 6px;
}
.wv-chip.good { color: var(--good); border-color: rgba(31,122,77,0.3); background: rgba(31,122,77,0.08); }
.wv-chip.warn { color: var(--warn); border-color: rgba(179,107,0,0.3); background: rgba(179,107,0,0.08); }
.wv-chip.bad { color: var(--bad); border-color: rgba(163,18,36,0.3); background: rgba(163,18,36,0.08); }
.wv-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 12px 24px rgba(0,0,0,0.06);
  animation: wvFade 0.6s ease both;
}
.wv-card + .wv-card { margin-top: 14px; }
.wv-title {
  font-size: 18px;
  margin: 0;
}
.wv-subtitle {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 13px;
}
.wv-section-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px 0;
}
.wv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.wv-table th, .wv-table td {
  border-bottom: 1px solid var(--border);
  padding: 8px 6px;
  text-align: left;
}
.wv-table th {
  color: var(--muted);
  font-weight: 600;
}
.wv-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  font-size: 11px;
  color: var(--muted);
  background: #ffffff;
}
.wv-pill.good { color: var(--good); border-color: rgba(31,122,77,0.3); background: rgba(31,122,77,0.08); }
.wv-pill.warn { color: var(--warn); border-color: rgba(179,107,0,0.3); background: rgba(179,107,0,0.08); }
.wv-pill.bad { color: var(--bad); border-color: rgba(163,18,36,0.3); background: rgba(163,18,36,0.08); }
.wv-kpi { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.wv-kpi-box { border: 1px solid var(--border); border-radius: 14px; padding: 10px; background: #ffffff; }
.wv-kpi-label { font-size: 11px; color: var(--muted); }
.wv-kpi-value { font-size: 16px; margin-top: 6px; font-weight: 600; }
.wv-mono { font-family: var(--mono); font-size: 12px; }
@keyframes wvFade {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
""",
    unsafe_allow_html=True,
)


def _split_scopes(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _parse_resources(text: str) -> list[str]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
<div class="wv-card" style="margin-bottom: 14px;">
  <div class="wv-title">{title}</div>
  <div class="wv-subtitle">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.image(str(LOGO_PATH))
    st.markdown("<div class='muted'>User-owned memory with consented commerce.</div>", unsafe_allow_html=True)
    st.markdown(
        """
<div style="display:flex; gap:6px; flex-wrap:wrap; margin:12px 0 8px;">
  <span class="wv-chip good">Vault online</span>
  <span class="wv-chip">DID ready</span>
  <span class="wv-chip warn">TTL short</span>
</div>
""",
        unsafe_allow_html=True,
    )
    section = st.radio(
        "Navigate",
        ["Issue Consent", "Approvals", "Revocation", "Audit", "Vault Data"],
    )

if section == "Issue Consent":
    header(
        "Issue Consent",
        "Create a short-lived Consent Token scoped to fields and purpose.",
    )
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.markdown("<div class='wv-card'>", unsafe_allow_html=True)
            st.markdown("<div class='wv-section-title'>Principals</div>", unsafe_allow_html=True)
            sub = st.text_input("User DID (sub)", "did:wv:user:0x1234...abcd")
            act = st.text_input("Agent DID (act)", "did:cobra:agent:orchestrator:0x9f...01")
            ttl = st.selectbox("TTL", ["5 minutes", "10 minutes", "15 minutes"], index=1)
            purpose = st.text_input("Purpose", "outreach_personalization")
            st.markdown("<div class='wv-section-title'>Scopes</div>", unsafe_allow_html=True)
            read_scopes = st.text_area(
                "Read scopes",
                "profile:name.read\nprefs:outreach_tone.read\nprefs:writing_style.read",
            )
            write_scopes = st.text_area("Write scopes", "prefs:outreach_tone.write")
            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown("<div class='wv-card'>", unsafe_allow_html=True)
            st.markdown("<div class='wv-section-title'>Limits</div>", unsafe_allow_html=True)
            max_reads = st.number_input("Max reads", min_value=0, value=30)
            max_writes = st.number_input("Max writes", min_value=0, value=5)
            rate_limit = st.number_input("Rate limit (per minute)", min_value=1, value=10)
            bytes_cap = st.number_input("Bytes cap", min_value=0, value=65536)
            resources = st.text_area(
                "Resource allowlist (res)",
                "[\"profile.name\", \"prefs.outreach_tone\", \"prefs.writing_style\"]",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='wv-card'>", unsafe_allow_html=True)
    st.markdown("<div class='wv-section-title'>Consent Token Preview (mock)</div>", unsafe_allow_html=True)
    preview_payload = {
        "iss": "did:wv:issuer:main",
        "sub": sub,
        "act": act,
        "aud": "memmachine-policy-adapter",
        "scp": _split_scopes(read_scopes) + _split_scopes(write_scopes),
        "res": _parse_resources(resources),
        "purpose": purpose,
        "limits": {
            "max_reads": max_reads,
            "max_writes": max_writes,
            "rate_per_min": rate_limit,
            "bytes_cap": bytes_cap,
        },
        "jti": "ctok_31afc1",
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
    }
    st.code(json.dumps(preview_payload, indent=2), language="json")
    st.markdown("</div>", unsafe_allow_html=True)

elif section == "Approvals":
    header(
        "Approvals Queue",
        "Risky writes are held for human approval before execution.",
    )
    st.markdown(
        """
<div class="wv-card">
  <div class="wv-section-title">Pending approvals</div>
  <table class="wv-table">
    <thead>
      <tr><th>Request</th><th>Tool</th><th>Cost</th><th>Status</th></tr>
    </thead>
    <tbody>
      <tr><td class="wv-mono">appr_91f2c3</td><td>worldvault.prefs.write</td><td>$0.010</td><td><span class="wv-pill warn">HOLD</span></td></tr>
    </tbody>
  </table>
</div>
""",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("Approve", type="primary")
    with col2:
        st.button("Deny")

elif section == "Revocation":
    header(
        "Revocation",
        "Revoke consent and broadcast cache purge to policy adapter.",
    )
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            """
<div class="wv-card">
  <div class="wv-section-title">Webhook payload (mock)</div>
  <pre class="wv-mono">{
  "event_type": "CONSENT_REVOKED",
  "subject_did": "did:wv:user:0x1234...abcd",
  "agent_did": "did:cobra:agent:orchestrator:0x9f...01",
  "jti": "ctok_31afc1",
  "scopes": ["profile:name.read", "prefs:outreach_tone.read", "prefs:outreach_tone.write"],
  "resources": ["profile.name", "prefs.outreach_tone"],
  "reason": "user_revoked",
  "idempotency_key": "rev_8f2c"
}</pre>
</div>
""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
<div class="wv-card">
  <div class="wv-section-title">Cache purge result</div>
  <table class="wv-table">
    <thead><tr><th>Action</th><th>Status</th></tr></thead>
    <tbody>
      <tr><td>Invalidate sessions</td><td><span class="wv-pill good">OK</span></td></tr>
      <tr><td>Purge cached pointers</td><td><span class="wv-pill good">OK</span></td></tr>
      <tr><td>Log audit event</td><td><span class="wv-pill good">OK</span></td></tr>
      <tr><td>Block future calls</td><td><span class="wv-pill good">OK</span></td></tr>
    </tbody>
  </table>
</div>
""",
            unsafe_allow_html=True,
        )
    st.button("Revoke token", type="primary")

elif section == "Audit":
    header(
        "Audit and Receipts",
        "Every consent, read, write, payment, and revocation is logged.",
    )
    st.markdown(
        """
<div class="wv-card">
  <div class="wv-section-title">Events</div>
  <table class="wv-table">
    <thead><tr><th>Time</th><th>Type</th><th>Token</th><th>Summary</th><th>Status</th></tr></thead>
    <tbody>
      <tr><td class="wv-mono">11:02:11</td><td>consent_issued</td><td class="wv-mono">ctok_31afc1</td><td>Issued consent for profile and prefs</td><td><span class="wv-pill good">OK</span></td></tr>
      <tr><td class="wv-mono">11:03:01</td><td>read</td><td class="wv-mono">ctok_31afc1</td><td>profile.name read (metered)</td><td><span class="wv-pill good">PAID</span></td></tr>
      <tr><td class="wv-mono">11:05:44</td><td>write</td><td class="wv-mono">ctok_31afc1</td><td>prefs.outreach_tone write (held for approval)</td><td><span class="wv-pill warn">HOLD</span></td></tr>
      <tr><td class="wv-mono">11:07:09</td><td>consent_revoked</td><td class="wv-mono">ctok_31afc1</td><td>User revoked token and purged caches</td><td><span class="wv-pill bad">REVOKED</span></td></tr>
    </tbody>
  </table>
</div>
""",
        unsafe_allow_html=True,
    )
    st.button("Export JSONL", type="primary")

elif section == "Vault Data":
    header(
        "Vault Data",
        "Encrypted profile store with pointers and envelopes.",
    )
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            """
<div class="wv-card">
  <div class="wv-section-title">Profile and preferences (redacted)</div>
  <table class="wv-table">
    <thead><tr><th>Field</th><th>Value</th><th>Class</th></tr></thead>
    <tbody>
      <tr><td class="wv-mono">profile.name</td><td>H****s</td><td><span class="wv-pill warn">Sensitive</span></td></tr>
      <tr><td class="wv-mono">prefs.outreach_tone</td><td>direct, friendly, concise</td><td><span class="wv-pill">Preference</span></td></tr>
      <tr><td class="wv-mono">prefs.writing_style</td><td>no emojis, no long dashes</td><td><span class="wv-pill">Preference</span></td></tr>
    </tbody>
  </table>
</div>
""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
<div class="wv-card">
  <div class="wv-section-title">Pointer model</div>
  <div class="muted">Pointers plus signed envelopes instead of raw values.</div>
  <pre class="wv-mono">memmachine_pointer = {
  "type": "wv_pointer",
  "vault_ref": "wv://enc/profile.name#v3",
  "envelope_sig": "sig_ed25519_..."
}</pre>
</div>
""",
            unsafe_allow_html=True,
        )
