from __future__ import annotations

import pytest


def test_required_product_failure_raises_and_marks_health() -> None:
    from jarvis.product_registration import register, registration_status, reset_for_tests

    reset_for_tests()

    with pytest.raises(RuntimeError):
        register("search_product", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    status = registration_status()
    assert status["ok"] is False
    assert status["failed"][0]["name"] == "search_product"
    assert "settings_product" in status["missing_required"]

    reset_for_tests()


def test_extension_api_failures_enter_registration_ledger(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.extensibility import loader
    from jarvis.product_registration import registration_status, reset_for_tests

    class BrokenExtension:
        class Meta:
            name = "broken"

        meta = Meta()

        def register_api(self, app, assistant) -> None:  # noqa: ANN001
            raise RuntimeError("extension api broken")

    reset_for_tests()
    monkeypatch.setattr(loader, "_LOADED", True)
    monkeypatch.setattr(loader, "_EXTENSIONS", [BrokenExtension()])

    loader.register_extension_api(object(), object())
    status = registration_status()

    assert status["ok"] is False
    assert any(f["name"] == "extension:broken:api" for f in status["failed"])

    reset_for_tests()
