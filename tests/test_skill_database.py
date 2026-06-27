"""Skill database tests."""

import json

import pytest

from jarvis.skill_database import (
    ensure_default_skills,
    list_skills,
    parse_skill_run_query,
    parse_skill_save_message,
    resolve_skill,
    run_skill,
    save_skill,
    slugify,
)


@pytest.fixture
def skills_env(data_dir, monkeypatch):
    skills = data_dir / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.skill_database.SKILLS_DIR", skills)
    monkeypatch.setattr("jarvis.skill_database.INDEX_FILE", skills / "index.json")
    return skills


def test_slugify():
    assert slugify("Install Docker!") == "install-docker"


def test_ensure_defaults(skills_env):
    installed = ensure_default_skills()
    assert installed or list_skills()
    assert resolve_skill("install-docker")


def test_save_and_resolve(skills_env):
    save_skill(
        "Test Repair",
        description="Fix the thing",
        steps=[{"type": "command", "title": "Ping", "command": "echo ok"}],
        tags=["test", "repair"],
        slug="test-repair",
    )
    skill = resolve_skill("test repair")
    assert skill is not None
    assert skill["slug"] == "test-repair"


def test_parse_skill_run_query():
    q, confirm = parse_skill_run_query("run docker repair skill confirm")
    assert "docker" in q
    assert confirm is True
    q2, confirm2 = parse_skill_run_query("run install-ollama skill")
    assert confirm2 is False


def test_parse_skill_save_message():
    parsed = parse_skill_save_message(
        "save skill install redis:\n1. sudo apt install redis\n2. sudo systemctl start redis"
    )
    assert parsed is not None
    assert "install redis" in parsed["name"].lower()
    assert len(parsed["steps"]) == 2


def test_run_skill_dry_run(skills_env):
    ensure_default_skills()
    result = run_skill("install-docker", dry_run=True)
    assert result["ok"]
    assert result["dry_run"] is True
    assert result["results"]


def test_router_skill_run():
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("run repair mongodb skill", SessionContext())
    assert intent["action"] == "skill_run"
    assert "mongodb" in intent["params"]["slug"].lower()
