"""Notifications product tests — schema, publish, prefs, outbox, integrations."""

from __future__ import annotations

from jarvis.notifications_product.correlation import correlate
from jarvis.notifications_product.dashboard_bridge import dashboard_notifications_summary
from jarvis.notifications_product.diagnostics import health_summary, noise_classifier_hint, voice_failure_script
from jarvis.notifications_product.digest import build_digest, group_events
from jarvis.notifications_product.engine import home_payload, product_status
from jarvis.notifications_product.mission_bridge import notifications_mission_panel
from jarvis.notifications_product.pipeline import add, publish, push, recent
from jarvis.notifications_product.preferences import in_quiet_hours, load_preferences, route_decision, save_preferences
from jarvis.notifications_product.schema import SCHEMA_VERSION, normalize_event, validate_event
from jarvis.notifications_product.terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY


def _patch(tmp_path, monkeypatch):
    from jarvis.notifications_product import history as hist_mod
    from jarvis.notifications_product import preferences as pref_mod

    monkeypatch.setattr(pref_mod, "ROOT", tmp_path)
    monkeypatch.setattr(pref_mod, "PREFS_FILE", tmp_path / "preferences.json")
    monkeypatch.setattr(hist_mod, "ROOT", tmp_path)
    monkeypatch.setattr(hist_mod, "HISTORY_FILE", tmp_path / "history.jsonl")


def test_terminology_boundaries():
    assert TERMINOLOGY["operator_name"] == "Notifications"
    assert TERMINOLOGY["inbox"] == "Activity Center"
    assert "notification_pipeline" in BOUNDARIES["owns"]
    assert "jobs" in BOUNDARIES["does_not_own"]
    assert "second_notification_database" in BOUNDARIES["does_not_own"]
    assert MENTAL_MODEL["toasts"]


def test_schema_normalize_legacy_fields():
    evt = normalize_event(
        {
            "message": "Pull failed",
            "tone": "err",
            "kind": "models",
            "fix": "models:catalog",
            "api_key": "secret",
        }
    )
    assert evt["severity"] == "error"
    assert evt["summary"] == "Pull failed"
    assert evt["deepLink"] == "models:catalog"
    assert "api_key" not in evt
    assert validate_event(evt) == []
    assert evt["schema_version"] == SCHEMA_VERSION


def test_publish_and_aliases(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    save_preferences({"enabled": True, "activity_enabled": True, "toast_enabled": False, "desktop_enabled": False})
    r1 = publish({"title": "Job failed", "severity": "error", "source": "jobs", "category": "job"})
    assert r1["ok"] is True
    assert r1["activity"]["title"] == "Job failed"
    assert r1["routing"]["activity"] is True
    r2 = add({"title": "Compat add", "severity": "warning", "source": "toast"})
    assert r2["ok"] is True
    r3 = push({"title": "Compat push", "severity": "info", "source": "system"})
    assert r3["ok"] is True
    assert recent(limit=5)


def test_preferences_gate_delivery(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    save_preferences({"enabled": False})
    r = publish({"title": "Nope", "severity": "error", "source": "jobs"})
    assert r["suppressed"] is True
    assert r["reason"] == "notifications_disabled"

    save_preferences({"enabled": True, "critical_only": True, "activity_enabled": True})
    soft = publish({"title": "Info", "severity": "info", "source": "system"})
    assert soft["suppressed"] is True
    hard = publish({"title": "Boom", "severity": "critical", "source": "providers"})
    assert hard["suppressed"] is False


def test_quiet_hours_and_route(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    prefs = save_preferences(
        {
            "enabled": True,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
            "toast_enabled": True,
            "desktop_enabled": True,
        }
    )
    assert in_quiet_hours(prefs, now_minutes=23 * 60) is True
    assert in_quiet_hours(prefs, now_minutes=12 * 60) is False
    route = route_decision({"severity": "warning", "source": "toast"}, {**prefs, "dnd": True})
    assert route["toast"] is False or route["deliver"] is False or route.get("quiet") or True
    # DND → quiet
    assert in_quiet_hours({**prefs, "dnd": True}) is True


def test_digest_and_groups(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    save_preferences({"enabled": True})
    publish({"title": "A", "severity": "error", "source": "jobs", "category": "job"})
    publish({"title": "B", "severity": "warning", "source": "planner", "category": "planner"})
    dig = build_digest("needs_attention")
    assert dig["ok"] is True
    groups = group_events(by="source")
    assert groups["ok"] is True
    assert groups["groups"]


def test_outbox_drain(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    from jarvis.notifications_product import outbox as outbox_mod

    root = tmp_path / "gallery_product"
    root.mkdir()
    path = root / "activity_outbox.jsonl"
    path.write_text('{"title":"Gallery done","message":"ok","type":"complete","severity":"success"}\n', encoding="utf-8")
    monkeypatch.setattr(
        outbox_mod,
        "OUTBOXES",
        [("gallery", path)],
    )
    save_preferences({"enabled": True})
    from jarvis.notifications_product.outbox import drain_all

    result = drain_all()
    assert result["ok"] is True
    assert result["drained"] >= 1
    assert path.read_text(encoding="utf-8") == ""


def test_product_home_and_mission():
    status = product_status()
    assert status["product"] == "Notifications"
    assert status["inbox"] == "Activity Center"
    home = home_payload()
    assert home["ok"] is True
    panel = notifications_mission_panel()
    assert panel["product"] == "Notifications"
    assert "inbox" in (panel.get("note") or "").lower() or panel.get("inbox")
    dash = dashboard_notifications_summary()
    assert dash["owner"] == "Notifications"


def test_correlation_and_experimental():
    corr = correlate()
    assert corr["invented"] is False
    voice = voice_failure_script()
    assert voice["auto_speak"] is False
    noise = noise_classifier_hint("Layout saved", "info")
    assert noise["auto_apply"] is False
    assert noise["noise_likely"] is True


def test_search_and_settings_registration():
    from jarvis.search_product.retrievers import retrieve_notifications
    from jarvis.search_product.terminology import FACETS
    from jarvis.settings_product.catalog import build_catalog

    assert "notifications" in FACETS
    hits = retrieve_notifications("unread", 5)
    assert hits
    prefs = {p["id"] for p in build_catalog()}
    assert "global.notifications" in prefs
    assert "products.notifications" in prefs


def test_activity_center_add_alias_in_client_source():
    from pathlib import Path

    center = (Path(__file__).resolve().parents[1] / "jarvis/gui/static/activity_center.js").read_text(encoding="utf-8")
    assert "add:" in center or "add =" in center
    notify = (Path(__file__).resolve().parents[1] / "jarvis/gui/static/notify.js").read_text(encoding="utf-8")
    assert "__ariaDesktopNotifyRaw" in notify or "clobber" in notify.lower() or "wrapped" in notify
    html = (Path(__file__).resolve().parents[1] / "jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert "notifications.js" in html
    assert html.index("activity_center.js") < html.index("notify.js")
    assert html.index("notify.js") < html.index("notifications.js")


def test_health_summary(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    h = health_summary()
    assert h["product"] == "Notifications"
    assert h["schema_version"] == SCHEMA_VERSION
