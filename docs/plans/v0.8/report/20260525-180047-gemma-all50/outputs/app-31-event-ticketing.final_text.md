

# Chained Vulnerability Static Audit Complete

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's a summary of findings:

## 3 Complete Chains Identified

### 🔴 Chain 1 — SQL Injection → Full DB Exfiltration (Critical)
- **Entry:** `GET /api/events/search` — unauthenticated SQL injection via string concatenation at `src/index.ts:95`
- **Path:** Injected query → verbose error leaks full query string → UNION SELECT dumps all tables including user password hashes
- **Remediation:** Parameterize the SQL query with `?` placeholders

### 🔴 Chain 2 — SQL Injection + Weak Passwords → Admin Takeover (Critical)
- **Entry:** Same SQL injection as Chain 1
- **Path:** Extract password hashes → crack weak seed passwords (`admin_tickets_2026`, `alice_pass_123`) → login as admin → hoard all tickets via unrate-limited booking endpoint with no race condition protection
- **Remediation:** Fix SQL injection + enforce password complexity + add booking rate limits

### 🟠 Chain 3 — Weak Sessions + No CSRF → Session Hijacking (High)
- **Entry:** 6-digit session IDs (`100000`–`999999`) = only ~900K possible values
- **Path:** Brute-force/guess sessions → impersonate any user → unauthorized bookings + data access via `/api/tickets/book` and `/api/bookings`
- **Remediation:** Use `crypto.randomBytes(32)` + add CSRF tokens + tighten CORS

## 5 Cross-Cutting Weaknesses (not forming chains)
1. Hardcoded seed credentials in source
2. No input validation on `ticket_count` (arbitrary large integers allowed)
3. Non-atomic booking check-then-update (race condition / overselling)
4. No session rotation on privilege change (session fixation)
5. No rate limiting on any endpoint

## Top 2 P0 Remediations (lowest effort, highest impact)
1. **Parameterize the SQL query** at `src/index.ts:95` — breaks Chains 1 and 2 simultaneously
2. **Replace session ID generation** with `crypto.randomBytes(32).toString('hex')` — breaks Chain 3 brute-force path
