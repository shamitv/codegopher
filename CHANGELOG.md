# Changelog

All notable changes to CodeGopher will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
