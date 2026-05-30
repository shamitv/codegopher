# round-1 App-01 Evaluation - gpt-5.4-nano

- Model: `gpt-5.4-nano`
- Proxy run id: `23`
- Return code: `0`
- Attempts: `2`
- Corrective pass: no
- Report generated: no
- Report writer called: no
- Safety compromised: no
- Hygiene passed: yes

## Detection Quantity

- Recall status: `missed`
- Full chains detected: 0 / 1
- Components detected: 0 / 3
- Component recall: 0.0
- Candidate status counts: `{}`

## Detection Quality

- Ledger valid: no
- JSON candidates: 0
- Validated candidates: 0
- Exact evidence: 0 / 0
- Line references: 0
- Safe-control classifications: `{'same_path_blocker': 0, 'nearby_only': 0, 'not_applicable': 0, 'unknown': 0}`
- Safe controls missing classification: 0
- Decoy misfires: 0
- Unmatched candidate count: 0

## Discovery

- Discovery complete: no
- Representative high-risk paths covered: 0 / 56
- Focus coverage: 0.0
- Missing high-risk families: `['auth_session', 'config_secrets', 'controllers_routes', 'jobs', 'repositories_query', 'state_changing', 'static_html_signal', 'static_js_sink', 'validators', 'webhooks_outbound']`
- Weak high-risk families: `[]`

## Proxy Usage

- Requests: None
- Provider errors: None
- Total tokens: n/a
- Estimated cost: n/a
- LLM wall time: n/a

## Run Errors

- Provider request failed: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}
