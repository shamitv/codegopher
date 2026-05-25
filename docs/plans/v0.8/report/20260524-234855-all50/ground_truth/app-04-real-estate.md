# Ground Truth - app-04-real-estate

- App key: `app-04-real-estate`
- Source path: `D:\work\secure-code-hunt\apps\python\app-04-real-estate`
- Language/framework: python / flask

## Expected Chained Attacks

### Debug Environment Exposure → SSRF Internal Recon → OS Command Injection RCE

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: Attacker reads internal environment variables via the exposed debug endpoint to discover service topology, then uses SSRF to probe internal endpoints and gather further context, then injects shell commands into the analyze endpoint to achieve RCE and exfiltrate data.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | low | `app.py` | `debug_env` | GET /api/debug/env returns full process environment variables and working directory without authentication |
| 2 | A10 | high | `app.py` | `import_external_image` | SSRF endpoint fetches arbitrary URLs with no IP-space restriction, enabling internal network mapping |
| 3 | A03 | high | `app.py` | `analyze_listing` | OS command injection via shell=True subprocess with user-controlled filename — executes arbitrary system commands |
