# Hygiene - app-07-airline-booking

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 7
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `src/main/java/com/airline/config/SecurityConfig.java:82` stripped-inline-comment: return new BCryptPasswordEncoder(); // BCrypt is secure (decoy)
- `src/main/java/com/airline/controller/BookingController.java:71` removed-line: // returned to the client; if rendered via innerHTML it executes as XSS.
- `src/main/java/com/airline/controller/BookingController.java:82` removed-line: // Vulnerable: no ownership check performed before returning data
- `src/main/java/com/airline/controller/BookingController.java:83` removed-line: // Vulnerable: passengerDisplay contains raw passenger name for HTML rendering (XSS)
- `src/main/java/com/airline/service/PnrGenerator.java:6` removed-line: // PNR trivially enumerable (BK000001, BK000002, ...). Individually this seems like
- `src/main/java/com/airline/service/PnrGenerator.java:7` removed-line: // a minor implementation detail, but it is the prerequisite for the IDOR and XSS
- `src/main/java/com/airline/service/PnrGenerator.java:8` removed-line: // links that follow.

## Residual Source Hints

- None
