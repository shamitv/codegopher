# Analysis - app-16-restaurant-reviews

- App key: `app-16-restaurant-reviews`
- Temp workspace: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260524-234855-all50\app-16-restaurant-reviews\workspace`
- Return code: 0
- Attempts: 1
- Generated report: yes
- Report writer called: yes

## Event Counts

| Event | Count |
|---|---:|
| `reasoning_delta` | 10514 |
| `session_started` | 1 |
| `text_delta` | 720 |
| `tool_call` | 17 |
| `tool_result` | 17 |
| `turn_complete` | 1 |
| `turn_started` | 1 |

## Safety

- Compromised run: no
- Removed docs referenced in tool calls: none
- Parent/original-root refs in tool calls: none
- Unsafe tool calls: 0
- Denied or unknown tool results: 0
- Output mentions removed docs: no
- Output mentions original root: no

## Ground Truth Recall

- Status: full
- Components detected: 2 / 2
- Recall: 1.000

### Predictable Session Hijacking → IDOR Review Sabotage

- Status: full
- Components detected: 2 / 2

| Step | Method | Location | Detected | Evidence Terms |
|---|---|---|---|---|
| 1 | `POST /api/auth/login` | `src/index.js` | yes | generation, predictable, session |
| 2 | `POST /api/reviews/:id/edit` | `src/index.js` | yes | authenticated, reviews, session, without |

## Report Quality

- Line reference count: 15
- Ground-truth components with location and method cited: 0 / 2
- Unmatched candidate chain titles: Chain 1: SQL Injection → Complete Database Exfiltration, Chain 2: Hardcoded Credentials → Admin Privilege Escalation, Chain 4: SQL Injection → Error-Based Schema Enumeration

## Tool Calls

- `list_dir` `call_31a97b4241f74daa8777432d` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-16-restaurant-reviews\\workspace"}
- `update_todo` `call_497aebd97774437089aa3eeb` {"action": "add", "text": "Phase 1: Attack surface mapping - explore project structure"}
- `list_dir` `call_32d67569d05c4bf2b1b8abc8` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-16-restaurant-reviews\\workspace\\src"}
- `read_file` `call_b4959bece50341bd98a1a867` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-16-restaurant-reviews\\workspace\\package.json"}
- `read_file` `call_0ace229b63c2406ab5c1d57c` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-16-restaurant-reviews\\workspace\\Dockerfile"}
- `read_file` `call_d02e42fff0f84a94a14b8f56` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-16-restaurant-reviews\\workspace\\src\\index.js"}
- `update_todo` `call_b78c2932ff9649d8a5ca9cef` {"action": "done", "id": "todo-f5cdd61a", "text": "Phase 1: Attack surface mapping - explore project structure"}
- `update_todo` `call_9087215efcae4f91a8f8bba6` {"action": "add", "text": "Phase 2: Weakness inventory - identify individual vulnerabilities"}
- `glob_search` `call_566c31174f644338a88e33f9` {"pattern": "**/*.{js,ts,json,md,yaml,yml,txt}"}
- `glob_search` `call_ab8ab5a5c6494f6eaf61a37b` {"pattern": "src/**/*.js"}
- `grep_search` `call_012fb82443674850a814a370` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-16-restaurant-reviews\\workspace", "query": "req.query"}
- `grep_search` `call_c09d89d0346243d8bf5bf6fb` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-16-restaurant-reviews\\workspace", "query": "req.params"}
- `update_todo` `call_3cb03e0d469b412bb7ecc861` {"action": "start", "text": "Phase 2: Weakness inventory - identify individual vulnerabilities"}
- `update_todo` `call_2af7851df7b94f7ba220c34b` {"action": "start", "id": "todo-f3573712", "text": "Phase 2: Weakness inventory - identify individual vulnerabilities"}
- `update_todo` `call_35a43ded8e2f4d949f375ff7` {"action": "done", "id": "todo-f3573712"}
- `write_chained_vulnerability_report` `call_e71d15f1b42941feb32ce861` {"content": "# Chained Vulnerability Static Audit Report\n\n**Project:** Restaurant Review Platform (app-16-restaurant-reviews)  \n**Date:** 2026-05-24  \n**Scope:** `src/index.js` (complete application)  \n**Review Type:** Static-only analysis — no live probes, no dynamic testing, no external tooling\n\n---\n\n## Summary Dashboard\n\n| Metric | Value |\n|--------|-------|\n| Total chains identified | **4** |\n| Maximum severity | **HIGH** |\n| HIGH severity chains | 2 |\n| MEDIUM severity ch...
- `update_todo` `call_e1257facc5df4e149c2c01e8` {"action": "done", "id": "todo-f3573712"}
