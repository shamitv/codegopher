

## Chained Vulnerability Static Audit Complete

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's what was found:

### 4 Chained Vulnerabilities Discovered

| # | Chain | Severity | Confidence |
|---|---|---|---|
| **1** | Debug Endpoint → Admin Token → Auth Bypass → `eval()` RCE | **CRITICAL** | HIGH |
| **2** | `Math.random()` Session ID → Prediction → Account Takeover | **HIGH** | HIGH |
| **3** | `eval()` Error → Verbose `err.message` → Information Disclosure → Recon | **MEDIUM** | HIGH |
| **4** | Missing CSRF + no `sameSite`/`secure` cookie flags → State Tampering | **MEDIUM** | MEDIUM |

### Key Findings

1. **CRITICAL — `eval()` on user input** at `src/index.ts:78`: The `POST /api/documents` endpoint evaluates raw user-controlled `metadata` via `eval()`, enabling full remote code execution.

2. **CRITICAL — Hardcoded admin credential** (`ADMIN-DEV-TOKEN-KEY-8871`): Exposed via the unauthenticated debug endpoint (`/api/admin/debug`), then used to bypass `requireAuth` middleware entirely.

3. **HIGH — Weak session IDs**: `Math.random()` + `Date.now()` produces predictable session tokens with insufficient entropy.

4. **MEDIUM — No CSRF protection + insecure cookie config**: `sameSite` and `secure` flags are missing from the session cookie, enabling cross-site state tampering.

### Priority Remediations
- **P0**: Replace `eval()` with `JSON.parse()` (the codebase already has a safe `/api/documents/safe` endpoint — use it)
- **P0**: Remove or properly gate the `/api/admin/debug` endpoint
- **P1**: Replace `Math.random()` with `crypto.randomBytes()` for session IDs
- **P1**: Remove the hardcoded `x-admin-token` auth bypass
