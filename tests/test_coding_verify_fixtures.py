from jarvis.coding_verify import _scaffold_pytest_fixtures
from jarvis.syntax_check import check_file, has_errors


def test_scaffold_test_data_for_generated_tests(tmp_path):
    items = [
        {
            "path": "data/scripts/script.py",
            "code": "def run(d):\n    pass\n",
        },
        {
            "path": "data/scripts/test_script.py",
            "code": "from script import run\n\ndef test_run():\n    run('./test_data')\n",
        },
    ]
    _scaffold_pytest_fixtures(items, tmp_path)
    assert (tmp_path / "test_data" / "sample1.txt").is_file()


def test_ruff_undefined_name_is_blocking(tmp_path):
    code = "def test_x():\n    csv.reader([])\n"
    diags = check_file(tmp_path / "test_script.py", content=code, deep=True, skip_typecheck=True)
    if not any(d.source == "ruff" for d in diags):
        return
    assert has_errors(diags)
    assert any("F821" in d.message for d in diags)
