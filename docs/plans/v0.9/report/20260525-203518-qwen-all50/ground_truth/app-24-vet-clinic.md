# Ground Truth - app-24-vet-clinic

- App key: `app-24-vet-clinic`
- Source path: `<secure-code-hunt>\apps\python\app-24-vet-clinic`
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

### Subtle State Confusion Pivot To Auth Session

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | medium | `app.py` | `update_prescription` | Modifications to drug prescriptions (such as controlled substances like Ketamine) produce no audit logs or monitoring warnings, permitting undetected dosage alteration. |
| 2 | A03 | high | `app.py` | `search_pets` | The pet search endpoint concatenates user input directly into a raw SQL query, allowing SQL injection to bypass role checks or leak DB records. |
| 3 | A02 | high | `app.py` | `generate_token` | JWT authentication tokens are signed with a weak, hardcoded secret ('secret123') using HS256, allowing an attacker to forge arbitrary tokens (such as possessing a VET or ADMIN role). |
