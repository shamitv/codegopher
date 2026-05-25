# Hygiene - app-07-airline-booking

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 3
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `src/main/java/com/airline/config/SecurityConfig.java:82` stripped-inline-comment: return new BCryptPasswordEncoder(); // BCrypt is secure (decoy)
- `src/main/java/com/airline/controller/BookingController.java:82` removed-line: // Vulnerable: no ownership check performed before returning data
- `src/main/java/com/airline/controller/BookingController.java:83` removed-line: // Vulnerable: passengerDisplay contains raw passenger name for HTML rendering (XSS)

## Residual Source Hints

- None
