"""Layer adapters — project existing extension systems without merging them."""

from __future__ import annotations

from typing import Any

from jarvis.capabilities_product.models import CapabilityRecord, risk_from_permissions
from jarvis.capabilities_product import policy as cap_policy


def _host_category(name: str, module_label: str = "") -> str:
    mapping = {
        "git": "Coding",
        "engineering": "Coding",
        "browser": "Browser",
        "voice": "Voice",
        "smarthome": "Smart Home",
        "planner": "Planner",
        "journal": "Memory",
        "memory": "Memory",
        "flytying": "Fly Tying",
        "projects": "Utilities",
        "security": "Security",
    }
    if name in mapping:
        return mapping[name]
    ml = (module_label or "").lower()
    if ml in ("coding", "vision", "audio", "image", "video", "memory", "journal"):
        return ml.title() if ml != "coding" else "Coding"
    return "System"


def discover_host() -> list[CapabilityRecord]:
    records: list[CapabilityRecord] = []
    try:
        from jarvis.extensibility.loader import list_extension_names_on_disk, list_extensions

        loaded_map = {e.get("name"): e for e in list_extensions()}
        for name in list_extension_names_on_disk():
            ext = loaded_map.get(name) or {}
            # Soft-read metadata without load when disabled
            if not ext:
                try:
                    from jarvis.extensibility.loader import _import_extension

                    obj = _import_extension(name)
                    if obj is not None:
                        ext = obj.to_dict()
                except Exception:
                    ext = {"name": name, "description": "", "version": "1.0.0", "module_label": ""}
            cap_id = f"host:{name}"
            trust = cap_policy.trust_override(cap_id) or "first_party"
            enabled = cap_policy.is_enabled(cap_id, trust=trust, default=True)
            quarantined = cap_policy.is_quarantined(cap_id)
            status = "quarantined" if quarantined else ("disabled" if not enabled else ("loaded" if name in loaded_map else "discovered"))
            rec = CapabilityRecord(
                id=cap_id,
                name=name,
                layer="host",
                category=_host_category(name, str(ext.get("module_label") or "")),
                description=str(ext.get("description") or ""),
                version=str(ext.get("version") or "1.0.0"),
                author="Aria",
                trust="quarantined" if quarantined else ("disabled" if not enabled else trust),
                enabled=enabled and not quarantined,
                status=status,
                health="healthy" if enabled and not quarantined else "unknown",
                permissions=[],
                isolation="none",
                source="jarvis.extensions",
                tags=["built-in", "host"],
                lazy=cap_policy.is_lazy(cap_id, False),
                risk_summary=risk_from_permissions([], trust),
                metadata={"module_label": ext.get("module_label")},
            )
            records.append(rec)
    except Exception as exc:
        records.append(
            CapabilityRecord(
                id="host:__error__",
                name="Host extensions",
                layer="host",
                status="failed",
                health="failed",
                trust="unknown",
                enabled=False,
                error=str(exc),
                risk_summary="Host discovery failed.",
            )
        )
    return records


def discover_sdk() -> list[CapabilityRecord]:
    records: list[CapabilityRecord] = []
    try:
        from jarvis.intelligence import plugin_sdk

        for item in plugin_sdk.list_plugins():
            if item.get("error") and not item.get("id"):
                records.append(
                    CapabilityRecord(
                        id=f"sdk:invalid:{item.get('path')}",
                        name="Invalid manifest",
                        layer="sdk",
                        status="failed",
                        health="failed",
                        trust="unknown",
                        enabled=False,
                        error=str(item.get("error")),
                        path=str(item.get("path") or ""),
                    )
                )
                continue
            pid = str(item.get("id") or "")
            cap_id = f"sdk:{pid}"
            perms = list(item.get("permissions") or [])
            trust = cap_policy.trust_override(cap_id) or "trusted_local"
            if item.get("experimental"):
                trust = cap_policy.trust_override(cap_id) or "experimental"
            enabled = cap_policy.is_enabled(cap_id, trust=trust)
            quarantined = cap_policy.is_quarantined(cap_id)
            loaded = bool(item.get("loaded"))
            sandbox_claimed = bool(item.get("sandbox", True))
            status = "quarantined" if quarantined else ("disabled" if not enabled else ("loaded" if loaded else "discovered"))
            contrib = item.get("contributions") or {}
            records.append(
                CapabilityRecord(
                    id=cap_id,
                    name=str(item.get("name") or pid),
                    layer="sdk",
                    category=str(item.get("category") or "Utilities"),
                    description=str(item.get("description") or ""),
                    version=str(item.get("version") or "0.1.0"),
                    author=str(item.get("author") or ""),
                    trust="quarantined" if quarantined else ("disabled" if not enabled else trust),
                    enabled=enabled and not quarantined,
                    status=status,
                    health="healthy" if loaded and not item.get("error") else ("failed" if item.get("error") else "unknown"),
                    permissions=perms,
                    dependencies=list(item.get("dependencies") or []),
                    path=str(item.get("path") or ""),
                    tags=list(item.get("tags") or ["local", "sdk"]),
                    contributions=contrib if isinstance(contrib, dict) else {},
                    isolation="none",
                    sandbox_claimed=sandbox_claimed,
                    source="data/plugins",
                    experimental=bool(item.get("experimental")),
                    lazy=cap_policy.is_lazy(cap_id, False),
                    error=str(item.get("error") or ""),
                    risk_summary=risk_from_permissions(perms, trust),
                    metadata={"entry": item.get("entry"), "settings_schema": item.get("settings_schema")},
                )
            )
    except Exception as exc:
        records.append(
            CapabilityRecord(
                id="sdk:__error__",
                name="Local capabilities",
                layer="sdk",
                status="failed",
                health="failed",
                trust="unknown",
                enabled=False,
                error=str(exc),
            )
        )
    return records


def discover_acm() -> list[CapabilityRecord]:
    records: list[CapabilityRecord] = []
    try:
        from aria_acm.acm.plugins.registry import ExtensionRegistry

        # ACM registry is per-engine; project known protocol surface as built-in hooks availability
        cap_id = "acm:extension_registry"
        trust = cap_policy.trust_override(cap_id) or "built_in"
        enabled = cap_policy.is_enabled(cap_id, trust=trust, default=True)
        records.append(
            CapabilityRecord(
                id=cap_id,
                name="ACM Extension Registry",
                layer="acm",
                category="AI",
                description=(
                    "In-process cognitive hooks (after_encode, after_remember, after_sleep, …). "
                    "Extensions register programmatically — no file discovery."
                ),
                version="1.0.0",
                author="Aria ACM",
                trust=trust if enabled else "disabled",
                enabled=enabled,
                status="loaded" if enabled else "disabled",
                health="healthy",
                permissions=[],
                isolation="none",
                source="aria_acm.acm.plugins",
                tags=["cognitive", "built-in"],
                risk_summary=risk_from_permissions([], trust),
                metadata={"registry_class": ExtensionRegistry.__name__, "file_discovery": False},
            )
        )
    except Exception as exc:
        records.append(
            CapabilityRecord(
                id="acm:__error__",
                name="ACM plugins",
                layer="acm",
                status="failed",
                health="failed",
                trust="unknown",
                enabled=False,
                error=str(exc),
            )
        )
    return records


def discover_platform() -> list[CapabilityRecord]:
    records: list[CapabilityRecord] = []
    try:
        from aiplatform.plugins.manager import plugins as plugin_manager

        for desc in plugin_manager.all() or []:
            pid = str(getattr(desc, "id", None) or getattr(desc, "name", "") or "")
            if not pid:
                continue
            cap_id = f"platform:{pid}"
            trust = cap_policy.trust_override(cap_id) or "built_in"
            enabled_flag = bool(getattr(desc, "enabled", True))
            policy_enabled = cap_policy.is_enabled(cap_id, trust=trust, default=enabled_flag)
            quarantined = cap_policy.is_quarantined(cap_id)
            loaded = bool(getattr(desc, "loaded", False))
            healthy = bool(getattr(desc, "healthy", True))
            status = (
                "quarantined"
                if quarantined
                else ("disabled" if not policy_enabled else ("loaded" if loaded else "discovered"))
            )
            records.append(
                CapabilityRecord(
                    id=cap_id,
                    name=str(getattr(desc, "display_name", None) or getattr(desc, "name", pid)),
                    layer="platform",
                    category=str(getattr(desc, "category", None) or "System"),
                    description=str(getattr(desc, "description", "") or ""),
                    version=str(getattr(desc, "version", "") or "1.0.0"),
                    author=str(getattr(desc, "author", "") or "AI Platform"),
                    trust="quarantined" if quarantined else ("disabled" if not policy_enabled else trust),
                    enabled=policy_enabled and not quarantined,
                    status=status,
                    health="healthy" if healthy else "degraded",
                    permissions=list(getattr(desc, "capabilities", None) or [])[:20]
                    if isinstance(getattr(desc, "capabilities", None), list)
                    else [],
                    dependencies=list(getattr(desc, "required_plugins", None) or []),
                    path=str(getattr(desc, "path", "") or ""),
                    tags=list(getattr(desc, "tags", None) or ["platform"]),
                    isolation="none",
                    source="aiplatform.plugins",
                    experimental=str(getattr(desc, "plugin_type", "") or "") == "experimental",
                    risk_summary=risk_from_permissions([], trust),
                    metadata={
                        "plugin_type": getattr(desc, "plugin_type", None),
                        "module": getattr(desc, "module", None),
                    },
                )
            )
    except Exception:
        # Platform optional — soft absence is normal
        records.append(
            CapabilityRecord(
                id="platform:__unavailable__",
                name="AI Platform plugins",
                layer="platform",
                category="System",
                description="AI Platform PluginManager is not attached in this process.",
                version="—",
                author="AI Platform",
                trust="built_in",
                enabled=False,
                status="discovered",
                health="unknown",
                isolation="none",
                source="aiplatform.plugins",
                tags=["platform", "optional"],
                risk_summary="Platform layer unavailable; Aria continues without it.",
            )
        )
    return records


def discover_all_layers(*, include_platform: bool = True, include_acm: bool = True) -> list[CapabilityRecord]:
    out: list[CapabilityRecord] = []
    out.extend(discover_host())
    out.extend(discover_sdk())
    if include_acm:
        out.extend(discover_acm())
    if include_platform:
        out.extend(discover_platform())
    return out


def layer_summary(records: list[CapabilityRecord]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for r in records:
        counts[r.layer] = counts.get(r.layer, 0) + 1
    return counts
