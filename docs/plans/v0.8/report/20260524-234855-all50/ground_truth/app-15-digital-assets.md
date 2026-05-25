# Ground Truth - app-15-digital-assets

- App key: `app-15-digital-assets`
- Source path: `D:\work\secure-code-hunt\apps\typescript\app-15-digital-assets`
- Language/framework: typescript / express

## Expected Chained Attacks

### SSRF File Fetch → Predictable Path RCE

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: An attacker uses the SSRF vulnerability on the import endpoint to fetch a script from an internal service or external host. The file is saved directly into the public web directory (`/uploads/`) with its original filename due to unvalidated upload logic, allowing the attacker to execute it via direct HTTP request.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `src/index.ts` | `POST /api/assets/import` | SSRF in asset import fetches arbitrary network URLs. |
| 2 | A08 | medium | `src/index.ts` | `POST /api/assets/import` | Unrestricted file writing places fetched script inside web public uploads directory, enabling RCE. |
