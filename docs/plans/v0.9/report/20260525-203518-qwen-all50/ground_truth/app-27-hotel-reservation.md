# Ground Truth - app-27-hotel-reservation

- App key: `app-27-hotel-reservation`
- Source path: `D:\work\secure-code-hunt\apps\java\app-27-hotel-reservation`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### Debug Info Leak → Session Fixation → Account Takeover

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: Attacker targets the unauthenticated debug endpoint to discover default credentials and environment details, sets up session fixation targeting the admin session, and successfully takes over the admin account once the admin logs in.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | medium | `src/main/java/com/hotel/reservation/controller/AdminController.java` | `getSystemInfo` | Unauthenticated debug configuration endpoint exposes system info and credentials. |
| 2 | A07 | medium | `src/main/java/com/hotel/reservation/config/SecurityConfig.java` | `filterChain` | Security config session management lacks session rotation, allowing session fixation. |

### Subtle Auth Session Pivot To Injection

- Chain ID: `chain-02`
- Impact: account_takeover
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | medium | `src/main/java/com/hotel/reservation/config/SecurityConfig.java` | `filterChain` | Session fixation protection is disabled via sessionFixation().none(), meaning session IDs are not rotated upon login |
| 2 | A05 | medium | `src/main/java/com/hotel/reservation/controller/AdminController.java` | `getSystemInfo` | Exposed admin debug endpoint without authentication leaks system variables and default admin credentials |
| 3 | A03 | high | `src/main/java/com/hotel/reservation/controller/RoomController.java` | `searchRooms` | JPQL query constructed using string concatenation with user-supplied parameters allows SQL/JPQL injection |
