---
name: CRUD OWASP Static Audit
description: Perform a static-only security review of a CRUD web application against OWASP Top 10:2025. Use when asked to audit source code for web application security risks without live probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.
keywords: owasp, security review, static audit, crud, web app, authentication, authorization, injection
---
# CRUD OWASP Static Audit

Use this skill for authorized source-only security review of CRUD web applications.

## Static-Only Boundary

- Review repository files, tests, schemas, routes, controllers, services, templates, middleware, configuration, and dependency manifests.
- Do not run live HTTP probing, fuzzing, credential attacks, dynamic scanners, exploit payloads, or network tests.
- Do not generate exploit payloads or step-by-step abuse instructions.
- If the user asks for active testing, explain that this skill is limited to static review and ask for a separate authorized testing workflow.

## Review Inputs

Inspect source that defines:

- Routes, controllers, handlers, serializers, validators, and templates.
- Authentication, session management, password reset, and account lifecycle code.
- Authorization checks, tenant scoping, ownership checks, roles, and admin paths.
- Models, migrations, ORM queries, raw SQL, file uploads, and background jobs.
- Configuration, environment handling, CORS, headers, cookies, CSRF, and deployment defaults.
- Dependency manifests, lockfiles, build scripts, generated clients, and vendored code.
- Error handling, exception mapping, logging, audit events, and alerting hooks.
- Tests that prove or omit expected security behavior.

## OWASP Top 10:2025 Checklist

- A01:2025 Broken Access Control.
- A02:2025 Security Misconfiguration.
- A03:2025 Software Supply Chain Failures.
- A04:2025 Cryptographic Failures.
- A05:2025 Injection.
- A06:2025 Insecure Design.
- A07:2025 Authentication Failures.
- A08:2025 Software or Data Integrity Failures.
- A09:2025 Security Logging and Alerting Failures.
- A10:2025 Mishandling of Exceptional Conditions.

## Analysis Rules

- Tie every finding to evidence in source, tests, configuration, or dependency metadata.
- Prefer concrete control-flow and data-flow evidence over broad checklist claims.
- Mark a category as not reviewed or unknown when the repository does not expose enough evidence.
- Include missing tests as findings when the code relies on security-sensitive assumptions.
- Rate risk as Critical, High, Medium, Low, or Informational based on impact, reachability, and likelihood from static evidence.
- Provide remediation that fits the framework and local patterns already present in the repository.

## Output

- If the user asks for a written artifact, default to `docs/security/OWASP_TOP10_2025_REVIEW.md`.
- If the user does not ask for files, produce a structured report in chat.
- Include summary, scope, methodology, findings, affected files, OWASP category, risk rating, evidence, remediation, missing tests, and unknown/not-reviewed areas.
