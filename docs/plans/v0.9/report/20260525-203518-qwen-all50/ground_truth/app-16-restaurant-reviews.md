# Ground Truth - app-16-restaurant-reviews

- App key: `app-16-restaurant-reviews`
- Source path: `<secure-code-hunt>\apps\javascript\app-16-restaurant-reviews`
- Language/framework: javascript / express

## Expected Chained Attacks

### Predictable Session Hijacking → IDOR Review Sabotage

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: An attacker predicts the session cookie values of an active customer or food critic generated via Math.random(). They hijack the target critic's session, call `/api/reviews/1/edit` to hijack or modify high-rating review comments to sabotage the restaurant status, achieving unauthorized data modification.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `src/index.js` | `POST /api/auth/login` | Weak session token generation via predictable random number generator. |
| 2 | A01 | medium | `src/index.js` | `POST /api/reviews/:id/edit` | Review editing allows users authenticated with hijacked session to overwrite reviews without owner check. |

### Subtle Auth Session Pivot To Idor

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `src/index.js` | `POST /api/auth/login` | Session keys are generated using non-cryptographic Math.random() function, making session IDs predictable and prone to hijacking. |
| 2 | A03 | high | `src/index.js` | `GET /api/restaurants/search` | User input in search parameter is concatenated directly into SQL query statement, exposing the database to SQL injection. |
| 3 | A01 | medium | `src/index.js` | `POST /api/reviews/:id/edit` | The review editing endpoint does not verify whether the authenticated user is the owner of the review or has admin privileges, allowing arbitrary review modification. |
