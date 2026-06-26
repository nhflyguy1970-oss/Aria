# Source Generated with Decompyle++
# File: test_gpu_routing_nvidia_vendor.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''NVIDIA vendor detection in detect_gpu.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
(lambda monkeypatch: detect_gpu = detect_gpuimport jarvis.gpumonkeypatch.setattr('jarvis.gpu_routing.parse_nvidia_smi', (lambda : {
'name': 'NVIDIA GeForce RTX 3060',
'vram_mb': 12288,
'vram_used_mb': 512,
'free_vram_mb': 11776,
'driver': '595.71',
'nvidia_available': True }))
    monkeypatch.setattr('jarvis.gpu_routing.gpu_preference', (lambda : 'nvidia'))
    monkeypatch.setattr('jarvis.gpu_routing.nvidia_available', (lambda : True))
    monkeypatch.setattr('jarvis.gpu._run', (lambda cmd, timeout = (10,): ''))
    info = detect_gpu(force = True)
    @py_assert0 = info['vendor']
    @py_assert3 = 'nvidia'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = info['nvidia_available']
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
    @py_assert0 = info['vram_mb']
    @py_assert3 = 12288
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
) = import _pytest.assertion.rewrite, assertion
