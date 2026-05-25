# Ground Truth - app-01-ecommerce-catalog

- App key: `app-01-ecommerce-catalog`
- Source path: `<secure-code-hunt>\apps\python\app-01-ecommerce-catalog`
- Language/framework: python / flask

## Expected Chained Attacks

### User Enumeration → Session Forge → Admin Takeover

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: Attacker confirms admin username via unauthenticated existence endpoint, then forges a Flask session cookie using the hardcoded secret_key visible in source code, gaining admin-level access without any credentials.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | low | `app.py` | `user_exists` | GET /api/users/exists returns 200/404 per username, confirming valid accounts without authentication |
| 2 | A05 | medium | `app.py` | `app_config` | Flask secret_key is a hardcoded string in source code, allowing any party with source access to forge valid signed session cookies for any user or role |
| 3 | A05 | low | `app.py` | `all_post_endpoints` | No CSRF tokens on any state-changing endpoint — the forged session cookie is sufficient to invoke admin-only mutations |

### Subtle State Confusion Pivot To Idor

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | medium | `app.py` | `create_order` | High-value and sensitive financial activities, including order checkouts, payment state mappings, and catalog stock alterations, are executed without producing any structured audit logs or trace monitoring records |
| 2 | A03 | high | `app.py` | `list_products` | Product search query parameter is concatenated directly into a raw SQLite SELECT statement without parameterization, permitting SQL injection bypasses |
| 3 | A01 | high | `app.py` | `get_order_details` | Order retrieval endpoint returns order data solely based on the order_id path variable, performing no owner validation checks between the authenticated user and the requested order's client |
