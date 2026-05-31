# Changelog

All notable changes to CodeGopher will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-05-31

### Added
- Task-local episode memory that captures concise evidence for file reads, searches, listings, TODO updates, report writes, tool errors, and final decisions without persisting to user/project memory.
- Richer TODO lifecycle with `blocked` and `cancelled` states, plus optional reason, related-file, and evidence-reference metadata.
- Expanded `update_todo` model-facing actions for update, block, unblock, and cancel flows.
- Chained-audit report validation gates for Candidate Chain Ledger JSON structure, exact evidence shape, safe-control classification, and required negative evidence for no-chain outcomes.
- Static-audit tool policy hardening to deny hidden evaluator metadata paths, dotfile/hidden paths, parent traversal, and answer-key terminology searches.

### Changed
- Provider context and compaction now preserve episode memory, TODO state, skill context, and mission context more reliably during long-running tasks.
- Mission contract TODO seeding now includes mission reasons and artifact evidence references.
- OpenAI-compatible Chat Completions streaming now requests `stream_options.include_usage` and retries without it when unsupported by upstream routes.
- Internal benchmark proxy startup now fails fast when another active run could contaminate request/token/cost attribution.
- Architecture docs and release planning docs were updated for current runtime behavior and verification outcomes.

### Fixed
- Reduced shallow no-chain conclusions in chained-audit workflows by requiring candidate and negative-evidence state in final report validation.
- Improved compatibility with OpenAI-compatible endpoints that reject streaming usage options.

## [0.2.1] - 2026-05-25

### Added
- Interactive Textual TUI, VS Code chat bridge, MCP stdio/SSE integration, context compaction, memories, Markdown skills, and session TODOs.
- Repository documentation skill packs and static security skill packs.
- Chained-vulnerability static audit skill, static-only chained audit policy, attack graph/report models, Mermaid/report generation, and dedicated chained report writer.
- Provider compatibility option for Chat Completions upstreams that require `reasoning_content` replay.
- Internal development benchmark tooling for sanitized chained-audit evaluation.
- Mission contracts and task ledgers for selected complex skill workflows.

### Changed
- Updated the PyPI README with current alpha status and sanitized release example outcomes.
- Compacted generated benchmark artifacts into summary files to keep the repository lightweight.

### Fixed
- Improved chained-audit completion reliability by validating required report writer/tool gates before final completion.
