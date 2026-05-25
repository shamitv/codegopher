# Ground Truth - app-04-real-estate

- App key: `app-04-real-estate`
- Source path: `<secure-code-hunt>\apps\python\app-04-real-estate`
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

### Subtle Ssrf Pivot To Injection

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | high | `app.py` | `import_external_image` | Server-Side Request Forgery (SSRF). The remote image import endpoint fetches image resources from user-provided URLs using requests.get without validating, restricting, or sanitizing internal local network IPs |
| 2 | A05 | medium | `app.py` | `app_config` | Security Misconfiguration. Flask debug mode is explicitly set to True in production run configs, and it utilizes a default widely known secret key (secret_key=dev), permitting session tampering and remote debugger access |
| 3 | A03 | high | `app.py` | `process_image_metadata` | OS Command Injection. The image analyzer tool uses subprocess.Popen with shell=True to execute a command containing an unvalidated property file path or image metadata name, permitting arbitrary shell execution |
