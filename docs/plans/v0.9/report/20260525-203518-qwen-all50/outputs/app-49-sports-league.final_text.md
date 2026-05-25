

The chained vulnerability static audit is complete. Here's a summary of the findings:

## Audit Complete

**Report written to:** `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### 3 Chains Detected:

| Chain | Severity | Confidence | Description |
|-------|----------|------------|-------------|
| **Chain-1** | HIGH | HIGH | Unauthenticated score update — any user can tamper with game results because the score endpoint has no authorization checks whatsoever |
| **Chain-2** | MEDIUM | HIGH | Debug mode on public interface — `debug=True` with `host='0.0.0.0'` exposes the Werkzeug debugger, enabling stack trace disclosure and potential remote code execution |
| **Chain-3** | MEDIUM | HIGH | Missing CSRF on COMMISSIONER endpoint — an authenticated commissioner can be tricked into creating teams on a malicious site via cross-site request forgery |

### Key Cross-Cutting Weaknesses:
- **Unused security utilities** (`allowed_callback`, `same_owner`, `normalize_identifier` in `reference_guards.py`) are never imported or used
- **No CSRF protection** on any mutating endpoints
- **No secret key** configured for Flask sessions
- **No rate limiting** or input sanitization beyond `.strip()`
- **Debug mode** enabled in what appears to be a deployable container

### Files Reviewed:
- `app.py` — 4 API routes (2 SQL queries, both parameterized)
- `reference_guards.py` — 3 security helper functions (all unused)
- `requirements.txt` — Flask 3.0.3 + bcrypt 4.1.3
- `Dockerfile` — Single-process Python 3.10 container
