# Analysis - app-12-crypto-wallet

- App key: `app-12-crypto-wallet`
- Temp workspace: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260524-234855-all50\app-12-crypto-wallet\workspace`
- Return code: 0
- Attempts: 1
- Generated report: yes
- Report writer called: yes

## Event Counts

| Event | Count |
|---|---:|
| `reasoning_delta` | 3479 |
| `session_started` | 1 |
| `text_delta` | 881 |
| `tool_call` | 14 |
| `tool_result` | 14 |
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
| 1 | `getWallet` | `src/wallet/wallet.controller.ts` | yes | /api/wallet, accepts, address, authenticated, including, matches, without |
| 2 | `getWallet` | `src/wallet/wallet.service.ts` | yes | control, getwallet, includes, plaintext, privatekey, victim's |
| 3 | `externalTransfer` | `src/wallet/wallet.controller.ts` | yes | /api/wallet/external-transfer, accepts, address, arbitrary, authenticated, fromaddress, request, transfers |

## Report Quality

- Line reference count: 2
- Ground-truth components with location and method cited: 2 / 3
- Unmatched candidate chain titles: Chain Breakdown, Chain Breakdown, Chain Breakdown, Chain Breakdown, Chain Breakdown

## Tool Calls

- `list_dir` `call_cbfd2a34fd814e0a86049c5f` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace"}
- `glob_search` `call_6ad71cebc981490aa336afc6` {"pattern": "**/*.{js,ts,jsx,tsx,py,go,java,rb,php,json,yaml,yml,toml}"}
- `glob_search` `call_f8c025d9459e48dfba860714` {"pattern": "**/*"}
- `read_many_files` `call_ef6c93c959dd4c5990e87b7e` {"paths": ["C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\src\\main.ts", "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\src\\app.module.ts", "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\src\\db.ts", "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-a...
- `list_dir` `call_5faab32dc206426380c271da` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\public"}
- `read_file` `call_2de08863415c4149aa3c4a7e` {"end_line": 50, "path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\public\\index.html", "start_line": 1}
- `read_file` `call_2bd5f80bfa874c4ab30d3412` {"end_line": 200, "path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\public\\js\\app.js", "start_line": 1}
- `read_file` `call_65ab86ec41254672bf001bc4` {"end_line": 100, "path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\public\\index.html", "start_line": 1}
- `read_file` `call_5673092227d74a798d1abd13` {"end_line": 200, "path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\src\\wallet\\wallet.service.ts", "start_line": 1}
- `read_file` `call_1086f3e9ad864432b676f412` {"end_line": 200, "path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\public\\index.html", "start_line": 40}
- `read_file` `call_23ba68040f9f4123aeb25a73` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\src\\wallet\\wallet.service.ts"}
- `read_file` `call_a57c8f5a216f4875905a7141` {"path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\public\\index.html"}
- `read_file` `call_a5a71d05bf5d4c54b0c94de2` {"end_line": 80, "path": "C:\\Users\\shamit\\AppData\\Local\\Temp\\codegopher-v08-chain-20260524-234855-all50\\app-12-crypto-wallet\\workspace\\public\\index.html", "start_line": 1}
- `write_chained_vulnerability_report` `call_55539749ca5a4444a2350f8a` {"content": "# Chained Vulnerability Static Audit Report\n\n**Project**: App-12 Crypto Wallet Service  \n**Date**: 2026-05-24  \n**Auditor**: CodeGopher (Chained Vulnerability Static Audit)  \n**Scope**: All files in workspace (source, templates, static assets, config)  \n**Mode**: Static-only — no live probes, no dynamic analysis\n\n---\n\n## Summary Dashboard\n\n| Metric | Value |\n|---|---|\n| Chains Identified | **5** |\n| Critical Severity | 2 |\n| High Severity | 2 |\n| Medium Severity ...
