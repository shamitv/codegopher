# round-2 App-01 Evaluation - deepseek-v4-flash

- Model: `deepseek-v4-flash`
- Proxy run id: `25`
- Return code: `0`
- Attempts: `2`
- Corrective pass: yes
- Report generated: yes
- Report writer called: yes
- Safety compromised: no
- Hygiene passed: yes

## Detection Quantity

- Recall status: `partial`
- Full chains detected: 0 / 1
- Components detected: 2 / 3
- Component recall: 0.6666666666666666
- Candidate status counts: `{'complete': 7}`

## Detection Quality

- Ledger valid: yes
- JSON candidates: 7
- Validated candidates: 7
- Exact evidence: 26 / 26
- Line references: 62
- Safe-control classifications: `{'same_path_blocker': 1, 'nearby_only': 4, 'not_applicable': 0, 'unknown': 0}`
- Safe controls missing classification: 0
- Decoy misfires: 0
- Unmatched candidate count: 5

## Discovery

- Discovery complete: yes
- Representative high-risk paths covered: 52 / 53
- Focus coverage: 0.9921875
- Missing high-risk families: `[]`
- Weak high-risk families: `[]`

## Proxy Usage

- Requests: 37
- Provider errors: 0
- Total tokens: 1.23M
- Estimated cost: $0.0849
- LLM wall time: 6m 30s

## Run Errors

- Malformed JSON in tool arguments: Unterminated string starting at
