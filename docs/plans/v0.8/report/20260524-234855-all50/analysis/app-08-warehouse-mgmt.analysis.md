# Analysis - app-08-warehouse-mgmt

- App key: `app-08-warehouse-mgmt`
- Temp workspace: `C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260524-234855-all50\app-08-warehouse-mgmt\workspace`
- Return code: 0
- Attempts: 2
- Generated report: yes
- Report writer called: yes

## Event Counts

| Event | Count |
|---|---:|
| `reasoning_delta` | 1772 |
| `session_started` | 1 |
| `text_delta` | 803 |
| `tool_call` | 76 |
| `tool_result` | 76 |
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

### LDAP Injection → Directory Structure Disclosure → Inventory Tampering

- Status: full
- Components detected: 3 / 3

| Step | Method | Location | Detected | Evidence Terms |
|---|---|---|---|---|
| 1 | `searchEmployees` | `src/main/java/com/warehouse/service/EmployeeLdapService.java` | yes | arbitrary, concatenation, directory, enabling, entries, enumerate, injection |
| 2 | `search` | `src/main/java/com/warehouse/controller/EmployeeController.java` | yes | attacker, directory, including, internal, returned, structure, verbatim |
| 3 | `adjustQuantity` | `src/main/java/com/warehouse/controller/InventoryController.java` | yes | allowing, authentication, quantities |

## Report Quality

- Line reference count: 20
- Ground-truth components with location and method cited: 0 / 3
- Unmatched candidate chain titles: Chain 2: Exposed Actuator Endpoints → Sensitive Configuration Disclosure → Credential Exposure, Chain 3: Unvalidated Carrier URL → SSRF → Internal Network Access & Data Exfiltration, Chain 4: Inconsistent Authorization → Inventory Manipulation & Order Data Abuse

## Tool Calls

- `list_dir` `call_138723506fd94195bda3a2fb` {"path": "."}
- `glob_search` `call_efa187b7c81e42b4bff633e3` {"pattern": "**/*.{js,ts,jsx,tsx,py,java,go,rb,php,json,yaml,yml,xml,html,ejs,pug}"}
- `list_dir` `call_ed97623b7a6c456c8c7ede98` {"path": "src"}
- `read_file` `call_c1b22eddcb8e4bf08d6b30f9` {"path": "pom.xml"}
- `read_file` `call_cdfd85cc530c4074952c5e8b` {"path": "Dockerfile"}
- `list_dir` `call_b3523d588c7a43f5bba85348` {"path": "src/main"}
- `list_dir` `call_80a1a0f6d6714df6a4667bde` {"path": "src/test"}
- `glob_search` `call_11e7b21c3a084c6692b8b162` {"pattern": "src/**/*.java"}
- `glob_search` `call_45f74ee9947d4f29a3fc9558` {"pattern": "src/**/*.yml"}
- `glob_search` `call_6197e3e9f0b5478892f0e392` {"pattern": "src/**/*.yaml"}
- `glob_search` `call_977ff72db2914c9c91069dd0` {"pattern": "src/**/*.properties"}
- `read_file` `call_2e6c74111398464180de7ad0` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java"}
- `read_file` `call_a5b0917cc98047dd8d4ea7a5` {"path": "src/main/java/com/warehouse/config/LdapConfig.java"}
- `read_file` `call_4cbb1dc681154a2f995e1e95` {"path": "src/main/java/com/warehouse/config/DataInitializer.java"}
- `read_file` `call_6f83460207454d07b2c39c93` {"path": "src/main/resources/application.properties"}
- `read_file` `call_be02ba2821bb4ab98acf21d7` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "start_line": 1}
- `read_file` `call_856220eba7274e2eadd2927b` {"path": "src/main/java/com/warehouse/controller/UserController.java"}
- `read_file` `call_7cdcbdc171354be6a9cafde1` {"path": "src/main/java/com/warehouse/controller/EmployeeController.java"}
- `read_file` `call_507944f4112645b48164601f` {"path": "src/main/java/com/warehouse/controller/InventoryController.java"}
- `grep_search` `call_19ec3f6824274a55a7aa2424` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "package"}
- `read_file` `call_67a37bd40c224c2a9685f56c` {"end_line": 80, "path": "src/main/java/com/warehouse/config/SecurityConfig.java", "start_line": 1}
- `grep_search` `call_8eeac48e76554b21a3e6d5c3` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "permitAll"}
- `grep_search` `call_df84200f45614875b5e45d12` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "requestMatchers"}
- `grep_search` `call_97b0e6956e5e40e890f7b762` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "authorizeHttpRequests"}
- `grep_search` `call_454ea65298244fdfa8ad4324` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "http.security"}
- `grep_search` `call_38b59876dce44062946c65c5` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "public"}
- `grep_search` `call_03851ad699bd4b50aed3c705` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "import"}
- `grep_search` `call_4517ca53902848219236b4d7` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "@Configuration"}
- `grep_search` `call_a64eb9dac8d340ed8ac326e9` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "@EnableMethodSecurity"}
- `grep_search` `call_0065938155b6413780b10158` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "http"}
- `grep_search` `call_5ae6f320f4bf4cda8219ae57` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "let"}
- `grep_search` `call_328d3292e7094c0ea166c9e4` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "var"}
- `read_file` `call_652cf95f40d347f682c8120e` {"end_line": 5, "path": "src/main/java/com/warehouse/config/SecurityConfig.java", "start_line": 1}
- `read_file` `call_8e22a7e7025147898c545c9b` {"end_line": 33, "path": "src/main/java/com/warehouse/config/SecurityConfig.java", "start_line": 15}
- `grep_search` `call_6798eb183f044476ace6ce5a` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "security"}
- `grep_search` `call_125a118d952842a4bc388875` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "SecurityFilterChain"}
- `grep_search` `call_6e6153f77e0e40e8a59ca1ca` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "@Bean"}
- `read_file` `call_5c99d77930ac4e169d49055e` {"path": "src/main/java/com/warehouse/controller/DashboardController.java"}
- `read_file` `call_16812e4978f0499ba79dea9e` {"path": "src/main/java/com/warehouse/controller/OrderController.java"}
- `read_file` `call_d50e4c20a0b546818fe60934` {"path": "src/main/java/com/warehouse/controller/ShippingController.java"}
- `read_file` `call_310beba32eaf40cf8e38272d` {"path": "src/main/java/com/warehouse/service/InventoryService.java"}
- `read_file` `call_a1ac2b6aba124b6298141265` {"path": "src/main/java/com/warehouse/service/OrderService.java"}
- `read_file` `call_a7f242455705499da90adf0f` {"path": "src/main/java/com/warehouse/service/EmployeeLdapService.java"}
- `read_file` `call_d098a82b91634bafa8329e52` {"path": "src/main/java/com/warehouse/service/ShippingService.java"}
- `read_file` `call_647bcb95e6be43f6bdd003fe` {"path": "src/main/java/com/warehouse/model/User.java"}
- `read_file` `call_b8dac9f24e544dab90a730fd` {"path": "src/main/java/com/warehouse/model/Employee.java"}
- `read_file` `call_51cbd97fd1824d67b7348ba4` {"path": "src/main/java/com/warehouse/model/InventoryItem.java"}
- `read_file` `call_5338539e374a43b187b86554` {"path": "src/main/java/com/warehouse/model/WarehouseOrder.java"}
- `read_file` `call_8fdcae0026664ccba3ce26a2` {"path": "src/main/java/com/warehouse/model/OrderItem.java"}
- `read_file` `call_e270d75b484349e797c04fab` {"path": "src/main/java/com/warehouse/model/ShippingLabel.java"}
- `read_file` `call_a027cf4c925742fe9dc18d74` {"path": "src/main/java/com/warehouse/dto/InventoryDTO.java"}
- `read_file` `call_ca2ab8f325814b4189b16def` {"path": "src/main/java/com/warehouse/dto/PickListDTO.java"}
- `read_file` `call_e03e554f38bb4e97aec2a1a3` {"path": "src/main/java/com/warehouse/dto/ShippingLabelRequest.java"}
- `read_file` `call_b278315f4ae14584a803b7cc` {"path": "src/main/java/com/warehouse/repository/InventoryRepository.java"}
- `read_file` `call_b9c01f6fc99b4a61b85a5f99` {"path": "src/main/java/com/warehouse/repository/OrderRepository.java"}
- `read_file` `call_fb30199d4dc74c3687712ce7` {"path": "src/main/java/com/warehouse/repository/OrderItemRepository.java"}
- `read_file` `call_2d9f76be3d294cc18f50bff0` {"path": "src/main/java/com/warehouse/repository/ShippingLabelRepository.java"}
- `read_file` `call_b06c25b280824de5ba65b65c` {"path": "src/main/java/com/warehouse/repository/UserRepository.java"}
- `read_file` `call_5281115cf5d34aa6aed3d29b` {"path": "src/main/java/com/warehouse/service/PickListService.java"}
- `read_file` `call_a4dd2740e75240699612c5d9` {"path": "src/main/java/com/warehouse/App08Application.java"}
- `read_file` `call_748cf9bfc9d842148a33927b` {"path": "src/test/java/com/warehouse/App08ApplicationTests.java"}
- `grep_search` `call_9ddc7382edb84ce8859c0a40` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "@EnableWebSecurity"}
- `grep_search` `call_0a5287ab2a26401385c5e3f4` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "PasswordEncoder"}
- `grep_search` `call_0ba10f3511c340cc95cd80b9` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "UserDetails"}
- `grep_search` `call_f2c1a4a1b552413797f9bdbe` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "HttpServletRequest"}
- `grep_search` `call_2cbcfebd66cd40919ad69e43` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "HttpServletResponse"}
- `grep_search` `call_4ab519d429994fd898d5df2e` {"path": "src/main/java/com/warehouse/config/SecurityConfig.java", "query": "csrf"}
- `list_dir` `call_79553860c087439d910f7bcf` {"path": "src/main/resources"}
- `glob_search` `call_73935776753647e38a585d96` {"pattern": "src/main/resources/**/*"}
- `read_file` `call_ad849a1f52a24e44a916af6d` {"path": "src/main/resources/ldap/warehouse.ldif"}
- `read_file` `call_45a29f24c50d4965a6efbd67` {"path": "src/main/resources/static/index.html"}
- `read_file` `call_2f32d0e341754d879dd3f03c` {"path": "src/main/resources/static/js/app.js"}
- `read_file` `call_c35ee25f305b4b72ab7ba387` {"path": "src/main/resources/static/css/main.css"}
- `write_chained_vulnerability_report` `call_817aef8e82484056951ea16d` {"content": "# Chained Vulnerability Static Audit Report\n\n**Project:** app-08-warehouse-mgmt (Warehouse Management System)  \n**Date:** 2026-05-24  \n**Auditor:** CodeGopher — Static-Only Chained Vulnerability Audit  \n**Tech Stack:** Spring Boot 3.2.5, JPA/H2, Spring Security, Spring LDAP, UnboundID LDAP SDK  \n**Files Reviewed:** 32 source files across controllers, services, repositories, models, DTOs, config, resources, and tests  \n\n---\n\n## Summary Dashboard\n\n| Metric | Value |\n|-...
- `read_file` `call_c3b96fcb4e274a9db64c0700` {"end_line": 50, "path": "docs/security/CHAINED_VULNERABILITIES_REVIEW.md", "start_line": 1}
- `read_file` `call_ae7f6da30d0a41d499f46562` {"path": "docs/security/CHAINED_VULNERABILITIES_REVIEW.md", "start_line": 310}
