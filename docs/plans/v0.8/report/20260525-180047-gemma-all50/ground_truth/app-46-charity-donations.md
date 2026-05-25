# Ground Truth - app-46-charity-donations

- App key: `app-46-charity-donations`
- Source path: `D:\work\secure-code-hunt\apps\python\app-46-charity-donations`
- Language/framework: python / flask

## Expected Chained Attacks

### API Key Exposure → SQLi Donor Dump → Silent Refund Fraud

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: An attacker reads the hardcoded Stripe key from the source code. They then use the SQL injection vulnerability on the search donation endpoint to extract transaction IDs and donor information. Lastly, using the leaked Stripe credentials and transaction details, they trigger a refund to themselves silently due to missing audit logs.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | medium | `app.py` | `STRIPE_KEY` | Stripe API key hardcoded in source. |
| 2 | A03 | medium | `app.py` | `search_donations` | SQL injection in search donation query reveals private database records. |
| 3 | A09 | low | `app.py` | `process_refund` | Refunding donation generates no audit logs. |
