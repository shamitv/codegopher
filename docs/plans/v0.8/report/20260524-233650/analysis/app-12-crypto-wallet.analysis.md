# Analysis - Crypto Wallet

- App key: `app-12-crypto-wallet`
- Temp workspace: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260524-233650\app-12-crypto-wallet\workspace`
- Return code: 0
- Attempts: 1
- Generated report: yes
- Report writer called: yes

## Event Counts

| Event | Count |
|---|---:|
| `reasoning_delta` | 3690 |
| `session_started` | 1 |
| `text_delta` | 749 |
| `tool_call` | 23 |
| `tool_result` | 23 |
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
- Components detected: 3 / 3
- Recall: 1.000

### Wallet IDOR → Private Key Exposure → Unauthorized Asset Transfer

- Status: full
- Components detected: 3 / 3

| Step | Method | Location | Detected | Evidence Terms |
|---|---|---|---|---|
| 1 | `getWallet` | `src/wallet/wallet.controller.ts` | yes | /api/wallet, accepts, address, authenticated, including, without |
| 2 | `getWallet` | `src/wallet/wallet.service.ts` | yes | control, cryptographic, getwallet, includes, plaintext, privatekey |
| 3 | `externalTransfer` | `src/wallet/wallet.controller.ts` | yes | /api/wallet/external-transfer, accepts, address, authenticated, fromaddress, request, transfers, without |

## Report Quality

- Line reference count: 2
- Ground-truth components with location and method cited: 3 / 3
- Unmatched candidate chain titles: Chain 2: Weak Session ID (Numeric User ID) → Account Takeover Without Credentials, Chain 4: Plaintext Credential Storage + Weak Session → Mass Account Compromise

## Tool Calls

- `list_dir` `call_746c8e39f302431ab4ddf500` {"path": "."}
- `list_dir` `call_b3f4b3ccc18a4618916b3597` {"path": "src"}
- `read_file` `call_5d3ac53fa20b47b7b4571a79` {"path": "package.json"}
- `list_dir` `call_96de4a2599a94ae9a44ca351` {"path": "src/auth"}
- `list_dir` `call_9ce03cfb1a9e4145b09ba06e` {"path": "src/wallet"}
- `read_file` `call_f179b8da786c449592eb747c` {"path": "src/main.ts"}
- `read_file` `call_2097f154197d4ec18fd3368d` {"path": "src/app.module.ts"}
- `read_file` `call_b1a55dee62984fa48bccbc40` {"path": "src/db.ts"}
- `read_many_files` `call_9e24e4379f48404e8e0660ac` {"paths": ["src/auth/auth.guard.ts", "src/auth/auth.module.ts", "src/wallet/wallet.controller.ts", "src/wallet/wallet.module.ts", "src/wallet/wallet.service.ts"]}
- `list_dir` `call_426d6d95d9c44883b988652d` {"path": "public"}
- `glob_search` `call_b345267cc2d047898f937529` {"pattern": "**/*.ts"}
- `read_file` `call_ca8a6c2f6382438bb9c0a747` {"path": "src/wallet/wallet.service.ts"}
- `update_todo` `call_6d666b07e152418fb2fe4635` {"action": "add", "text": "Phase 1: Attack Surface Mapping"}
- `update_todo` `call_f93248abb7e24549bc1c1f40` {"action": "add", "text": "Phase 2: Weakness Inventory"}
- `update_todo` `call_93ba1e7b00bf45fbbb2d18ec` {"action": "add", "text": "Phase 3: Attack Graph Synthesis"}
- `update_todo` `call_60d349cd65734a689d9d85ea` {"action": "add", "text": "Phase 4: Report Writing"}
- `update_todo` `call_9c0a2abd7a32439a831c2ed4` {"action": "done", "id": "todo-680f9ed8"}
- `update_todo` `call_61c5d078c66d4054ae55c450` {"action": "done", "id": "todo-117dd41c"}
- `update_todo` `call_bacb6d0919a141efb8083f28` {"action": "done", "id": "todo-49e8d546"}
- `update_todo` `call_51154876b30a4fb3b66e451c` {"action": "start", "id": "todo-55ef23d8"}
- `write_chained_vulnerability_report` `call_4f6d5049202d48b9908bc21a` {"content": "# Chained Vulnerability Audit Report\n\n**Project:** Crypto Wallet Service (app-12-crypto-wallet)  \n**Audit Date:** 2026-05-24  \n**Auditor:** CodeGopher (Static-Only Analysis)  \n**Scope:** All source files in `src/` directory  \n\n---\n\n## Executive Summary\n\n| Metric | Value |\n|---|---|\n| Total chains identified | **4** |\n| Maximum severity | **CRITICAL** |\n| High confidence chains | **2** |\n| Medium confidence chains | **2** |\n| Weaknesses not forming a chain | **5**...
- `read_file` `call_ffdea82d791a4c96ac359e80` {"path": "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"}
- `update_todo` `call_c8b5758050964be297a94c90` {"action": "done", "id": "todo-55ef23d8"}
