# Ground Truth - app-31-event-ticketing

- App key: `app-31-event-ticketing`
- Source path: `<secure-code-hunt>\apps\typescript\app-31-event-ticketing`
- Language/framework: typescript / express

## Expected Chained Attacks

### Predictable Session Hijacking → SQLi Ticket Theft

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker predicts the session tokens of other active customers due to the use of Math.random(). They hijack a customer's session, execute SQL injection on the event search to dump private ticket orders, and cancel or steal premium reservations.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `src/index.ts` | `login` | Weak session token generation via predictable random number generator. |
| 2 | A03 | medium | `src/index.ts` | `GET /api/events/search` | SQL injection in event search reveals customer details and transaction info. |

### Subtle Auth Session Pivot To Injection

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `src/index.ts` | `login` | Session identifiers are generated using Math.random() (a predictable PRNG) instead of cryptographically secure random values, permitting session hijacking. |
| 2 | A04 | medium | `src/index.ts` | `POST /api/tickets/book` | The ticket booking endpoint lacks rate limits, transactional locking, or concurrency limits, permitting automated scripting to deplete ticket inventories. |
| 3 | A03 | high | `src/index.ts` | `GET /api/events/search` | Event search endpoint concatenates user search queries directly into raw SQL statements, exposing the system to SQL injection. |
