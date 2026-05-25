

The chained vulnerability static audit is complete. Here's a summary of findings:

## Audit Summary

**4 chained vulnerability paths** identified across this LMS codebase, with **2 CRITICAL** severity chains.

### Chains Found

| # | Chain | Severity | Confidence |
|---|---|---|---|
| 1 | **Pickle RCE** via `/api/courses/import` — untrusted `pickle.loads()` on base64-decoded user input | Critical | High |
| 2 | **Credential → Session Forgery → Account Takeover** — hardcoded secret key + plaintext passwords enable forged session cookies | Critical | High |
| 3 | **IDOR on `/api/submissions/<id>`** — any authenticated user can view any other student's exam answers and scores | High | High |
| 4 | **Unauthenticated debug dump** — `/api/debug/config` exposes Flask secret key, env vars, Python version, server path | High | Medium |

### Most Dangerous Combined Path
Debug endpoint (unauthenticated) → Secret key exposed → Session forgery (become admin) → Pickle import → **Complete system RCE**

### Key Cross-Cutting Weaknesses
- Plaintext password storage (not even hashed)
- No CSRF protection on any POST endpoint
- Debug mode (`debug=True`) enabled for production
- Verbose error messages leaking internals
- `reference_guards.py` contains unused security helpers (`same_owner`, `allowed_callback`)

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with Mermaid attack graphs, line-level evidence, and prioritized remediation recommendations (P0/P1/P2).
