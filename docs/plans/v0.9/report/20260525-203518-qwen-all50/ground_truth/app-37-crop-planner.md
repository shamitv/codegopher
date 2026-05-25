# Ground Truth - app-37-crop-planner

- App key: `app-37-crop-planner`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-37-crop-planner`
- Language/framework: javascript / express

## Expected Chained Attacks

### Diagnostics Configuration Exposure → SSRF Crop Analytics Pivoting

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: An attacker queries `/api/system/config?debug=true` to obtain the weather service token key `CROP-DEV-WEATHER-API-TOKEN-2026`. Utilizing the weather lookup proxy `/api/weather/proxy`, they submit `weatherUrl: 'http://localhost:8037/api/internal/telemetry?token=CROP-DEV-WEATHER-API-TOKEN-2026'`, leveraging the SSRF vulnerability to bypass authentication and retrieve all farm crop records from the internal analytics database.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.js` | `GET /api/system/config` | System diagnostics endpoint leaks weather integration API secret token key. |
| 2 | A10 | medium | `src/index.js` | `GET /api/weather/proxy` | Weather query proxy makes external requests with no IP filtering rules. |

### Subtle Ssrf Pivot To Injection

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | high | `src/index.js` | `GET /api/weather/proxy` | The weather forecast query proxy makes HTTP calls using axios on user-supplied URL inputs with no address block restriction, enabling SSRF. |
| 2 | A06 | high | `src/index.js` | `POST /api/crop-plan/import-layout` | An layout zip importer extracts files using relative archive paths without checking target folder bounds, allowing Zip Slip path traversal file overwrite. |
| 3 | A05 | medium | `src/index.js` | `GET /api/system/config` | An open diagnostics route leaks system node settings and an administrative weather integration API token key when active debug query options are provided. |
