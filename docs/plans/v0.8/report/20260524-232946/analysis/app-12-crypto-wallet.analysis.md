# Analysis - Crypto Wallet

- App key: `app-12-crypto-wallet`
- Temp workspace: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260524-232946\app-12-crypto-wallet\workspace`
- Return code: 0
- Attempts: 1
- Generated report: yes
- Report writer called: yes

## Event Counts

| Event | Count |
|---|---:|
| `reasoning_delta` | 3101 |
| `session_started` | 1 |
| `text_delta` | 670 |
| `tool_call` | 11 |
| `tool_result` | 11 |
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
| 1 | `getWallet` | `src/wallet/wallet.controller.ts` | yes | /api/wallet, accepts, address, authenticated, including, verifying, without |
| 2 | `getWallet` | `src/wallet/wallet.service.ts` | yes | control, cryptographic, getwallet, plaintext, privatekey, victim's |
| 3 | `externalTransfer` | `src/wallet/wallet.controller.ts` | yes | /api/wallet/external-transfer, accepts, address, arbitrary, authenticated, fromaddress, request, transfers |

## Report Quality

- Line reference count: 1
- Ground-truth components with location and method cited: 3 / 3
- Unmatched candidate chain titles: none

## Tool Calls

- `list_dir` `call_7e8c41aa81604509b1d52621` {"path": "."}
- `list_dir` `call_10291cfc66534ccbb10aafe4` {"path": "docs"}
- `list_dir` `call_9e6acfc08fb948e99bf19900` {"path": "src"}
- `read_file` `call_a23df299a2d44956a113bca8` {"end_line": 50, "path": "package.json", "start_line": 1}
- `glob_search` `call_b993eba687134d5ea3dc9465` {"pattern": "src/**/*.ts"}
- `list_dir` `call_bcc77fa8d83e45bb9508e139` {"path": "src/auth"}
- `list_dir` `call_3eae2a7cf79d4a68ae53a01f` {"path": "src/wallet"}
- `read_many_files` `call_154cbaec74df4311828335cd` {"paths": ["src/main.ts", "src/app.module.ts", "src/db.ts", "src/auth/auth.module.ts", "src/auth/auth.guard.ts", "src/wallet/wallet.module.ts", "src/wallet/wallet.controller.ts", "src/wallet/wallet.service.ts", "Dockerfile"]}
- `list_dir` `call_8e6bb4fd7ca74ea6a811d650` {"path": "public"}
- `read_file` `call_ac0894fdf31741f99e285b6f` {"path": "Dockerfile"}
- `write_chained_vulnerability_report` `call_1b574a5c85004eba9c196c9b` {"content": "# Chained Vulnerability Audit Report\n\n**Project:** app-12-crypto-wallet  |  **Date:** 2026-05-24  |  **Auditor:** CodeGopher (Static-Only)\n\n---\n\n## 1. Summary Dashboard\n\n| Metric | Value |\n|---|---|\n| Total attack chains identified | **4** |\n| Maximum severity | **CRITICAL** |\n| High-severity chains | **3** |\n| Critical-severity chains | **1** |\n| Medium-severity chains | **0** |\n| Low-severity chains | **0** |\n| Total cross-cutting weaknesses | **8** |\n| Confide...
