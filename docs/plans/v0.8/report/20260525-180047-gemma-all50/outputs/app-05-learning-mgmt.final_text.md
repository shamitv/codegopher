

## Audit Complete

The chained vulnerability static audit has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### Summary of Findings

| Chain | Severity | Description | Confidence |
|---|---|---|---|
| **Chain 1** | **Critical** | Remote Code Execution via untrusted pickle deserialization at `/api/courses/import` | High |
| **Chain 2** | **High** | Unauthenticated debug endpoint → secret key leak → session forgery → full privilege escalation | High |
| **Chain 3** | **Medium** | IDOR on `/api/submissions/<id>` → any authenticated user can view all student submissions | High |

### Key Weaknesses (Not in Chains)

- **Verbose error leakage** (`str(e)` returned on all error paths)
- **Debug mode + host binding** (`debug=True`, `host='0.0.0.0'`)
- **No CSRF protection** or CORS policy
- **Plaintext passwords** hardcoded in source
- **No input validation** on any user inputs

### P0 Remediation Actions

1. **Remove `pickle.loads()`** — Replace with JSON/JSONL import to eliminate RCE
2. **Hash all passwords** with bcrypt/argon2 — Never store or compare plaintext
3. **Delete `/api/debug/config`** — Exposes secret key, env vars, and internal config
4. **Use cryptographically random secret key** — Never hardcode `app.secret_key`

The report includes full Mermaid attack graphs, line-level evidence, chain breakdowns, a priority matrix, and recommendations for additional testing.
