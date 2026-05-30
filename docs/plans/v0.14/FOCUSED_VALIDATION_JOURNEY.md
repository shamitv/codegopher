# v0.14 Focused Validation Journey

This report summarizes the latest focused-validation run from 2026-05-30 and
explains how the agent worked, what it inspected, where it found chains, and
why some chains were missed. The underlying raw artifacts lived in temporary
benchmark output; this committed report keeps only sanitized conclusions.

## Executive Summary

The GPT-5.4-mini run worked as intended: it started with broad workspace
inventory, expanded into source-family sweeps, updated TODO state as it
collected evidence, and wrote chained-vulnerability reports for all three apps.
It succeeded on the targeted runs but still showed coverage gaps in
`auth_session` and candidate-flow bridging.

The Qwen 3.5 35B local-responses run did not reach workspace inspection at all.
Every attempt failed at provider startup with an upstream connection error, so
there is no meaningful source-navigation journey to summarize for that model.

## What The Agent Actually Did

The latest run did not use `grep_search`. Discovery was built from:

- `list_dir` to confirm the workspace root and the top-level file layout.
- `glob_search` to expand the search space by file family.
- `read_file` and `read_many_files` to inspect the most relevant source,
  template, config, and support files.
- `update_todo` to mark evidence items as the agent formed chain hypotheses.
- `write_chained_vulnerability_report` to emit the final audit report.
- In one later repair pass, `write_file` was used as part of report cleanup.

No README-specific read was observed in the latest run. The agent did search for
Markdown files in one app, but the actual journey was source-led rather than
doc-led.

## GPT-5.4-Mini Journey

### App-05: Online Learning Management System

The first attempt was a broad sweep:

- `list_dir(".")`
- `glob_search("src/**/*.py")`
- `glob_search("templates/**/*.html")`
- `glob_search("static/js/**/*.js")`
- `glob_search("*.md")`
- batched `read_many_files` over routes/controllers/services/repositories/
  config/workers/support files
- repeated `update_todo` calls as candidate evidence accumulated
- `write_chained_vulnerability_report`

That attempt showed the main working style of the model: it did not jump to a
single sink. It fanned out across routes, controllers, services, repositories,
configuration, and worker code, then used TODO updates to keep track of the
candidate chain set.

The selected second attempt was more targeted and focused on the missing
rendering branch:

- `read_file` on `src/routes/dashboard_routes.py`
- `read_file` on `templates/dashboard_instructor.html`
- `read_file` on `src/routes/auth_routes.py`
- `read_file` on `src/routes/course_routes.py`
- `read_file` on `src/routes/instructor_routes.py`
- `read_file` on `src/routes/submission_routes.py`
- `read_file` on `src/services/debug_service.py`
- `read_file` on `src/services/prereq_validator.py`
- `read_file` on `src/controllers/auth_controller.py`
- `read_file` on `src/controllers/course_controller.py`
- `read_file` on `src/controllers/instructor_controller.py`
- `read_file` on `src/controllers/submission_controller.py`
- `read_file` on `src/services/submission_service.py`
- `read_file` on `src/services/grade_override_service.py`
- `read_file` on `src/services/import_service.py`
- `read_file` on `src/services/rate_limiter.py`
- `write_chained_vulnerability_report`

That corrective pass was triggered because rendering/raw HTML sinks had not been
reviewed yet. The model then closed the report-quality gap by reading the
missing template area, but it still left some source-to-sink paths only partially
connected.

What it found:

- a partial IDOR chain around config leak -> session forgery -> quiz submission
  exfiltration
- a full SSRF chain around debug config leak -> internal fetch pivot
- evidence for a second IDOR-style chain remained incomplete

What it missed and why:

- It read `auth_routes.py` and `auth_service.py`, but it did not connect the
  `current_user` step strongly enough to complete the session-forgery chain.
- It under-covered `auth_session` as a high-risk family, so the IDOR path never
  became a full chain.
- The discovery path was broad but still uneven: it covered routes, services,
  repositories, config, and worker code, yet candidate-flow coverage left gaps.

### App-10: Telecom Billing Platform

This run used the most straightforward discovery pattern of the three GPT apps:

- `list_dir(".")`
- `glob_search("src/main/java/com/telecom/billing/**/*.java")`
- `glob_search("src/test/**/*.java")`
- `glob_search("src/main/resources/**/*")`
- batched `read_many_files` across controllers, security/config, search,
  services, models, repositories, runtime config, messaging, and cache
- `update_todo`
- `write_chained_vulnerability_report`

The read batches were intentionally structured rather than random. The agent moved
from controllers to config, then to search/service layers, then to models and
repositories, then to runtime files and messaging/cache.

What it found:

- a full chain for usage SQL injection -> invoice IDOR -> audit bypass -> DB
  exfiltration
- a partial auth/session chain around weak billing admin auth -> unvalidated
  custom rate -> missing audit logs -> data modification

What it missed and why:

- It did not cover `auth_session` as a high-risk family, so the admin-auth chain
  never got the evidence needed to become complete.
- The model’s coverage was strong on controllers, repositories, and support
  infrastructure, but not on the privileged update path that would have closed
  the missing chain.
- There was no corrective pass here, so the first-pass coverage limits remained
  visible in the final result.

### App-14: Telemedicine Appointment System

This run was more iterative and showed the clearest repair behavior.

Attempt 1:

- `read_file` on `src/app.ts`
- `read_file` on `src/controllers/AuthController.ts`
- `read_file` on `src/controllers/AppointmentController.ts`
- `read_file` on `src/controllers/PatientSearchController.ts`
- `read_file` on `src/controllers/DebugController.ts`
- `read_file` on the route files for auth, appointments, patient search,
  clinical notes, and debug
- `read_file` on `src/services/AuthService.ts`
- `read_file` on `src/services/TokenService.ts`
- `read_file` on `src/services/AppointmentService.ts`
- `read_file` on `src/services/ScheduleValidator.ts`
- `read_file` on `src/repositories/UserRepository.ts`
- `read_file` on `src/repositories/AppointmentRepository.ts`
- `read_file` on `src/search/PatientSearchClient.ts`
- `read_file` on `src/referenceGuards.ts`
- `read_file` on `src/services/ClinicalNoteService.ts`
- `read_file` on `src/controllers/ClinicalNoteController.ts`
- `write_chained_vulnerability_report`

Attempt 2 was the selected attempt and was explicitly corrective. It reread the
same core files, then used previous report context:

- `list_dir(".")`
- `read_file` on the controllers, routes, services, repositories, and support
  files again
- `read_file` on `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`
- another small reread of `src/consumers/PrescriptionConsumer.ts`,
  `src/db/migrate.ts`, `src/config/appConfig.ts`, and `src/controllers/DebugController.ts`
- `write_chained_vulnerability_report`

That pass was triggered because the earlier attempt left unresolved evidence
markers and contradictory complete/incomplete conclusions. The model used the
previous report as a repair hint, which is a good example of report-driven
iteration.

Attempt 3 did not become the selected result. It started with a smaller
reconciliation pass:

- `list_dir(".")`
- `list_dir(".github")`
- `read_many_files` over a few repositories and the previous report file
- `read_file` on `src/controllers/AppointmentController.ts`
- `read_file` on `docs/security/CHAINED_VULNERABILITIES_REVIEW.md`
- `write_file`

What it found:

- a full schedule override -> missing audit -> undetected prescription tampering
  chain
- a full debug topology leak -> SSRF internal pivot chain
- a partial JWT validation -> patient notes IDOR -> DB exfiltration chain

What it missed and why:

- The `verify` step in `src/services/TokenService.ts` was not connected tightly
  enough to complete the IDOR chain.
- Candidate-flow repair was needed because the valid ledger still lacked
  candidate-flow coverage for `repositories_query` and `webhooks_outbound`.
- The run also registered one unsafe tool call and generic security vocabulary
  in visible source, so the report had to be treated carefully.

## Qwen Journey

The Qwen 3.5 35B local-responses run did not produce a source-navigation
journey.

All three attempts failed immediately with provider errors, so the run never got
past session startup:

- no `list_dir`
- no `glob_search`
- no `read_file`
- no `read_many_files`
- no `update_todo`
- no report writer call

In other words, the model failure happened before the agent could inspect any
workspace files or attempt chain construction.

## What The Run Missed Overall

Across the successful GPT run, the repeated miss pattern was not random. It was
coverage shape:

- `auth_session` was the main weak spot.
- `repositories_query` and `webhooks_outbound` were still gap areas in the
  telemedicine run’s candidate flow.
- The GPT runs were good at expanding from entry points into supporting code,
  but they sometimes failed to connect the last source hop that would complete a
  chain.
- The corrective passes helped the report quality, but they did not always
  eliminate the underlying coverage gap.

The stronger parts of the run were also consistent:

- source-family discovery was broad and deliberate
- chain evidence was gathered from concrete source files rather than guesses
- TODO state was used to preserve evidence collection progress
- report writing happened only after the model had enough context to synthesize
  a candidate ledger

## Bottom Line

GPT-5.4-mini succeeded by combining broad source discovery with corrective
re-reads and report-driven refinement. It found the highest-value chains in each
app, but it still missed some auth/session-driven paths because it did not fully
bridge the last hop in those chains.

Qwen 3.5 35B did not reach the analysis stage at all in the latest run, so its
failure is a provider/runtime failure rather than a source-discovery failure.
