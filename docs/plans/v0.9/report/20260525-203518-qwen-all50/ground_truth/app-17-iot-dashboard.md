# Ground Truth - app-17-iot-dashboard

- App key: `app-17-iot-dashboard`
- Source path: `<secure-code-hunt>\apps\javascript\app-17-iot-dashboard`
- Language/framework: javascript / express

## Expected Chained Attacks

### Diagnostic Trace Leak → SSRF Internal Network Pivoting

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: An attacker sends a TRIGGER-ERROR command to `/api/devices/command` to force a server exception, which leaks the telemetry API credentials: `INTERNAL-SECRET-TELEMETRY-TOKEN-2026`. The attacker then makes a POST request to `/api/devices/refresh` with `statusUrl: 'http://localhost:8017/api/internal/telemetry?token=INTERNAL-SECRET-TELEMETRY-TOKEN-2026'`, leveraging the SSRF vulnerability to bypass authentication and exfiltrate internal system telemetry.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.js` | `POST /api/devices/command` | Verbose stack trace leaks internal telemetry server token. |
| 2 | A10 | medium | `src/index.js` | `POST /api/devices/refresh` | Status update proxy fetches internal endpoints without IP filtering. |

### Subtle Ssrf Pivot To Crypto

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | high | `src/index.js` | `POST /api/devices/refresh` | The device status refresh handler calls external URLs using axios without validating if the IP is internal, allowing SSRF. |
| 2 | A05 | medium | `src/index.js` | `POST /api/devices/command` | Detailed configuration details (such as API secret keys) and stack traces are returned to the user on execution failure. |
| 3 | A02 | medium | `src/index.js` | `initDb` | Device secret access keys are stored in plaintext in the database instead of being hashed or encrypted. |
