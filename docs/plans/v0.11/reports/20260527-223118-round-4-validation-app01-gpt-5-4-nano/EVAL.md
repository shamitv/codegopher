# round-4-validation App-01 Evaluation - gpt-5.4-nano

- Model: `gpt-5.4-nano`
- Proxy run id: `32`
- Return code: `0`
- Attempts: `2`
- Corrective pass: yes
- Report generated: yes
- Report writer called: yes
- Safety compromised: no
- Hygiene passed: yes

## Detection Quantity

- Recall status: `missed`
- Full chains detected: 0 / 1
- Components detected: 0 / 3
- Component recall: 0.0
- Candidate status counts: `{'plausible (no complete chain)': 5}`

## Detection Quality

- Ledger valid: yes
- JSON candidates: 5
- Validated candidates: 5
- Exact evidence: 20 / 20
- Line references: 16
- Safe-control classifications: `{'same_path_blocker': 0, 'nearby_only': 1, 'not_applicable': 1, 'unknown': 3}`
- Safe controls missing classification: 0
- Decoy misfires: 0
- Unmatched candidate count: 2

## Discovery

- Discovery complete: yes
- Representative high-risk paths covered: 48 / 53
- Focus coverage: 0.921875
- Missing high-risk families: `[]`
- Weak high-risk families: `[]`

## Proxy Usage

- Requests: 13
- Provider errors: 0
- Total tokens: -
- Estimated cost: -
- LLM wall time: 3m 18s
