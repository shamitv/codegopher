

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Complete — 4 Chains Detected, 5 Cross-Cutting Weaknesses

### Chains Found

| # | Chain | Severity | Confidence |
|---|-------|----------|------------|
| 1 | **Unauthenticated Admin Endpoint + No Rate Limiting → Mass Financial Drain** | CRITICAL | HIGH |
| 2 | **NoSQL Injection in Transaction Filter → Unauthorized Data Access** | HIGH | HIGH |
| 3 | **Hardcoded Debug Credentials + Missing CSRF → Full Account Takeover** | HIGH | HIGH |
| 4 | **Race Condition in Balance Check → Negative Balance / Double-Spend** | MEDIUM | MEDIUM |

### Key Findings

1. **Chain 1 (CRITICAL)**: The `/api/admin/users` endpoint requires **zero authentication** and returns all usernames, account numbers, and routing numbers. Combined with `POST /api/transfers` having **no rate limiting** (explicitly commented in `app.py` lines 1-2), an attacker can drain any account by spamming wire transfers.

2. **Chain 2 (HIGH)**: The `/api/transactions` endpoint accepts a `filter` query parameter that is passed directly as a MongoDB query. The frontend **explicitly teaches** NoSQL injection operators (`$ne`, `$gt`) in the UI, confirming the vulnerability is known but unmitigated.

3. **Chain 3 (HIGH)**: Plaintext credentials for all three users (`alice/alice123`, `bob/bob123`, `charlie/charlie123`) are hardcoded in `static/index.html`. With no CSRF protection on login or transfer endpoints, any site can forge requests on an authenticated user's behalf.

4. **Chain 4 (MEDIUM)**: The balance read-check-write sequence in transfers is not atomic — a TOCTOU race condition allows concurrent requests to all pass the balance check, potentially producing negative balances.

### Report Location
📄 `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`

### Top Priority Remediations (P0)
- Remove hardcoded credentials from HTML
- Add rate limiting to transfer endpoint
- Protect admin endpoint with authentication + admin role check
