# Ground Truth - app-43-music-streaming

- App key: `app-43-music-streaming`
- Source path: `D:\work\secure-code-hunt\apps\javascript\app-43-music-streaming`
- Language/framework: javascript / express

## Expected Chained Attacks

### Diagnostics Configuration Exposure → SSRF Playlist Analytics Pivoting

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: An attacker queries `/api/system/status?debug=true` to obtain the metrics service token key `INTERNAL-METRICS-API-SECRET-2026`. Utilizing the cover lookup proxy `/api/cover`, they submit `url: 'http://localhost:8043/api/internal/analytics?token=INTERNAL-METRICS-API-SECRET-2026'`, leveraging the SSRF vulnerability to bypass authentication and retrieve all private playlists from the internal analytics database.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.js` | `GET /api/system/status` | System status endpoint leaks metrics integration API secret token key. |
| 2 | A10 | medium | `src/index.js` | `GET /api/cover` | Cover art proxy makes external requests with no IP filtering rules. |
