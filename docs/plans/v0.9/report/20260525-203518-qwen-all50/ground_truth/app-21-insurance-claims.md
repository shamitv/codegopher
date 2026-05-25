# Ground Truth - app-21-insurance-claims

- App key: `app-21-insurance-claims`
- Source path: `D:\work\secure-code-hunt\apps\python\app-21-insurance-claims`
- Language/framework: python / flask

## Expected Chained Attacks

### SQL Injection → IDOR Claim Access → Silent Payout Fraud

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker uses SQL injection in the claim search endpoint to discover internal claim IDs and amounts. They then exploit the IDOR vulnerability on the claim detail endpoint to view and understand claim data. Finally, they leverage the lack of audit logging on the approval endpoint to approve fraudulent claims and trigger payouts without any trace.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `app.py` | `search_claims` | SQL injection in claim search reveals internal claim IDs, amounts, and status values that are not normally visible to the attacker's role. |
| 2 | A01 | medium | `app.py` | `get_claim` | IDOR on claim detail endpoint allows viewing any claim's full details including claimant PII, policy information, and payout history. |
| 3 | A09 | low | `app.py` | `approve_claim` | Claim approval endpoint writes no audit logs, enabling an attacker with adjuster access to approve fraudulent claims and trigger payouts silently. |

### Subtle Auth Session Pivot To Idor

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | medium | `app.py` | `approve_claim` | High-value claim approvals and automatic payout dispatches produce no audit logs, making it impossible to detect fraudulent approvals or trace who authorized payouts. |
| 2 | A03 | high | `app.py` | `search_claims` | Claim search endpoint concatenates user input directly into a raw SQL WHERE clause without parameterization, permitting SQL injection to extract arbitrary data from the database. |
| 3 | A01 | high | `app.py` | `get_claim` | Claim detail endpoint returns any claim by ID without verifying the requesting user is the claimant, exposing other customers' PII, payout amounts, and policy details. |
