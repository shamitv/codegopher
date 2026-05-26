from __future__ import annotations

import pytest

from codegopher.devtools.benchmark.proxy import ProxyRunClient, ProxyRunError


def test_proxy_run_client_starts_and_ends_owned_run() -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def transport(
        method: str,
        path: str,
        payload: dict[str, object] | None,
    ) -> dict[str, object]:
        calls.append((method, path, payload))
        if path == "/admin/api/runs":
            return {"active_run": {"id": 7, "name": "CodeGopher stale", "status": "active"}}
        if path == "/admin/api/runs/start":
            return {"run": {"id": 8, "name": payload["name"], "status": "active"}}
        if path == "/admin/api/runs/8":
            return {"run": {"id": 8, "request_count": 3}}
        if path == "/admin/api/runs/end":
            return {"run": {"id": 8, "status": "complete"}}
        raise AssertionError(path)

    client = ProxyRunClient("http://proxy.example/admin", transport=transport)

    handle = client.start_run(name="CodeGopher test", notes="notes")
    snapshot = client.get_run(handle.run_id)
    ended = client.end_run()

    assert handle.run_id == 8
    assert handle.run_url == "http://proxy.example/admin/runs/8"
    assert snapshot["run"] == {"id": 8, "request_count": 3}
    assert ended["run"] == {"id": 8, "status": "complete"}
    assert calls[1] == (
        "POST",
        "/admin/api/runs/start",
        {"name": "CodeGopher test", "notes": "notes"},
    )


def test_proxy_run_client_aborts_for_foreign_active_run() -> None:
    def transport(
        method: str,
        path: str,
        payload: dict[str, object] | None,
    ) -> dict[str, object]:
        assert method == "GET"
        assert path == "/admin/api/runs"
        assert payload is None
        return {"active_run": {"id": 7, "name": "Other benchmark", "status": "active"}}

    client = ProxyRunClient("http://proxy.example/admin", transport=transport)

    with pytest.raises(ProxyRunError, match="not owned"):
        client.start_run(name="CodeGopher test", notes="")
