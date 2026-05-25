

The static chained vulnerability audit is complete. Here's a summary of findings:

---

## Audit Summary: Library Book Reservation System

**3 chains detected**, **5 cross-cutting weaknesses**, maximum severity **CRITICAL**.

### Chain 1 — SQL Injection → Admin Takeover (CRITICAL / High Confidence)
- **Entry:** `GET /api/books/search?q=` (line 112) — unsanitized query parameter
- **Hop:** String concatenation builds raw SQL (line 113-114) — no parameterized binding
- **Sink:** `db.all(sql)` executes arbitrary SQL on all tables
- **Compounded by:** MD5 password hashing (crackable) + hardcoded admin credentials in source + verbose error leaks

### Chain 2 — Weak Sessions + Permissive CORS + No CSRF → Session Hijacking (HIGH / High Confidence)
- **CORS** (`origin: true`, `credentials: true` at line 14) allows any origin to read cookies
- **CSRF gap:** POST endpoints have no token, `SameSite`, or Origin validation
- **Weak sessions:** `Math.random()` generates predictable IDs (~27-40 bits entropy)
- **No `secure` flag** on cookies, no session expiration

### Chain 3 — SQL Injection + Weak Sessions → Privilege Escalation (HIGH / Medium Confidence)
- Injection enumerates all users + reservations
- Weak session IDs or CORS/CSRF gaps enable session hijacking
- Architectural mitigant: app has **no mutation endpoints** for reservations/books, limiting worst-case data integrity impact

### P0 Remediations (do first)
1. Parameterize the search query
2. Replace MD5 with bcrypt/argon2
3. Restrict CORS to specific origins
4. Add `SameSite=Strict` cookie attribute
5. Use `crypto.randomBytes()` for session IDs

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
