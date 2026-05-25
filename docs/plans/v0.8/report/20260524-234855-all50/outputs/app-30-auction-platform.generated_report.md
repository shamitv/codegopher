# Chained Vulnerability Static Audit Report

**Project:** Auction Platform (app-30-auction-platform)  
**Audit Type:** Static-only source code review  
**Date:** 2026-05-24  
**Auditor:** CodeGopher  

---

## Summary Dashboard

| Metric | Value |
|---|---|
| **Total chained vulnerabilities** | 3 |
| **Maximum severity** | **CRITICAL** |
| **High severity** | 1 |
| **Medium severity** | 1 |
| **Low severity** | 0 |
| **Cross-cutting weaknesses (non-chained)** | 5 |
| **Areas reviewed** | Controllers, Services, Models, Repositories, Security Config, Data Initializer, Tests, Build Config |
| **Areas NOT reviewed** | Runtime behavior, external payment gateway integration, infrastructure, network topology |

---

## Methodology and Static-Only Boundary

This audit follows a four-phase methodology:

1. **Attack Surface Mapping** — Identifies all public routes, API endpoints, webhook handlers, request parameters, headers, cookies, and other user-controlled input sources.
2. **Weakness Inventory** — Catalogs individually modest security weaknesses (weak auth, missing validation, race conditions, hardcoded credentials, etc.).
3. **Attack Graph Synthesis** — Connects sources to weaknesses to sinks to form chained attacks using only static code evidence.
4. **Impact Assessment** — Rates each chain by impact, reachability, confidence, and easiest remediation link.

**Static-only safety note:** No live HTTP probes, dynamic scanners, SQL injection payloads, credential attacks, exploit scripts, port scans, or external network tests were performed. All findings are derived from source code, configuration files, test code, and dependency manifests.

---

## Chained Vulnerabilities

### Chain 1: Unauthenticated Transaction Injection via Payment Webhook

**Severity: CRITICAL**  
**Impact:** Unauthorized fund creation / financial fraud — arbitrary transaction records with platform fees can be injected by any unauthenticated actor.

**Mermaid Attack Graph:**

```mermaid
flowchart LR
    A["Unauthenticated Actor\n(External/System)"] -->|"POST /api/webhooks/payment\nwith crafted JSON body"| B["WebhookController.handlePaymentWebhook\n(WebhookController.java:24-25)\nPermitAll, no auth"]
    B -->|"No signature, credential,\nor HMAC validation"| C["Raw payload processed\nwithout any verification\n(WebhookController.java:26-30)"]
    C -->|"Long.valueOf(payload.get(\"listingId\").toString())\nNo null, negative, or bounds check"| D["Transaction saved to DB\n(status=COMPLETED)\n(WebhookController.java:31-38)"]
    D --> E["COMPLETED transaction record\nwith platform fee collected\n(permanent financial impact)")"]
```

**Chain Breakdown:**

| Link | File | Lines | Symbol | Evidence |
|---|---|---|---|---|
| **Source** | `src/main/java/com/auction/platform/controller/WebhookController.java` | 17 | `@RequestMapping("/api/webhooks")` | Path `/api/webhooks/**` is `permitAll()` in SecurityConfig |
| **Hop 1** | `src/main/java/com/auction/platform/config/SecurityConfig.java` | 24 | `.requestMatchers("/api/webhooks/**").permitAll()` | No authentication or authorization guard |
| **Hop 2** | `src/main/java/com/auction/platform/controller/WebhookController.java` | 25-30 | `handlePaymentWebhook(@RequestBody Map<String, Object> payload)` | Comment on line 25: "Direct processing ... without validating signatures or credentials". All fields (`listingId`, `buyerId`, `sellerId`, `amount`) coerced from `Map<String, Object>` via raw `.toString()` then `Long.valueOf()`/`Double.valueOf()` — no null checks, no range validation |
| **Hop 3** | `src/main/java/com/auction/platform/controller/WebhookController.java` | 31-38 | `transaction.setStatus("COMPLETED"); transactionRepository.save(transaction);` | Transaction immediately marked COMPLETED and persisted with no external confirmation |
| **Sink** | Database — `transactions` table | 31-38 | `Transaction` entity | Arbitrary financial records with `COMPLETED` status and calculated `platformFee` |

**Preconditions:**
- H2 database is attached to the Spring Boot app
- The `transactions` table is auto-created by JPA (`@Entity` on `Transaction`)

**Confidence: High** — Every link is statically provable from source code. The absence of signature validation is explicitly acknowledged in a code comment. The `permitAll()` authorization is a hard-coded Spring Security config.

**Remediation (easiest link to break):**
1. Add HMAC or signature-based verification of webhook payloads using a secret key known only to the payment provider and the platform.
2. Require authentication for `/api/webhooks/**` endpoints.
3. Validate all field types and ranges (e.g., positive amounts, valid user/listing IDs).

---

### Chain 2: Race Condition — Double-Bid / Overbid Exploitation in Auction Bidding

**Severity: HIGH**  
**Impact:** A single listing can receive multiple overlapping bids at the same price level or a bid that should be rejected due to insufficient increment. This enables a user to potentially place multiple winning bids or manipulate auction outcomes.

**Mermaid Attack Graph:**

```mermaid
flowchart LR
    A["Authenticated Bidder\n(Any authenticated user)"] -->|"POST /api/bids\nlistingId + bidderId + amount"| B["BidController.placeBid\n(BidController.java:19-24)\nRequires auth only"]
    B -->|"BidService.placeBid\n(listingId, bidderId, amount)"| C["Listing fetched — status check only\n(listingRepository.findById)\nBidService.java:20-23"]
    C -->|"Current max bid read WITHOUT locking\n(bidRepository.findHighestBids)\nBidService.java:26-27"| D["TOCTOU gap — no SELECT FOR UPDATE"]
    D -->|"Thread.sleep(50) simulates delay\nBidService.java:32-34"| E["Race window widened — 50ms lock-free gap"]
    E -->|"Amount checked against stale\nsnapshot (not current DB state)\nBidService.java:28"| F["Bid saved with stale approval\n(bidRepository.save)\nBidService.java:36-38"]
    F --> G["Duplicate/invalid bid committed\n(manipulated auction outcome)")"]
```

**Chain Breakdown:**

| Link | File | Lines | Symbol | Evidence |
|---|---|---|---|---|
| **Source** | `src/main/java/com/auction/platform/controller/BidController.java` | 19-24 | `@PostMapping` → `placeBid(@RequestParam Long listingId, @RequestParam Long bidderId, @RequestParam Double amount)` | No CSRF protection (global CSRF is disabled), no authorisation check — any authenticated user can place a bid on any listing |
| **Hop 1** | `src/main/java/com/auction/platform/config/SecurityConfig.java` | 21 | `.csrf(AbstractHttpConfigurer::disable)` | CSRF protection globally disabled for all endpoints |
| **Hop 2** | `src/main/java/com/auction/platform/service/BidService.java` | 26-27 | `List<Bid> bids = bidRepository.findHighestBids(listingId);` | Query returns highest bids but with **no optimistic/pessimistic locking** |
| **Hop 3** | `src/main/java/com/auction/platform/service/BidService.java` | 28 | `Double currentMax = bids.isEmpty() ? listing.getStartingPrice() : bids.get(0).getAmount();` | Amount compared against in-memory snapshot, not fresh DB state |
| **Hop 4** | `src/main/java/com/auction/platform/service/BidService.java` | 32-34 | `Thread.sleep(50);` | Explicit simulated delay widening the TOCTOU window — visible in source, possibly a debug residual |
| **Sink** | Database — `bids` table | 36-38 | `bidRepository.save(newBid);` | Bid committed without re-checking current state, leading to stale-data acceptance |

**Preconditions:**
- Concurrent bid requests for the same listing
- Thread contention triggers the race window

**Confidence: High** — The race condition is explicitly documented in the source (`// Read highest bid without locking...`) and the `Thread.sleep(50)` line intentionally widens the window. Spring Data JPA `JpaRepository` by default does not use `SELECT FOR UPDATE`.

**Remediation (easiest link to break):**
1. Use `@Lock(LockModeType.PESSIMISTIC_WRITE)` on `findHighestBids` query in `BidRepository`.
2. Remove the `Thread.sleep(50)` debug code.
3. Add a database-level unique constraint or version column for bid validation.
4. Re-check the highest bid immediately before saving (optimistic locking with `@Version`).

---

### Chain 3: Credential Harvesting — Plaintext Passwords with No-Op Encoder + Hardcoded Seed Accounts

**Severity: HIGH**  
**Impact:** Compromised database directly yields all user credentials in plaintext. Combined with the disabled CSRF, this enables session hijacking and account takeover on any downstream system that reuses passwords.

**Mermaid Attack Graph:**

```mermaid
flowchart LR
    A["Database Attacker\n(Any attacker with DB access)"] -->|"SQL injection or\nserver-side compromise"| B["H2 Database\nembedded in Spring Boot"]
    B -->|"users table with\nplaintext passwords"| C["User.password contains raw passwords\nSecurityConfig.java:48: .password(u.getPassword())"]
    C -->|"PasswordEncoder = NoOp\nSecurityConfig.java:53-55"| D["Full plaintext credentials\nrecoverable without any transform"]
    D -->|"seeded accounts:\nbuyer/buyerpwd123\nseller/sellerpwd123\nadmin/adminpwd123"| E["Hardcoded seed accounts\n(DataInitializer.java:30-32)"]
    E --> F["Admin account compromised\n(role=ADMIN — full platform control)")"]
```

**Chain Breakdown:**

| Link | File | Lines | Symbol | Evidence |
|---|---|---|---|---|
| **Source** | `src/main/java/com/auction/platform/model/User.java` | 22 | `private String password; // Store passwords in plaintext` | Entity stores passwords as raw strings; comment confirms design decision |
| **Hop 1** | `src/main/java/com/auction/platform/config/SecurityConfig.java` | 53-55 | `return NoOpPasswordEncoder.getInstance();` | `PasswordEncoder` bean explicitly returns no-op encoder — no hashing of any passwords at any point |
| **Hop 2** | `src/main/java/com/auction/platform/config/SecurityConfig.java` | 48 | `.password(u.getPassword())` | `UserDetailsService` passes the plaintext password directly to the Spring `User` builder, feeding it back to the authentication filter unchanged |
| **Hop 3** | `src/main/java/com/auction/platform/config/DataInitializer.java` | 30-32 | `new User(null, "buyer", "buyerpwd123", "BUYER")`, etc. | Three hardcoded seed accounts with weak, predictable passwords (e.g., `adminpwd123`) |
| **Sink** | `User` entity + Spring Security auth flow | 22 (User), 48 (SecurityConfig), 30-32 (DataInitializer) | — | Database dump = full credential set with admin-level access |

**Preconditions:**
- Attacker obtains read access to the H2 database (file-based, stored on the application server)
- H2 console is accessible at `/h2-console/**` (permitAll) — see cross-cutting weaknesses

**Confidence: High** — The `NoOpPasswordEncoder` bean, the plaintext `User.password` field, and the `DataInitializer` seed data are all explicitly visible in source.

**Remediation (easiest link to break):**
1. Replace `NoOpPasswordEncoder` with `BCryptPasswordEncoder`.
2. Hash all passwords at user creation time (including seed data in `DataInitializer`).
3. Use strong, random passwords for seed accounts; remove seed accounts from production.

---

## Cross-Cutting Weaknesses (Not Forming Complete Chains)

These are security-relevant issues that, while independently concerning, do not independently form a full exploit chain with the current codebase context.

| # | Weakness | File | Lines | Impact |
|---|---|---|---|---|
| 1 | **H2 Console exposed without authentication** | `SecurityConfig.java` | 23 | `.requestMatchers("/h2-console/**").permitAll()` — gives direct SQL access to the embedded database. Enables arbitrary SQL execution, data exfiltration, and potential command execution via H2's `RUNSCRIPT` or `CREATE ALIAS` features. |
| 2 | **CSRF protection globally disabled** | `SecurityConfig.java` | 21 | `.csrf(AbstractHttpConfigurer::disable)` — combined with any state-changing endpoint, enables cross-origin request forgery attacks. Affects `POST /api/bids` and `POST /api/webhooks/payment`. |
| 3 | **Basic auth with no HTTPS guidance** | `SecurityConfig.java` | 29 | `.httpBasic(Customizer.withDefaults())` — credentials sent as weak Base64 encoding on every request. No TLS enforcement in Spring config. |
| 4 | **Listing authorization by role, not ownership** | `ListingController.java` | 15 | `@PreAuthorize("hasRole('SELLER')")` — any authenticated seller can view ALL listings, not just their own. No `sellerId` scoping. |
| 5 | **Bid authorization by auth only, not bidder identity** | `BidController.java` | 19-24 | No `@PreAuthorize` check — any authenticated user can place a bid on any listing for any `bidderId`. No identity assertion that `bidderId` matches the authenticated user. |

---

## Unknowns and Areas Not Reviewed

| Area | Reason |
|---|---|
| Runtime environment | TLS/HTTPS configuration, reverse proxy setup, and infrastructure security are not visible in source |
| H2 persistence configuration | Whether H2 runs in embedded mode (file-based) vs. in-memory; file path and external accessibility |
| External webhook source | The expected payment provider and its documented API — no verification of incoming payload format or source IP filtering |
| Production data initializer | `DataInitializer` seeds are currently unconditionally created on every startup — may or may not be conditional on a profile flag |
| Input validation on all endpoints | Only bid and webhook payloads are examined in detail; other endpoints may have hidden issues |
| Dependency vulnerabilities | `pom.xml` dependencies were not scanned for known CVEs |

---

## Recommended Tests to Add

| Test | Target |
|---|---|
| Concurrent bid race condition test (simultaneous POST requests to `/api/bids`) | `BidService.placeBid()` |
| Webhook signature validation bypass test (POST without HMAC) | `WebhookController.handlePaymentWebhook()` |
| Plaintext password verification test (verify stored hash differs from input) | `User` persistence + `PasswordEncoder` |
| CSRF token requirement test (POST without CSRF token) | All `@PostMapping` endpoints |
| Owner-scoped listing access test (SELLER accessing other users' listings) | `ListingController.getListings()` |
| H2 console access test (unauthenticated GET to `/h2-console`) | Security filter chain |
| Admin seed account credential strength test | `DataInitializer` |

---

## Remediation Priority Summary

| Priority | Chain | Easiest Fix |
|---|---|---|
| **P0 — Immediate** | Chain 1 (Webhook) | Add HMAC signature validation to `/api/webhooks/payment` |
| **P0 — Immediate** | Chain 3 (Passwords) | Switch `PasswordEncoder` to `BCryptPasswordEncoder` and hash seed data |
| **P1 — Short-term** | Chain 2 (Race Condition) | Add `@Lock(PESSIMISTIC_WRITE)` to `findHighestBids` and remove `Thread.sleep` |
| **P2 — Medium-term** | Cross-cutting #1 | Require authentication for `/h2-console/**` in production |
| **P2 — Medium-term** | Cross-cutting #3 | Enforce TLS and migrate from Basic Auth to JWT/session-based auth |
| **P3 — Long-term** | Cross-cutting #4, #5 | Implement fine-grained authorization (owner checks) on listings and bids |

---

*Report generated by CodeGopher — Chained Vulnerability Static Audit*
