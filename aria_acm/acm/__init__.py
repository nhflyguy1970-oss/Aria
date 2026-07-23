"""ACM — Aria Cognitive Memory: host-agnostic cognitive memory engine."""

from __future__ import annotations

# Aria nested-vendor shim: ``import acm`` and ``import aria_acm.acm`` must share
# identical module objects (and therefore class identity) for policy gates.
import sys as _acm_sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec

_PKG = "aria_acm.acm"
_ALIAS = "acm"


def _sync_acm_aliases() -> None:
    """Force acm.* ↔ aria_acm.acm.* to reference the same module objects."""
    for name, mod in list(_acm_sys.modules.items()):
        if name == _PKG or name.startswith(_PKG + "."):
            alias = _ALIAS + name[len(_PKG) :]
            other = _acm_sys.modules.get(alias)
            if other is None or other is not mod:
                _acm_sys.modules[alias] = mod
        elif name == _ALIAS or name.startswith(_ALIAS + "."):
            real = _PKG + name[len(_ALIAS) :]
            other = _acm_sys.modules.get(real)
            if other is None:
                _acm_sys.modules[real] = mod
            elif other is not mod:
                # Collapse split: keep the aria_acm.acm.* object as canonical.
                _acm_sys.modules[name] = other


class _AliasLoader(Loader):
    def __init__(self, module: object) -> None:
        self._module = module

    def create_module(self, spec: ModuleSpec):  # type: ignore[no-untyped-def]
        return self._module

    def exec_module(self, module: object) -> None:  # noqa: ARG002
        return None


class _AcmAliasFinder(MetaPathFinder):
    """When one spelling is already loaded, serve the twin as the same object.

    Important: do not pre-insert into ``sys.modules`` here — that breaks
    importlib's loader handshake and can replace the canonical module.
    """

    def find_spec(self, fullname, path=None, target=None):  # type: ignore[no-untyped-def]
        twin = None
        if fullname == _ALIAS or fullname.startswith(_ALIAS + "."):
            twin = _PKG + fullname[len(_ALIAS) :]
        elif fullname == _PKG or fullname.startswith(_PKG + "."):
            twin = _ALIAS + fullname[len(_PKG) :]
        else:
            return None
        if twin not in _acm_sys.modules:
            return None
        mod = _acm_sys.modules[twin]
        return ModuleSpec(
            fullname,
            loader=_AliasLoader(mod),
            is_package=hasattr(mod, "__path__"),
            origin=getattr(mod, "__file__", None),
        )


_acm_sys.modules[_ALIAS] = _acm_sys.modules[__name__]
_acm_sys.meta_path[:] = [f for f in _acm_sys.meta_path if not isinstance(f, _AcmAliasFinder)]
_acm_sys.meta_path.insert(0, _AcmAliasFinder())
_sync_acm_aliases()


from acm._version import __version__
from acm.api.engine import CognitiveEngine, RememberResult
from acm.authority import (
    CognitiveIntent,
    CognitiveMemoryResult,
    MemoryStatus,
    classify_memory_request,
    speak_cognitive_result,
)
from acm.observability.trace import CognitiveTraceEvent
from acm.plugins import BaseExtension, ExtensionRegistry
from acm.provenance import (
    TRUSTED_USER_CORRECTION,
    TRUSTED_USER_STATEMENT,
    TRUSTED_USER_TEACHING,
    HostOperation,
    IngestionActor,
    IngestionDecision,
    IngestionProvenance,
    MessageRole,
)
from acm.validation.harness import ValidationHarness

_sync_acm_aliases()

__all__ = [
    "CognitiveEngine",
    "CognitiveIntent",
    "CognitiveMemoryResult",
    "MemoryStatus",
    "RememberResult",
    "CognitiveTraceEvent",
    "ValidationHarness",
    "BaseExtension",
    "ExtensionRegistry",
    "HostOperation",
    "IngestionActor",
    "IngestionDecision",
    "IngestionProvenance",
    "MessageRole",
    "TRUSTED_USER_CORRECTION",
    "TRUSTED_USER_STATEMENT",
    "TRUSTED_USER_TEACHING",
    "classify_memory_request",
    "speak_cognitive_result",
    "__version__",
]
