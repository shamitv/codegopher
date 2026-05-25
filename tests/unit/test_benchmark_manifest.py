from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegopher.devtools.benchmark.manifest import (
    load_benchmark_suite,
    load_vulnerability_manifest,
    parse_app_spec,
)


def write_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "app_id": "app-test",
                "app_name": "Test App",
                "language": "python",
                "framework": "flask",
                "chained_attacks": [
                    {
                        "chain_id": "chain-01",
                        "chain_name": "Open Redirect To Admin",
                        "attack_scenario": "redirect then access admin",
                        "impact": "account_takeover",
                        "difficulty": "hard",
                        "subtlety_tags": ["cross_file", "implicit_trust"],
                        "required_evidence": ["redirect allowlist fallback"],
                        "chain_prerequisites": ["attacker controls redirect target"],
                        "negative_evidence": ["safe_redirect"],
                        "vulnerability_family": "idor",
                        "components": [
                            {
                                "step": 1,
                                "owasp_id": "A01",
                                "description": "open redirect source",
                                "location": "app.py",
                                "method": "redirect",
                                "severity": "medium",
                                "cwe": "CWE-601",
                                "required_evidence": ["return redirect(target)"],
                                "negative_evidence": ["url_has_allowed_host_and_scheme"],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_load_vulnerability_manifest_parses_chained_attack(tmp_path: Path) -> None:
    manifest_path = tmp_path / ".vulns"
    write_manifest(manifest_path)

    manifest = load_vulnerability_manifest(manifest_path)

    assert manifest.app_id == "app-test"
    assert manifest.chained_attacks[0].chain_id == "chain-01"
    assert manifest.chained_attacks[0].difficulty == "hard"
    assert manifest.chained_attacks[0].subtlety_tags == ("cross_file", "implicit_trust")
    assert manifest.chained_attacks[0].required_evidence == ("redirect allowlist fallback",)
    assert manifest.chained_attacks[0].chain_prerequisites == (
        "attacker controls redirect target",
    )
    assert manifest.chained_attacks[0].negative_evidence == ("safe_redirect",)
    assert manifest.chained_attacks[0].vulnerability_family == "idor"
    assert manifest.chained_attacks[0].components[0].method == "redirect"
    assert manifest.chained_attacks[0].components[0].required_evidence == (
        "return redirect(target)",
    )
    assert manifest.chained_attacks[0].components[0].negative_evidence == (
        "url_has_allowed_host_and_scheme",
    )


def test_load_benchmark_suite_resolves_relative_paths(tmp_path: Path) -> None:
    suite = tmp_path / "suite.toml"
    suite.write_text(
        """
[[apps]]
key = "test-app"
display_name = "Test App"
source = "apps/test"
manifest = "apps/test/.vulns"
""".strip(),
        encoding="utf-8",
    )

    cases = load_benchmark_suite(suite)

    assert len(cases) == 1
    assert cases[0].source == tmp_path / "apps/test"
    assert cases[0].manifest == tmp_path / "apps/test/.vulns"


def test_load_benchmark_suite_accepts_utf8_bom(tmp_path: Path) -> None:
    suite = tmp_path / "suite.toml"
    suite.write_text(
        '\ufeff[[apps]]\nkey = "test-app"\nsource = "apps/test"\nmanifest = "apps/test/.vulns"\n',
        encoding="utf-8",
    )

    cases = load_benchmark_suite(suite)

    assert cases[0].key == "test-app"


def test_parse_app_spec_requires_four_parts() -> None:
    with pytest.raises(ValueError, match="KEY"):
        parse_app_spec("too|short")


def test_parse_app_spec_accepts_explicit_paths() -> None:
    case = parse_app_spec("key|Display|D:/src|D:/src/.vulns")

    assert case.key == "key"
    assert case.display_name == "Display"
    assert case.source == Path("D:/src")
    assert case.manifest == Path("D:/src/.vulns")
