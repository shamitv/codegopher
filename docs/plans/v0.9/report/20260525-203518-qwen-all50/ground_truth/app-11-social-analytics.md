# Ground Truth - app-11-social-analytics

- App key: `app-11-social-analytics`
- Source path: `<secure-code-hunt>\apps\typescript\app-11-social-analytics`
- Language/framework: typescript / express

## Expected Chained Attacks

### SSRF to Cloud Metadata → Full Credential Response → IAM Key Exfiltration

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: Attacker posts the AWS IMDS URL to the SSRF preview endpoint; the now-untruncated response returns full IAM credential JSON including AccessKeyId, SecretAccessKey, and Token, enabling lateral movement across the cloud environment.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `src/index.ts` | `POST /api/preview` | POST /api/preview fetches any URL server-side via axios without IP or hostname validation, allowing access to cloud metadata services at 169.254.169.254 |
| 2 | A05 | low | `src/index.ts` | `POST /api/preview` | SSRF response body previously truncated to 500 chars; truncation removed, returning the full metadata credential payload (600+ bytes for AWS IMDSv1) |
| 3 | A05 | low | `src/index.ts` | `GET /api/debug/headers` | GET /api/debug/headers returns all request headers verbatim including internal proxy headers injected by cloud load balancers |

### Subtle State Confusion Pivot To Ssrf

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `public/js/app.js` | `global` | Security Misconfiguration. Sensitive internal reporting API keys are hardcoded directly into the client-side JavaScript bundle, exposing them to any end-user. |
| 2 | A03 | high | `public/js/app.js` | `renderWidgets` | Cross-Site Scripting (XSS). The frontend renders dashboard widget titles directly into the DOM using innerHTML without HTML entity encoding, allowing execution of arbitrary Javascript. |
| 3 | A10 | high | `src/index.ts` | `generatePreview` | Server-Side Request Forgery (SSRF) in URL preview generation. The /api/preview endpoint fetches remote URLs using axios.get without verifying the target domain or restricting internal IP spaces. |
