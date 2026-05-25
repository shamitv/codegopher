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
