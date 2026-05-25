The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Summary of Findings

### 4 Attack Chains Detected

| Chain | Severity | Confidence | Path |
|---|---|---|---|
| **Chain 1: PNR Enumeration → IDOR → XSS** | **High** | **High** | Sequential PNR (`BK000001`, `BK000002`...) allows any authenticated user to enumerate all bookings via the boarding-summary endpoint, which lacks an ownership check and returns the passenger name as raw HTML — enabling reflected XSS. |
| **Chain 2: Public SQL Injection** | **Critical** | **High** | The unauthenticated `/api/flights/search` endpoint passes user input directly into SQL string concatenation in `FlightSearchDao.java`, allowing full database read access (and potential writes). |
| **Chain 3: Exposed H2 Console → RCE** | **Critical** | **Medium** | H2 console is enabled, remotely accessible (`web-allow-others=true`), behind a `permitAll` path, with an empty password — giving unauthenticated attackers full SQL access and potential Java code execution via H2's `CREATE ALIAS`. |
| **Chain 4: CSRF Disabled + Session Fixation → ATO** | **High** | **High** | Both CSRF and session fixation protections are explicitly disabled, enabling cross-origin state-changing attacks. |

### Key Cross-Cutting Weaknesses
- **Clickjacking** (frame options disabled)
- **Double-booking race condition** (no locking on seat reservation)
- **Price manipulation** by staff (no validation/auditing)
- **No password strength enforcement** server-side
