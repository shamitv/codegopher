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
