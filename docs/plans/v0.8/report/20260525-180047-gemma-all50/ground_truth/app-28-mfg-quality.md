# Ground Truth - app-28-mfg-quality

- App key: `app-28-mfg-quality`
- Source path: `<secure-code-hunt>\apps\java\app-28-mfg-quality`
- Language/framework: java / spring-boot

## Expected Chained Attacks

### Privilege Escalation → Silent Defect Closure → Undetected Quality Fraud

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker registers as WORKER, updates profile via mass assignment to gain QA_MANAGER role, marks critical defects as resolved, and changes failed inspection records to passed without any audit trails.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | medium | `src/main/java/com/manufacturing/qc/controller/AuthController.java` | `updateProfile` | Mass assignment allows escalating privilege from WORKER to QA_MANAGER. |
| 2 | A04 | medium | `src/main/java/com/manufacturing/qc/controller/DefectController.java` | `resolveDefect` | Lack of defect closure approval allows self-resolution of major defects. |
| 3 | A09 | low | `src/main/java/com/manufacturing/qc/service/InspectionService.java` | `updateInspectionResult` | No logging on inspection modifications allows silent data tampering. |
