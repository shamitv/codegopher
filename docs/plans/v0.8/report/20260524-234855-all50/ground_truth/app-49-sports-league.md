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
