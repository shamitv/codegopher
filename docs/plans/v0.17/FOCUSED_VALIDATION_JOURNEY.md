# v0.17 Focused GPT-5.4-Mini Journey

This report explains how the agent and `chained-vulnerability-static-audit` skill moved through the focused source-only scan. Raw event logs, generated reports, proxy snapshots, temp workspaces, endpoint values, usernames, API key names/values, and original corpus paths are intentionally omitted.

## Overall Journey

The run used the internal benchmark harness to create sanitized workspaces, start one proxy stats run, execute CodeGopher in events mode, and end the proxy run. The model route was validated first through the proxy diagnostics route simulator.

Across the three apps, the agent used:

- `list_dir` to establish workspace shape.
- `glob_search` to map candidate source files by language and subsystem.
- `read_file` with line numbers to inspect routes, controllers, services, repositories, configuration, workers/consumers, guards, validators, and outbound/query clients.
- Mission/task contract updates to track audit obligations, candidate evidence, report gates, and completion state.
- `write_chained_vulnerability_report` to write final chained-audit reports.

No persistent memory writes, shell execution, live probing, MCP calls, or arbitrary file writes were observed. The explicit `update_todo` tool was not called; the task ledger and task-local evidence memory carried the working state instead.

## app-05 Journey

The agent started with a workspace listing, then globbed Python source, templates, static JavaScript, and root Python files. It read route and controller files first, then moved into auth, enrollment, course, submission, grading, import, debug, repository, worker, and settings code.

Navigation pattern:

- Entry surfaces: auth, course, enrollment, instructor, submission, import, dashboard, and debug routes/controllers.
- Bridge code: auth/session service, enrollment/course/submission services, grading and import workers.
- Sinks: submission lookup, grade override/grading paths, import fetch path, debug configuration exposure.
- Controls/decoys: prerequisite validator, repository patterns, and nearby route/service boundaries.

What it identified:

- Full debug configuration leak to internal import/fetch pivot chain.
- Partial config/session/submission exfiltration chain.
- Partial enrollment/grade-tampering chain.

What held it back:

- The auth/session bridge was not completed.
- Enrollment role escalation evidence was missed.
- Candidate-flow coverage missed or under-reviewed state-changing and validator paths.

The app finished in one complete attempt with a valid ledger and exact evidence, but recall stayed partial at `1/3` complete chains and `5/7` components.

## app-10 Journey

The agent listed the Java workspace and source tree, then globbed Java source. It read security config, customer, usage, admin, auth, billing, health, model, repository, service, search, messaging, cache, and build files.

Navigation pattern:

- Entry surfaces: admin, billing, usage, customer, auth, and health controllers.
- Bridge code: billing, usage, payment, audit, cache, and search services.
- Sinks: native usage query construction, invoice lookup, billing audit behavior, plan-rate mutation.
- Controls/decoys: security config, reference guards, repositories, audit producer/consumer, and cache boundaries.

What it identified:

- Full usage SQL injection to invoice IDOR and audit-bypass exfiltration chain.
- Partial weak billing-admin custom-rate data-modification chain.

What held it back:

- Two components of the billing-admin chain were missed, leaving the auth/session family incomplete.
- The visible candidate set satisfied the report gates, but hidden recall still showed only `1/2` complete chains.

The app finished in one complete attempt with no corrective pass, no provider recovery, and a valid ledger.

## app-14 Journey

The agent first globbed broad TypeScript source and docs, then read app bootstrap, auth controller/service, token service, appointment controller/service/repository, schedule validator, patient search controller/client, clinical note controller/service, debug controller, and route files. The first attempt generated a report but hit a report-format gate, so the benchmark launched a corrective second pass.

The corrective pass narrowed the search around controllers, services, repositories, consumers, routes, auth, patient search, schedule validation, audit producer, prescription consumer, Kafka config, and app wiring. It then rewrote the final report through the report writer.

Navigation pattern:

- Entry surfaces: auth, appointment, clinical-note, patient-search, and debug routes/controllers.
- Bridge code: token verification, appointment service/repository, schedule validation, patient search client, audit producer, prescription consumer.
- Sinks: appointment detail lookup, prescription processing, search-client outbound path, debug topology output.
- Controls/decoys: blacklist/token lifecycle, route ownership checks, repository lookup boundaries, audit behavior, and search override handling.

What it identified:

- Full weak JWT validation to patient-notes IDOR and database-exfiltration chain.
- Full schedule override to missing-audit prescription-tampering chain.
- Full debug topology leak to internal search pivot chain.

What held it back:

- Candidate-flow coverage still had state-changing and webhook/outbound gaps.
- Line-reference count was lower than the other two apps even though exact evidence validation passed.

The app finished with full hidden recall, a valid ledger, exact evidence coverage, and no provider or tool-parse recovery events.

## Cross-App Pattern

The agent consistently found concrete route-to-service-to-sink flows when the bridge was visible in the same family of files. It performed best when the chain crossed debug or query/outbound surfaces and weakest when the chain required subtle auth/session or state-changing interpretation.

Task-local continuity worked well enough for this short run: mission contract updates captured progress, the second app-14 attempt repaired the report, and final report selection chose the usable attempt. Persistent memory was not needed and was not written.

## Bottom Line

GPT-5.4-mini produced fast, clean, source-only reports with strong evidence structure and full app-14 recall. The remaining quality gap is not report format; it is discovery and chain bridging, especially auth/session and state-changing paths in app-05 and app-10.
