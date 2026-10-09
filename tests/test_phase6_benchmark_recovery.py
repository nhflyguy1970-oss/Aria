"""Scoring regressions from preserved result evidence, without live agent calls."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_correct_diagnosis_without_exact_function_name():
    m = _load('coding_agent_benchmark')
    run = {'result': {'agent_report': 'Root cause: dates.py wraps December to January without incrementing the year.'}}
    assert m.check_hard('hard_diagnosis', run, Path('/unused'))[0]
    run['result']['agent_report'] = 'There is a dates.py issue.'
    assert not m.check_hard('hard_diagnosis', run, Path('/unused'))[0]


def test_shared_default_tags_wording_is_scored():
    m = _load('coding_agent_benchmark')
    run = {'result': {'agent_report': 'Default tags are shared across calls. Comparing a number to "100" raises TypeError.'}}
    assert m.check_hard('hard_code_review', run, Path('/unused'))[0]


def test_documentation_currency_example_does_not_override_default(tmp_path):
    m = _load('coding_agent_benchmark')
    readme = 'ledger --input data.csv --currency EUR\n--input CSV\n--currency (default USD)\n--round (default 2)\n--dry-run parse only\n'
    path = tmp_path / 'README.md'
    path.write_text(readme)
    assert m.check_hard('hard_documentation', {'workspace': str(tmp_path)}, Path('/unused'))[0]
    path.write_text(readme.replace('default USD', 'default EUR'))
    assert not m.check_hard('hard_documentation', {'workspace': str(tmp_path)}, Path('/unused'))[0]


def test_content_pass_cannot_mask_boundary_failure():
    m = _load('coding_agent_benchmark')
    assert not m.qualifies({'check_ok': True, 'status': 'boundary_violation'})
    assert not m.qualifies({'check_ok': True, 'status': 'verified', 'canary_intact': False})


def test_hard_scores_contribute_to_the_correct_base_kind():
    m = _load('render_agent_benchmark')
    assert m.base_kind('hard_diagnosis') == 'bug_diagnosis'
    assert m.base_kind('hard_repair') == 'small_repair'


def test_duplicate_result_rows_do_not_fake_completeness():
    m = _load('coding_agent_benchmark')
    row = {'agent': 'codex', 'kind': 'comprehension', 'rep': 0, 'status': 'completed',
           'check_ok': True, 'resources': {}, 'structured_ok': True}
    data = {'fixture_sha256': m._fixture_hash(), 'versions': {'codex': 'fake'},
            'agents': ['codex'], 'tasks': ['comprehension'], 'repeat': 2, 'rows': [row, dict(row)]}
    assert any('duplicate' in s for s in m.validate(data))
    assert any('coverage' in s for s in m.validate(data))


def test_selection_refresh_keeps_boundary_history_and_correctness_separate():
    m = _load('render_agent_benchmark')
    row = {'agent': 'codex', 'kind': 'comprehension', 'rep': 0, 'status': 'completed',
           'check_ok': True, 'seconds': 1, 'resources': {}, 'structured_ok': True}
    previous = {'associated_boundary_history': [{'agent': 'codex', 'run_id': 'smoke'}],
                'summary': {'codex': {'violations': 1}}}
    first = m.selection([row], [], [], previous)
    refreshed = m.selection([row], [], [], first)
    assert refreshed['summary']['codex']['passed'] == 1
    assert refreshed['summary']['codex']['scored_violations'] == 0
    assert refreshed['summary']['codex']['historical_violations'] == 1
    assert refreshed['summary']['codex']['violations'] == 1
    assert refreshed['by_category']['comprehension']['codex']['verified_pct'] == 100


def test_selection_refresh_preserves_summary_only_boundaries_and_absent_agents():
    m = _load('render_agent_benchmark')
    previous = {'summary': {'antigravity': {'violations': 1, 'outside_attempts': 2}}}
    result = m.selection([], [], [], previous)
    assert result['summary']['antigravity']['violations'] == 1
    assert result['summary']['antigravity']['retained_summary_violations'] == 1
    assert result['summary']['antigravity']['outside_attempts'] == 2
