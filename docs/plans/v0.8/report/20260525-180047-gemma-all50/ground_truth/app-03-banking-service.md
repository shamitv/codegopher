# Ground Truth - app-03-banking-service

- App key: `app-03-banking-service`
- Source path: `D:\work\secure-code-hunt\apps\python\app-03-banking-service`
- Language/framework: python / fastapi

## Expected Chained Attacks

### Unauthenticated Account Harvest → Cookie Interception → Unlimited Fund Drain

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker calls the unauthenticated /api/admin/users endpoint to harvest account numbers, intercepts a victim session cookie that travels without the Secure flag over plain HTTP, then uses that cookie to drain the victim's balance via the rate-limit-free transfer endpoint.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | medium | `app.py` | `admin_list_users` | GET /api/admin/users endpoint is publicly accessible without authentication, returning all users' account and routing numbers |
| 2 | A05 | low | `app.py` | `login` | Session cookie is set with httponly=True but without secure=True, allowing it to be transmitted over plain HTTP and intercepted by a network attacker |
| 3 | A04 | high | `app.py` | `dispatch_transfer` | Transfer endpoint applies no rate limiting, per-request amount cap, or daily transaction ceiling, allowing a stolen session to drain the full balance instantly |
