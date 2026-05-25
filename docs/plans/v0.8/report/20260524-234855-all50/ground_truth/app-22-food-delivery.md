# Ground Truth - app-22-food-delivery

- App key: `app-22-food-delivery`
- Source path: `D:\work\secure-code-hunt\apps\python\app-22-food-delivery`
- Language/framework: python / fastapi

## Expected Chained Attacks

### Hardcoded Secret Key → Webhook Forgery → Free Orders

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: An attacker extracts the hardcoded PAYMENT_SECRET from the source code. They then call the payment webhook endpoint directly, providing this secret as the auth token, to mark their pending orders as paid without completing actual payment.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A02 | medium | `app.py` | `PAYMENT_SECRET` | Payment secret is hardcoded in the source code. |
| 2 | A04 | medium | `app.py` | `payment_webhook` | Payment webhook verifies authority by checking the hardcoded PAYMENT_SECRET without checking signature or request origin. |
