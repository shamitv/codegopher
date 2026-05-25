# Ground Truth - app-37-crop-planner

- App key: `app-37-crop-planner`
- Source path: `<secure-code-hunt>\apps\javascript\app-37-crop-planner`
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
