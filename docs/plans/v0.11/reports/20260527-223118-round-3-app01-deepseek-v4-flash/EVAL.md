# round-3 App-01 Evaluation - deepseek-v4-flash

- Model: `deepseek-v4-flash`
- Proxy run id: `28`
- Return code: `0`
- Attempts: `2`
- Corrective pass: yes
- Report generated: yes
- Report writer called: yes
- Safety compromised: no
- Hygiene passed: yes

## Detection Quantity

- Recall status: `full`
- Full chains detected: 1 / 1
- Components detected: 3 / 3
- Component recall: 1.0
- Candidate status counts: `{'complete': 5, 'rejected': 3}`

## Detection Quality

- Ledger valid: no
- JSON candidates: 8
- Validated candidates: 5
- Exact evidence: 18 / 18
- Line references: 58
- Safe-control classifications: `{'same_path_blocker': 0, 'nearby_only': 3, 'not_applicable': 0, 'unknown': 0}`
- Safe controls missing classification: 0
- Decoy misfires: 0
- Unmatched candidate count: 4

## Discovery

- Discovery complete: yes
- Representative high-risk paths covered: 52 / 53
- Focus coverage: 0.984375
- Missing high-risk families: `[]`
- Weak high-risk families: `[]`

## Proxy Usage

- Requests: 35
- Provider errors: 0
- Total tokens: 1.38M
- Estimated cost: $0.1023
- LLM wall time: 7m 42s

## Run Errors

- Malformed JSON in tool arguments: Unterminated string starting at
