

The chained vulnerability static audit is complete. Here's a summary of what was found:

**4 Attack Chains Detected:**

1. **CRITICAL** — SSRF via `/api/properties/import-image` → Internal network reconnaissance → Cloud metadata exfiltration. The SSRF endpoint accepts any URL with `requests.get()` and no IP restrictions, allowing attackers to probe internal services and potentially steal cloud IAM credentials.

2. **HIGH** — Hardcoded credentials in `static/index.html` → Login as agent_smith → Unauthenticated message injection. Plaintext credentials (`alice/alice123`, `agent_smith/agent123`) are embedded in the HTML. The `POST /api/messages` write endpoint has zero authentication, enabling arbitrary message injection.

3. **HIGH** — Debug mode (`debug=True`) + verbose errors + `/api/debug/env` → Werkzeug debugger PIN exposure → Arbitrary Python RCE. Flask runs with debug mode, the env dump endpoint leaks all environment variables (including potential Werkzeug PIN material), and the debugger provides a Python REPL.

4. **MEDIUM** — Unauthenticated property creation → Data pollution → Social engineering via fake listings and agent message queue hijacking.

**7 Cross-Cutting Weaknesses** were catalogued, including missing CSRF protection, no Content Security Policy, session without SECRET_KEY, unbound host (`0.0.0.0`), unused security guard functions in `reference_guards.py`, and no CORS configuration.

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with full Mermaid attack graphs, source code line references, confidence ratings, and prioritized remediation guidance.
