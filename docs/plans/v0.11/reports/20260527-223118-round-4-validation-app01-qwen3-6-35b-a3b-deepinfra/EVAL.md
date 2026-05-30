# round-4-validation App-01 Evaluation - Qwen/Qwen3.6-35B-A3B:deepinfra

- Model: `Qwen/Qwen3.6-35B-A3B:deepinfra`
- Proxy run id: `30`
- Return code: `0`
- Attempts: `3`
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
- Candidate status counts: `{}`

## Detection Quality

- Ledger valid: no
- JSON candidates: 0
- Validated candidates: 0
- Exact evidence: 0 / 0
- Line references: 51
- Safe-control classifications: `{'same_path_blocker': 0, 'nearby_only': 0, 'not_applicable': 0, 'unknown': 0}`
- Safe controls missing classification: 0
- Decoy misfires: 0
- Unmatched candidate count: 0

## Discovery

- Discovery complete: yes
- Representative high-risk paths covered: 53 / 53
- Focus coverage: 1.0
- Missing high-risk families: `[]`
- Weak high-risk families: `[]`

## Proxy Usage

- Requests: 61
- Provider errors: 0
- Total tokens: 2.16M
- Estimated cost: $0.4091
- LLM wall time: 13m 53s

## Run Errors

- Malformed JSON in tool arguments: Expecting property name enclosed in double quotes
