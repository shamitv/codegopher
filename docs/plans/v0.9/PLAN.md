# CodeGopher v0.9 Plan - Harder Chained Vulnerability Benchmark Corpus

## Background

v0.8 added development-only benchmark tooling and produced sanitized all-50 `secure-code-hunt` benchmark reports. The later model-comparison review found an important proxy-routing caveat: both compared all-50 runs were served by Qwen upstream, even when one run was requested with a Gemma model id. Those reports remain useful as historical Qwen baselines, but they are not a clean model comparison.

The current corpus is also becoming too easy for the chained-audit workflow. Each app currently has one planted chain, most chains have only two or three components, and the common families are direct IDOR, SQL injection, SSRF, weak auth, debug/config leaks, and predictable session issues. v0.9 raises benchmark difficulty by modifying the existing 50 apps in place and making evaluation stricter.

## Goals

- Make the all-50 benchmark harder and more diagnostic while keeping every finding statically discoverable from source.
- Modify all 50 existing apps in place, preserving app identity, language, framework, and toy-app readability.
- Increase the benchmark from 50 chains to roughly 80-100 chains by adding second subtle chains to most apps.
- Add a mixed difficulty ladder: 15 medium apps, 25 hard apps, and 10 expert apps.
- Strengthen manifest and evaluator semantics so subtle chains are scored by source evidence, difficulty, vulnerability family, and decoy behavior.
- Produce a new Qwen baseline after proxy routing is verified.

## Difficulty Model

- Medium chains have three components and require direct cross-file review of routes, services, repositories, or models.
- Hard chains have four components and require layered control-flow or data-flow reasoning across validation, auth, state, config, and sink behavior.
- Expert chains have four to six components and require subtle reasoning about state confusion, parser differences, framework defaults, delayed jobs, background processing, or trust-boundary mismatches.

Target app distribution:

- 15 medium apps.
- 25 hard apps.
- 10 expert apps.

## Corpus Strategy

- Preserve each app's stack and domain while making old reports insufficient as direct answers.
- Evolve each existing chain by moving at least one link to another file or layer, adding one realistic prerequisite, and adding one safe-looking decoy near the vulnerable path.
- Add second chains to most apps using subtle variants of IDOR, SQL/NoSQL injection, SSRF, auth/session weakness, crypto misuse, deserialization, path traversal, template injection, parser confusion, race/state confusion, logging/debug artifact leakage, webhook/background-job abuse, or frontend/backend trust-boundary bugs.
- Remove or rewrite source, UI, test, and documentation hints that contain benchmark labels such as `vulnerability`, `OWASP`, `CWE`, `target`, `exploit`, `ground truth`, `scenario`, or `security analysis`.
- Keep evaluator-only docs and manifests hidden from benchmark temp workspaces.

## Manifest And Evaluator Strategy

- Extend `.vulns` manifests with chain-level `difficulty`, `subtlety_tags`, `required_evidence`, `chain_prerequisites`, `negative_evidence`, and `vulnerability_family`.
- Support multiple chains per app without changing the development-only runner interface.
- Score full-chain recall and component recall separately.
- Require stronger evidence for component detection: expected file path plus method/symbol evidence, or file path plus a strong description match.
- Report recall by difficulty tier and vulnerability family.
- Track decoy misfires and missing evidence so benchmark reports explain why a chain was only partially detected.
- Keep unmatched candidate chains as manual-review items, not automatic false positives.

## Verification Strategy

- Validate all 50 manifests parse with the extended schema.
- Validate every manifest location and required-evidence file anchor exists in source.
- Validate sanitized temp workspaces remove evaluator files and obvious benchmark hints.
- Run focused unit tests for manifest parsing, evaluator scoring, hygiene, and report rendering.
- Run the Python test suite, Ruff, and mypy.
- After proxy routing is confirmed, run the all-50 benchmark with Qwen and archive results under `docs/plans/v0.9/report/<timestamp>`.

## Out Of Scope

- Public benchmark CLI or compatibility guarantees.
- Dynamic/runtime vulnerability testing.
- Automated remediation or code-fix generation.
- Clean model comparison before proxy routing is verified.
