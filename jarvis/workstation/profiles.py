"""Install profiles for workstation install command."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstallProfile:
    name: str
    description: str
    deps_args: tuple[str, ...] = ()
    extra_scripts: tuple[str, ...] = ()
    platform_init: bool = True
    skip_ollama_pull: bool = False
    headless: bool = False


PROFILES: dict[str, InstallProfile] = {
    "minimal": InstallProfile(
        name="minimal",
        description="Aria core: Python venv, system tools, no large model pulls",
        deps_args=("--skip-ollama", "--skip-whisper", "--skip-desktop"),
        platform_init=False,
        skip_ollama_pull=True,
    ),
    "developer": InstallProfile(
        name="developer",
        description="Aria + dev tools, LSP, platform init, git tooling",
        deps_args=("--skip-ollama",),
        extra_scripts=("install-dev-tools.sh", "install-lsp-servers.sh"),
        platform_init=True,
    ),
    "full": InstallProfile(
        name="full",
        description="Complete workstation: deps, docker, dev tools, models, platform",
        extra_scripts=("install-docker.sh", "install-dev-tools.sh", "install-lsp-servers.sh"),
        platform_init=True,
    ),
    "gpu": InstallProfile(
        name="gpu",
        description="GPU stack on top of developer profile (CUDA or ROCm PyTorch)",
        deps_args=("--skip-ollama",),
        extra_scripts=(
            "install-dev-tools.sh",
            "install-cuda-pytorch.sh",
            "install-rocm-pytorch.sh",
        ),
        platform_init=True,
    ),
    "headless": InstallProfile(
        name="headless",
        description="API server only — no desktop shortcuts or GUI deps",
        deps_args=("--skip-desktop",),
        platform_init=True,
        headless=True,
    ),
}


def resolve_profile(argv: list[str]) -> tuple[InstallProfile | None, list[str]]:
    """Return (profile, remaining_args). Default profile is developer-like full deps."""
    profile: InstallProfile | None = None
    remaining: list[str] = []
    for arg in argv:
        if arg.startswith("--") and arg[2:] in PROFILES:
            profile = PROFILES[arg[2:]]
        else:
            remaining.append(arg)
    return profile, remaining
