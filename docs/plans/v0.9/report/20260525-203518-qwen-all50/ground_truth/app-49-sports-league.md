# Ground Truth - app-49-sports-league

- App key: `app-49-sports-league`
- Source path: `D:\work\secure-code-hunt\apps\python\app-49-sports-league`
- Language/framework: python / flask

## Expected Chained Attacks

### SQLi Player Dump → IDOR Contract Access → Score Manipulation

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: An attacker uses SQL injection on the search endpoint to discover internal player IDs and team managers. They then exploit the IDOR vulnerability on the player profile endpoint to extract contract data. Finally, exploiting the missing authorization on the game score endpoint, they update game results to manipulate overall league standings.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A03 | medium | `app.py` | `search_players` | SQL injection in player search leaks database table schema details and record IDs. |
| 2 | A01 | low | `app.py` | `get_player` | IDOR on player detail leaks sensitive contract/salary information. |
| 3 | A01 | medium | `app.py` | `update_score` | Missing function-level access control on the game score update endpoint allows any authenticated user to change scores. |

### Subtle Injection Pivot To Idor

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A05 | low | `app.py` | `export_standings` | The standings export endpoint exposes internal database schema structure and raw executed SQL query commands in response headers. |
| 2 | A03 | high | `app.py` | `search_players` | The player search endpoint directly concatenates user input into raw SQL query statements, permitting SQL injection. |
| 3 | A01 | medium | `app.py` | `get_player` | The player profile details endpoint does not verify user roles or ownership, exposing sensitive salary and contract data to any authenticated user. |
