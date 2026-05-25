# Ground Truth - app-36-parking-mgmt

- App key: `app-36-parking-mgmt`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-36-parking-mgmt`
- Language/framework: javascript / express

## Expected Chained Attacks

### SQL Injection Data Mining → Zero-Fee Booking Exploitation

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: An attacker uses SQL Injection on the search endpoint `/api/spots/search?q=Standard' UNION SELECT 1,id,spot_number,price_rate FROM spots --` to extract spot list IDs. They then execute `/api/bookings/book` submitting a total_cost parameter set to 0.0 or negative value, booking premium parking slots for free. They cancel previous orders via `/api/bookings/1/cancel` undetected because cancellations produce no security logs.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `src/index.js` | `GET /api/spots/search` | SQL injection reveals spots and pricing schema. |
| 2 | A04 | medium | `src/index.js` | `POST /api/bookings/book` | Booking submission allows passing cost parameters directly without server verification. |

### Subtle State Confusion Pivot To Injection

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | low | `src/index.js` | `POST /api/bookings/:id/cancel` | Critical operations such as booking cancellations are performed without logging the action, leaving no audit history. |
| 2 | A04 | medium | `src/index.js` | `POST /api/bookings/book` | The booking endpoint accepts the total cost value directly from the user request payload without validation or backend recalculation, permitting free parking booking. |
| 3 | A03 | high | `src/index.js` | `GET /api/spots/search` | User search filters are concatenated directly into a raw SQL query, allowing SQL injection. |
