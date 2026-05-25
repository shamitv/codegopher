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
