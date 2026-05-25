

The full chained vulnerability audit is complete. Here is the final summary:

---

# Audit Complete: Construction Tracker (app-42)

## What was reviewed

| File | Purpose |
|---|---|
| `src/index.js` | Main Express app — 8 routes, SQLite in-memory DB, session store |
| `src/referenceGuards.js` | Unused security utility functions (`sameOwner`, `allowedCallback`, `normalizeIdentifier`) |
| `package.json` | Dependencies (Express, bcryptjs, sqlite3, cors, cookie-parser) |
| `Dockerfile` | Node 20-slim container, exposes port 8042 |

## Chains detected: **3**

### 🔴 Chain #1 — RCE via `eval()` (Critical / High confidence)
An authenticated user POSTs to `/api/contracts/template` with arbitrary JavaScript in `templateConfig`. The raw string is passed to `eval()` with no validation. This is a **confirmed direct Remote Code Execution** path — any registered user can execute arbitrary Node.js code in the process context.

### 🟠 Chain #2 — Account Takeover via predictable sessions (High / High confidence)
Session IDs are generated with `Math.random() + Date.now()`. V8's `Math.random()` is a predictable Xorshift PRNG. No session expiry, fingerprinting, or regeneration is implemented. An attacker who sees one session ID can predict/fake others and hijack any user account (including admin).

### 🟡 Chain #3 — Privilege escalation via hardcoded creds (Medium / Medium confidence)
The admin user `admin_inspector` is seeded with password `inspector2026Secure!` in source code. Combined with Chain #2 (session hijacking), a single weak hop gives full admin access. The registration endpoint also leaks username existence.

## Cross-cutting weaknesses (not forming complete chains)

1. **Hardcoded admin password** in source — identical across every deployment
2. **No CSRF protection** — any site can POST to authenticated endpoints
3. **Verbose error leakage** — `evalErr.message` exposed to clients
4. **No rate limiting** on `/login` or `/register`
5. **No persistence** — in-memory SQLite, lost on restart
6. **Dead security code** — `referenceGuards.js` exports helpers that are never wired in

## Prioritized remediation

| Priority | Fix | Effort |
|---|---|---|
| **P0** | Replace `eval()` with `JSON.parse()` + schema validation | ~10 min |
| **P1** | Swap `Math.random()` → `crypto.randomUUID()` | ~5 min |
| **P1** | Move admin password to environment variable | ~5 min |
| **P2** | Add CSRF tokens | ~30 min |
| **P2** | Add rate limiting on auth routes | ~15 min |
| **P3** | Wire or remove `referenceGuards.js` | ~10 min |

---

The full report has been written to **`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`**.
