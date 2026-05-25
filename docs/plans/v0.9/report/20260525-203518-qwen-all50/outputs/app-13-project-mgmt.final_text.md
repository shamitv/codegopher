

I've completed the chained vulnerability static audit and written the full report to `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`. Here's a summary of what was found:

## Audit Summary

### 3 Attack Chains Identified

| Chain | Severity | Confidence | Description |
|-------|----------|------------|-------------|
| **Stored XSS via Task Comments** | HIGH | High | User-submitted content in comments/task descriptions is stored raw and rendered via `innerHTML` in `app.js` without sanitization — allowing arbitrary script execution |
| **Cross-Tenant Data Access (IDOR)** | MEDIUM-HIGH | Medium | Users can directly enter arbitrary board IDs in the UI to access boards from other organizations (e.g., Alice from Org 101 accessing Org 202's boards) |
| **Unlogged Permission Changes** | MEDIUM | High | Board visibility changes by MANAGERs produce no audit logs — the code even contains a TODO comment acknowledging this omission, making incident response difficult |

### Key Cross-Cutting Weaknesses
- No Content Security Policy (CSP) headers
- Missing CSRF protection on state-changing endpoints
- Hardcoded test account hints in HTML (reconnaissance aid)
- In-memory data store with no rate limiting or pagination
- No input validation on URL parameters

### Priority Actions
1. **P0**: Fix XSS by replacing `innerHTML` with `textContent` or DOMPurify
2. **P1**: Add org-scoped authorization to board retrieval
3. **P1**: Add audit logging for permission changes
