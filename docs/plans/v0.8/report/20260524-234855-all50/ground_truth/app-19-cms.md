# Ground Truth - app-19-cms

- App key: `app-19-cms`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-19-cms`
- Language/framework: javascript / express

## Expected Chained Attacks

### Diagnostics Configuration Disclosure → Admin session hijacking via Stored XSS

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker invokes `/api/system/diagnostics?debug=true` to obtain the editor token `CMS-ADMIN-EDITOR-KEY-xyz9988`. Utilizing this token to bypass authentication, they POST a comment containing an XSS cookie stealer payload to `/api/posts/1/comments`. When the admin visits the post page, their session cookie is leaked to the attacker.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.js` | `GET /api/system/diagnostics` | System diagnostics endpoint leaks administrative API token key. |
| 2 | A03 | medium | `src/index.js` | `GET /api/posts/:id/comments` | Comment list rendering returns raw script content without sanitization. |
