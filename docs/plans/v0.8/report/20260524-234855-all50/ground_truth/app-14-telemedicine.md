# Ground Truth - app-14-telemedicine

- App key: `app-14-telemedicine`
- Source path: `D:\work\secure-code-hunt\apps\typescript\app-14-telemedicine`
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
