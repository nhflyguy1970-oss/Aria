"""Data module and routing tests."""

import csv
from pathlib import Path

import pytest
from jarvis.modules.data import DataEngine, parse_chart_request
from jarvis.router import route
from jarvis.session import SessionContext


@pytest.fixture
def session():
    return SessionContext()


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def test_data_load_route(session):
    att = {"path": "/tmp/sales.csv", "kind": "data"}
    intent = route("", session, att)
    assert intent["action"] == "data_load"


def test_data_query_follow_up(session):
    session.last_data_path = "/tmp/sales.csv"
    intent = route("How many rows are there?", session)
    assert intent["action"] == "data_query"


def test_data_export_route(session):
    session.last_data_path = "data/sales.csv"
    intent = route("export results to csv", session)
    assert intent["action"] == "data_export"


def test_data_export_pdf_route(session):
    session.last_data_path = "data/sales.csv"
    intent = route("export report to pdf", session)
    assert intent["action"] == "data_export"


def test_data_clean_route(session):
    session.last_data_path = "data/sales.csv"
    intent = route("clean drop duplicates", session)
    assert intent["action"] == "data_clean"


def test_data_chart_route(session):
    session.last_data_path = "data/sales.csv"
    intent = route("plot revenue pie chart", session)
    assert intent["action"] == "data_chart"


def test_parse_chart_request():
    spec = parse_chart_request("plot revenue as pie chart")
    assert spec["chart_type"] == "pie"


def test_compute_row_count(assistant, data_dir):
    csv_path = data_dir / "uploads" / "nums.csv"
    _write_csv(csv_path, [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}, {"a": "5", "b": "6"}])
    assistant.data.load_dataset(str(csv_path))
    answer = assistant.data.compute_answer("How many rows are there?")
    assert answer and "3" in answer


def test_data_load_handler(assistant, data_dir):
    csv_path = data_dir / "uploads" / "sales.csv"
    _write_csv(csv_path, [{"item": "apple", "qty": "10"}, {"item": "pear", "qty": "5"}])
    result = assistant.process(
        "",
        attachment={"path": str(csv_path), "kind": "data", "name": "sales.csv"},
    )
    assert result["ok"] is True
    assert result["module"] == "data"
    assert result.get("data_preview", {}).get("row_count") == 2


def test_data_query_average(assistant, data_dir):
    csv_path = data_dir / "uploads" / "prices.csv"
    _write_csv(csv_path, [{"price": "10"}, {"price": "20"}, {"price": "30"}])
    assistant.data.load_dataset(str(csv_path))
    assistant.session.last_data_path = str(csv_path)
    result = assistant.process("What is the average price?")
    assert result["ok"] is True
    assert "20" in result["message"]


def test_data_export(assistant, data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.modules.data.EXPORT_DIR", data_dir / "exports")
    csv_path = data_dir / "uploads" / "out.csv"
    _write_csv(csv_path, [{"x": "1"}])
    assistant.data.load_dataset(str(csv_path))
    session = assistant.session
    session.last_data_path = str(csv_path)
    result = assistant.process("export to json")
    assert result["ok"] is True
    assert result.get("export_path")


def test_streaming_csv_load(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.modules.data.STREAM_THRESHOLD_BYTES", 1)
    engine = DataEngine()
    csv_path = data_dir / "uploads" / "big.csv"
    rows = [{"id": str(i), "value": str(i * 10)} for i in range(100)]
    _write_csv(csv_path, rows)
    assert engine.load_dataset(str(csv_path)) == "OK"
    assert engine.dataset["streaming"] is True
    assert engine.dataset["row_count"] == 100
    assert len(engine.dataset["rows"]) <= 20


def test_streaming_average(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.modules.data.STREAM_THRESHOLD_BYTES", 1)
    engine = DataEngine()
    csv_path = data_dir / "uploads" / "avg.csv"
    rows = [{"price": str(i)} for i in range(1, 101)]
    _write_csv(csv_path, rows)
    engine.load_dataset(str(csv_path))
    answer = engine.compute_answer("What is the average price?")
    assert answer and "50.5" in answer
    assert "full file" in answer


def test_streaming_export_copy(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.modules.data.STREAM_THRESHOLD_BYTES", 1)
    monkeypatch.setattr("jarvis.modules.data.EXPORT_DIR", data_dir / "exports")
    engine = DataEngine()
    csv_path = data_dir / "uploads" / "copy.csv"
    _write_csv(csv_path, [{"x": "1"}, {"x": "2"}, {"x": "3"}])
    engine.load_dataset(str(csv_path))
    out = engine.export(fmt="csv")
    assert not out.startswith("ERROR")
    assert Path(out).read_text(encoding="utf-8").count("\n") >= 3


def test_export_pdf(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.modules.data.EXPORT_DIR", data_dir / "exports")
    engine = DataEngine()
    csv_path = data_dir / "uploads" / "report.csv"
    _write_csv(
        csv_path,
        [
            {"item": "apple", "qty": "10", "price": "1.5"},
            {"item": "pear", "qty": "5", "price": "2.0"},
            {"item": "banana", "qty": "3", "price": "0.9"},
        ],
    )
    engine.load_dataset(str(csv_path))
    out = engine.export(fmt="pdf")
    assert not out.startswith("ERROR"), out
    pdf = Path(out)
    assert pdf.exists()
    assert pdf.read_bytes()[:4] == b"%PDF"


def test_data_clean_duplicates(assistant, data_dir):
    csv_path = data_dir / "uploads" / "dup.csv"
    _write_csv(csv_path, [{"id": "1"}, {"id": "1"}, {"id": "2"}])
    assistant.data.load_dataset(str(csv_path))
    assistant.session.last_data_path = str(csv_path)
    result = assistant.process("clean drop duplicates")
    assert result["ok"] is True
    assert assistant.data.dataset["row_count"] == 2
