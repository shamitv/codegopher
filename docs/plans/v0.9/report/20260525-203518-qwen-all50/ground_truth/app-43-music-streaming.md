# Ground Truth - app-43-music-streaming

- App key: `app-43-music-streaming`
- Source path: `<secure-code-hunt>\apps\javascript\app-43-music-streaming`
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

### Subtle Ssrf Pivot To Idor

- Chain ID: `chain-02`
- Impact: lateral_movement
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A10 | high | `src/index.js` | `GET /api/cover` | The cover art query proxy makes HTTP calls using axios on user-supplied URL inputs with no address block restriction, enabling SSRF. |
| 2 | A05 | medium | `src/index.js` | `GET /api/system/status` | An open diagnostics route leaks system node settings and an administrative metrics integration API token key when active debug query options are provided. |
| 3 | A01 | medium | `src/index.js` | `GET /api/playlists/:id` | Viewing private playlists by ID lacks checking user ownership, allowing any authenticated user to retrieve details of another listener's playlists. |
