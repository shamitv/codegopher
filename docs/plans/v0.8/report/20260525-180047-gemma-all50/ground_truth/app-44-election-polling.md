# Ground Truth - app-44-election-polling

- App key: `app-44-election-polling`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-44-election-polling`
- Language/framework: javascript / express

## Expected Chained Attacks

### Predictable Voter Ballot Retrieval → Concurrent Vote Casting

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: An attacker queries `/api/candidates` to read all cast voter ballots in plaintext (`A02`). Finding active user accounts who have not yet voted, the attacker sends concurrent, parallel HTTP requests to `/api/vote/cast` exploiting the race condition (`A04`) to submit multiple unauthorized votes under those users' identities, achieving data manipulation without logging triggers (`A09`).

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | medium | `src/index.js` | `GET /api/candidates` | Exposing plaintext database ballots compromises voter selection details. |
| 2 | A04 | medium | `src/index.js` | `POST /api/vote/cast` | Casting votes has an asynchronous timing window enabling race-based double-voting. |
