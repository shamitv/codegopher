# Analysis - app-49-sports-league

- App key: `app-49-sports-league`
- Temp workspace: `%LOCALAPPDATA%\Temp\codegopher-v08-chain-20260525-180047-gemma-all50\app-49-sports-league\workspace`
- Return code: 0
- Attempts: 1
- Generated report: yes
- Report writer called: yes

## Event Counts

| Event | Count |
|---|---:|
| `reasoning_delta` | 7157 |
| `session_started` | 1 |
| `text_delta` | 1025 |
| `tool_call` | 112 |
| `tool_result` | 112 |
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

### SQLi Player Dump → IDOR Contract Access → Score Manipulation

- Status: full
- Components detected: 3 / 3

| Step | Method | Location | Detected | Evidence Terms |
|---|---|---|---|---|
| 1 | `search_players` | `app.py` | yes | database, injection |
| 2 | `get_player` | `app.py` | yes | sensitive |
| 3 | `update_score` | `app.py` | yes | authenticated, control, endpoint, missing |

## Report Quality

- Line reference count: 9
- Ground-truth components with location and method cited: 1 / 3
- Unmatched candidate chain titles: Chain 1: Bypass Authorization on Score Update (HIGH), Chain 2: Debug Mode + Open Binding Enables Unauthorized Access (MEDIUM)

## Tool Calls

- `list_dir` `call_7d2ce8e90b1b4301857184f5` {"path": "."}
- `glob_search` `call_d9f246d7e8c245518023f7af` {"pattern": "**/*.py"}
- `glob_search` `call_b77944843bfb48c08dc18a2a` {"pattern": "**/*.{json,yaml,yml,toml,ini,cfg,conf}"}
- `read_file` `call_e80bd158215247e3bc140404` {"path": "app.py"}
- `read_file` `call_2e0bbc035e224074bb114d3a` {"path": "Dockerfile"}
- `read_file` `call_fd4c4831988944ecad16bf68` {"path": "requirements.txt"}
- `read_file` `call_2c92eaf877a44f0b9e6ea618` {"end_line": 300, "path": "app.py", "start_line": 1}
- `glob_search` `call_75a50df432f8401799ea369a` {"pattern": "app.py"}
- `grep_search` `call_4a689de466a844939d92c88a` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_c1e34f2a4dca4d64897380c2` {"path": "app.py", "query": "import"}
- `read_file` `call_850f3785e1ab4c9fa73fcaf8` {"path": "app.py", "start_line": 1}
- `grep_search` `call_1db405d12dc04f8d8204c360` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_1382c4fc86a844a1915b3b19` {"path": "app.py", "query": "def "}
- `grep_search` `call_24b3862975b143e19299fba4` {"path": "app.py", "query": "db_conn"}
- `list_dir` `call_1ea3c51300444a068d2439d6` {"path": "."}
- `grep_search` `call_c6e3b6d27fbe48e5bd02509e` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_bf4e5bc6eb7f4c3c83f5101c` {"path": "app.py", "query": "def "}
- `grep_search` `call_96c27b83fe3d472d89789742` {"path": "app.py", "query": "session"}
- `grep_search` `call_ece4bda78b15450a96adb342` {"path": "app.py", "query": "request"}
- `grep_search` `call_ddbf8f6cf0b34052a32dba6e` {"path": "app.py", "query": "cursor"}
- `grep_search` `call_166356ad674c4286816a6d89` {"path": "app.py", "query": "password"}
- `grep_search` `call_c84705f0ba1d444f8b634469` {"path": "app.py", "query": "auth"}
- `read_file` `call_dc005d545342489191158228` {"end_line": 50, "path": "app.py", "start_line": 1}
- `grep_search` `call_eeec362b6158402a96b6bbc4` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_c73946fe22b24cc4a290ec39` {"path": "app.py", "query": "def "}
- `grep_search` `call_cfc1d5fa48ae4438b1e292af` {"path": "app.py", "query": "return jsonify"}
- `grep_search` `call_7d075dbb6e364d06861e6f44` {"path": "app.py", "query": "session"}
- `grep_search` `call_fa58ef6a86794f7ba2e87760` {"path": "app.py", "query": "cursor.execute"}
- `grep_search` `call_e38d2bfeb9dd473fae2878ea` {"path": "app.py", "query": "request"}
- `grep_search` `call_355f16f2ca6d4426bb624086` {"path": "app.py", "query": "game"}
- `grep_search` `call_3ba5acc398fd46d08f8a4c64` {"path": "app.py", "query": "Score updating"}
- `grep_search` `call_813875e15b024ba5a347cc72` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_4c5938532f7c41e5b4ed6ff4` {"path": "app.py", "query": "import"}
- `grep_search` `call_e93c1e10e73d4b259ded7329` {"path": "app.py", "query": "jsonify"}
- `grep_search` `call_92a5fa7c21b64ad0bbe1d006` {"path": "app.py", "query": "sqlite3"}
- `grep_search` `call_d404ae49c8694ef194153531` {"path": "app.py", "query": "debug"}
- `grep_search` `call_50a6ebaf74ab441a894ebaad` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_86048848015447d68e4d79a8` {"path": "app.py", "query": "def "}
- `grep_search` `call_565c1f2580e84a75995f530a` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_22c2e062ebec4da380b85bea` {"path": "app.py", "query": "def "}
- `read_file` `call_5c34319b14c44d1d93cbded0` {"end_line": 10, "path": "app.py", "start_line": 1}
- `read_file` `call_1b24439a3a8a4932bd430f8b` {"path": "app.py"}
- `grep_search` `call_b7e7fffd10754ef4aa841e71` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_0e84bfe429c44213b0934165` {"path": "app.py", "query": "def "}
- `grep_search` `call_8c0270defd6443b88e24e822` {"path": "app.py", "query": "return "}
- `read_file` `call_c91f2091e0714dcd9d92cb6e` {"end_line": 5, "path": "app.py", "start_line": 1}
- `grep_search` `call_3dde7a5175344827aab7b38c` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_8c75793109e4435294145200` {"path": "app.py", "query": "def "}
- `grep_search` `call_6e720c76cfb242eeba2769b9` {"path": "app.py", "query": "init"}
- `grep_search` `call_211cbb5a3e9e4a99a9facccf` {"path": "app.py", "query": "flask"}
- `grep_search` `call_0230ca1322ac4b47a2b0b0eb` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_c9bc1a8d8f6847a0a510be3f` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_b306c90c85d547a6916d48e7` {"path": "app.py", "query": "def "}
- `grep_search` `call_ba2e81e9615340d3b5795c9f` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_ab93b0d892e84b169364863f` {"path": "app.py", "query": "def "}
- `grep_search` `call_5207a8a788d746f3aed3eedf` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_1fe711c3096b455ca0b4f504` {"path": "app.py", "query": "def "}
- `grep_search` `call_0a204e6bbc7a4f73b86b88a8` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_79e2bb6120ae44eb990eba9b` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_5d39410593eb4942b4a3e548` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_397dbfa3e1eb4948b08ad0bf` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_5814f7a34de64d9c849abaff` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_81655fe6874e4ecca81875ec` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_f9b05a3a124b4e87931d2886` {"path": "app.py", "query": "/api/"}
- `grep_search` `call_0fc37ba7796b437781e528a3` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_07873a86185b47368e53ebae` {"path": "app.py", "query": "@app.route('/"}
- `grep_search` `call_fd67d02e45ce4e36bea7db6c` {"path": "app.py", "query": "from"}
- `grep_search` `call_249133117d4d4d31a2a4a498` {"path": "app.py", "query": "#!/"}
- `grep_search` `call_76ebb6036ba9414487237a6f` {"path": "app.py", "query": "app.run"}
- `grep_search` `call_5418900f584c40baacb1ee6f` {"path": "app.py", "query": "__name__"}
- `grep_search` `call_99611781fc9746c797250e63` {"path": "app.py", "query": "sqlite"}
- `grep_search` `call_cc1bc1a30eec4c4eb472dd70` {"path": "app.py", "query": "update_score"}
- `grep_search` `call_f20c8fde2f634432835fa323` {"path": "app.py", "query": "update_game"}
- `grep_search` `call_e6ef2a4cd10341448225ded9` {"path": "app.py", "query": "@app.route"}
- `read_many_files` `call_720ab1ef3bff4c77825739ee` {"paths": ["app.py"]}
- `grep_search` `call_40e560d2fcd04ccf8b0d9691` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_16fe17c23ffd490d9a342b45` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_d0100f87dfb84c2ab80d7398` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_366b4aeb62084c2aa0b85a11` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_588cf7f4a24c4001a2398e3e` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_78322ea6da9c4979901a5790` {"path": "app.py", "query": "def "}
- `grep_search` `call_f654538e78f74a32a8df08ce` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_02bc887ec8b84ae392abf0f2` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_f9920ec78dd94c6794babfc9` {"path": "app.py", "query": "def "}
- `grep_search` `call_803025513f3c45a7a79ece6d` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_38996135a6df4b25a84c7620` {"path": "app.py", "query": "Flask"}
- `grep_search` `call_5646d50ea4a44d1cada18f75` {"path": "app.py", "query": "from"}
- `grep_search` `call_212268b464c948798c1f069f` {"path": "app.py", "query": "import"}
- `grep_search` `call_40b917bea5ad417eaa84a2dc` {"path": "app.py", "query": "@"}
- `grep_search` `call_ece8f0ea1e054991a90e01e7` {"path": "app.py", "query": "@app.route"}
- `read_file` `call_8a0368d345914276b7ce265b` {"end_line": 20, "path": "app.py", "start_line": 1}
- `grep_search` `call_3aa00095fca34fb6b789b5b2` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_cf84dfec661f47ea96222c61` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_64cc1a8f9fcb48a0a692f726` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_720aba2be61a42a2aed6d7b6` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_5093fa13a27b4ec3b20e8214` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_ead7de04f87d449ea252e834` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_55680ea5bc1f4d66959e17bd` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_7a0fca5594c8488c8e9838bb` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_be7cba515ec94d059b3e7f76` {"path": "app.py", "query": "@app.route"}
- `grep_search` `call_72f65ac80469464b90f8299e` {"path": "app.py", "query": "@app.route"}
- `read_file` `call_b00dda8f8f6d476b97669fee` {"end_line": 1, "path": "app.py", "start_line": 1}
- `read_file` `call_b670536b8ec4478e81fc678a` {"end_line": 2, "path": "app.py", "start_line": 2}
- `read_file` `call_351ac36fe5fd40c7a56b43b9` {"end_line": 3, "path": "app.py", "start_line": 3}
- `read_file` `call_5b364d43908449f58c8b9a12` {"end_line": 4, "path": "app.py", "start_line": 4}
- `read_file` `call_29c356a5da354f45ada9203a` {"end_line": 5, "path": "app.py", "start_line": 5}
- `read_file` `call_8e627a4d93b3487b8cbbb625` {"end_line": 1, "path": "app.py", "start_line": 1}
- `read_file` `call_993cf7ac397343faa61f9992` {"end_line": 3, "path": "app.py", "start_line": 1}
- `read_file` `call_97b6f58eed6f4f29a075dfa2` {"end_line": 5, "path": "app.py", "start_line": 1}
- `read_file` `call_d8c79d76bd9741ccbce1083a` {"end_line": 10, "path": "app.py", "start_line": 1}
- `write_chained_vulnerability_report` `call_4217269eee8144de8a0905ce` {"content": "# Chained Vulnerability Static Audit Report\n\n**Project**: Sports League Application (Flask)  \n**Date**: 2026-05-25  \n**Scope**: Full static analysis of `app.py`, `Dockerfile`, `requirements.txt`  \n**Audit Type**: Static-only (no live probes, no dynamic testing)\n\n---\n\n## Summary Dashboard\n\n| Metric                    | Value     |\n|---------------------------|-----------|\n| Total chains identified   | 2         |\n| Maximum severity          | **HIGH**  |\n| Medium se...
- `read_file` `call_03644a60e2924f9d846d5bb1` {"path": "docs/security/CHAINED_VULNERABILITIES_REVIEW.md"}
