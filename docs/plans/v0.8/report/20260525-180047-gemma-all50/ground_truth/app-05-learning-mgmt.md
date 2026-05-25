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
