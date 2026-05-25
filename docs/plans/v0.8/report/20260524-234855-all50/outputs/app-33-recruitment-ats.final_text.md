

The chained vulnerability static audit is complete. Here's a summary of findings:

## Audit Results

**3 Chained Vulnerabilities Found | Max Severity: High**

### Chain 1 (High) — Account Takeover via Weak API Key Derivation
- **Source**: Hardcoded plaintext passwords in `src/index.ts:70-73` (alice uses `candidate123`, bob uses `candidate456`, charlie uses `recruiter2026ATS!`)
- **Hop**: API keys are derived as `MD5(userId)` — since user IDs are sequential integers (1, 2, 3), any API key can be trivially computed
- **Sink**: Full account impersonation including RECRUITER access to dashboard and all application data

### Chain 2 (High) — Arbitrary File Write via ZIP Directory Traversal
- **Source**: `POST /api/applications/upload-portfolio` accepts ZIP files from RECRUITER
- **Hop**: `entry.entryName` used directly in `path.join()` without sanitization or path canonicalization
- **Sink**: `fs.writeFileSync()` writes to attacker-controlled paths, enabling code injection into source files or other critical paths

### Chain 3 (Medium) — Cross-Origin Session Hijack
- **Source**: `cors({ origin: true, credentials: true })` allows any origin to send credentialed requests
- **Hop**: No CSRF protection on any `POST` endpoint
- **Sink**: Session cookie (`session_id`) can be hijacked via cross-origin requests from malicious sites

### 5 Cross-Cutting Weaknesses
Verbose error messages, missing cookie security flags (SameSite/Secure), no rate limiting on auth, ephemeral in-memory store, no input validation middleware

The full report with Mermaid attack graphs, code references, line numbers, and prioritized remediation has been written to:
**`docs/security/CHAINED_VULNERABILITIES_REVIEW.md`**
