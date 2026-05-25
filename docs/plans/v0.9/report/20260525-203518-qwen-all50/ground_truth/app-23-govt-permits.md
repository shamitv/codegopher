# Ground Truth - app-23-govt-permits

- App key: `app-23-govt-permits`
- Source path: `D:\work\secure-code-hunt\apps\python\app-23-govt-permits`
- Language/framework: python / django

## Expected Chained Attacks

### Debug Page Info Leak → Unrestricted Upload → RCE

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: The attacker triggers an error page on the application. Because DEBUG=True is active, the error page leaks internal paths, system configurations, and settings. Using this information, the attacker uploads a malicious script through the permit document upload feature. Knowing the internal media paths leaked via the debug page, the attacker invokes the script directly to execute arbitrary code.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | low | `govt_permits/settings.py` | `settings` | DEBUG=True is enabled, exposing settings and path structures via error pages. |
| 2 | A08 | medium | `permits/views.py` | `upload_document` | Unrestricted file upload accepts arbitrary executable scripts and saves them in a predictable web-accessible directory. |

### Subtle Path Traversal Pivot To Idor

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A08 | high | `permits/views.py` | `upload_document` | The permit document upload endpoint does not validate file extensions or MIME types, permitting users to upload arbitrary scripts (e.g. Python scripts) that can then be executed by direct request because of the static files handler running in DEBUG mode. |
| 2 | A05 | medium | `govt_permits/settings.py` | `settings` | The application runs with DEBUG=True, wildcard ALLOWED_HOSTS, and a hardcoded SECRET_KEY, disclosing system details on error pages and exposing session signatures. |
| 3 | A01 | medium | `permits/views.py` | `permit_detail` | Permit detail endpoint fails to verify if the requesting user is the applicant or has reviewer privileges, allowing any authenticated user to view other citizens' permit applications. |
