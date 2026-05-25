

The chained vulnerability static audit is complete. The report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

## Key Findings

**3 confirmed attack chains** were identified:

### Chain 1 — SQL Injection (Critical, High Confidence)
- **Location:** `MeterController.java:25–29` — `searchReadings()` concatenates `meterSerial` and `dateRange` directly into a native SQL string, executed via `entityManager.createNativeQuery()`. No parameterized queries, no input sanitization.
- **Impact:** Full database read/write/delete, including user credential hashes, customer PII, invoices, and meter data.

### Chain 2 — SSRF (Critical, High Confidence)
- **Location:** `IntegrationController.java:17` — `fetchSmartMeterData()` accepts `meterEndpointUrl` as a request parameter and passes it verbatim to `RestTemplate.getForObject()`. Zero validation.
- **Impact:** Server-side HTTP requests to arbitrary destinations — cloud metadata endpoints (`169.254.169.254`), internal LAN services, database admin panels — leaking credentials and enabling lateral movement.

### Chain 3 — IDOR / Incomplete Authorization (High, High Confidence)
- **Location:** `BillingController.java:19` — `getInvoice()` has **no** authorization check at all; any authenticated user can retrieve any invoice.
- **Location:** `CustomerController.java:33–35` — The role guard only restricts `CUSTOMER` users. Non-customer roles (`BILLING_ADMIN`, `TECHNICIAN`, `ADMIN`) bypass all ownership checks and can fetch any customer record.
- **Impact:** Systematic privacy violation — bulk enumeration of all customer records and invoice data.

### 5 Cross-Cutting Weaknesses
H2 console exposed without auth, weak seeded credentials (`cust123`/`billing123`), CSRF disabled, no CORS config, missing input validation across controllers.
