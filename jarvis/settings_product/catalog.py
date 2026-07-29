"""Preference catalog — indexes product settings; does not move stores."""

from __future__ import annotations

from typing import Any

from jarvis.settings_product.schema import make_preference
from jarvis.settings_product.terminology import CATEGORIES


def build_catalog() -> list[dict[str, Any]]:
    """Return the full preference catalog (static index + live capability hooks)."""
    entries: list[dict[str, Any]] = []

    # —— Global ——
    entries.extend(
        [
            make_preference(
                id="global.language",
                title="Language",
                description="Operator UI language (English default).",
                category="global",
                owner="Settings",
                type="select",
                default="en",
                deep_link={"view": "settings", "section": "global", "pref": "global.language"},
                aliases=["locale", "i18n"],
                keywords="language locale english",
                editable_in_settings=True,
            ),
            make_preference(
                id="global.notifications",
                title="Notifications",
                description="Toast and soft-tip notification preferences.",
                category="global",
                owner="Settings",
                type="link",
                deep_link={"view": "settings", "section": "global", "pref": "global.notifications"},
                aliases=["toasts", "alerts"],
                keywords="notifications toasts tips",
                editable_in_settings=True,
            ),
            make_preference(
                id="global.keyboard_hints",
                title="Keyboard hints",
                description="Show keyboard shortcut hints in chrome.",
                category="global",
                owner="Settings",
                type="toggle",
                default=True,
                deep_link={"view": "settings", "section": "global", "pref": "global.keyboard_hints"},
                aliases=["shortcuts hints"],
                keywords="keyboard shortcuts hints",
                editable_in_settings=True,
            ),
            make_preference(
                id="global.accessibility",
                title="Accessibility",
                description="High contrast, reduced motion, focus visibility.",
                category="global",
                owner="Settings",
                type="link",
                deep_link={"view": "settings", "section": "appearance", "pref": "global.accessibility"},
                aliases=["a11y", "contrast", "motion"],
                keywords="accessibility a11y contrast reduced motion",
                editable_in_settings=True,
            ),
        ]
    )

    # —— Appearance (Settings-owned chrome) ——
    entries.extend(
        [
            make_preference(
                id="appearance.theme",
                title="Theme",
                description="Light or dark theme.",
                category="appearance",
                owner="Settings",
                type="select",
                default="dark",
                deep_link={"view": "settings", "section": "appearance", "pref": "appearance.theme"},
                aliases=["dark", "light", "color scheme"],
                keywords="theme dark light appearance",
                editable_in_settings=True,
            ),
            make_preference(
                id="appearance.accent",
                title="Accent color",
                description="Highlight accent (gold, blue, green, …).",
                category="appearance",
                owner="Settings",
                type="select",
                default="gold",
                deep_link={"view": "settings", "section": "appearance", "pref": "appearance.accent"},
                aliases=["color", "swatch"],
                keywords="accent color swatch gold blue",
                editable_in_settings=True,
            ),
            make_preference(
                id="appearance.dock",
                title="Quick dock",
                description="Show or hide the quick dock.",
                category="appearance",
                owner="Settings",
                type="toggle",
                default=True,
                deep_link={"view": "settings", "section": "appearance", "pref": "appearance.dock"},
                aliases=["dock"],
                keywords="dock chrome layout",
                editable_in_settings=True,
            ),
            make_preference(
                id="appearance.status_bar",
                title="Status bar",
                description="Show or hide the status bar.",
                category="appearance",
                owner="Settings",
                type="toggle",
                default=True,
                deep_link={"view": "settings", "section": "appearance", "pref": "appearance.status_bar"},
                aliases=["statusbar"],
                keywords="status bar chrome",
                editable_in_settings=True,
            ),
            make_preference(
                id="appearance.mini_chat",
                title="Mini chat",
                description="Floating mini chat panel visibility.",
                category="appearance",
                owner="Settings",
                type="toggle",
                default=True,
                deep_link={"view": "settings", "section": "appearance", "pref": "appearance.mini_chat"},
                aliases=["floating chat"],
                keywords="mini chat floating",
                editable_in_settings=True,
            ),
            make_preference(
                id="appearance.split",
                title="Split view",
                description="Split-view layout preference.",
                category="appearance",
                owner="Settings",
                type="toggle",
                default=False,
                deep_link={"view": "settings", "section": "appearance", "pref": "appearance.split"},
                aliases=["split pane"],
                keywords="split view layout panes",
                editable_in_settings=True,
            ),
            make_preference(
                id="appearance.sidebar",
                title="Sidebar",
                description="Sidebar width and collapse state.",
                category="appearance",
                owner="Settings",
                type="link",
                deep_link={"view": "settings", "section": "appearance", "pref": "appearance.sidebar"},
                aliases=["nav width"],
                keywords="sidebar chrome navigation",
                editable_in_settings=True,
            ),
            make_preference(
                id="appearance.home_density",
                title="Home density",
                description="Dashboard Home widget density (comfortable / compact). Presentation owned by Dashboard; indexed here.",
                category="appearance",
                owner="Dashboard",
                type="select",
                default="comfortable",
                deep_link={"view": "dashboard", "section": "layout", "pref": "density"},
                aliases=["dashboard density", "home density"],
                keywords="home density dashboard compact comfortable",
            ),
            make_preference(
                id="appearance.home_layout",
                title="Home layout",
                description="Widget order, visibility, and role layouts for Home.",
                category="appearance",
                owner="Dashboard",
                type="link",
                deep_link={"view": "dashboard", "action": "customize"},
                aliases=["dashboard layout", "home widgets"],
                keywords="home layout widgets customize dashboard",
            ),
            make_preference(
                id="appearance.home_role",
                title="Home role layout",
                description="Role presets: default, maker, developer, media, operations, research.",
                category="appearance",
                owner="Dashboard",
                type="select",
                default="default",
                deep_link={"view": "dashboard", "section": "layout", "pref": "role"},
                aliases=["role layout", "home role"],
                keywords="home role maker developer operations media research",
            ),
        ]
    )

    # —— Security (deep links only) ——
    entries.extend(
        [
            make_preference(
                id="security.pin",
                title="PIN lock",
                description="Workstation PIN lock — managed by Security.",
                category="security",
                owner="Security",
                type="link",
                deep_link={"view": "security", "section": "pin", "focus": "securityPinSetup"},
                aliases=["pin", "lock", "password lock"],
                keywords="pin lock security unlock",
                sensitive=True,
            ),
            make_preference(
                id="security.trusted_devices",
                title="Trusted devices",
                description="Manage trusted devices — Security view.",
                category="security",
                owner="Security",
                type="link",
                deep_link={"view": "security", "section": "devices"},
                aliases=["devices", "trust"],
                keywords="trusted devices revoke",
                sensitive=True,
            ),
            make_preference(
                id="security.uncensored",
                title="Uncensored mode",
                description="Password-gated uncensored mode — Mode sidebar.",
                category="security",
                owner="Security",
                type="link",
                deep_link={"view": "chat", "action": "uncensored", "focus": "uncensoredToggle"},
                aliases=["uncensored", "no filter"],
                keywords="uncensored mode filter refusals",
                sensitive=True,
            ),
            make_preference(
                id="security.gestures",
                title="Gesture controls",
                description="Gesture settings — Presence / Security.",
                category="security",
                owner="Security",
                type="link",
                deep_link={"view": "presence", "section": "gestures"},
                aliases=["gestures", "hand"],
                keywords="gestures presence",
            ),
        ]
    )

    # —— Secrets (Integrations) ——
    entries.extend(
        [
            make_preference(
                id="secrets.integrations",
                title="API keys & providers",
                description="Provider credentials — Integrations Home owns secrets.",
                category="secrets",
                owner="Integrations",
                type="link",
                deep_link={"view": "integrations", "section": "secrets"},
                aliases=["api key", "gemini", "openai", "secrets", "env"],
                keywords="api keys secrets providers jarvis.env",
                sensitive=True,
            ),
            make_preference(
                id="secrets.hygiene",
                title="Secret hygiene",
                description="Plaintext jarvis.env warnings and chmod guidance.",
                category="secrets",
                owner="Integrations",
                type="link",
                deep_link={"view": "integrations", "section": "hygiene"},
                aliases=["world readable", "chmod"],
                keywords="hygiene plaintext permissions",
                sensitive=True,
            ),
        ]
    )

    # —— Products (deep links) ——
    product_links = [
        ("voice", "Voice", "voice", "speak whisper ptt cloud live duplex", ["speak", "whisper", "ptt"]),
        ("vision", "Vision", "vision", "ocr compare webcam quality", ["ocr", "vision model"]),
        ("models", "Models", "models", "ollama chat coder embed roles", ["model", "ollama", "llm"]),
        ("search", "Search", "search", "facets corpora gallery ha opt-in", ["federated search"]),
        ("capabilities", "Capabilities", "capabilities", "plugins extensions trust", ["plugins"]),
        ("integrations", "Integrations", "integrations", "providers unlock matrix", ["providers"]),
        ("smarthome", "Smart Home", "workstation", "home assistant entities rooms", ["ha", "home assistant"]),
        ("flytying", "Fly Tying", "flytying", "patterns recipes", ["fly"]),
        ("audio", "Audio", "audio", "studio whisper mic sinks", ["mic", "audio studio"]),
        ("gallery", "Gallery / Image", "gallery", "comfy image engine", ["comfy", "image"]),
        ("video", "Video", "video", "video studio motion", ["animatediff"]),
        ("memory", "Memory", "memory", "acm recall namespaces", ["memory"]),
        ("coding", "Coding", "coding", "preferences lsp propose", ["coding prefs"]),
        ("browser", "Browser", "browser", "agent research", ["browser"]),
        ("automation", "Automation", "automation", "rules workflows", ["automation"]),
        ("planner", "Planner", "planner", "tasks focus", ["planner"]),
        ("calendar", "Calendar", "calendar", "schedule ics", ["calendar", "ics"]),
        ("dashboard", "Home / Dashboard", "dashboard", "home widgets daily brief attention", ["home", "dashboard", "daily brief"]),
        ("documents", "Documents", "documents", "library rag index", ["documents"]),
        ("connections", "Connections", "connections", "knowledge graph", ["graph"]),
    ]
    for pid, label, view, kw, aliases in product_links:
        entries.append(
            make_preference(
                id=f"products.{pid}",
                title=f"{label} settings",
                description=f"Open {label} Home — product owns its preference store.",
                category="products",
                owner=label,
                type="link",
                deep_link={"view": view, "section": "settings", "product": pid},
                aliases=aliases,
                keywords=f"{label.lower()} settings {kw}",
            )
        )

    # Explicit Voice & Chat modal entry (not Settings Home)
    entries.append(
        make_preference(
            id="products.voice.speak_replies",
            title="Speak replies",
            description="Voice owns speak_replies — open Voice & Chat modal or Voice Home.",
            category="products",
            owner="Voice",
            type="link",
            deep_link={"view": "voice", "action": "voice_chat_modal", "pref": "speak_replies"},
            aliases=["speak", "tts", "read aloud"],
            keywords="speak replies tts voice chat",
        )
    )
    entries.append(
        make_preference(
            id="products.voice.server_whisper",
            title="Server Whisper",
            description="Server-side Whisper for mic without browser STT — Voice product.",
            category="products",
            owner="Voice",
            type="link",
            deep_link={"view": "voice", "action": "voice_chat_modal", "pref": "server_whisper"},
            aliases=["whisper", "stt", "mic"],
            keywords="whisper server mic stt",
        )
    )

    # —— Environment ——
    entries.extend(
        [
            make_preference(
                id="environment.jarvis_env",
                title="jarvis.env",
                description="Environment flags and secrets file — see CONFIG.md / Integrations.",
                category="environment",
                owner="Host",
                type="link",
                deep_link={"view": "integrations", "section": "env"},
                aliases=["env", "config", "flags"],
                keywords="jarvis.env environment config flags",
                sensitive=True,
            ),
            make_preference(
                id="environment.config_docs",
                title="Configuration reference",
                description="Operator config documentation.",
                category="environment",
                owner="Host",
                type="link",
                deep_link={"view": "settings", "section": "environment", "doc": "CONFIG.md"},
                aliases=["docs config"],
                keywords="documentation config reference",
            ),
        ]
    )

    # —— Diagnostics ——
    entries.extend(
        [
            make_preference(
                id="diagnostics.health",
                title="Settings diagnostics",
                description="Preference health, migrations, missing stores.",
                category="diagnostics",
                owner="Settings",
                type="link",
                deep_link={"view": "settings", "section": "diagnostics"},
                aliases=["health", "migration"],
                keywords="diagnostics health migration corrupt",
                editable_in_settings=True,
            ),
            make_preference(
                id="diagnostics.runtime_config",
                title="Runtime configuration (Mission Control)",
                description="Ops runtime snapshot — not editable preferences.",
                category="diagnostics",
                owner="Mission Control",
                type="link",
                deep_link={"view": "workstation", "mc_tab": "runtime_config"},
                aliases=["mc settings", "runtime"],
                keywords="mission control runtime configuration ops",
            ),
        ]
    )

    # —— Profiles ——
    entries.extend(
        [
            make_preference(
                id="profiles.active",
                title="Active preference profile",
                description="Named chrome/global preference profiles.",
                category="profiles",
                owner="Settings",
                type="select",
                default="default",
                deep_link={"view": "settings", "section": "profiles"},
                aliases=["profile", "preset"],
                keywords="profiles presets work lab locked",
                editable_in_settings=True,
            ),
        ]
    )

    # Capability settings_schema contributions (optional — Capabilities owns schemas)
    try:
        from jarvis.capabilities_product.registry import list_capabilities

        for cap in list_capabilities() or []:
            if not isinstance(cap, dict):
                continue
            schema = cap.get("settings_schema") or (cap.get("metadata") or {}).get("settings_schema")
            if not schema:
                continue
            cid = str(cap.get("id") or "")
            if not cid:
                continue
            entries.append(
                make_preference(
                    id=f"products.capability.{cid}",
                    title=str(cap.get("title") or cap.get("name") or cid),
                    description=str(cap.get("description") or "Capability settings"),
                    category="products",
                    owner="Capabilities",
                    type="link",
                    deep_link={"view": "capabilities", "capability": cid, "section": "settings"},
                    aliases=[],
                    keywords=f"capability {cid}",
                )
            )
    except Exception:
        pass

    return entries


def catalog_by_category(category: str = "") -> list[dict[str, Any]]:
    items = build_catalog()
    if category and category != "all":
        items = [e for e in items if e.get("category") == category]
    return items


def search_catalog(query: str, *, limit: int = 24) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return build_catalog()[:limit]
    tokens = [t for t in q.replace(",", " ").split() if t]
    scored: list[tuple[float, dict[str, Any]]] = []
    for e in build_catalog():
        blob = " ".join(
            [
                str(e.get("id") or ""),
                str(e.get("title") or ""),
                str(e.get("description") or ""),
                str(e.get("keywords") or ""),
                str(e.get("owner") or ""),
                str(e.get("category") or ""),
                " ".join(e.get("aliases") or []),
            ]
        ).lower()
        if q in blob:
            score = 1.0 if blob.startswith(q) or q in str(e.get("title") or "").lower() else 0.85
        elif tokens and all(t in blob for t in tokens):
            score = 0.7
        elif tokens and any(t in blob for t in tokens):
            score = 0.45
        else:
            continue
        scored.append((score, e))
    scored.sort(key=lambda x: (-x[0], str(x[1].get("title") or "")))
    return [e for _, e in scored[:limit]]


def categories() -> list[str]:
    return list(CATEGORIES)
