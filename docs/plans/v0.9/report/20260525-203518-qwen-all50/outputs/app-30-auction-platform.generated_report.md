# Chained Vulnerability Static Audit Report

**Project:** app-30-auction-platform  
**Date:** 2026-05-25  
**Scope:** Static-only review of all source files in `src/`, `pom.xml`, `Dockerfile`, and `application.properties`  
**Methodology:** Attack surface mapping → weakness inventory → attack graph synthesis → impact assessment  
**Safety Boundary:** No live HTTP probes, no dynamic scanners, no exploit payloads, no shell commands. Source evidence only.

---

## Summary Dashboard

| Metric | Value |
|---|---|
| Total chained vulnerabilities detected | **4** |
| Maximum severity | **CRITICAL** |
| High-confidence chains | 3 |
| Medium-confidence chains | 1 |
| Cross-cutting weaknesses (non-chaining) | 5 |
| Authentication evaluated | Partial (Spring Security Basic Auth) |
| Authorization evaluated | Partial (@PreAuthorize on one endpoint only) |
| Input validation evaluated | Minimal (none on webhook) |
| Rate limiting / Throttling | Not present |

---

## Methodology & Static-Only Safety Note

This audit examines repository files only — controllers, services, config, models, repositories, support utilities, dependency manifests, and existing documentation. No network requests, fuzzing, or runtime probes were performed. Confidence ratings reflect the degree to which each chain link is provably present in the static source.

---

## Reviewed Areas

| Area | Files Reviewed |
|---|---|
| Entry points | `AuthController.java`, `BidController.java`, `ListingController.java`, `WebhookController.java` |
| Security config | `SecurityConfig.java`, `application.properties` |
| Business logic | `BidService.java`, `ListingService.java`, `WalletService.java` |
| Data models | `User.java`, `Listing.java`, `Bid.java`, `Transaction.java`, `Wallet.java` |
| Data access | `*Repository.java` (5 files) |
| Seeding | `DataInitializer.java` |
| Utilities | `ReferenceGuards.java` |
| Infrastructure | `pom.xml`, `Dockerfile`, `App30Application.java` |
| Tests | `App30ApplicationTests.java` |

---

## Areas Not Reviewed / Unknowns

- No frontend templates or XSS-prone views examined (none present — REST-only API).
- No file upload handlers present.
- No SSRF-prone URL fetchers present.
- No deserialization sinks present.
- No background job consumers present.
- Container image does not pin base image digest (pinned version tags only).
- No database migration tool (Flyway/Liquibase) — schema is auto-created by Hibernate.

---

# Chain 1: Unauthenticated Webhook → Fake Financial Transactions → Downstream Fraud

**Severity:** CRITICAL  
**Confidence:** HIGH  
**Impact:** Unauthorized creation of financial transaction records. If downstream services (payment processors, item release workflows) trust `Transaction` records with status `COMPLETED`, an attacker can trigger false payments, causing sellers to release items without actual funds being received.

### Attack Graph

```mermaid
flowchart LR
    A[Unauthenticated Actor] --> B[POST /api/webhooks/payment\nSecurityConfig.java]
    B --> C[No signature validation\nWebhookController.java: L33-34]
    C --> D[Direct Map casting with no bounds\nWebhookController.java: L36-40]
    D --> E[Transaction written with COMPLETED status\nWebhookController.java: L42-48]
    E --> F[Platform fee auto-calculated\nWebhookController.java: L45]
    F --> G[Financial fraud / false revenue]\nDownstream trust in COMPLETED status]
    style A fill:#f9f,stroke:#333
    style G fill:#f00,stroke:#fff,color:#fff
```

### Detailed Chain Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `config/SecurityConfig.java` | ~28 | `.requestMatchers("/api/webhooks/**").permitAll()` — no authentication required |
| **Hop 1** | `controller/WebhookController.java` | ~33-34 | Comment: "Direct processing of payment webhooks without validating signatures or credentials" — no HMAC, no mutual TLS, no API key verification |
| **Hop 2** | `controller/WebhookController.java` | ~36-40 | `Long.valueOf(payload.get("listingId").toString())` — no null checks, no negative-number guards, no amount caps |
| **Hop 3** | `controller/WebhookController.java` | ~42-48 | Transaction created with hardcoded `status="COMPLETED"` and `platformFee = amount * 0.05` — attacker controls `amount` arbitrarily |
| **Sink** | Database (`transactions` table) | — | Arbitrary financial records persist; no reconciliation step |

### Preconditions & Assumptions

- The application has downstream consumers that trust `Transaction` records (e.g., releasing auction items, updating wallet balances).
- H2 in-memory database retains data across request handling.

### Remediation (Easiest Link to Break)

Add signature verification to `WebhookController.java`:

```java
// Verify HMAC-SHA256 signature from trusted payment provider
String providedSig = request.getHeader("X-Payment-Signature");
byte[] expected = hmacSha252(secretKey, payloadBytes);
if (!MessageDigest.isEqual(providedSig.getBytes(), expected)) {
    return ResponseEntity.status(401).body("Invalid signature");
}
```

Or at minimum: restrict `/api/webhooks/**` to a dedicated service account role instead of `permitAll`.

---

# Chain 2: Race Condition (TOCTOU) in Bid Placement → Underpriced Sales

**Severity:** HIGH  
**Confidence:** HIGH  
**Impact:** Multiple concurrent bids can pass the "higher than current max" check because there is no database-level locking or optimistic locking. Combined with the deliberate `Thread.sleep(50)` in `BidService`, a time-of-check-to-time-of-use window exists where multiple bids below the true current maximum are accepted, allowing items to be sold below their true market value.

### Attack Graph

```mermaid
flowchart LR
    A[Authenticated User] --> B[POST /api/bids\nBidController.java]
    B --> C[BidService.placeBid]\nReads current max bid]
    C --> D[Check: amount > currentMax]
    D --> E[Thread.sleep(50)\nBidService.java: L39-42]
    E --> F[Bid persisted without @Lock\nBidRepository.save]
    F --> G[Race: another request reads]\nstale max bid during sleep]
    G --> H[Second bid passes check]\nbut is below true current max]
    H --> I[Item sold at underpriced amount]\nSeller financial loss]
    style A fill:#f9f,stroke:#333
    style I fill:#ff6600,stroke:#fff,color:#fff
```

### Detailed Chain Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `controller/BidController.java` | ~20-26 | `placeBid` accepts `listingId`, `bidderId`, `amount` as raw `@RequestParam` values with no contextual identity binding |
| **Hop 1** | `service/BidService.java` | ~27-32 | Reads highest bid via `bidRepository.findHighestBids(listingId)` — plain SELECT, no `@Lock`, no optimistic `@Version` |
| **Hop 2** | `service/BidService.java` | ~34 | `if (amount <= currentMax) throw ...` — the correctness check |
| **Hop 3** | `service/BidService.java` | ~39-42 | `Thread.sleep(50)` — explicitly simulates database query delay, widening the race window |
| **Hop 4** | `service/BidService.java` | ~47 | `bidRepository.save(newBid)` — unguarded INSERT after stale read |
| **Sink** | `repository/BidRepository.java` | ~15 | `JpaRepository.save()` — no `@Lock(PESSIMISTIC_WRITE)` on the find query |

### Preconditions & Assumptions

- Concurrent requests to the same `listingId` arrive within the 50ms sleep window.
- H2's default isolation is `READ_COMMITTED`; concurrent transactions can observe stale data.

### Remediation (Easiest Link to Break)

Apply pessimistic locking on the bid query in `BidRepository.java`:

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT b FROM Bid b WHERE b.listingId = :listingId ORDER BY b.amount DESC")
List<Bid> findHighestBids(@Param("listingId") Long listingId);
```

Remove the `Thread.sleep(50)` from `BidService.java` (it serves no production purpose).

---

# Chain 3: Plaintext Passwords + Public H2 Console → Full Credential Theft

**Severity:** CRITICAL  
**Confidence:** HIGH  
**Impact:** Every user's password is stored and compared in plaintext. The H2 database console is publicly accessible at `/h2-console/**` with no authentication. An unauthenticated attacker can connect to the H2 console, browse all tables, and read all usernames and plaintext passwords — enabling full account takeover of all platform users.

### Attack Graph

```mermaid
flowchart LR
    A[Unauthenticated Actor] --> B[GET /h2-console/**\nSecurityConfig.java: permitAll]
    B --> C[H2 Console UI exposed\napplication.properties: spring.h2.console.enabled=true]
    C --> D[Connect to jdbc:h2:mem:auctiondb\nusing default credentials sa/empty]
    D --> E[Browse USERS table → read all passwords in plaintext]
    E --> F[Browse USERS table → read roles]
    F --> G[Log in as any user via /api/auth/me]\nFull account takeover]
    style A fill:#f9f,stroke:#333
    style G fill:#f00,stroke:#fff,color:#fff
```

### Detailed Chain Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `resources/application.properties` | ~3-5 | `spring.datasource.username=sa`, `spring.datasource.password=`, `spring.h2.console.enabled=true` |
| **Hop 1** | `config/SecurityConfig.java` | ~27 | `.requestMatchers("/h2-console/**").permitAll()` — no auth gate |
| **Hop 2** | `config/SecurityConfig.java` | ~64 | `return NoOpPasswordEncoder.getInstance()` — passwords compared as plain strings |
| **Hop 3** | `model/User.java` | ~16 | `private String password;` — comment: "Store passwords in plaintext" |
| **Hop 4** | `config/DataInitializer.java` | ~28-30 | Seeds users with hardcoded plaintext passwords (`"buyerpwd123"`, `"sellerpwd123"`, `"adminpwd123"`) |
| **Sink** | Memory — H2 DB | — | All credentials readable without any authentication |

### Remediation (Easiest Link to Break)

1. Replace `NoOpPasswordEncoder` with `BCryptPasswordEncoder`:
```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}
```
2. Remove `/h2-console/**` from permitAll or disable H2 console entirely in production.
3. Never seed production passwords — use environment variables or a secrets manager.

---

# Chain 4: Unauthenticated Bidding Impersonation → Unauthorized Financial Actions

**Severity:** HIGH  
**Confidence:** HIGH  
**Impact:** The `/api/bids` endpoint accepts `bidderId` as a plain request parameter. Any authenticated user can place a bid on behalf of *any* user by supplying an arbitrary `bidderId`. Combined with the wallet deduction service (`WalletService.deductBalance`), an attacker can drain another user's wallet by placing bids under their identity.

### Attack Graph

```mermaid
flowchart LR
    A[Attacker — authenticated user] --> B[POST /api/bids?bidderId=999\nBidController.java]
    B --> C[BidService.placeBid]\naccepts bidderId=999 without verification]
    C --> D[Bid recorded as placed by user 999]
    D --> E[If WalletService.deductBalance]\nuses bidderId, user 999 funds drained]
    E --> F[Financial fraud on behalf of victim]\nVictim's wallet depleted]
    style A fill:#f9f,stroke:#333
    style F fill:#ff6600,stroke:#fff,color:#fff
```

### Detailed Chain Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `controller/BidController.java` | ~20-26 | `placeBid(@RequestParam Long bidderId, ...)` — `bidderId` is user-supplied, not derived from the authenticated principal |
| **Hop 1** | `config/SecurityConfig.java` | ~29 | `.anyRequest().authenticated()` — user must be authenticated, but no role/identity mapping to the bidder |
| **Hop 2** | `service/BidService.java` | ~44 | `newBid.setBidderId(bidderId)` — directly stores the attacker-supplied value, no ownership check |
| **Sink** | Wallet via `WalletService.deductBalance` | `service/WalletService.java` ~27 | Uses `userId` to deduct — if invoked with the attacker-supplied `bidderId`, victim's wallet is drained |

### Preconditions & Assumptions

- The bidding flow is expected to later deduct the winner's wallet balance via `WalletService.deductBalance(userId, amount)`.
- The victim wallet exists and has sufficient balance.

### Remediation (Easiest Link to Break)

Derive the bidder identity from the authenticated principal instead of accepting it as a parameter:

```java
@PostMapping
public ResponseEntity<Bid> placeBid(
        @RequestParam Long listingId,
        @RequestParam Double amount,
        @AuthenticationPrincipal UserDetails userDetails) {
    String username = userDetails.getUsername();
    // Resolve username to user ID internally, or better: include userId in User entity
    Bid bid = bidService.placeBid(listingId, username, amount);
    return ResponseEntity.ok(bid);
}
```

Add authorization checks in `BidService.placeBid` to verify the bidder is not impersonating another user.

---

# Chain 5 (Medium Confidence): Missing CSRF + State-Changing Endpoints → Cross-Site Request Forgery

**Severity:** MEDIUM  
**Confidence:** MEDIUM  
**Impact:** CSRF is globally disabled. All state-changing POST endpoints (`/api/bids`, `/api/webhooks/payment`) are vulnerable to CSRF attacks. An attacker could craft a malicious page that submits forged requests to create fake bids or transactions while a victim is logged in.

### Attack Graph

```mermaid
flowchart LR
    A[Attacker crafts malicious page] --> B[Victim logs into auction platform\nBasic Auth or cookie still active]
    B --> C[Malicious page submits POST to /api/bids\nBidController.java]
    C --> D[Bid placed without CSRF token]\nBidController.java]
    D --> E[Bid recorded for victim's session]\nor webhook triggers fake transaction]
    E --> F[Unauthorized financial action]
    style F fill:#ff6600,stroke:#fff,color:#fff
```

### Detailed Chain Breakdown

| Link | File | Lines | Evidence |
|---|---|---|---|
| **Source** | `config/SecurityConfig.java` | ~24 | `.csrf(AbstractHttpConfigurer::disable)` — CSRF protection disabled globally |
| **Hop 1** | `controller/BidController.java` | ~20 | `@PostMapping` — state-changing endpoint with no CSRF token check |
| **Hop 2** | `controller/WebhookController.java` | ~28 | `@PostMapping("/payment")` — state-changing endpoint with no CSRF token check |
| **Sink** | Database (`bids`, `transactions` tables) | — | Unauthorized state mutations via forged requests |

### Remediation

Re-enable CSRF or switch to token-based auth (JWT) that is not vulnerable to CSRF:

```java
.csrf(csrf -> csrf.ignoringRequestMatchers("/api/webhooks/**"))
```

For REST APIs, consider JWT bearer tokens which are immune to CSRF.

---

# Cross-Cutting Weaknesses (Not Forming Complete Chains)

The following security-relevant issues were identified but either lack a confirmed critical sink in the static source, or represent standalone weaknesses:

| Weakness | File | Lines | Description |
|---|---|---|---|
| **No rate limiting** | All controllers | — | No throttling on bid placement or webhook ingestion — vulnerable to abuse/scalping |
| **No input validation on amount** | `BidController.java` ~22 | Negative or zero bid amounts are not rejected before reaching `BidService` |
| **No reserve price enforcement on close** | `BidService.java` | No logic to check if the winning bid meets the listing's `reservePrice` |
| **Sensitive data in error messages** | `BidService.java` ~31 | `new IllegalArgumentException("Listing not found")` — could leak existence of listings |
| **`ReferenceGuards` utility unused** | `support/ReferenceGuards.java` | Contains `sameOwner()` and `allowedCallback()` methods that are not referenced anywhere — dead security code. Suggests ownership checks were considered but never wired into controllers. |

---

# Unknowns & Recommended Tests

| Unknown | Recommended Test |
|---|---|
| Whether H2 console exposes SQL injection — verify console is disabled in prod | Add integration test: `GET /h2-console` → expect 401/403 in non-dev profiles |
| Whether wallet deduction is invoked post-bid | Audit integration between `BidService` and `WalletService` — currently not wired in source |
| Whether concurrent bid tests exist | Add concurrent bid placement tests with `CountDownLatch` to verify race condition |
| Whether webhook signature verification is planned | Review integration tests for `WebhookController` |
| Docker image security — runs as root, no non-root user | Add Docker non-root user and scan for CVEs in base images |

---

# Recommendations Summary (Prioritized)

1. **CRITICAL** — Replace `NoOpPasswordEncoder` with `BCryptPasswordEncoder` and disable H2 console in production profiles.
2. **CRITICAL** — Add HMAC signature verification to the payment webhook endpoint.
3. **HIGH** — Apply pessimistic locking (`@Lock(PESSIMISTIC_WRITE)`) to the `findHighestBids` query and remove `Thread.sleep(50)` from `BidService`.
4. **HIGH** — Derive `bidderId` from the authenticated principal instead of accepting it as a request parameter.
5. **MEDIUM** — Re-enable CSRF protection or adopt JWT-based authentication.
6. **MEDIUM** — Add rate limiting on bid placement and webhook endpoints.
7. **LOW** — Wire the `ReferenceGuards.sameOwner()` utility into ownership checks or remove it to eliminate dead security code.

---

*Report written by CodeGopher — static-only analysis. No live probes or exploit payloads were generated.*
