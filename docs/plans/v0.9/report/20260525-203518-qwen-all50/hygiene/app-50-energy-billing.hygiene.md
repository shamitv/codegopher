# Hygiene - app-50-energy-billing

- Passed: yes
- Removed evaluator files: 3
- Sanitized source hints: 1
- Residual source hints: 0

## Removed Evaluator Files

- `.vulns`
- `README.md`
- `scenarios.md`

## Sanitized Source Hints

- `src/main/java/com/energy/billing/controller/BillingController.java:18` removed-line: // IDOR: directly return the invoice by ID without checking if it belongs to the current user

## Residual Source Hints

- None
