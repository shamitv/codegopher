# Chained Vulnerability Static Audit Report

**Project:** app-08-warehouse-mgmt (Warehouse Management System)  
**Date:** 2026-05-24  
**Auditor:** CodeGopher — Static-Only Chained Vulnerability Audit  
**Tech Stack:** Spring Boot 3.2.5, JPA/H2, Spring Security, Spring LDAP, UnboundID LDAP SDK  
**Files Reviewed:** 32 source files across controllers, services, repositories, models, DTOs, config, resources, and tests  

---

## Summary Dashboard

| Metric | Value |
|---|---|
| **Total Chains Identified** | **4** |
| **Maximum Severity** | **HIGH** (Chain 3 – SSRF → Sensitive Data Exposure) |
| **Confidence Levels** | 2 High, 1 Medium, 1 High |
| **Chains by Severity** | 1 HIGH, 2 MEDIUM, 1 LOW |
| **Areas Reviewed** | Controllers, Services, Repositories, Security Config, LDAP Config, Data Initializer, Application Properties, Frontend SPA, LDIF, Dockerfile |
| **Areas Not Fully Reviewed** | Runtime behavior (session fixations, CORS headers, CSRF mitigation in non-form contexts), internal network topology, TLS configuration |

---

## Methodology & Safety Note

- **Static-only review.** No live probes, dynamic scanners, shell commands, SQL injection payloads, or exploit scripts were executed.
- Evidence was gathered from source code, configuration files, test files, and static analysis of control/data flow.
- Confidence ratings: **High** = every link statically provable from cited source. **Medium** = plausible but one link depends on runtime behavior not fully visible. **Low** = weakly supported hypothesis.
- Remediation is always the **easiest link to break** in each chain.

---

## Chain 1: LDAP Injection → Directory Structure Exposure → Employee PII Harvesting

### Attack Graph

```mermaid
flowchart LR
    A["User Search Query<br>(/api/employees/search?q=)"] --> B["LDAP Filter Concatenation<br>EmployeeLdapService.java:34"]
    B --> C["Unsanitized LDAP Query<br>ldapTemplate.search()"]
    C --> D["LDAP Server Response<br>Or Exception On Error"]
    D --> E["Verbose Error in HTTP Body<br>EmployeeController.java:56-58"]
    E --> F["Attacker Harvests PII & DN Paths"]
    
    classA entry; classB hop; classC hop; classD hop; classE hop; classF sink
    classDef entry fill:#00695C,color:#fff
    classDef hop fill:#1565C0,color:#fff
    classDef sink fill:#C62828,color:#fff
```

### Detailed Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Entry** | `EmployeeController.java` | `@GetMapping("/search")` | Accepts `@RequestParam("q") String searchTerm` — raw user input, no sanitization or validation |
| **Hop 1** | `EmployeeLdapService.java:34` | `String filter = "(&(objectClass=inetOrgPerson)(|(cn=*" + searchTerm + "*)(uid=*" + searchTerm + "*)))";` | **LDAP injection** — `searchTerm` is directly concatenated into an LDAP filter string. An attacker can inject `*)(uid=*))(|(uid=*` to alter the filter semantics (e.g., bypass `cn` and `uid` conditions, match all entries) |
| **Hop 2** | `EmployeeLdapService.java:37` | `ldapTemplate.search("ou=employees", filter, ...)` | The crafted filter is passed to Spring LDAP's `LdapTemplate.search()`, which builds and executes the query against the embedded UnboundID LDAP server |
| **Hop 3** | `EmployeeController.java:56-58` | `return ResponseEntity.status(500).body(Map.of("error", e.getMessage(), "cause", String.valueOf(e.getCause())));` | When the LDAP server rejects a malformed filter, the **exception message and cause** are returned verbatim in the HTTP 500 body — exposing LDAP DN paths, directory hierarchy, and server internals |
| **Sink** | Application-level | Multiple endpoints | Attacker can (a) manipulate filter to **bypass search constraints**, potentially extracting PII of all employees, (b) trigger errors to **enumerate directory structure** (DNs, OUs, base DN), and (c) craft filters to **extract all attributes** including email addresses, job titles, and department numbers |

### Preconditions & Assumptions

- The embedded LDAP server (`LdapConfig.java`) starts on every application launch (`@PostConstruct`) with seed data from `warehouse.ldif`
- No input length limit or character allowlist is enforced on the `q` parameter
- LDAP is the **only** employee data source (no database backup)

### Impact

- **Medium** severity. LDAP injection can enumerate all employee records and PII. Error messages expose internal directory paths. While this does not directly lead to authentication bypass (LDAP is a directory service, not the auth store for Spring Security), it provides reconnaissance data useful for social engineering or targeted attacks.

### Confidence: High

Every link is statically provable from cited source files. The LDAP filter concatenation, the LDAP query execution, and the verbatim error return are all concrete.

### Remediation (Easiest Link)

1. **Escape LDAP special characters** in user input before building the filter, or better yet, use **LDAP's built-in safe escaping** via `DirContextMatcher` or parameterized search with `SearchControls`.
2. **Remove verbose error response** — return a generic "Search failed" message without internal exception details.

---

## Chain 2: Exposed Actuator Endpoints → Sensitive Configuration Disclosure → Credential Exposure

### Attack Graph

```mermaid
flowchart LR
    A["Unauthenticated HTTP Request<br>/actuator/env, /actuator/health, /actuator/heapdump"] --> B["SecurityConfig.permitAll Actuator<br>SecurityConfig.java"]
    B --> C["application.properties Exposure<br>management.endpoints.web.exposure.include=*,<br>management.endpoint.env.show-values=ALWAYS"]
    C --> D["Environment Variables, DB Config,<br>LDAP Connection URL, DB Credentials"]
    D --> E["Heap Dump Contains In-Memory Data<br>management.endpoint.heapdump.enabled=true"]
    E --> F["Attacker Exposes Secrets & Session Data"]
    
    classA entry; classB hop; classC hop; classD hop; classE hop; classF sink
    classDef entry fill:#00695C,color:#fff
    classDef hop fill:#1565C0,color:#fff
    classDef sink fill:#C62828,color:#fff
```

### Detailed Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Entry** | `SecurityConfig.java` | `.requestMatchers("/actuator/**").permitAll()` | Actuator endpoints are **explicitly exempted** from authentication. Any unauthenticated user can access them |
| **Hop 1** | `application.properties` | `management.endpoints.web.exposure.include=*` | **All** actuator endpoints are exposed (health, env, beans, configprops, heapdump, threaddump, info, etc.) |
| **Hop 2** | `application.properties` | `management.endpoint.env.show-values=ALWAYS` | The `/actuator/env` endpoint returns **all environment variable values**, including database credentials, LDAP URLs, and any other secrets configured as environment variables |
| **Hop 3** | `application.properties` | `management.endpoint.heapdump.enabled=true` | The `/actuator/heapdump` endpoint is enabled and returns a full Java heap dump — which can contain **in-memory passwords, session data, cached LDAP entries**, and application state |
| **Sink** | Application-level | Multiple properties | The `application.properties` also reveals: `spring.datasource.username=sa`, `spring.datasource.password=` (empty), `spring.datasource.url=jdbc:h2:mem:warehousedb`, `ldap://localhost:8389` base DN, and `spring.jpa.show-sql=true` (verbose SQL logging) |

### Preconditions & Assumptions

- The application is accessible on port 8082 from the network
- Spring Boot Actuator defaults are inherited for any endpoint not explicitly overridden
- The heapdump endpoint generates a live dump of the JVM memory

### Impact

- **Medium** severity. An unauthenticated attacker can enumerate the entire application configuration, database credentials, LDAP connection details, and dump in-memory application state. The empty H2 database password combined with exposed JDBC URL allows direct database access if the H2 console is reachable. Heap dumps may contain hashed (and potentially cracked) passwords.

### Confidence: High

Every link is statically provable from `SecurityConfig.java` and `application.properties`. The exposure is explicit and unambiguous.

### Remediation (Easiest Link)

1. **Remove `/actuator/**` from `permitAll()`** — apply security guards to all actuator endpoints or at minimum require admin role.
2. Set `management.endpoints.web.exposure.include=health,info` (least privilege).
3. Set `management.endpoint.env.show-values=NONE` and disable heapdump in non-prod: `management.endpoint.heapdump.enabled=false`.

---

## Chain 3: Unvalidated Carrier URL → SSRF → Internal Network Access & Data Exfiltration

### Attack Graph

```mermaid
flowchart LR
    A["Carrier Label URL from Request Body<br>/api/shipping/label (POST)"] --> B["ShippingService.generateLabel()"]
    B --> C["new URL(userInput) + HttpURLConnection<br>NO validation, NO allowlist"]
    C --> D["Server-side HTTP GET to arbitrary URL"]
    D --> E["Internal Services / Cloud Metadata /<br>Internal APIs / External Resources"]
    E --> F["Downloaded Content Saved to DB<br>& Returned to Attacker"]
    
    classA entry; classB hop; classC hop; classD hop; classE hop; classF sink
    classDef entry fill:#00695C,color:#fff
    classDef hop fill:#1565C0,color:#fff
    classDef sink fill:#C62828,color:#fff
```

### Detailed Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Entry** | `ShippingController.java:27-28` | `@PostMapping("/label")` + `@RequestBody ShippingLabelRequest request` | Receives `carrierLabelUrl` from authenticated user. The DTO at `ShippingLabelRequest.java:10` has no `@NotBlank`, no URL validation, no annotation restricting schemes |
| **Hop 1** | `ShippingService.java:23-24` | `URL url = new URL(request.getCarrierLabelUrl()); HttpURLConnection conn = (HttpURLConnection) url.openConnection();` | **Direct use of user-supplied URL** with no validation of scheme (http/https/file), no hostname allowlist/denylist, no protection against `file://`, `gopher://`, or internal IP addresses |
| **Hop 2** | `ShippingService.java:24-25` | `conn.setRequestMethod("GET"); conn.setConnectTimeout(5000); conn.setReadTimeout(5000);` | The `connectTimeout` is only 5 seconds, but `readAllBytes()` will read the entire response regardless of size. No response type validation |
| **Sink** | `ShippingService.java:30-35` | `shippingLabelRepository.save(...)` saves the downloaded content to the database | The fetched content is persisted and can be retrieved via `GET /api/shipping/label/{orderId}`, returning `application/octet-stream` to any caller |

### Preconditions & Assumptions

- The user is **authenticated** (not anonymous). The required role is `OPERATOR`, `SUPERVISOR`, or `ADMIN`.
- No CORS restrictions are configured in `SecurityConfig.java` (no `cors()` block visible), so any browser-originated requests would be permitted by Spring Security defaults.
- The host running the WMS likely has access to internal services, cloud metadata endpoints (`http://169.254.169.254/`), or other internal APIs.
- The 5-second connect/read timeout prevents long-polling SSRF but not rapid byte extraction.

### Impact

- **High** severity. SSRF can: (a) access **cloud instance metadata** to steal IAM credentials, (b) probe **internal services** (databases, admin panels, inter-service APIs), (c) exfiltrate data via DNS or HTTP tunneling, and (d) potentially reach **internal network segments** inaccessible from the external perimeter. The fetched content is stored and retrievable, enabling asynchronous data exfiltration.

### Confidence: High

The lack of URL validation at the DTO level and the direct pass-through to `new URL()` + `HttpURLConnection` are concrete, statically verifiable facts. The SSRF chain is complete from user input to server-side network access.

### Remediation (Easiest Link)

1. **Validate the URL scheme and hostname** against an allowlist of permitted carrier domains before making the HTTP request.
2. Reject `file://`, `gopher://`, and any non-`http`/`https` schemes.
3. Use a **URL allowlist** in `ShippingLabelRequest` with a custom `@Valid` constraint or validator.
4. Consider **isolating** outbound connections to a restricted egress zone.

---

## Chain 4: Inconsistent Authorization → Inventory Manipulation & Order Data Abuse

### Attack Graph

```mermaid
flowchart LR
    A["Authenticated USER<br>(OPERATOR / SUPERVISOR / ADMIN)"] --> B["/api/inventory/adjust/{id}?delta=N<br>NO @PreAuthorize"]
    B --> C["InventoryService -> save item with new qty<br>create() overwrites entire entity"]
    C --> D["Inventory Quantity Arbitrarily Changed<br>No operator audit, no threshold"]
    D --> E["Impact: Stock fraud, supply chain tampering"]
    
    A --> F["/api/orders<br>/api/orders/{id}/items<br>/api/dashboard/stats"]
    F --> G["NO @PreAuthorize — <br>read access to all data"]
    G --> H["Order data, customer info,<br>pick lists visible to any role"]
    H --> I["Impact: Data exfiltration,<br>business intelligence leak"]
    
    classA entry; classB hop; classC hop; classD sink; classE sink
    classF hop; classG hop; classH hop; classI sink
    classDef entry fill:#00695C,color:#fff
    classDef hop fill:#1565C0,color:#fff
    classDef sink fill:#C62828,color:#fff
```

### Detailed Breakdown

#### 4a: Unauthorized Inventory Quantity Adjustment

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Entry** | `InventoryController.java:52-58` | `@PostMapping("/{id}/adjust")` with **no `@PreAuthorize` annotation** | Any authenticated user (including OPERATOR role) can call this endpoint |
| **Hop** | `InventoryController.java:56-57` | `item.setQuantity(item.getQuantity() + delta);` then `inventoryService.create(item)` | The `create()` method saves the **entire modified entity** back to the database. The `delta` parameter is an `int` with **no upper/lower bounds**, enabling arbitrary quantity changes |
| **Sink** | Inventory database | Quantity can be set to any value, including negative numbers or values exceeding physical stock | No audit trail of who adjusted quantities, no stock reconciliation, no approval workflow |

Note: The `adjustQuantity` method creates a **new entity** (via `create()`), not an update, so it generates a new `createdAt` timestamp and the existing entity is orphaned (unless the repository cascade-delete handles it). This is a data integrity bug that compounds the authorization issue.

#### 4b: Unrestricted Data Reading

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Entry** | `InventoryController.java:16-19` | `@GetMapping` with **no `@PreAuthorize`** | Any authenticated user can list all inventory items, including prices, stock levels, locations |
| **Entry** | `OrderController.java:17-20` | `@GetMapping` with **no `@PreAuthorize`** | Any authenticated user can list all orders with customer names, addresses, statuses |
| **Entry** | `DashboardController.java:22` | `@GetMapping("/stats")` returns low-stock items with full details | Sensitive stock alert data is readable by any role |
| **Sink** | All controllers | Resource-level access control is missing on read endpoints | OPERATOR can access the same data as ADMIN/SUPERVISOR. There is no tenancy scoping (warehouse_id, organization_id) |

### Preconditions & Assumptions

- The application uses Spring Security role-based access control via `@PreAuthorize`
- No additional method-level or resource-level authorization is implemented in service methods
- The SPA front-end attempts to hide buttons based on role, but **client-side enforcement is not security**

### Impact

- **Medium** severity. A low-privileged OPERATOR can arbitrarily adjust inventory quantities (potentially hiding stock discrepancies or creating phantom inventory), read all order data including customer PII and addresses, and access dashboard analytics. The authorization inconsistency allows lateral movement from a low-privilege role to effectively full data access.

### Confidence: High

The absence of `@PreAuthorize` annotations on multiple endpoints is statically provable. The role hierarchy and endpoint exposure are concrete.

### Remediation (Easiest Link)

1. **Add `@PreAuthorize("hasAnyRole('SUPERVISOR', 'ADMIN')")`** to `/api/inventory/adjust/{id}` and all read endpoints that should be role-gated.
2. **Implement resource-level authorization** — operators should only see/modify orders assigned to them (enforced in service layer, not just controller).
3. Add **audit logging** for inventory adjustments (who changed what, when, by how much).
4. Bound the `delta` parameter to reasonable limits (e.g., max ±1000).

---

## Cross-Cutting Weaknesses (Not Full Chains)

### W1: Verbose Error Messages Across Multiple Controllers

| Files | Lines | Evidence |
|---|---|---|
| `InventoryController.java:35,45,53` | `return ResponseEntity.badRequest().body(e.getMessage());` | Exception messages returned verbatim to client |
| `OrderController.java:37` | Same pattern | Internal error details exposed |
| `ShippingController.java:29` | Same pattern | Could leak stack traces or path information |

**Impact:** Aids enumeration during other attacks. Always strip error details in production.

### W2: Hardcoded Test Credentials with Weak Passwords

| File | Lines | Evidence |
|---|---|---|
| `DataInitializer.java:36-44` | Creates `operator`/`operator123`, `supervisor`/`supervisor123`, `admin`/`admin123` | While BCrypt-encoded, the base passwords are trivially guessable. The admin123 pattern is in common breach lists. |

**Impact:** If the database is re-initialized (e.g., H2 restarts), weak credentials are recreated. The `admin` role could be compromised via offline cracking.

### W3: H2 In-Memory Database with Empty Password

| File | Line | Evidence |
|---|---|---|
| `application.properties` | `spring.datasource.password=` | Empty password for H2 database. If the H2 TCP server is enabled or file mode is used, credentials are trivially exploit-able. |

### W4: No CSRF Protection Explicitly Configured

The `SecurityConfig.java` does not explicitly configure `.csrf()` — Spring Security 3.x defaults to CSRF protection for form login, but since the SPA uses fetch/XHR for login via `/login` (which triggers the `UsernamePasswordAuthenticationFilter`), CSRF token handling may be inconsistent. The frontend `app.js` uses `fetch()` without reading or submitting a CSRF token (no `_csrf` parameter or `X-CSRF-TOKEN` header). This means **state-changing operations via the SPA may be vulnerable to CSRF** if the Spring Security CSRF filter is initsensitive (form-based CSRF is typically enforced for POST/PUT/DELETE).

### W5: SQL Logging Enabled in Production Config

| File | Line | Evidence |
|---|---|---|
| `application.properties` | `spring.jpa.show-sql=true` | Full SQL statements logged to console, aiding query-based reconnaissance |

### W6: No Content-Security-Policy or CORS Configuration

The `SecurityConfig.java` does not configure CORS (`cors()` block absent) or CSP headers. With a public-facing SPA, this could lead to cross-origin data theft.

### W7: ShippingService `readAllBytes()` Without Size Limit

`ShippingService.java:27` calls `is.readAllBytes()` which reads the entire response body into memory with **no size cap**. A malicious carrier URL returning a very large response could cause an OOM condition.

---

## Unknowns & Areas Not Reviewed

| Area | Reason |
|---|---|
| **Runtime session management** | Cannot verify from source alone if `CookieSerializer` is configured for `Secure`/`HttpOnly` flags |
| **TLS/HTTPS configuration** | No application.properties entries for server SSL; the Dockerfile does not configure nginx/SSL termination |
| **LDAP bind authentication** | The embedded LDAP is only used for search; Spring Security's `UserDetailsService` reads from H2. Cannot verify if LDAP bind/SSO is configured for auth |
| **Rate limiting** | No rate limiting is visible; brute-force attacks against `/login` may be feasible (though BCrypt mitigates speed) |
| **Input sanitization on `POST /api/inventory`** | No `@Valid` annotations on DTOs; SQL injection via JPA is not a concern (parameterized), but business logic abuse (negative prices, etc.) is possible |
| **Docker image security** | The image runs as root by default; no `USER` directive; no base image vulnerability scanning |

---

## Remediation Priority Summary

| Priority | Chain/Weakness | Action |
|---|---|---|
| **P0** | Chain 3 (SSRF) | Add URL allowlist validation in `ShippingService` |
| **P0** | Chain 2 (Actuator) | Secure `/actuator/**` endpoints; restrict env/heapdump exposure |
| **P1** | Chain 4 (IDOR/Authorization) | Add `@PreAuthorize` to all read/mutate endpoints; implement role-based scoping |
| **P1** | Chain 1 (LDAP Injection) | Sanitize LDAP filter input; suppress verbose errors |
| **P2** | W1 (Verbose Errors) | Centralize error handling with generic messages |
| **P2** | W2 (Weak Test Credentials) | Use environment-variable-seeded passwords; skip seed in production |
| **P3** | W3-W7 | Apply standard hardening: CSRF tokens, CSP, rate limiting, TLS, USER directive in Docker |
