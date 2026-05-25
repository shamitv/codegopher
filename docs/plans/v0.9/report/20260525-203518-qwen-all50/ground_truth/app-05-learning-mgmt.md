# Ground Truth - app-05-learning-mgmt

- App key: `app-05-learning-mgmt`
- Source path: `<secure-code-hunt>\apps\python\app-05-learning-mgmt`
- Language/framework: python / flask

## Expected Chained Attacks

### Config Leak → Session Forgery → Pickle RCE → Data Exfiltration

- Chain ID: `chain-01`
- Impact: db_exfiltration
- Scenario: Attacker calls the unauthenticated /api/debug/config endpoint to read the Flask secret_key. Using this key, they forge a session cookie with admin/instructor role. With the forged admin session, they upload a malicious pickle payload via /api/courses/import to execute arbitrary code on the server and dump the entire database.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | low | `app.py` | `debug_config` | GET /api/debug/config returns the Flask secret_key and full server environment without authentication, enabling session cookie forgery. |
| 2 | A08 | medium | `app.py` | `import_course` | POST /api/courses/import deserializes user-supplied pickle data with pickle.loads(), allowing arbitrary code execution once an admin session is forged. |

### Subtle Deserialization Pivot To Idor

- Chain ID: `chain-02`
- Impact: db_exfiltration
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A08 | critical | `app.py` | `import_course` | Course import endpoint deserializes untrusted base64-encoded pickle data from user input using pickle.loads(), allowing arbitrary remote code execution. |
| 2 | A05 | medium | `app.py` | `debug_config` | Unauthenticated debug endpoint at /api/debug/config exposes the Flask secret_key, database path, full environment variables, and server working directory to any caller. |
| 3 | A01 | high | `app.py` | `get_submission` | Quiz submission retrieval endpoint returns any submission by ID without verifying the requesting user is the submission owner, allowing any authenticated student to view other students' answers and scores. |
