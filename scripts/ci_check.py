#!/usr/bin/env python3
"""CI gates for ARIA — lint and test maintained paths only.

The full tree still contains legacy decompile artifacts; CI scopes ruff/pytest
to paths that are syntactically valid and expected to pass on GitHub runners.
"""

from __future__ import annotations

import argparse
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Maintained application code (expand as modules are recovered).
RUFF_PATHS: tuple[str, ...] = (
    "jarvis/async_util.py",
    "jarvis/gpu_routing.py",
    "jarvis/comfyui_video.py",
    "jarvis/video_settings.py",
    "jarvis/modules/video.py",
    "jarvis/resource_router.py",
    "jarvis/torch_device.py",
    "jarvis/env_loader.py",
    "jarvis/gpu.py",
    "jarvis/comfyui.py",
    "jarvis/services.py",
    "jarvis/vram_guard.py",
    "jarvis/model_pull.py",
    "jarvis/daemon.py",
    "jarvis/extensibility",
    "jarvis/extensions/__init__.py",
    "jarvis/extensions/memory/extension.py",
    "jarvis/extensions/memory/handlers.py",
    "jarvis/extensions/memory/routes.py",
    "jarvis/extensions/git",
    "jarvis/extensions/journal/extension.py",
    "jarvis/extensions/journal/handlers.py",
    "jarvis/extensions/voice/extension.py",
    "jarvis/extensions/voice/handlers.py",
    "jarvis/extensions/security/extension.py",
    "jarvis/extensions/security/handlers.py",
    "jarvis/handlers/__init__.py",
    "jarvis/modules/vector_store.py",
    "jarvis/modules/memory_adapter_store.py",
    "jarvis/modules/knowledge_retrieval_adapter.py",
    "jarvis/platform_cutover.py",
    "jarvis/workflows",
    "jarvis/behaviors/daily",
    "jarvis/observability",
    "jarvis/tools/runner.py",
    "jarvis/tools/executor.py",
    "jarvis/proactive_scheduler.py",
    "jarvis/application",
    "jarvis/runtime_introspection.py",
    "jarvis/runtime_formatters.py",
    "jarvis/runtime_routing.py",
    "jarvis/runtime_routing_trace.py",
    "jarvis/routing_inspector.py",
    "jarvis/nlu",
    "jarvis/nlu/benchmark.py",
    "jarvis/nlu/confidence.py",
    "jarvis/nlu/health.py",
    "jarvis/learning_governor.py",
    "aria_core",
    "jarvis/reference_engine.py",
    "jarvis/documentation_engine.py",
    "jarvis/timeline_commands.py",
    "jarvis/mission_control.py",
    "jarvis/platform_metrics.py",
    "jarvis/platform_notifications.py",
    "jarvis/workstation_activity.py",
    "jarvis/learning_notice.py",
    "jarvis/workstation",
    "jarvis/personalization",
    "jarvis/context",
    "jarvis/jobs",
    "jarvis/memory/hierarchy.py",
    "jarvis/knowledge/git_sync.py",
    "jarvis/knowledge/repo_index.py",
    "jarvis/knowledge/registry.py",
    "jarvis/inference",
    "jarvis/automation",
    "jarvis/interfaces",
    "jarvis/morning_briefing.py",
    "jarvis/router_hints.py",
    "jarvis/jobs_center.py",
    "jarvis/agents/coordinator.py",
    "jarvis/agents/__init__.py",
)

# Unit tests expected to pass on a clean ubuntu-latest runner (no Ollama/GPU/Docker).
PYTEST_PATHS: tuple[str, ...] = (
    "tests/test_async_util.py",
    "tests/test_gpu_routing.py",
    "tests/test_platform_cutover.py",
    "tests/test_daily_workflow.py",
    "tests/test_self_healing.py",
    "tests/test_memory_adapter.py",
    "tests/test_checkpointed_jobs.py",
    "tests/test_personalization_context.py",
    "tests/test_tool_runner.py",
    "tests/test_inference.py",
    "tests/test_ollama_runtime.py",
    "tests/test_workstation.py",
    "tests/test_workstation_inventory.py",
    "tests/test_workstation_acceptance.py",
    "tests/test_workstation_repair.py",
    "tests/test_workstation_integration.py",
    "tests/test_application_boundary.py",
    "tests/test_desktop_shortcuts.py",
    "tests/test_runtime_introspection.py",
    "tests/test_runtime_formatters.py",
    "tests/test_runtime_routing.py",
    "tests/test_routing_inspector.py",
    "tests/test_routing_regression.py",
    "tests/test_nlu_routing.py",
    "tests/test_nlu_routing_variants.py",
    "tests/test_teaching_recognition_routing.py",
    "tests/test_workstation_polish.py",
    "tests/test_mission_control.py",
    "tests/test_automation_ops.py",
    "tests/test_knowledge_registry.py",
    "tests/test_agents.py",
    "tests/test_learning_governor.py",
    "tests/test_aria_core_contract.py",
    "tests/test_aria_core_phase2.py",
    "tests/test_aria_core_phase3.py",
    "tests/test_aria_core_phase4.py",
    "tests/test_aria_core_phase5.py",
    "tests/test_aria_core_phase6.py",
    "tests/test_cognitive_compose.py",
    "tests/test_observability_maturity.py",
    "tests/test_reference_intelligence.py",
    "tests/test_execution_routing.py",
    "tests/test_memory_intent_routing.py",
    "tests/test_memory_retrieval_quality.py",
    "tests/test_memory_retrieval_consistency.py",
    "tests/test_aria_core_phase7.py",
    "tests/test_aria_core_phase8.py",
    "tests/test_greeting_latency.py",
    "tests/test_conversation_trace.py",
    "tests/test_uncensored_auth.py",
    "tests/test_aria_acm_m0.py",
    "tests/test_aria_acm_m0a.py",
    "tests/test_aria_acm_m0b.py",
    "tests/test_aria_acm_m0c.py",
    "tests/test_aria_acm_m0d.py",
    "tests/test_aria_acm_m0e.py",
    "tests/test_aria_acm_m0f.py",
    "tests/test_aria_acm_m0g.py",
    "tests/test_aria_acm_m0h.py",
    "tests/test_aria_acm_m0i.py",
    "tests/test_aria_acm_m0j.py",
    "tests/test_aria_acm_m0k.py",
    "tests/test_aria_acm_m0l.py",
    "tests/test_aria_acm_m1.py",
    "tests/test_aria_acm_m1_episodic.py",
    "tests/test_aria_acm_semantic_autobio.py",
    "tests/test_aria_acm_memory_evolution.py",
    "tests/test_aria_acm_relational_reasoning.py",
    "tests/test_aria_acm_relational_stabilization.py",
    "tests/test_aria_acm_prediction.py",
    "tests/test_language_stability.py",
    "tests/test_m1_aria_integration_polish.py",
    "tests/test_capability_routing.py",
    "tests/test_m2_routing_architecture.py",
    "tests/test_m2_post_validation_repairs.py",
    "tests/test_m3_integration_repairs.py",
    "tests/test_aria_acm_m2.py",
    "tests/test_aria_acm_m3.py",
    "tests/test_aria_acm_m4.py",
    "tests/test_cognitive_infrastructure_conversion.py",
)


def _resolve(path: str) -> Path:
    return ROOT / path


def _compilable(path: Path) -> bool:
    if path.is_dir():
        return all(_compilable(p) for p in path.rglob("*.py"))
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except py_compile.PyCompileError:
        return False


def _expand_ruff_targets() -> list[Path]:
    targets: list[Path] = []
    seen: set[Path] = set()
    for rel in RUFF_PATHS:
        path = _resolve(rel)
        if not path.exists():
            raise SystemExit(f"CI ruff path missing: {rel}")
        if path.is_dir():
            for child in sorted(path.rglob("*.py")):
                if child not in seen:
                    seen.add(child)
                    targets.append(child)
        elif path not in seen:
            seen.add(path)
            targets.append(path)
    missing = [p for p in targets if not _compilable(p)]
    if missing:
        lines = "\n".join(f"  - {p.relative_to(ROOT)}" for p in missing)
        raise SystemExit(f"CI ruff target has syntax errors:\n{lines}")
    return targets


def _ruff_cmd(*extra: str) -> list[str]:
    targets = _expand_ruff_targets()
    return [
        sys.executable,
        "-m",
        "ruff",
        *extra,
        "--config",
        str(ROOT / "ruff.toml"),
        *[str(p) for p in targets],
    ]


def run_ruff() -> int:
    return subprocess.run(_ruff_cmd("check"), cwd=ROOT, check=False).returncode


def run_format_check() -> int:
    return subprocess.run(_ruff_cmd("format", "--check"), cwd=ROOT, check=False).returncode


def run_format() -> int:
    fix = subprocess.run(_ruff_cmd("check", "--fix"), cwd=ROOT, check=False).returncode
    if fix != 0:
        return fix
    return subprocess.run(_ruff_cmd("format"), cwd=ROOT, check=False).returncode


def run_pytest() -> int:
    for rel in PYTEST_PATHS:
        path = _resolve(rel)
        if not path.is_file() or not _compilable(path):
            raise SystemExit(f"CI pytest path not compilable: {rel}")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *PYTEST_PATHS,
        "-q",
        "--tb=short",
        "-m",
        "not network and not workstation and not integration and not gpu",
    ]
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


def run_supremacy() -> int:
    script = ROOT / "scripts" / "acm_supremacy_check.py"
    return subprocess.run([sys.executable, str(script)], cwd=ROOT, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="ARIA CI gates")
    parser.add_argument(
        "command",
        choices=("ruff", "format", "format-check", "pytest", "supremacy", "all"),
    )
    args = parser.parse_args()
    if args.command == "ruff":
        return run_ruff()
    if args.command == "format":
        return run_format()
    if args.command == "format-check":
        return run_format_check()
    if args.command == "pytest":
        return run_pytest()
    if args.command == "supremacy":
        return run_supremacy()
    for step in (run_ruff, run_format_check, run_supremacy, run_pytest):
        code = step()
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
