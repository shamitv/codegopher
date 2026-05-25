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
