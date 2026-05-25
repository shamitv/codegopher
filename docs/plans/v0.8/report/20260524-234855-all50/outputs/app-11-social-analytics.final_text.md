

## Chained Vulnerability Static Audit — Complete

The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's the summary:

### Chains Detected: 4

| # | Chain | Severity | Confidence |
|---|-------|----------|------------|
| 1 | **SSRF → Cloud Metadata Credential Exfiltration** | **CRITICAL** | High |
| 2 | **SSRF → Header Exfiltration via `/api/debug/headers`** | **HIGH** | High |
| 3 | **Stored XSS via Widget Title → Session Theft** | **HIGH** | High |
| 4 | **Hardcoded Test Creds + Missing CSRF → Account Takeover** | **MEDIUM** | Medium |

### Key Findings

- **CRITICAL SSRF:** The `/api/preview` endpoint uses `axios.get(url)` with **no IP restrictions**, directly fetching user-supplied URLs. The comments explicitly document that the previous 500-character response cap was removed to allow "complete exfiltration of cloud metadata API responses" (e.g., AWS IAM credentials from `169.254.169.254`).

- **HIGH Header Leak:** The `/api/debug/headers` endpoint (`app.get('/api/debug/headers')`) returns **all request headers** with no authentication. Combined with SSRF reaching `127.0.0.1:8011/api/auth/me`, authenticated headers can be proxy-forwarded and dumped.

- **HIGH XSS:** Widget titles are rendered via `card.innerHTML` with **zero sanitization**. The HTML hint text even demonstrates the XSS payload: `<img src=x onerror=alert(1)>`. SSRF responses are similarly rendered via `innerHTML`.

- **MEDIUM Creds Exposed:** Test credentials (`alice/alice123`, `bob/bob123`) are hardcoded in the login page HTML, visible to any page visitor.

### Remediation Priority

1. **P0:** Block internal IPs in the SSRF fetcher; re-apply response size limits
2. **P0:** Sanitize all DOM insertions (replace `innerHTML` with `textContent`)
3. **P1:** Remove or authenticate `/api/debug/headers`
4. **P1:** Remove hardcoded credentials; add CSRF tokens

All code references, line numbers, Mermaid attack graphs, and detailed chain breakdowns are in the full report.
