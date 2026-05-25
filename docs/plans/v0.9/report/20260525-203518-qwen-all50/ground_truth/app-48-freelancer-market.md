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

### Subtle Auth Session Pivot To Idor

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `app.py` | `login` | Session tokens are generated using a predictable PRNG (random.randint) rather than a cryptographically secure random generator, allowing session prediction and hijacking. |
| 2 | A04 | medium | `app.py` | `release_payment` | The payment release feature allows clients or unauthorized users to release escrow funds before delivery verification is performed and fails to check client-job association. |
| 3 | A01 | medium | `app.py` | `get_proposal` | The proposal detail endpoint returns competitor bids to any authenticated user without validating if the user is the hiring client or the submitting freelancer. |
