

The chained vulnerability static audit is complete. The full report has been written to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`.

### What was found

**5 chained vulnerabilities**, ranging from CRITICAL to MEDIUM:

1. **CRITICAL** — `eval()` on user-supplied `layout_metadata` in `POST /api/posts` allows **Remote Code Execution**. The token-scoped route means this is reachable by any authenticated user (or anyone using the hardcoded debug token).

2. **HIGH** — Hardcoded static token `CMS-ADMIN-EDITOR-KEY-xyz9988` in `requireAuth()` provides **unauthenticated admin bypass** via `x-editor-token` header or `?editor_token=` query param.

3. **HIGH** — Public `GET /api/system/diagnostics?debug=true` **leaks the admin token** in plaintext, making the bypass in #2 trivially discoverable without any code access.

4. **MEDIUM** — `cors({ origin: true, credentials: true })` allows **any origin** to read credential-bearing API responses, enabling cross-origin session data exfiltration.

5. **MEDIUM** — `Math.random() + Date.now()` generates **predictable session IDs**, enabling session hijacking via ID prediction.

The report includes detailed source citations (file paths, line numbers, code snippets), Mermaid attack graphs, remediation priorities (P0–P3), cross-cutting weaknesses, and unknowns requiring runtime testing.
