# Source Generated with Decompyle++
# File: test_service_policy.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Lazy startup policy defaults.'''
import builtins as @py_builtins

rewrite
from jarvis.service_policy import autostart_comfyui, autostart_ha, autostart_memgraph, auto_pull_models_enabled, lazy_startup_enabled, model_warmup_enabled, router_warmup_enabled
autostart_ha = autostart_ha
autostart_memgraph = autostart_memgraph
auto_pull_models_enabled = auto_pull_models_enabled
lazy_startup_enabled = lazy_startup_enabled
model_warmup_enabled = model_warmup_enabled
router_warmup_enabled = router_warmup_enabled
import _pytest.assertion.rewrite, assertion

def test_lazy_defaults_on(monkeypatch):
    monkeypatch.delenv('JARVIS_LAZY_STARTUP', raising = False)
    @py_assert1 = lazy_startup_enabled()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(lazy_startup_enabled) if 'lazy_startup_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(lazy_startup_enabled) else 'lazy_startup_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_heavy_autostart_defaults_off(monkeypatch):
    for name in ('JARVIS_AUTOSTART_COMFYUI', 'JARVIS_HA_AUTOSTART', 'JARVIS_MODEL_WARMUP', 'JARVIS_WARM_ROUTER', 'JARVIS_AUTO_PULL_MODELS'):
        monkeypatch.delenv(name, raising = False)
    @py_assert1 = autostart_comfyui()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(autostart_comfyui) if 'autostart_comfyui' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(autostart_comfyui) else 'autostart_comfyui',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = autostart_ha()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(autostart_ha) if 'autostart_ha' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(autostart_ha) else 'autostart_ha',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = model_warmup_enabled()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(model_warmup_enabled) if 'model_warmup_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(model_warmup_enabled) else 'model_warmup_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = router_warmup_enabled()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(router_warmup_enabled) if 'router_warmup_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(router_warmup_enabled) else 'router_warmup_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = auto_pull_models_enabled()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(auto_pull_models_enabled) if 'auto_pull_models_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auto_pull_models_enabled) else 'auto_pull_models_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_memgraph_autostart_default_off_without_backend(monkeypatch):
    monkeypatch.delenv('JARVIS_GRAPH_BACKEND', raising = False)
    monkeypatch.delenv('JARVIS_MEMGRAPH_AUTOSTART', raising = False)
    @py_assert1 = autostart_memgraph()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(autostart_memgraph) if 'autostart_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(autostart_memgraph) else 'autostart_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_memgraph_autostart_default_on_with_memgraph_backend(monkeypatch):
    monkeypatch.setenv('JARVIS_GRAPH_BACKEND', 'memgraph')
    monkeypatch.delenv('JARVIS_MEMGRAPH_AUTOSTART', raising = False)
    @py_assert1 = autostart_memgraph()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(autostart_memgraph) if 'autostart_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(autostart_memgraph) else 'autostart_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

