#!/usr/bin/env python3
"""Jarvis — local AI assistant. Run a module: python main.py <module>"""

import os
import sys

from jarvis.env_loader import load_jarvis_env
from jarvis.modules import MODULES

load_jarvis_env()

from jarvis.platform_attachment import attach_platform_infrastructure
from jarvis.platform_inference import attach_platform_inference
from jarvis.platform_memory import attach_platform_memory
from jarvis.platform_semantic_memory import attach_platform_semantic_memory
from jarvis.platform_knowledge_retrieval import attach_platform_knowledge_retrieval
from jarvis.platform_tool_capability import attach_platform_tool_capability
from jarvis.platform_workflow_orchestration import attach_platform_workflow_orchestration
from jarvis.platform_automation_event import attach_platform_automation_event
from jarvis.platform_behavior_extraction import attach_platform_behavior_extraction

attach_platform_infrastructure()
attach_platform_inference()
attach_platform_memory()
attach_platform_semantic_memory()
attach_platform_knowledge_retrieval()
attach_platform_tool_capability()
attach_platform_workflow_orchestration()
attach_platform_automation_event()
attach_platform_behavior_extraction()


def print_help():
    from jarvis.branding import assistant_full_name, assistant_name

    name = assistant_name()
    print(f"\n{name} — {assistant_full_name()}")
    print("\nUsage: python main.py <module>")
    print("\nModules:")
    for name in sorted(MODULES):
        print(f"  {name}")
    print("  tray             system tray + background (recommended)")
    print("  gui              web interface only")
    print("  serve            headless server (for tray daemon)")
    print("  tray-uncensored  tray mode, uncensored models")
    print("  gui-uncensored   web interface, uncensored models")
    print("\nExample: python main.py tray\n")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        return

    module_name = sys.argv[1].lower()
    if module_name == "serve":
        if os.getenv("JARVIS_UNCENSORED"):
            pass
        if os.getenv("JARVIS_SERVICES_MANAGED") != "1":
            from jarvis.services import ensure_services
            ensure_services(pull_models=os.getenv("JARVIS_AUTO_PULL_MODELS", "1") != "0")
        from jarvis.gui.server import serve
        serve()
        return

    if module_name in ("tray", "tray-uncensored"):
        from jarvis.daemon import run_tray
        run_tray(uncensored=module_name == "tray-uncensored")
        return

    if module_name in ("gui", "gui-uncensored"):
        if module_name == "gui-uncensored":
            os.environ["JARVIS_UNCENSORED"] = "1"
        from jarvis.services import ensure_services
        ensure_services(pull_models=os.getenv("JARVIS_AUTO_PULL_MODELS", "1") != "0")
        from jarvis.gui.server import main as gui_main
        gui_main()
        return
    if module_name == "chat":
        module_name = "general"
    if module_name not in MODULES:
        print(f"\nUnknown module: {module_name}\n")
        print_help()
        sys.exit(1)

    MODULES[module_name].main()


if __name__ == "__main__":
    main()
