# Ground Truth - app-38-museum-catalog

- App key: `app-38-museum-catalog`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-38-museum-catalog`
- Language/framework: javascript / express

## Expected Chained Attacks

### Stored Guestbook XSS → Session Hijack IDOR Exfiltration

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: An attacker posts an XSS cookie stealer payload to `/api/guestbook`. When the curator admin reviews the guestbook, their session cookie is leaked to the attacker. Using the hijacked admin cookie, the attacker bypasses access controls and queries `/api/exhibits/2` (IDOR) to exfiltrate private, high-value catalog notes.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `src/index.js` | `GET /api/guestbook` | Stored guestbook XSS script allows cookie theft. |
| 2 | A01 | medium | `src/index.js` | `GET /api/exhibits/:id` | Details endpoint permits IDOR exfiltration of sensitive records. |

### Subtle State Confusion Pivot To Idor

- Chain ID: `chain-02`
- Impact: db_exfiltration
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | low | `src/index.js` | `POST /api/exhibits/:id/delete` | Deleting sensitive museum artifacts from the catalog produces no audit log tracking outputs, blinding administrators to record destruction. |
| 2 | A03 | high | `src/index.js` | `GET /api/guestbook` | Visitor guestbook comments are rendered to the client without HTML entity encoding, leaving visitors vulnerable to Stored XSS. |
| 3 | A01 | medium | `src/index.js` | `GET /api/exhibits/:id` | The exhibit detail retrieval endpoint fails to verify if the requesting user owns the exhibit or possesses curator/admin permissions, allowing authenticated users to access confidential notes. |
