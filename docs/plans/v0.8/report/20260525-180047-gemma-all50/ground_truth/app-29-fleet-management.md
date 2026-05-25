# Ground Truth - app-29-fleet-management

- App key: `app-29-fleet-management`
- Source path: `D:\work\secure-code-hunt\apps\java\app-29-fleet-management`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### Log4Shell → SSRF → Lateral Movement

- Chain ID: `chain-01`
- Impact: lateral_movement
- Scenario: Attacker triggers Log4Shell injection via search parameter which gets logged via Log4j 2.14.1, gains initial execution environment access, and exploits the unvalidated SSRF endpoint to query cloud metadata (169.254.169.254) and retrieve IAM credentials.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A06 | medium | `src/main/java/com/fleet/mgmt/controller/VehicleController.java` | `searchVehicles` | Application uses Log4j 2.14.1 and logs query inputs, making it vulnerable to JNDI injection. |
| 2 | A10 | medium | `src/main/java/com/fleet/mgmt/controller/IntegrationController.java` | `fetchExternalVehicleData` | Integration endpoint does not validate URLs before fetching them, permitting SSRF to internal/cloud metadata networks. |
