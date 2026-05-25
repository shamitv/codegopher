

The chained vulnerability static audit is complete. Here's what was accomplished:

### Audit Summary

**🔴 1 confirmed HIGH-severity chained vulnerability found:**

1. **Hardcoded JWT Secret → Token Forgery → Privilege Escalation → Unauthorized Data Access** (HIGH)
   - The hardcoded secret `healthcare123` on line 13 allows anyone to forge arbitrary JWT tokens with any role
   - Forged admin tokens grant access to all appointments without any resource-level authorization checks
   - The `/api/appointments/:id` endpoint has an IDOR — it never verifies the user owns/associated with the requested appointment

### 5 Cross-Cutting Weaknesses Identified:

| # | Weakness | Risk |
|---|---|---|
| WC-1 | Permissive CORS (`origin: true` + `credentials: true`) | Latent XSS data theft risk |
| WC-2 | Insecure cookies (`httpOnly: false`, `secure: false`) | Cookie theft via XSS/network sniffing |
| WC-3 | Hardcoded seed credentials | Source code credential exposure |
| WC-4 | Verbose SQLite error messages | Schema/DB info leakage |
| WC-5 | No rate limiting on auth endpoints | Brute-force attack surface |

### What Was Written

The full report has been saved to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md` with:
- Mermaid attack graph for the confirmed chain
- Detailed source/code/line references for every link
- Impact, severity, confidence, and remediation recommendations
- 6 recommended tests to add
- Unknowns and not-reviewed areas

### Highest Priority Remediation

**Replace the hardcoded JWT secret** with a strong random value from environment variables — this single change breaks the entire chain.
