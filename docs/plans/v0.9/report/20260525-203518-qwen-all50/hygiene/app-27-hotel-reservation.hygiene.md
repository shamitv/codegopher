# Hygiene - app-27-hotel-reservation

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 1
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `src/main/java/com/hotel/reservation/model/User.java:18` stripped-inline-comment: private String password; // Store hashed password (or plaintext if vulnerable, but we hash for decoy here)

## Residual Source Hints

- None
