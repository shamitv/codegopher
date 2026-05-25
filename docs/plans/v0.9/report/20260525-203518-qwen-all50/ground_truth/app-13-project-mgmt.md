# Ground Truth - app-13-project-mgmt

- App key: `app-13-project-mgmt`
- Source path: `<secure-code-hunt>\apps\typescript\app-13-project-mgmt`
- Language/framework: typescript / express

## Expected Chained Attacks

### Board IDOR → Stored XSS in Task Comments → Session Token Exfiltration

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: Attacker accesses a cross-org board via IDOR, posts a script payload as a task comment. When the victim org's manager views the board and the comment is rendered via innerHTML, the script exfiltrates their session_id cookie (readable because httpOnly is absent). Attacker hijacks the manager session.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | medium | `src/index.ts` | `GET /api/boards/:id` | GET /api/boards/:id does not verify board.orgId matches the authenticated user's orgId, allowing cross-organization board and task access |
| 2 | A03 | medium | `src/index.ts` | `POST /api/boards/:boardId/tasks/:taskId/comments` | Task comments stored and returned without HTML sanitization; script tags in comment content execute as Stored XSS when rendered via innerHTML by the frontend |
| 3 | A07 | medium | `src/index.ts` | `POST /api/auth/login cookie` | Session cookie set without httpOnly flag; JavaScript can read document.cookie, enabling the XSS payload to exfiltrate the session token |

### Subtle State Confusion Pivot To Ssrf

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A09 | medium | `src/index.ts` | `updateBoardPermissions` | Security Logging and Monitoring Failures. The endpoint modifies sensitive project access permissions but fails to generate any audit logs or trace events. |
| 2 | A03 | high | `public/js/app.js` | `renderTasks` | Cross-Site Scripting (XSS). Task descriptions are rendered into the DOM using innerHTML without HTML entity encoding, allowing execution of malicious Javascript payloads. |
| 3 | A01 | high | `src/index.ts` | `getBoardById` | Broken Access Control. The endpoint fetches project boards directly by their numeric ID without verifying if the requested board belongs to the currently authenticated user's organization. |
