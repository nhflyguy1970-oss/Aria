# Source Generated with Decompyle++
# File: test_gpu_routing.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for NVIDIA / AMD GPU routing.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
(lambda monkeypatch: gpu_routing = gpu_routingimport jarvis
def fake_run(cmd, timeout = (8,)):
if 'nvidia-smi' in cmd[0]:
'NVIDIA GeForce RTX 3060, 12288, 1024, 595.71.05, 12\n'''monkeypatch.setattr(gpu_routing, '_run', fake_run)info = gpu_routing.parse_nvidia_smi()@py_assert0 = info['nvidia_available']@py_assert3 = True@py_assert2 = @py_assert0 is @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = None@py_assert0 = info['vram_mb']@py_assert3 = 12288@py_assert2 = @py_assert0 == @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = None@py_assert0 = 'RTX 3060'@py_assert3 = info['name']@py_assert2 = @py_assert0 in @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = None) = import _pytest.assertion.rewrite, assertion

def test_resolve_whisper_cuda_when_nvidia(monkeypatch):
    gpu_routing = gpu_routing
    import jarvis
    monkeypatch.setenv('JARVIS_GPU_PREFER', 'nvidia')
    monkeypatch.setenv('JARVIS_WHISPER_DEVICE', '')
    monkeypatch.setattr(gpu_routing, 'ctranslate2_cuda_count', (lambda : 1))
    @py_assert1 = gpu_routing.resolve_whisper_device
    @py_assert3 = @py_assert1()
    @py_assert6 = 'cuda'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.resolve_whisper_device\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(gpu_routing) if 'gpu_routing' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gpu_routing) else 'gpu_routing',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_resolve_functiongemma_cpu_when_rocm_and_nvidia_pref(monkeypatch):
    gpu_routing = gpu_routing
    import jarvis
    monkeypatch.setenv('JARVIS_GPU_PREFER', 'nvidia')
    monkeypatch.setenv('JARVIS_FUNCTIONGEMMA_DEVICE', 'auto')
    monkeypatch.setattr(gpu_routing, 'torch_backend', (lambda : 'cuda_rocm'))
    @py_assert1 = gpu_routing.resolve_functiongemma_device
    @py_assert3 = @py_assert1()
    @py_assert6 = 'cpu'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.resolve_functiongemma_device\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(gpu_routing) if 'gpu_routing' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gpu_routing) else 'gpu_routing',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_resolve_functiongemma_cpu_when_rocm_and_nvidia_available(monkeypatch):
    gpu_routing = gpu_routing
    import jarvis
    monkeypatch.setenv('JARVIS_GPU_PREFER', 'amd')
    monkeypatch.setenv('JARVIS_FUNCTIONGEMMA_DEVICE', 'auto')
    monkeypatch.setattr(gpu_routing, 'torch_backend', (lambda : 'cuda_rocm'))
    monkeypatch.setattr(gpu_routing, 'nvidia_available', (lambda : True))
    @py_assert1 = gpu_routing.resolve_functiongemma_device
    @py_assert3 = @py_assert1()
    @py_assert6 = 'cpu'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.resolve_functiongemma_device\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(gpu_routing) if 'gpu_routing' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gpu_routing) else 'gpu_routing',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_detect_gpu_ollama_on_gpu_via_nvidia_smi(monkeypatch):
    detect_gpu = detect_gpu
    import jarvis.gpu
    monkeypatch.setattr('jarvis.gpu_routing.parse_nvidia_smi', (lambda : {
'name': 'NVIDIA GeForce RTX 3060',
'vram_mb': 12288,
'vram_used_mb': 9000,
'free_vram_mb': 3288,
'driver': '595.71',
'nvidia_available': True }))
    monkeypatch.setattr('jarvis.gpu_routing.gpu_preference', (lambda : 'nvidia'))
    monkeypatch.setattr('jarvis.gpu_routing.nvidia_available', (lambda : True))
    
    def fake_run(cmd, timeout = (10,)):
        if cmd and cmd[0] == 'nvidia-smi' and 'compute-apps' in ' '.join(cmd):
            return '12345, /usr/bin/ollama, 8192'
        if cmd and cmd[0] == 'lspci':
            return 'VGA compatible controller: NVIDIA Corporation GA106'
        return ''

    monkeypatch.setattr('jarvis.gpu._run', fake_run)
    info = detect_gpu(force = True)
    @py_assert0 = info['ollama_using_gpu']
    @py_assert3 = True
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None

