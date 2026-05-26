from __future__ import annotations

from pathlib import Path

from codegopher.devtools.benchmark.prepass import build_static_prepass


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

    assert "Source-Derived Static Inventory" in inventory
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
