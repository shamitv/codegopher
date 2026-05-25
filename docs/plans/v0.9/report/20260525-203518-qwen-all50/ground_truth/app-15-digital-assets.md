# Ground Truth - app-15-digital-assets

- App key: `app-15-digital-assets`
- Source path: `<secure-code-hunt>\apps\typescript\app-15-digital-assets`
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

### Subtle Ssrf Pivot To Ssrf

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `src/index.ts` | `POST /api/assets/import` | Import endpoint fetches file content from user-specified URLs using the global fetch API without restricting requests to loopback or private IP ranges. |
| 2 | A08 | high | `src/index.ts` | `POST /api/assets/upload` | Upload endpoint uses Multer disk storage and accepts any file extension with no validation, writing files directly into the web-accessible directory. |
| 3 | A01 | high | `src/index.ts` | `GET /api/assets/:id` | Asset detail endpoint returns private files and download URLs by ID without checking if the requesting user owns the asset. |
