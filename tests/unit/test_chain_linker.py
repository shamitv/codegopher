from __future__ import annotations

import json

from codegopher.security.linker import (
    ScannerOutput,
    chain_linker_prompt,
    link_findings,
    parse_scanner_output,
)


def test_parse_scanner_output_validates_structured_json() -> None:
    output = parse_scanner_output(
        json.dumps(
            {
                "target": "routing",
                "findings": [
                    {
                        "id": "source",
                        "kind": "source",
                        "label": "Webhook",
                        "category": "route",
                    }
                ],
            }
        )
    )

    assert output.target == "routing"
    assert output.findings[0].kind == "source"


def test_link_findings_builds_chain_from_source_hop_and_sink() -> None:
    outputs = [
        ScannerOutput.model_validate(
            {
                "target": "fixture",
                "findings": [
                    {"id": "source", "kind": "source", "label": "Upload URL", "category": "route"},
                    {"id": "hop", "kind": "hop", "label": "SSRF fetch", "category": "SSRF"},
                    {
                        "id": "sink",
                        "kind": "sink",
                        "label": "Metadata endpoint",
                        "category": "cloud metadata",
                        "description": "Credential exposure",
                    },
                ],
            }
        )
    ]

    chains = link_findings(outputs)

    assert len(chains) == 1
    assert chains[0].title == "Upload URL to Metadata endpoint via SSRF fetch"
    assert chains[0].edges[1].target_id == "sink"


def test_chain_linker_prompt_summarizes_scanner_outputs() -> None:
    prompt = chain_linker_prompt([ScannerOutput(target="routing")])

    assert "routing: 0 findings" in prompt
    assert "without exploit payloads" in prompt
