# Ground Truth - app-33-recruitment-ats

- App key: `app-33-recruitment-ats`
- Source path: `<secure-code-hunt>\apps\typescript\app-33-recruitment-ats`
- Language/framework: typescript / express

## Expected Chained Attacks

### Predictable API Key Derivation → Zip Slip Arbitrary File Write

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: An attacker targets a recruiter account (user ID 3) and computes their MD5-based API key: md5('3') = 'eccbc87e4b5ce2fe28308fd9f2a7baf3'. Authenticating with this admin key, they call the `/api/applications/upload-portfolio` endpoint and upload a ZIP archive containing a file entry named `../../package.json` to overwrite the application root files.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | medium | `src/index.ts` | `POST /api/auth/api-key` | User API tokens are derived predictably from the user ID via MD5. |
| 2 | A06 | medium | `src/index.ts` | `POST /api/applications/upload-portfolio` | Admin endpoint extracts ZIP archives without validating target paths, enabling file overwrite. |
