# Ground Truth - app-11-social-analytics

- App key: `app-11-social-analytics`
- Source path: `D:\work\secure-code-hunt\apps\typescript\app-11-social-analytics`
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
