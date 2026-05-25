# Ground Truth - Airline Booking

- App key: `app-07-airline-booking`
- Source path: `D:\work\secure-code-hunt\apps\java\app-07-airline-booking`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### Sequential PNR Enumeration → Booking IDOR → Stored XSS on Staff View

- Chain ID: `chain-01`
- Impact: account_takeover
- Scenario: Attacker registers with a name containing a script tag, enumerates sequential PNRs to access other passengers' bookings via the IDOR boarding-summary endpoint, and the malicious name executes as XSS when airline staff renders the boarding list, stealing staff session cookies.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A04 | low | `src/main/java/com/airline/service/PnrGenerator.java` | `generate` | PNR generated as an incrementing integer counter making all booking references predictable and enumerable |
| 2 | A01 | medium | `src/main/java/com/airline/controller/BookingController.java` | `getBoardingSummary` | GET /api/bookings/{pnr}/boarding-summary returns full booking details without verifying the requesting user owns the PNR |
| 3 | A03 | medium | `src/main/java/com/airline/controller/BookingController.java` | `getBoardingSummary` | Passenger name is concatenated into a raw HTML string in the API response without encoding; executes as Stored XSS when rendered via innerHTML on staff UI |
