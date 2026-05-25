# Hygiene - app-08-warehouse-mgmt

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 3
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `src/main/java/com/warehouse/config/SecurityConfig.java:50` stripped-inline-comment: return new BCryptPasswordEncoder(); // SAFE decoy pattern
- `src/main/java/com/warehouse/service/ShippingService.java:20` removed-line: // User-controlled URL retrieved directly by the server (SSRF A10 target)
- `src/main/resources/application.properties:10` removed-line: # Planted Vulnerability: Actuator exposure without restrictions

## Residual Source Hints

- None
