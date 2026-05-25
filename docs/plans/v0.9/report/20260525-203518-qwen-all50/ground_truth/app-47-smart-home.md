# Ground Truth - app-47-smart-home

- App key: `app-47-smart-home`
- Source path: `D:\work\secure-code-hunt\apps\python\app-47-smart-home`
- Language/framework: python / fastapi

## Expected Chained Attacks

### Debug Token Leak → SSRF Internal Recon → Unsigned Firmware Injection

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: An attacker queries the public /api/debug/devices debug endpoint to leak private device tokens. They then use the SSRF vulnerability in the sensor proxy endpoint to scan internal port ranges and locate private network hosts. Finally, the attacker uses the firmware update endpoint to point a device to a malicious unsigned binary stored on an internal host, achieving persistent compromise of the smart device.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `app.py` | `debug_devices` | Debug endpoint leaks device tokens. |
| 2 | A10 | medium | `app.py` | `fetch_sensor_data` | SSRF in sensor data proxy allows internal service scanning. |
| 3 | A08 | medium | `app.py` | `update_firmware` | Firmware update accepts arbitrary unsigned firmware binaries. |

### Subtle Ssrf Pivot To Auth Session

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | medium | `app.py` | `fetch_sensor_data` | The sensor data proxy endpoint processes user-provided URLs without validating if they point to private network addresses or internal hosts, allowing SSRF. |
| 2 | A08 | high | `app.py` | `update_firmware` | The firmware update endpoint accepts any URL and downloads the firmware binary without checking signatures, hashes, or origin authority. |
| 3 | A05 | high | `app.py` | `debug_devices` | An unauthenticated debug endpoint (/api/debug/devices) is exposed, leaking details of all registered devices along with their private access API tokens. |
