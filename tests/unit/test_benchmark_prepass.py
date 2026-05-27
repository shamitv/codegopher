from __future__ import annotations

from pathlib import Path

from codegopher.devtools.benchmark.prepass import (
    MAX_MATCHES_PER_CATEGORY,
    MAX_SOURCE_GRAPH_EDGES,
    build_source_graph,
    build_static_focus_queue,
    build_static_prepass,
)


def test_static_prepass_finds_generic_security_inventory(tmp_path: Path) -> None:
    app = tmp_path / "app"
    app.mkdir()
    (app / "BookingController.java").write_text(
        "\n".join(
            [
                "@RestController",
                "class BookingController {",
                "  @GetMapping(\"/bookings/{id}\")",
                "  String get(String tenantId, String id) {",
                "    return service.findBooking(tenantId, id);",
                "  }",
                "  @PostMapping(\"/admin/refund\")",
                "  String refund(String bookingId) { return service.refund(bookingId); }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (app / "BookingService.java").write_text(
        "\n".join(
            [
                "class BookingService {",
                "  String findBooking(String tenantId, String id) {",
                "    return jdbcTemplate.queryForObject(\"SELECT * FROM bookings WHERE id = \" + id);",
                "  }",
                "  void callback(String url) { restTemplate.getForObject(url, String.class); }",
                "  boolean safeGuard(String url) { return allowedCallback(url); }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (app / "PnrGenerator.java").write_text(
        "class PnrGenerator { String generate() { return \"BK\" + sequence++; } }\n",
        encoding="utf-8",
    )

    inventory = build_static_prepass(app)

    assert "Source-Derived Static Focus Queue" in inventory
    assert "Focus Queue Summary" in inventory
    assert "Lightweight Source Graph" in inventory
    assert "SG001" in inventory
    assert "FQ001" in inventory
    assert "`BookingController.java:1`" in inventory
    assert "`BookingController.java:3`" in inventory
    assert "`BookingService.java:3`" in inventory
    assert "`BookingService.java:5`" in inventory
    assert "`PnrGenerator.java:1`" in inventory
    assert "Identifier, token, reference, and display helpers" in inventory
    assert "Safe controls and possible decoys" in inventory


def test_static_prepass_skips_evaluator_and_vendor_noise(tmp_path: Path) -> None:
    app = tmp_path / "app"
    vendor = app / "node_modules" / "pkg"
    vendor.mkdir(parents=True)
    (vendor / "index.js").write_text("router.get('/vendor', handler)\n", encoding="utf-8")
    (app / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (app / "README.md").write_text("@GetMapping('/hint')\n", encoding="utf-8")
    (app / "server.ts").write_text("router.post('/orders', createOrder)\n", encoding="utf-8")

    inventory = build_static_prepass(app)

    assert "server.ts:1" in inventory
    assert "node_modules" not in inventory
    assert "README.md" not in inventory


def test_static_focus_queue_caps_matches_deterministically(tmp_path: Path) -> None:
    app = tmp_path / "app"
    app.mkdir()
    (app / "routes.py").write_text(
        "\n".join(f"@app.route('/item/{index}')" for index in range(40)),
        encoding="utf-8",
    )

    queue = build_static_focus_queue(app)
    routes = next(
        category
        for category in queue.categories
        if category.name == "Routes and entry points"
    )

    assert len(routes.items) == MAX_MATCHES_PER_CATEGORY
    assert routes.items[0].item_id == "FQ001"
    assert routes.items[0].path == "routes.py"
    assert routes.items[-1].line == MAX_MATCHES_PER_CATEGORY


def test_source_graph_links_related_source_items_without_manifest_hints(
    tmp_path: Path,
) -> None:
    app = tmp_path / "app"
    app.mkdir()
    (app / "FlightController.java").write_text(
        "\n".join(
            [
                "@RestController",
                "class FlightController {",
                "  @GetMapping(\"/flights/{flightId}\")",
                "  String showFlight(String flightId) { return flightService.showFlight(flightId); }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (app / "FlightRepository.java").write_text(
        "\n".join(
            [
                "class FlightRepository {",
                "  String loadFlight(String flightId) {",
                "    return jdbcTemplate.queryForObject(\"SELECT * FROM flights WHERE id=\" + flightId);",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (app / ".vulns").write_text(
        '{"chains":[{"title":"do not leak me"}]}',
        encoding="utf-8",
    )

    queue = build_static_focus_queue(app)
    graph = build_source_graph(queue)
    inventory = build_static_prepass(app)

    assert graph.edges
    assert len(graph.edges) <= MAX_SOURCE_GRAPH_EDGES
    assert any(
        edge.source_path == "FlightController.java"
        and edge.target_path == "FlightRepository.java"
        for edge in graph.edges
    )
    assert "do not leak me" not in inventory
    assert ".vulns" not in inventory
