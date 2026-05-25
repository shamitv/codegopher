

The chained vulnerability static audit is complete. Here's a summary of what was found:

## Audit Complete — 5 Chains Detected

| Chain | Severity | Confidence | Summary |
|---|---|---|---|
| **1** | CRITICAL | High | SQL Injection → Admin Credential Harvest → Full Data Exfiltration |
| **2** | HIGH | High | Hardcoded Secret Key → Session Forgery → Privilege Escalation |
| **3** | HIGH | High | Adjuster Role → Claim Approval → Unauthorized Payouts (No Audit) |
| **4** | MEDIUM | Medium | Debug Mode + Public Binding → Arbitrary Code Execution |
| **5** | MEDIUM | High | IDOR on Claims → Mass PII Exfiltration |

## 12 Weaknesses Cataloged

Key findings across the single-file Flask application (`app.py`, ~191 lines):
- **SQL injection** in the claims search endpoint (lines 133–141) with no parameterization
- **Plaintext passwords** stored directly in seed data (lines 58–61), never hashed
- **Hardcoded Flask secret key** enabling session forgery (line 9)
- **No ownership checks** on claims endpoints — any authenticated user can read any claim's PII (line 147)
- **No audit trail** on claim approvals/payouts, with the code explicitly acknowledging this (line 174 comment)
- **Debug mode enabled** in a deployable Docker image (line 191)

## Report Location

The full report with Mermaid attack graphs, source line references, impact assessments, and a prioritized remediation roadmap has been written to:

`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`
