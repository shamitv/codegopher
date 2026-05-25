# Ground Truth - app-40-pet-adoption

- App key: `app-40-pet-adoption`
- Source path: `<secure-code-hunt>\apps\javascript\app-40-pet-adoption`
- Language/framework: javascript / express

## Expected Chained Attacks

### Diagnostics Configuration Disclosure → Remote Code Execution via Insecure Deserialization

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: An attacker invokes `/api/system/diagnostics?debug=true` to obtain the layout configuration token `PET-PORTAL-DEV-LAYOUT-KEY-2026`. Utilizing this token in the header `x-layout-token` to bypass authentication, they POST a layout configuration payload to `/api/pets/layout` containing a system command execution string evaluated via eval().

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/index.js` | `GET /api/system/diagnostics` | System diagnostics endpoint leaks layout customization token key. |
| 2 | A08 | medium | `src/index.js` | `POST /api/pets/layout` | Layout update route executes custom strings using eval() without checks. |
