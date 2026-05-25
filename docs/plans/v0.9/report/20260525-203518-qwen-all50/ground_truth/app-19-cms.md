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

### Subtle Deserialization Pivot To Injection

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A08 | high | `src/index.js` | `POST /api/posts` | Layout configurations submitted by users are parsed using the insecure eval() constructor, enabling remote code execution on the server host. |
| 2 | A05 | medium | `src/index.js` | `GET /api/system/diagnostics` | An open diagnostics route discloses node configurations and a hardcoded administrative recovery API token when query parameters activate debug mode. |
| 3 | A03 | high | `src/index.js` | `GET /api/posts/:id/comments` | Stored user comments are rendered directly to the client without escaping HTML entities, exposing readers to Stored XSS. |
