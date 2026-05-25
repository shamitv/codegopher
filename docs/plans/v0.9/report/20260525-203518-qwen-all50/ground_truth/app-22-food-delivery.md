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

### Subtle Auth Session Pivot To Injection

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `app.py` | `login` | Session cookie is set without the HttpOnly or Secure flags, making it vulnerable to extraction via Cross-Site Scripting (XSS). |
| 2 | A04 | medium | `app.py` | `place_order` | No rate limiting or idempotency checks on order placement, allowing clients to send infinite duplicate order requests, leading to resource exhaustion or denial of service. |
| 3 | A02 | medium | `app.py` | `PAYMENT_SECRET` | Payment processing API key is hardcoded as a module-level constant in the source code. |
