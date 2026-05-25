# Ground Truth - app-24-vet-clinic

- App key: `app-24-vet-clinic`
- Source path: `D:\work\secure-code-hunt\apps\python\app-24-vet-clinic`
- Language/framework: python / fastapi

## Expected Chained Attacks

### Weak JWT → SQL Injection → Prescription Tampering

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: An attacker cracks or guesses the weak JWT secret, forging a Veterinarian ('VET') session token. They then use the SQL injection vulnerability on the pet search endpoint to enumerate pet IDs and find targeted records. Finally, they call the prescription update endpoint to alter controlled substance prescriptions undetected due to the absence of logging.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | medium | `app.py` | `generate_token` | JWT signed with easily guessable hardcoded secret key. |
| 2 | A03 | medium | `app.py` | `search_pets` | SQL injection in pet search allows database exploration. |
| 3 | A09 | low | `app.py` | `update_prescription` | Prescription updating produces no audit logs. |
