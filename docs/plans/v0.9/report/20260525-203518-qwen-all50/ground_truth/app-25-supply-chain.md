# Ground Truth - app-25-supply-chain

- App key: `app-25-supply-chain`
- Source path: `<secure-code-hunt>\apps\python\app-25-supply-chain`
- Language/framework: python / flask

## Expected Chained Attacks

### SSRF → YAML Deserialization → Lateral Movement

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: An attacker uses the SSRF vulnerability in the supplier health check endpoint to fetch an internal URL. By pointing the inventory import endpoint to an internal server or using the SSRF capability to retrieve a payload, they feed a malicious YAML document to yaml.load(), triggering unsafe deserialization and arbitrary code execution.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `app.py` | `check_supplier_api` | SSRF endpoint fetches arbitrary URL. |
| 2 | A06 | medium | `app.py` | `import_inventory` | Deserializes fetched contents with unsafe yaml.load(), executing arbitrary system commands. |

### Subtle Ssrf Pivot To Deserialization

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `app.py` | `check_supplier_api` | Supplier API check endpoint allows fetching user-supplied URLs without restricting requests to external public IPs, causing SSRF. |
| 2 | A07 | medium | `app.py` | `login` | Passwords are stored in plaintext in the database and queried directly without hashing, and the session cookie lacks the Secure flag. |
| 3 | A06 | high | `requirements.txt` | `PyYAML` | Pins vulnerable PyYAML==5.3.1 which permits arbitrary code execution (RCE) via yaml.load() when parsing untrusted serialization inputs. |
