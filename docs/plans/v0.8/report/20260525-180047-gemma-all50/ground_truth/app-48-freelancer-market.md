# Ground Truth - app-48-freelancer-market

- App key: `app-48-freelancer-market`
- Source path: `<secure-code-hunt>\apps\python\app-48-freelancer-market`
- Language/framework: python / fastapi

## Expected Chained Attacks

### Weak Token → IDOR Bid Espionage → Payment Fraud

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker logs in, takes note of the generated session token structure, and predicts another user's session token offline due to the predictable PRNG. The attacker hijacks the victim's session, uses the IDOR vulnerability on the proposal endpoint to read competitor bid values and pricing details, and then triggers the payment release endpoint to steal project funds.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `app.py` | `login` | Weak session token generation via predictable random number generator. |
| 2 | A01 | medium | `app.py` | `get_proposal` | IDOR on proposal details endpoint leaks sensitive competitor bid info. |
