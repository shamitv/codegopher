"""Proxy run helpers for development benchmark stats capture."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

JsonObject = dict[str, Any]
Transport = Callable[[str, str, JsonObject | None], JsonObject]


@dataclass(frozen=True)
class ProxyRunHandle:
    run_id: int
    admin_url: str
    run_url: str
    start_snapshot: JsonObject


class ProxyRunError(RuntimeError):
    """Raised when proxy run setup or teardown cannot be completed safely."""


class ProxyRunClient:
    def __init__(self, admin_url: str, *, transport: Transport | None = None) -> None:
        self.admin_url = admin_url.rstrip("/")
        self._transport = transport or self._default_transport

    def active_run(self) -> JsonObject | None:
        payload = self._request("GET", "/admin/api/runs")
        active = payload.get("active_run") or payload.get("active")
        if isinstance(active, dict):
            return active
        runs = payload.get("runs")
        if isinstance(runs, list):
            for run in runs:
                if not isinstance(run, dict):
                    continue
                status = str(run.get("status", "")).lower()
                if run.get("active") or status == "active":
                    return run
        return None

    def ensure_no_active_run(self) -> None:
        active = self.active_run()
        if active is None:
            return
        name = str(active.get("name", ""))
        raise ProxyRunError(
            "active proxy run would contaminate benchmark stats: "
            f"{name or '<unnamed>'}"
        )

    def start_run(self, *, name: str, notes: str) -> ProxyRunHandle:
        self.ensure_no_active_run()
        payload = self._request(
            "POST",
            "/admin/api/runs/start",
            {"name": name, "notes": notes},
        )
        run = _extract_run(payload)
        run_id = _run_id(run)
        if run_id is None:
            raise ProxyRunError("proxy start response did not include a run id")
        snapshot = self.get_run(run_id)
        return ProxyRunHandle(
            run_id=run_id,
            admin_url=self.admin_url,
            run_url=f"{self.admin_url}/runs/{run_id}",
            start_snapshot=snapshot,
        )

    def get_run(self, run_id: int) -> JsonObject:
        return self._request("GET", f"/admin/api/runs/{run_id}")

    def end_run(self) -> JsonObject:
        return self._request("POST", "/admin/api/runs/end", {})

    def _request(self, method: str, path: str, payload: JsonObject | None = None) -> JsonObject:
        return self._transport(method, path, payload)

    def _default_transport(
        self,
        method: str,
        path: str,
        payload: JsonObject | None,
    ) -> JsonObject:
        request_path = path
        if self.admin_url.endswith("/admin") and request_path.startswith("/admin/"):
            request_path = request_path[len("/admin") :]
        url = urljoin(f"{self.admin_url}/", request_path.lstrip("/"))
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ProxyRunError(f"proxy request failed: HTTP {exc.code} {body}") from exc
        if not body.strip():
            return {}
        value = json.loads(body)
        if not isinstance(value, dict):
            raise ProxyRunError("proxy response was not a JSON object")
        return value


def _extract_run(payload: JsonObject) -> JsonObject:
    for key in ("run", "active_run", "data"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return payload


def _run_id(run: JsonObject) -> int | None:
    for key in ("id", "run_id"):
        value = run.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None
