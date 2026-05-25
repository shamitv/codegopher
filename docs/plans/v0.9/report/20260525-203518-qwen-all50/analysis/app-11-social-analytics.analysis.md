# Analysis - app-11-social-analytics

- App key: `app-11-social-analytics`
- Temp workspace: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260525-203518-qwen-all50\app-11-social-analytics\workspace`
- Return code: 0
- Attempts: 1
- Generated report: yes
- Report writer called: yes

## Event Counts

| Event | Count |
|---|---:|
| `reasoning_delta` | 3614 |
| `session_started` | 1 |
| `text_delta` | 720 |
| `tool_call` | 50 |
| `tool_result` | 50 |
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
- Components detected: 6 / 6
- Recall: 1.000
- Full chains: 2 / 2
- Full-chain recall: 1.000

## Recall By Difficulty

| Group | Chains | Components |
|---|---:|---:|
| hard | 1/1 | 3/3 |
| medium | 1/1 | 3/3 |

## Recall By Family

| Group | Chains | Components |
|---|---:|---:|
| ssrf | 2/2 | 6/6 |

### SSRF to Cloud Metadata → Full Credential Response → IAM Key Exfiltration

- Status: full
- Difficulty: medium
- Vulnerability family: ssrf
- Components detected: 3 / 3
- Missing required evidence: GET /api/debug/headers
- Decoy misfires: none

| Step | Method | Location | Detected | Evidence Terms | Required Hits | Missing Required | Negative Hits |
|---|---|---|---|---|---|---|---|
| 1 | `POST /api/preview` | `src/index.ts` | yes | /api/preview, 169.254.169.254, fetches, hostname, metadata, server-side, services, validation | src/index.ts, POST /api/preview | none | none |
| 2 | `POST /api/preview` | `src/index.ts` | yes | credential, metadata, payload, previously, removed, response, returning | src/index.ts, POST /api/preview | none | none |
| 3 | `GET /api/debug/headers` | `src/index.ts` | yes | /api/debug/headers, headers, including, injected, internal, request, returns | src/index.ts | GET /api/debug/headers | none |

### Subtle State Confusion Pivot To Ssrf

- Status: full
- Difficulty: hard
- Vulnerability family: ssrf
- Components detected: 3 / 3
- Missing required evidence: global, renderWidgets, generatePreview
- Decoy misfires: none

| Step | Method | Location | Detected | Evidence Terms | Required Hits | Missing Required | Negative Hits |
|---|---|---|---|---|---|---|---|
| 1 | `global` | `public/js/app.js` | yes | client-side, directly, hardcoded, internal, security, sensitive | public/js/app.js | global | none |
| 2 | `renderWidgets` | `public/js/app.js` | yes | arbitrary, dashboard, directly, encoding, execution, innerhtml, renders, without | public/js/app.js | renderWidgets | none |
| 3 | `generatePreview` | `src/index.ts` | yes | /api/preview, axios.get, endpoint, fetches, internal, preview, request, server-side | src/index.ts | generatePreview | none |

## Report Quality

- Line reference count: 15
- Ground-truth components with location and method cited: 2 / 6
- Unmatched candidate chain titles: Chain 2: Stored XSS via Widget Title → Session/Data Theft, Chain 3: SSRF + Debug Header Leak → Authorization Bypass / Account Takeover
- Decoy misfire count: 0

## Tool Calls

- `list_dir` `call_1578b6a478a041f5871a202a` {"path": "."}
- `list_dir` `call_7b47f59769064b5a8c964ff6` {"path": "src"}
- `list_dir` `call_03b71a88f11442cfaa0b382e` {"path": "public"}
- `glob_search` `call_6ac8d1606c654411be232feb` {"pattern": "**/*"}
- `read_many_files` `call_c7dbdfddb86348d6bf6393af` {"paths": ["src/index.ts", "src/referenceGuards.ts", "public/index.html", "public/js/app.js", "public/css/main.css", "package.json", "Dockerfile", "tsconfig.json"]}
- `read_file` `call_1dfe2693ae734f139a1f4775` {"path": "src/index.ts"}
- `read_file` `call_4769b1ec57974fd6840895b2` {"path": "public/js/app.js"}
- `read_file` `call_5e82b7c65ea24d45ab775c22` {"end_line": 80, "path": "src/index.ts", "start_line": 1}
- `grep_search` `call_e1b9b800d00e4a46976e98a2` {"path": "src/index.ts", "query": "app.listen"}
- `grep_search` `call_47174499cec04022ac873889` {"path": "src/index.ts", "query": "app.get"}
- `grep_search` `call_3bb2e4bcae8840b39c56c96b` {"path": "src/index.ts", "query": "app.post"}
- `grep_search` `call_78e801b27fa541f3b1785fae` {"path": "src/index.ts", "query": "app.use"}
- `read_file` `call_ab34a9c5f4a14adb99aca2dd` {"end_line": 25, "path": "src/index.ts", "start_line": 20}
- `read_file` `call_8ee7a0c3a34941d8b3c1a540` {"end_line": 12, "path": "src/index.ts", "start_line": 1}
- `grep_search` `call_a4fa5b6f462447db8d7edbcf` {"path": "src/index.ts", "query": "/auth"}
- `grep_search` `call_baaaaabcbbe34164a56a4573` {"path": "src/index.ts", "query": "POST"}
- `grep_search` `call_1c580acd99964ed889fea6a9` {"path": "src/index.ts", "query": "widgets"}
- `grep_search` `call_81802c592a6b4d4c938037c6` {"path": "src/index.ts", "query": "cors"}
- `grep_search` `call_91419aa873504021b5b1c902` {"path": "src/index.ts", "query": "cookie"}
- `grep_search` `call_3b6bc175ab274cd3afc6a57a` {"path": "src/index.ts", "query": "PORT"}
- `grep_search` `call_7a995e606b864c71bd78e1de` {"path": "src/index.ts", "query": "localhost"}
- `grep_search` `call_11c74ad78f604cf499b95380` {"path": "src/index.ts", "query": "express"}
- `grep_search` `call_d48c0ba38f8f4117afc70f4d` {"path": "src/index.ts", "query": "axios"}
- `grep_search` `call_f9d5a193b76e40448a89470b` {"path": "src/index.ts", "query": "url"}
- `read_file` `call_96bd2b2057db46f9b117f1dc` {"end_line": 1, "path": "src/index.ts", "start_line": 1}
- `grep_search` `call_048cb08262e449c48847b30d` {"path": "src/index.ts", "query": "app.post('/api"}
- `grep_search` `call_857dec9427a94dd0af44b8f4` {"path": "src/index.ts", "query": "debug"}
- `grep_search` `call_d11f65f6b8b74f9385d705fe` {"path": "src/index.ts", "query": "preview"}
- `grep_search` `call_ffd72fd121ee45b997e1f0fe` {"path": "src/index.ts", "query": "users"}
- `grep_search` `call_423dd3c6d5b64bdcae71c263` {"path": "src/index.ts", "query": "cors"}
- `grep_search` `call_2be94d05f6d949b0a2dd04fd` {"path": "src/index.ts", "query": "Cookie"}
- `read_file` `call_30766cd3687341849de54ba3` {"end_line": 5, "path": "src/index.ts", "start_line": 1}
- `read_file` `call_38e8cdee9a174778ac24d197` {"end_line": 15, "path": "src/index.ts", "start_line": 1}
- `read_file` `call_824ebc6392774fa381ff89b0` {"path": "public/index.html"}
- `read_file` `call_42deb830c5744b7c8cadfb0a` {"path": "public/js/app.js"}
- `read_file` `call_c5114950e0e54bbb8d760953` {"path": "src/referenceGuards.ts"}
- `read_file` `call_a7a4a913c2384d3bb46ecc32` {"path": "package.json"}
- `read_file` `call_77278488a7fb4614bb975122` {"path": "Dockerfile"}
- `grep_search` `call_d0365606b3804e3d950bf5c9` {"query": "validateLogin"}
- `grep_search` `call_582a38ce50df4165a09eb419` {"query": "handleLogin"}
- `grep_search` `call_fc2a3cd22bd34d4f85ba7369` {"query": "login"}
- `grep_search` `call_090eb1bc0cea45cdb71b0444` {"query": "getALL"}
- `grep_search` `call_9108ad43c9de42dbb89d2e61` {"query": "get('/api"}
- `grep_search` `call_8388d8b042ce42afa7548765` {"query": "/app.post"}
- `grep_search` `call_8837a908d9eb44f6ae489b37` {"query": "/preview"}
- `grep_search` `call_f143c7e850284535a30f926d` {"query": "/"}
- `grep_search` `call_99176c0987ef4668b87058b2` {"query": "respond"}
- `grep_search` `call_f8241a918c3f4ad1a990d9b8` {"query": "user"}
- `grep_search` `call_ccf421d29e6e41a894a1a0e5` {"query": "port"}
- `write_chained_vulnerability_report` `call_57a6a127edfb4ac98c78f635` {"content": "# Chained Vulnerability Static Audit Report\n\n**Application:** app-11-social-analytics (Neon Metrics Platform)\n**Audit Type:** Static-only chained vulnerability review\n**Date:** 2026-05-25\n**Reviewer:** CodeGopher (Static-Only)\n**Scope:** All files under `src/`, `public/`, configuration, and dependency manifests\n\n---\n\n## Summary Dashboard\n\n| Metric | Value |\n|---|---|\n| **Total chained vulnerabilities found** | 3 |\n| **Maximum severity** | Critical |\n| **Cross-cutt...
