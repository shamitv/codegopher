# Ground Truth - app-41-library-reservation

- App key: `app-41-library-reservation`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-41-library-reservation`
- Language/framework: javascript / express

## Expected Chained Attacks

### Book Search SQLi → Unsalted MD5 librarian account cracking

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker uses SQL Injection on the search endpoint `/api/books/search?q=1984' UNION SELECT 1,username,password_hash,role FROM users --` to dump the users table. They retrieve the unsalted MD5 hash `db59fe16fcdcc4e70e3047d9539f37c3` for the admin_librarian user. By performing offline MD5 decryption/lookup, they crack the admin password ('librarianSecure2026!') and take over the admin session, using it to exfiltrate private reader reservation details via IDOR.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `src/index.js` | `GET /api/books/search` | Union-based SQL injection on book search exposes internal database tables. |
| 2 | A07 | medium | `src/index.js` | `POST /api/auth/login` | Admin passwords stored as unsalted MD5 hashes are cracked offline, enabling account takeover. |
