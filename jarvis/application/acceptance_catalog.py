"""Aria acceptance catalog entries — registered with platform extensions."""

from __future__ import annotations


def register() -> None:
    try:
        from aiplatform.workstation.extensions import register_acceptance_catalog
    except ImportError:
        return

    from jarvis.application.standalone.workstation_impl import acceptance as aria_acc

    def _catalog():
        # Aria-only entries from legacy catalog (exclude platform infra duplicates)
        platform_ids = {
            "ollama",
            "litellm",
            "lmstudio",
            "open_webui",
            "postgres",
            "redis",
            "qdrant",
            "mongodb",
            "n8n",
            "prometheus",
            "grafana",
            "scheduler",
            "workstation",
            "git",
            "python",
            "uv",
            "docker",
            "docker_compose",
            "ruff",
            "pytest",
            "pytorch",
            "transformers",
            "aiplatform",
        }
        return [entry for entry in aria_acc._CATALOG if entry[0] not in platform_ids]

    register_acceptance_catalog(_catalog)
