# v0.15 Focused Validation Journey

This report summarizes the focused-validation run from 2026-05-30 and explains
how the agent worked, what it inspected, where it found chains, and why some
chains were missed. The underlying raw artifacts lived in temporary benchmark
output; this committed report keeps only sanitized conclusions.

## Executive Summary

The v0.15 implementation improved observability and made Qwen viable again as a
local validation participant, but it did not improve GPT recall.

GPT-5.4-mini completed all three apps in one attempt each with valid ledgers and
writer calls, but it found fewer components and chains than v0.14. Its source
navigation was orderly and source-led, yet it still missed key auth/session and
state-changing bridges.

Qwen 3.5 35B passed a lightweight hello check and completed all three focused
apps. Unlike v0.14, it reached workspace inspection, read source heavily, called
the report writer, and found strong recall. Its weak spots were malformed
tool-call recovery, invalid ledger repair on one app, candidate-flow repair that
missed a writer call, and very slow local throughput.

## What The Agent Actually Did

Across successful attempts, discovery used:

- `list_dir` to confirm workspace layout.
- `glob_search` to expand TypeScript source and docs in the telemedicine app.
- `read_file` and `read_many_files` to inspect routes, controllers, services,
  repositories, configuration, models, search clients, support guards, workers,
  and templates.
- `update_todo` to preserve candidate evidence during longer runs.
- `write_chained_vulnerability_report` to emit final reports.

The run did not need shell execution, live probing, MCP calls, memory writes, or
arbitrary writes as successful audit paths.

## GPT-5.4-Mini Journey

### App-05: Online Learning Management System

GPT used a single broad source sweep:

- listed the workspace and major source/template/static/doc directories
- read batches across controllers, routes, services, repositories, config,
  worker/support files, templates, and static JavaScript
- reread selected auth, import, debug, submission, and instructor files with
  line numbers
- updated TODO state repeatedly before calling the report writer

What it found:

- a full debug config leak -> SSRF internal pivot chain
- partial evidence for config leak -> session forgery -> quiz submission
  exfiltration

What it missed:

- the enrollment role escalation -> missing audit -> grade tampering chain
- enough auth/session bridging evidence to complete the session-forgery chain

### App-10: Telecom Billing Platform

GPT completed in one attempt:

- listed the workspace
- read Java controllers, config/security, services, repositories, models,
  search, support guards, health, and payment/billing files
- updated TODO state and called the report writer

What it found:

- partial evidence for usage SQL injection -> invoice IDOR -> audit bypass

What it missed:

- the full weak admin auth -> custom rate -> missing audit data-modification
  chain
- one component of the SQL/IDOR/data-exfiltration chain

This was the largest GPT regression in the focused subset.

### App-14: Telemedicine Appointment System

GPT used one broad TypeScript pass:

- listed the workspace
- globbed source and docs
- read app bootstrap, auth, token, appointment, patient search, debug,
  clinical note, schedule validation, repositories, route files, migrations,
  configuration, and reference guards
- called the report writer

What it found:

- a full weak JWT validation -> patient notes IDOR -> DB exfiltration chain
- a full debug topology leak -> SSRF internal pivot chain
- partial evidence for schedule override -> missing audit -> prescription
  tampering

What it missed:

- one component needed to complete the schedule override chain
- candidate-flow coverage for jobs, state-changing paths, and
  webhook/outbound-call families

## Qwen 3.5 35B Journey

### App-05: Online Learning Management System

Qwen had the richest local journey:

- attempts 1, 2, and 4 had malformed tool-call argument failures
- attempt 2 still produced the selected last-good report
- attempt 3 hit a quality-gate failure
- candidate-flow repair ran as attempt 4 but did not call the report writer

The model read broadly across config, auth, repositories, routes, services,
debug/import paths, workers, database clients, templates, and support files. It
used TODO updates and called the report writer in usable attempts.

What it found:

- a full enrollment role escalation -> missing audit -> grade tampering chain
- a full debug config leak -> SSRF internal pivot chain
- partial evidence for config leak -> session forgery -> quiz submission
  exfiltration

What it missed:

- the final component needed to complete the session-forgery chain
- candidate-flow representation for repositories/query sinks, state-changing
  paths, and validators

### App-10: Telecom Billing Platform

Qwen completed this app in one attempt:

- listed the workspace
- read the existing report path as part of source context
- read batches across security config, auth/admin/customer/billing/usage
  controllers, services, repositories, models, search, cache, support guards,
  application bootstrap, and deployment manifests
- called the report writer

What it found:

- a full weak billing admin auth -> custom rate -> missing audit logs ->
  data-modification chain
- a full usage SQL injection -> invoice IDOR -> audit bypass -> data
  exfiltration chain

What remained weak:

- candidate-flow coverage still had a validator-family gap, but recall and
  ledger validity were strong.

### App-14: Telemedicine Appointment System

Qwen showed strong recall but unstable repair:

- attempt 1 wrote a report but had malformed tool-call arguments
- attempt 2 timed out or ended without turn completion
- attempt 3 became the selected last-good report but still had malformed
  tool-call recovery
- ledger repair ran as attempt 4 but also ended with malformed tool-call
  arguments

The model read app bootstrap, auth controllers/services, token service,
repositories, user and clinical-note models, appointment and clinical note
routes, patient search, debug, configuration, Kafka/database support,
reference guards, and schedule validation.

What it found:

- a full weak JWT validation -> patient notes IDOR -> DB exfiltration chain
- a full debug topology leak -> SSRF internal pivot chain
- partial evidence for schedule override -> missing audit -> prescription
  tampering

What it missed or failed to stabilize:

- one component needed to complete the schedule override chain
- exact evidence in the JSON ledger for several candidates
- candidate-flow coverage for jobs, repositories/query sinks, state-changing
  paths, and webhook/outbound-call flows
- a clean safety/hygiene gate, because answer-key leakage diagnostics were
  triggered in visible source

## What The Run Missed Overall

Across GPT and Qwen, the repeated miss pattern remained chain bridging rather
than first-hop discovery:

- GPT underperformed on auth/session and state-changing chain completion.
- GPT did not benefit enough from the v0.15 focus queue and lost recall.
- Qwen found more chains but still struggled with malformed tool-call JSON during
  retry and repair work.
- Candidate-flow repair observability improved: Qwen `app-05` now clearly shows
  a failed repair because the repair attempt missed the writer call while the
  last-good report was preserved.
- Ledger repair observability improved: Qwen `app-14` clearly shows that repair
  was attempted but did not produce a valid final ledger.

The stronger parts of the run were also clear:

- both models stayed inside static-only boundaries for successful audit paths
- all completed app summaries had report writer calls
- Qwen was no longer transport-blocked and produced high recall on all three
  focused apps
- last-good preservation protected usable reports from later malformed or repair
  failures

## Bottom Line

v0.15 improved observability and restored local Qwen as a real validation model,
but it did not improve GPT recall. Full validation should remain blocked until
GPT recall recovers and Qwen ledger/tool-call stability improves.
