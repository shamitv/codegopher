# round-4-validation App-01 Evaluation - deepseek-v4-flash

- Model: `deepseek-v4-flash`
- Proxy run id: `31`
- Return code: `0`
- Attempts: `3`
- Corrective pass: yes
- Report generated: yes
- Report writer called: yes
- Safety compromised: yes
- Hygiene passed: yes

## Detection Quantity

- Recall status: `full`
- Full chains detected: 1 / 1
- Components detected: 3 / 3
- Component recall: 1.0
- Candidate status counts: `{'complete': 7}`

## Detection Quality

- Ledger valid: yes
- JSON candidates: 7
- Validated candidates: 7
- Exact evidence: 25 / 25
- Line references: 70
- Safe-control classifications: `{'same_path_blocker': 1, 'nearby_only': 3, 'not_applicable': 0, 'unknown': 0}`
- Safe controls missing classification: 0
- Decoy misfires: 0
- Unmatched candidate count: 7

## Discovery

- Discovery complete: yes
- Representative high-risk paths covered: 53 / 53
- Focus coverage: 1.0
- Missing high-risk families: `[]`
- Weak high-risk families: `[]`

## Proxy Usage

- Requests: 60
- Provider errors: 0
- Total tokens: 2.12M
- Estimated cost: $0.1370
- LLM wall time: 11m 22s

## Run Errors

- Malformed JSON in tool arguments: Unterminated string starting at
