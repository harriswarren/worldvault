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
/* FORCE LIGHT THEME - MAKE EVERYTHING READABLE */
.stApp {
  background-color: #ffffff !important;
}
section.main {
  background-color: #ffffff !important;
}
section.main > div {
  padding-top: 5px;
  background-color: #ffffff !important;
}
/* Force all text to be DARK */
.stApp, .stApp * {
  color: #000000 !important;
}
/* Input fields - LIGHT background, DARK text */
input, textarea, select {
  background-color: #ffffff !important;
  color: #000000 !important;
  font-size: 15px !important;
}
/* Labels - DARK text */
label {
  color: #000000 !important;
  font-size: 15px !important;
}
/* Sidebar - LIGHT background */
div[data-testid="stSidebar"] {
  background-color: #f5f5f5 !important;
}
div[data-testid="stSidebar"] * {
  color: #000000 !important;
}
/* Buttons */
button {
  background-color: #ffffff !important;
  color: #000000 !important;
}
/* Headings */
h1, h2, h3, h4, h5, h6 {
  color: #000000 !important;
}
/* Simple card styling */
.wv-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}
.wv-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #000000 !important;
}
.wv-subtitle {
  font-size: 15px;
  color: #666666 !important;
  margin-bottom: 12px;
}
.wv-section-title {
  font-size: 17px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #000000 !important;
}
.wv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: white;
}
.wv-table th, .wv-table td {
  border-bottom: 1px solid #ddd;
  padding: 10px;
  text-align: left;
  color: #000000 !important;
}
.wv-table th {
  background: #f8f8f8;
  font-weight: bold;
  color: #000000 !important;
}
.wv-chip {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}
.wv-chip.good { background: #d4edda; color: #155724; }
.wv-chip.warn { background: #fff3cd; color: #856404; }
.wv-chip.bad { background: #f8d7da; color: #721c24; }
.wv-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}
.wv-pill.good { background: #d4edda; color: #155724; }
.wv-pill.warn { background: #fff3cd; color: #856404; }
.wv-pill.bad { background: #f8d7da; color: #721c24; }
.wv-kpi {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}
.wv-kpi-box {
  border: 1px solid #ddd;
  padding: 12px;
  border-radius: 6px;
  background: white;
}
.wv-kpi-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}
.wv-kpi-value {
  font-size: 20px;
  font-weight: bold;
}
.wv-mono {
  font-family: monospace;
  font-size: 14px;
  color: #000000 !important;
}
/* Code blocks */
pre, code {
  background-color: #f5f5f5 !important;
  color: #000000 !important;
}
/* Markdown */
p, div, span {
  color: #000000 !important;
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
    st.markdown("<p style='font-size: 14px; color: #666; margin-bottom: 16px;'>User-owned memory with consented commerce.</p>", unsafe_allow_html=True)
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
            st.markdown("<div class='wv-section-title'>Scopes & Pricing</div>", unsafe_allow_html=True)
            read_scopes = st.text_area(
                "Read scopes",
                "profile:name.read ($0.002)\nprofile:company.read ($0.002)\nprefs:outreach_tone.read ($0.001)\nprefs:writing_style.read ($0.001)",
                height=100,
            )
            write_scopes = st.text_area(
                "Write scopes (HITL approval)",
                "prefs:outreach_tone.write ($0.015)",
                height=60,
            )
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
      <tr><th>Request</th><th>Tool</th><th>Change</th><th>Cost</th><th>Status</th></tr>
    </thead>
    <tbody>
      <tr>
        <td class="wv-mono">appr_b8f2</td>
        <td>worldvault.prefs.write</td>
        <td><span style="color: #666;">outreach_tone</span> → "direct, warm, data-driven"</td>
        <td>$0.015</td>
        <td><span class="wv-pill warn">HOLD</span></td>
      </tr>
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
<div class="wv-kpi" style="margin-bottom: 14px;">
  <div class="wv-kpi-box">
    <div class="wv-kpi-label">Total Operations</div>
    <div class="wv-kpi-value">12</div>
  </div>
  <div class="wv-kpi-box">
    <div class="wv-kpi-label">Total Revenue</div>
    <div class="wv-kpi-value" style="color: var(--good);">$0.047</div>
  </div>
  <div class="wv-kpi-box">
    <div class="wv-kpi-label">Control Events</div>
    <div class="wv-kpi-value">2</div>
  </div>
</div>
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
  <div style="color: #666666; font-size: 13px; margin-bottom: 8px;">Pointers plus signed envelopes instead of raw values.</div>
  <pre class="wv-mono">memmachine_pointer = {
  "type": "wv_pointer",
  "vault_ref": "wv://enc/profile.name#v3",
  "envelope_sig": "sig_ed25519_..."
}</pre>
</div>
""",
            unsafe_allow_html=True,
        )
