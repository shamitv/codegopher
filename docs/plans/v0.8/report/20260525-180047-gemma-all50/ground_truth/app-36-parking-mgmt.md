# Ground Truth - app-36-parking-mgmt

- App key: `app-36-parking-mgmt`
- Source path: `<secure-code-hunt>\apps\javascript\app-36-parking-mgmt`
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
