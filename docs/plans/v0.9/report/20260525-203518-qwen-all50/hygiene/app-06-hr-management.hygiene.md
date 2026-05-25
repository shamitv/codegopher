# Hygiene - app-06-hr-management

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 2
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `src/main/java/com/hr/config/SecurityConfig.java:44` stripped-inline-comment: return new BCryptPasswordEncoder(); // Safe decoy pattern
- `src/main/java/com/hr/controller/EmployeeController.java:86` removed-line: // call this for any employee ID. Individually a minor IDOR, but the exposed hash

## Residual Source Hints

- None
