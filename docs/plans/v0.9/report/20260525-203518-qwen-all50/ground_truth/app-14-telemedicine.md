# Ground Truth - app-14-telemedicine

- App key: `app-14-telemedicine`
- Source path: `<secure-code-hunt>\apps\typescript\app-14-telemedicine`
- Language/framework: typescript / express

## Expected Chained Attacks

### Weak JWT Signatures → IDOR Records Exfiltration

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: An attacker cracks or guesses the weak JWT secret offline, then crafts a custom JWT asserting a doctor role. Using this forged token, they query the appointment details endpoint to exfiltrate private patient records and doctor consultation notes via IDOR.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | medium | `src/index.ts` | `login` | JWT signed with weak secret key. |
| 2 | A01 | medium | `src/index.ts` | `GET /api/appointments/:id` | IDOR on appointment endpoint reveals sensitive notes and details. |

### Subtle Auth Session Pivot To Idor

- Chain ID: `chain-02`
- Impact: db_exfiltration
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `src/index.ts` | `login` | Session token cookie is set with httpOnly: false, permitting client-side scripts to access it and exposing users to session hijacking via XSS. |
| 2 | A02 | high | `src/index.ts` | `generateJWT` | Authentication tokens are signed with a weak, hardcoded secret ('healthcare123') using HS256, allowing offline key cracking or token forgery. |
| 3 | A01 | high | `src/index.ts` | `GET /api/appointments/:id` | Appointment details endpoint retrieves private physician notes and patient PII by ID without checking if the requesting user is the patient or doctor assigned to the appointment. |
