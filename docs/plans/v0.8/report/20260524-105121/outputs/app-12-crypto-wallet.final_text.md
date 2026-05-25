The chained vulnerability audit is complete. Here is a summary of what was found:

---

## Audit Results

### 🔴 Chain 01 (Critical) — IDOR → Private Key Exposure → Unauthorized Fund Transfer

This three-hop chain is **fully provable from source** with High confidence:

| Hop | Weakness | File | Lines |
|---|---|---|---|
| **Entry** | Login with hardcoded plaintext credentials | `src/auth/auth.module.ts` | 14–23 |
| **Hop 1** | IDOR: `?userId=N` accepted without ownership check | `src/wallet/wallet.controller.ts` | 17–23 |
| **Hop 2** | A02: Private key returned in plaintext (no DTO filtering) | `src/wallet/wallet.service.ts` | 7–13 |
| **Sink** | External transfer accepts `fromAddress` without verifying ownership | `src/wallet/wallet.controller.ts` + `src/wallet/wallet.service.ts` | 31–42 / 57–93 |

An attacker who logs in as any user can view **any other user's wallet** (including the private key) via the unvalidated `?userId` query parameter, then drain funds by calling `external-transfer` with the victim's address.

### Additional Weaknesses Catalogued (7 total)

- W-01: Plaintext password storage
- W-02: No CSRF protection
- W-03: Weak session token (user ID as cookie value)
- W-04: No rate limiting
- W-05: No transaction confirmation step
- W-06: No MFA for high-value transfers
- W-07: Verbose error messages enabling address enumeration

The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.
