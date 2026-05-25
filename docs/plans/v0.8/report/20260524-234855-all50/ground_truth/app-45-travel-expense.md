# Ground Truth - app-45-travel-expense

- App key: `app-45-travel-expense`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-45-travel-expense`
- Language/framework: javascript / express

## Expected Chained Attacks

### Expense Search SQLi → Unsalted MD5 administrator credentials extraction → Corporate Expenses Exfiltration via IDOR

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: An attacker logs in as a low-privilege customer and uses SQL Injection on the `/api/expenses/search?q=xyz' UNION SELECT 1,username,password_hash,role,5.0,'USD' FROM users --` endpoint to dump the user credentials. The attacker retrieves the unsalted MD5 password hash `97b9f87efd939e99eb015560b43ffbb4` for user `admin_accountant`. They decrypt this hash offline to recover the password ('accountantSecure2026!') and log in. Once authenticated as an administrator, they use IDOR on `/api/expenses/:id` to retrieve and exfiltrate all employee expense records.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `src/index.js` | `GET /api/expenses/search` | Union-based SQL injection on expense search exposes all user table credentials. |
| 2 | A07 | medium | `src/index.js` | `POST /api/auth/login` | Unsalted MD5 password storage allows offline recovery of the administrator password. |
