"""MCP / tool ecosystem — providers, transports, discovery, authority, safety."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from jarvis import mcp, skills
from jarvis import specialized_agents as agents
from jarvis.mcp import client as mcp_client
from jarvis.mcp import definitions as defs
from jarvis.mcp import engine as mcp_engine
from jarvis.mcp import registry as mcp_registry
from jarvis.mcp import secrets as mcp_secrets
from jarvis.mcp import store as mcp_store
from jarvis.mcp.fixtures import CRASH_SERVER, DEMO_SERVER, MALFORMED_SERVER
from jarvis.skills import registry as skill_registry
from jarvis.specialized_agents import registry as agent_registry

PY_BIN = sys.executable


@pytest.fixture(autouse=True)
def _clean_registries():
    mcp_registry.reset()
    skill_registry.reset()
    agent_registry.reset()
    yield
    mcp_registry.reset()
    skill_registry.reset()
    agent_registry.reset()


def provider(
    provider_id: str = "fixture_demo",
    *,
    server: Path = DEMO_SERVER,
    trust: str = defs.TRUSTED,
    **kw,
) -> defs.ProviderDefinition:
    base = {
        "provider_id": provider_id,
        "name": provider_id.replace("_", " ").title(),
        "description": "local fixture provider",
        "transport": defs.STDIO,
        "command": (PY_BIN, str(server)),
        "trust": trust,
        "impact": defs.READ,
        "tool_impacts": (("delete_everything", defs.HIGH_IMPACT),),
        "allowed_agents": ("research_specialist", "coding_specialist", "analysis_specialist"),
        "timeout_s": 20.0,
    }
    base.update(kw)
    return defs.ProviderDefinition(**base)


def reg(defn: defs.ProviderDefinition, **kw) -> defs.ProviderDefinition:
    return mcp_registry.register(defn, persist=kw.pop("persist", False), **kw)


@pytest.fixture
def demo(data_dir: Path) -> defs.ProviderDefinition:
    """A registered, trusted, discovered fixture provider."""
    defn = reg(provider())
    mcp.discover(defn.provider_id)
    return defn


# ------------------------------------------------------------- definitions


def test_valid_provider_accepted(data_dir: Path):
    assert defs.validate(provider()).provider_id == "fixture_demo"


@pytest.mark.parametrize(
    "kw, fragment",
    [
        ({"provider_id": "X"}, "Invalid provider_id"),
        ({"name": ""}, "name is required"),
        ({"transport": "carrier_pigeon"}, "unknown transport"),
        ({"trust": "sort_of"}, "unknown trust"),
        ({"impact": "apocalyptic"}, "unknown impact"),
        ({"timeout_s": 0}, "timeout_s must be positive"),
        ({"max_output_bytes": 0}, "max_output_bytes must be positive"),
        ({"schema_version": 99}, "schema_version"),
    ],
)
def test_invalid_providers_rejected(data_dir: Path, kw, fragment):
    with pytest.raises(defs.ProviderDefinitionError) as exc:
        defs.validate(provider(**kw))
    assert fragment in str(exc.value)


def test_unsupported_transport_is_reported_not_faked(data_dir: Path):
    """websocket is a real MCP transport, but not one this build supports."""
    assert defs.WEBSOCKET in defs.TRANSPORTS
    assert defs.WEBSOCKET not in defs.SUPPORTED_TRANSPORTS
    with pytest.raises(defs.ProviderDefinitionError, match="not supported by the installed"):
        defs.validate(provider(transport=defs.WEBSOCKET, url="ws://example.com"))


def test_contradictory_policy_rejected(data_dir: Path):
    with pytest.raises(defs.ProviderDefinitionError, match="both allowed and denied"):
        defs.validate(provider(allowed_agents=("a",), denied_agents=("a",)))
    with pytest.raises(defs.ProviderDefinitionError, match="tool.*both allowed and denied"):
        defs.validate(provider(allowed_tools=("t",), denied_tools=("t",)))


def test_provider_definition_is_frozen(data_dir: Path):
    """A live session must not be able to raise its own trust level."""
    defn = provider()
    with pytest.raises(Exception):
        defn.trust = defs.TRUSTED  # type: ignore[misc]


def test_qualified_names_avoid_collisions(data_dir: Path):
    assert defs.qualified("a", "search") == "a:search"
    assert defs.qualified("b", "search") != defs.qualified("a", "search")
    assert defs.split_qualified("a:search") == ("a", "search")
    with pytest.raises(defs.ProviderDefinitionError):
        defs.split_qualified("no_colon")


# ------------------------------------------------------- command / url safety


def test_arbitrary_command_refused(data_dir: Path):
    """A provider definition must never become a way to run any program."""
    with pytest.raises(defs.ProviderDefinitionError, match="not an approved MCP launcher"):
        defs.validate(provider(command=("/bin/sh", "-c", "rm -rf /")))
    with pytest.raises(defs.ProviderDefinitionError, match="not an approved MCP launcher"):
        defs.validate(provider(command=("curl", "http://evil.example")))


def test_missing_executable_refused(data_dir: Path):
    with pytest.raises(defs.ProviderDefinitionError, match="no such executable"):
        defs.validate(provider(command=("/nonexistent/python", "x.py")))


def test_stdio_provider_needs_a_command(data_dir: Path):
    with pytest.raises(defs.ProviderDefinitionError, match="needs a command"):
        defs.validate(provider(command=()))


def test_bad_cwd_refused(data_dir: Path):
    with pytest.raises(defs.ProviderDefinitionError, match="cwd is not a directory"):
        defs.validate(provider(cwd="/definitely/not/here"))


def test_network_provider_reuses_browser_url_policy(data_dir: Path):
    """SSRF protection comes from the browser layer, not a second policy."""
    with pytest.raises(defs.ProviderDefinitionError, match="internal host blocked"):
        defs.validate(provider(transport=defs.HTTP, command=(), url="http://127.0.0.1:8765/mcp"))
    with pytest.raises(defs.ProviderDefinitionError, match="Scheme not permitted"):
        defs.validate(provider(transport=defs.HTTP, command=(), url="file:///etc/passwd"))
    # An explicitly local fixture endpoint is allowed only when asked for.
    defs.validate(
        provider(transport=defs.HTTP, command=(), url="http://127.0.0.1:9/mcp", allow_local=True)
    )


def test_network_provider_needs_a_url(data_dir: Path):
    with pytest.raises(defs.ProviderDefinitionError, match="needs a url"):
        defs.validate(provider(transport=defs.HTTP, command=(), url=""))


# ---------------------------------------------------------------- registry


def test_register_and_lookup(data_dir: Path):
    reg(provider())
    assert mcp_registry.get("fixture_demo").provider_id == "fixture_demo"
    assert [p.provider_id for p in mcp_registry.list_providers()] == ["fixture_demo"]


def test_duplicate_provider_rejected(data_dir: Path):
    reg(provider())
    with pytest.raises(mcp_registry.ProviderRegistryError, match="already registered"):
        reg(provider())
    reg(provider(), replace=True)


def test_unregister(data_dir: Path):
    reg(provider())
    assert mcp_registry.unregister("fixture_demo", persist=False) is True
    assert mcp_registry.get("fixture_demo") is None
    assert mcp_registry.unregister("fixture_demo", persist=False) is False


def test_new_provider_is_not_trusted_by_default(data_dir: Path):
    """Discovery must never confer trust."""
    defn = defs.ProviderDefinition(
        provider_id="fresh_one", name="Fresh", command=(PY_BIN, str(DEMO_SERVER))
    )
    assert defn.trust == defs.UNTRUSTED
    assert defn.may_execute() is False
    assert "untrusted" in defn.unavailable_reason()


def test_trust_is_an_explicit_decision(data_dir: Path):
    reg(provider(trust=defs.UNTRUSTED))
    assert mcp_registry.get("fixture_demo").may_execute() is False
    mcp_registry.set_trust("fixture_demo", defs.TRUSTED)
    assert mcp_registry.get("fixture_demo").may_execute() is True
    with pytest.raises(mcp_registry.ProviderRegistryError, match="Unknown trust"):
        mcp_registry.set_trust("fixture_demo", "very")


def test_configured_trust_discovers_but_cannot_execute(data_dir: Path):
    """The middle state: look, don't touch."""
    defn = reg(provider(trust=defs.CONFIGURED))
    assert defn.may_discover() is True
    assert defn.may_execute() is False
    assert mcp.discover("fixture_demo")["status"] == mcp_engine.SUCCESS
    out = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})
    assert out["status"] == mcp_engine.DENIED
    assert "discovery only" in out["error"]


def test_persistence_round_trip(data_dir: Path):
    reg(provider(), persist=True)
    mcp_registry.reset()
    assert mcp_registry.get("fixture_demo") is None
    restored = mcp_registry.load_persisted()
    assert "fixture_demo" in restored
    assert mcp_registry.get("fixture_demo").trust == defs.TRUSTED


def test_store_lives_in_the_isolated_root(data_dir: Path):
    reg(provider(), persist=True)
    assert data_dir in mcp_store.DB_PATH.resolve().parents
    assert data_dir in mcp_secrets.SECRETS_FILE.resolve().parents


# --------------------------------------------------------------- discovery


def test_discovery_returns_real_protocol_data(demo):
    env = mcp.discover("fixture_demo")
    assert env["status"] == mcp_engine.SUCCESS
    snapshot = env["result"]
    assert snapshot["server_info"]["name"] == "aria-fixture"
    assert snapshot["capabilities"]["tools"] is True
    names = {t["name"] for t in snapshot["tools"]}
    assert {"lookup_doc", "add_numbers", "always_fails", "slow_op"} <= names
    # Schemas come from the provider and are kept for validation.
    add = next(t for t in snapshot["tools"] if t["name"] == "add_numbers")
    assert "properties" in add["input_schema"]


def test_resource_and_prompt_discovery(demo):
    snapshot = mcp.discover("fixture_demo")["result"]
    assert any(r["uri"] == "fixture://docs/tides" for r in snapshot["resources"])
    assert any(p["name"] == "summarise" for p in snapshot["prompts"])


def test_qualified_tool_listing(demo):
    reg(provider("second_demo"))
    mcp.discover("second_demo")
    tools = mcp.qualified_tools()
    names = {t["qualified_name"] for t in tools}
    assert "fixture_demo:add_numbers" in names
    assert "second_demo:add_numbers" in names, "providers must not shadow each other"
    high = next(t for t in tools if t["qualified_name"] == "fixture_demo:delete_everything")
    assert high["impact"] == defs.HIGH_IMPACT


def test_discovery_grants_no_execution(data_dir: Path):
    reg(provider(trust=defs.CONFIGURED))
    assert mcp.discover("fixture_demo")["status"] == mcp_engine.SUCCESS
    assert mcp.call_tool("fixture_demo", "lookup_doc", {"topic": "tides"})["status"] == (
        mcp_engine.DENIED
    )


def test_unknown_provider_is_unavailable(data_dir: Path):
    env = mcp.discover("nobody_here")
    assert env["status"] == mcp_engine.UNAVAILABLE
    assert env["error_kind"] == "unknown_provider"


# --------------------------------------------------------------- invocation


def test_tool_invocation_really_runs(demo):
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": 19, "b": 23})
    assert env["status"] == mcp_engine.SUCCESS
    assert env["result"]["text"] == "42"
    assert env["provenance"]["provider"] == "fixture_demo"
    assert env["provenance"]["content_state"] == "retrieved_unverified"


def test_envelope_has_every_required_field(demo):
    env = mcp.call_tool("fixture_demo", "lookup_doc", {"topic": "tides"})
    for field in (
        "provider_id",
        "operation",
        "target",
        "invocation_id",
        "requester",
        "skill_id",
        "mission_id",
        "status",
        "impact",
        "result",
        "error",
        "error_kind",
        "truncated",
        "provenance",
        "duration_ms",
        "side_effects",
    ):
        assert field in env, field


def test_provider_error_is_a_failure_not_a_success(demo):
    env = mcp.call_tool("fixture_demo", "always_fails", {"reason": "boom"})
    assert env["status"] == mcp_engine.FAILED
    assert env["ok"] is False
    assert env["result"] is None
    assert "boom" in (env["error"] or "")


def test_unknown_tool_fails_cleanly(demo):
    env = mcp.call_tool("fixture_demo", "no_such_tool", {})
    assert env["status"] in (mcp_engine.FAILED, mcp_engine.UNAVAILABLE)
    assert env["ok"] is False


def test_resource_retrieval(demo):
    env = mcp.read_resource("fixture_demo", "fixture://docs/roche")
    assert env["status"] == mcp_engine.SUCCESS
    assert "Roche limit" in env["result"]["contents"][0]["text"]
    assert env["provenance"]["uri"] == "fixture://docs/roche"


def test_prompt_is_content_not_execution(demo):
    env = mcp.get_prompt("fixture_demo", "summarise", {"topic": "tides"})
    assert env["status"] == mcp_engine.SUCCESS
    assert env["provenance"]["prompt_state"] == "content_not_executed"
    assert "Summarise" in env["result"]["messages"][0]["text"]


# -------------------------------------------------------- schema validation


def test_model_generated_arguments_are_validated(demo):
    """A model's arguments are checked against the provider's own schema first."""
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": "not a number", "b": 1})
    assert env["status"] == mcp_engine.INVALID
    assert env["error_kind"] == "schema"


def test_missing_required_argument_rejected(demo):
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1})
    assert env["status"] == mcp_engine.INVALID
    assert "missing required" in env["error"]


def test_undeclared_argument_rejected(demo):
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 2, "sneaky": True})
    assert env["status"] == mcp_engine.INVALID
    assert "undeclared" in env["error"]


def test_oversized_input_rejected(demo):
    env = mcp.call_tool(
        "fixture_demo", "lookup_doc", {"topic": "x" * (defs.BOUNDS["max_input_bytes"] + 10)}
    )
    assert env["status"] == mcp_engine.INVALID
    assert env["error_kind"] == "input_size"


def test_oversized_output_is_bounded(data_dir: Path):
    """One provider must not be able to hand ARIA unlimited data."""
    reg(provider(max_output_bytes=4096))
    mcp.discover("fixture_demo")
    env = mcp.call_tool("fixture_demo", "big_output", {"size": 200000})
    assert env["status"] == mcp_engine.SUCCESS
    assert env["truncated"] is True
    assert len(str(env["result"])) < 20000


# ------------------------------------------------------ failure and recovery


def test_provider_that_dies_during_handshake(data_dir: Path):
    reg(provider("crashy", server=CRASH_SERVER))
    env = mcp.discover("crashy")
    assert env["status"] == mcp_engine.UNAVAILABLE
    assert env["error_kind"] == "provider_unavailable"


def test_malformed_provider_is_a_protocol_failure(data_dir: Path):
    reg(provider("nonsense", server=MALFORMED_SERVER, timeout_s=8.0))
    env = mcp.discover("nonsense")
    assert env["status"] in (mcp_engine.UNAVAILABLE, mcp_engine.TIMEOUT)
    assert env["ok"] is False


def test_provider_crash_mid_operation_does_not_kill_aria(demo):
    env = mcp.call_tool("fixture_demo", "crash_now", {})
    assert env["ok"] is False
    assert env["status"] in (mcp_engine.UNAVAILABLE, mcp_engine.FAILED)
    # ARIA is still fine: the very next call succeeds against a fresh session.
    recovered = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})
    assert recovered["status"] == mcp_engine.SUCCESS


def test_timeout_is_bounded_and_truthful(data_dir: Path):
    reg(provider(timeout_s=1.0))
    mcp.discover("fixture_demo")
    env = mcp.call_tool("fixture_demo", "slow_op", {"seconds": 20})
    assert env["status"] == mcp_engine.TIMEOUT
    assert env["error_kind"] == "timeout"
    # ARIA stopped waiting; it does not claim the remote side stopped.
    assert env["provenance"]["remote_state"] == "unknown_after_timeout"


def test_health_tracks_failures(demo):
    mcp.call_tool("fixture_demo", "always_fails", {})
    detail = mcp.health("fixture_demo")
    assert detail["invocations"] >= 1
    assert detail["failures"] >= 1


def test_cancellation_before_invocation(demo):
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1}, cancel_check=lambda: True)
    assert env["status"] == mcp_engine.CANCELLED
    assert env["ok"] is False


# ------------------------------------------------------------- permissions


def test_disabled_provider_cannot_execute(data_dir: Path):
    reg(provider())
    mcp_registry.set_enabled("fixture_demo", False)
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})
    assert env["status"] == mcp_engine.DENIED
    assert "disabled" in env["error"]


def test_untrusted_provider_cannot_execute(data_dir: Path):
    reg(provider(trust=defs.UNTRUSTED))
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})
    assert env["status"] == mcp_engine.DENIED


def test_denied_tool_refused(data_dir: Path):
    reg(provider(denied_tools=("always_fails",)))
    mcp.discover("fixture_demo")
    assert mcp.call_tool("fixture_demo", "always_fails", {})["status"] == mcp_engine.DENIED
    assert mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})["status"] == (
        mcp_engine.SUCCESS
    )


def test_allow_list_restricts_tools(data_dir: Path):
    reg(provider(allowed_tools=("add_numbers",)))
    mcp.discover("fixture_demo")
    assert mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})["status"] == (
        mcp_engine.SUCCESS
    )
    assert mcp.call_tool("fixture_demo", "lookup_doc", {"topic": "tides"})["status"] == (
        mcp_engine.DENIED
    )


def test_provider_grants_nothing_until_an_agent_is_named(data_dir: Path):
    """A tool being exposed does not make it available to every agent."""
    reg(provider(allowed_agents=()))
    mcp.discover("fixture_demo")
    env = mcp.call_tool(
        "fixture_demo", "add_numbers", {"a": 1, "b": 1}, requester="research_specialist"
    )
    assert env["status"] == mcp_engine.DENIED
    assert "not permitted" in env["error"]


def test_denied_agent_beats_allow_list(data_dir: Path):
    reg(provider(allowed_agents=("research_specialist",), denied_agents=("analysis_specialist",)))
    mcp.discover("fixture_demo")
    assert (
        mcp.call_tool(
            "fixture_demo", "add_numbers", {"a": 1, "b": 1}, requester="research_specialist"
        )["status"]
        == mcp_engine.SUCCESS
    )
    assert (
        mcp.call_tool(
            "fixture_demo", "add_numbers", {"a": 1, "b": 1}, requester="analysis_specialist"
        )["status"]
        == mcp_engine.DENIED
    )


def test_agent_without_the_gate_is_denied(demo):
    """general_specialist may list providers but never invoke."""
    env = mcp.call_tool(
        "fixture_demo", "add_numbers", {"a": 1, "b": 1}, requester="general_specialist"
    )
    assert env["status"] == mcp_engine.DENIED


def test_unknown_agent_denied(demo):
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1}, requester="ghost")
    assert env["status"] == mcp_engine.DENIED
    assert "No such agent" in env["error"]


def test_high_impact_tool_needs_explicit_authorization(demo):
    env = mcp.call_tool(
        "fixture_demo", "delete_everything", {"confirm": True}, requester="research_specialist"
    )
    assert env["status"] == mcp_engine.DENIED
    assert "explicit authorization" in env["error"]
    allowed = mcp.call_tool(
        "fixture_demo", "delete_everything", {"confirm": True}, authorized_high_impact=True
    )
    assert allowed["status"] == mcp_engine.SUCCESS


def test_no_builtin_agent_may_run_high_impact_mcp(demo):
    for agent_id in (
        "research_specialist",
        "coding_specialist",
        "analysis_specialist",
        "general_specialist",
    ):
        env = mcp.call_tool(
            "fixture_demo",
            "delete_everything",
            {"confirm": True},
            requester=agent_id,
            authorized_high_impact=True,
        )
        assert env["status"] == mcp_engine.DENIED, agent_id


def test_provider_required_actions_must_be_held_by_the_agent(data_dir: Path):
    """A provider needing an ARIA action cannot lend it to the caller."""
    reg(provider(required_actions=("dev_command",)))
    mcp.discover("fixture_demo")
    assert (
        mcp.call_tool(
            "fixture_demo", "add_numbers", {"a": 1, "b": 1}, requester="coding_specialist"
        )["status"]
        == mcp_engine.SUCCESS
    )
    denied = mcp.call_tool(
        "fixture_demo", "add_numbers", {"a": 1, "b": 1}, requester="research_specialist"
    )
    assert denied["status"] == mcp_engine.DENIED
    assert "dev_command" in denied["error"]


def test_provider_cannot_invoke_arbitrary_aria_actions(demo):
    """There is no route from provider output back into the action registry."""
    import inspect

    from jarvis.mcp import client as client_mod

    for module in (mcp_engine, client_mod):
        source = inspect.getsource(module)
        assert "call_action" not in source, f"{module.__name__} can reach the action registry"


# ------------------------------------------------------------------ secrets


def test_secrets_are_not_persisted_in_the_audit_trail(data_dir: Path):
    reg(provider(), persist=True)
    mcp_secrets.set_provider_env("fixture_demo", {"API_TOKEN": "sk-live-do-not-leak-123456"})
    mcp.discover("fixture_demo")
    mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})

    raw = mcp_store.DB_PATH.read_bytes()
    assert b"sk-live-do-not-leak-123456" not in raw, "secret reached the audit database"
    row = mcp_store.get_provider("fixture_demo")
    assert "sk-live-do-not-leak-123456" not in str(row)


def test_provider_config_never_exposes_secret_values(data_dir: Path):
    reg(provider(env=(("API_TOKEN", "sk-super-secret-value"),)))
    detail = mcp.health("fixture_demo")
    assert "sk-super-secret-value" not in str(detail)
    mcp_secrets.set_provider_env("fixture_demo", {"OTHER": "top-secret"})
    detail = mcp.health("fixture_demo")
    assert detail["env_keys"] == ["OTHER"], "key names only"
    assert "top-secret" not in str(detail)


def test_secret_shaped_arguments_are_redacted(demo):
    env = mcp.call_tool("fixture_demo", "echo_credential", {"token": "sk-abcdefghijklmnop"})
    assert env["status"] == mcp_engine.SUCCESS
    assert "sk-abcdefghijklmnop" not in str(env["arguments"])
    record = mcp_store.get_invocation(env["invocation_id"])
    assert "sk-abcdefghijklmnop" not in str(record)


def test_provider_env_is_not_the_whole_aria_environment(data_dir: Path, monkeypatch):
    """A third-party process must not inherit tokens held for other integrations."""
    monkeypatch.setenv("SOME_OTHER_API_KEY", "must-not-be-inherited")
    env = mcp_client._stdio_env(provider())
    assert "SOME_OTHER_API_KEY" not in env
    assert "PATH" in env


# ------------------------------------------------------------- integration


def _call(action: str, params: dict, assistant=None):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    return call_action(assistant, action, params, action)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "mcp_repo"
    repo.mkdir()
    (repo / "mod.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (repo / "test_mod.py").write_text(
        "from mod import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8"
    )
    for args in (
        ["init", "-q"],
        ["config", "user.email", "t@e.com"],
        ["config", "user.name", "T"],
        ["add", "."],
        ["commit", "-qm", "initial"],
    ):
        subprocess.run(["git", *args], cwd=str(repo), capture_output=True, timeout=30)
    return repo


def test_mcp_actions_are_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {a["action"] for a in all_actions()}
    for action in (
        "mcp_provider_list",
        "mcp_provider_status",
        "mcp_discover",
        "mcp_tools",
        "mcp_invoke",
        "mcp_invoke_high_impact",
        "mcp_resource",
        "mcp_prompt",
        "mcp_set_trust",
        "mcp_history",
        "mcp_step",
    ):
        assert action in names, action


def test_earlier_milestone_actions_survive(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {a["action"] for a in all_actions()}
    for action in (
        "mission_create",
        "research_create",
        "evidence_verify",
        "collab_delegate",
        "browser_use_act",
        "dev_task_create",
        "skill_invoke",
        "skill_discover",
    ):
        assert action in names, action


def test_action_to_mcp(demo):
    """action → MCP, through the real registry."""
    out = _call(
        "mcp_invoke",
        {"provider_id": "fixture_demo", "tool": "add_numbers", "arguments": {"a": 20, "b": 22}},
    )
    assert out["ok"] is True
    assert out["envelope"]["result"]["text"] == "42"


def test_action_reports_failure_as_failure(demo):
    out = _call(
        "mcp_invoke", {"provider_id": "fixture_demo", "tool": "always_fails", "arguments": {}}
    )
    assert out["ok"] is False
    assert out["envelope"]["status"] == mcp_engine.FAILED


def test_qualified_name_addressing(demo):
    out = _call(
        "mcp_invoke", {"qualified_name": "fixture_demo:add_numbers", "arguments": {"a": 1, "b": 2}}
    )
    assert out["ok"] is True
    assert out["envelope"]["result"]["text"] == "3"
    bad = _call("mcp_invoke", {"qualified_name": "no_colon", "arguments": {}})
    assert bad["ok"] is False


def test_high_impact_gate_action_is_not_an_operation(data_dir: Path):
    out = _call("mcp_invoke_high_impact", {})
    assert out["ok"] is False
    assert out["error_kind"] == "gate_only"


def test_skill_to_mcp(demo):
    """skill → MCP, with the skill's permission chain intact."""
    mcp.ensure_mcp_skills_loaded()
    env = skills.execute(
        "mcp_tool_call",
        {"provider_id": "fixture_demo", "tool": "lookup_doc", "arguments": {"topic": "tides"}},
        requester="research_specialist",
    )
    assert env["status"] == skills.SUCCESS
    assert "gravitational" in env["output"]["result"]["text"]
    assert env["output"]["provenance"]["provider"] == "fixture_demo"
    assert env["side_effects"], "external tool use is a side effect worth recording"


def test_skill_cannot_escalate_through_mcp(data_dir: Path):
    """The skill chain cannot reach a provider its caller may not use."""
    reg(provider(allowed_agents=("coding_specialist",)))
    mcp.discover("fixture_demo")
    mcp.ensure_mcp_skills_loaded()
    env = skills.execute(
        "mcp_tool_call",
        {"provider_id": "fixture_demo", "tool": "add_numbers", "arguments": {"a": 1, "b": 1}},
        requester="research_specialist",
    )
    assert env["status"] == skills.DENIED


def test_skill_denied_when_provider_excludes_the_skill(demo):
    reg(provider(allowed_skills=("some_other_skill",)), replace=True)
    mcp.discover("fixture_demo")
    mcp.ensure_mcp_skills_loaded()
    env = skills.execute(
        "mcp_tool_call",
        {"provider_id": "fixture_demo", "tool": "add_numbers", "arguments": {"a": 1, "b": 1}},
        requester="research_specialist",
    )
    assert env["status"] == skills.DENIED


def test_agent_to_mcp_through_the_agent_framework(demo):
    """agent → MCP, with the agent's own permissions applied."""
    out = agents.invoke(
        "research_specialist",
        "look something up",
        action="mcp_invoke",
        params={
            "provider_id": "fixture_demo",
            "tool": "lookup_doc",
            "arguments": {"topic": "roche"},
        },
    )
    assert out["ok"] is True
    assert out["result"]["envelope"]["requester"] == "research_specialist"
    assert "Roche" in out["result"]["envelope"]["result"]["text"]


def test_general_specialist_denied_invocation(demo):
    out = agents.invoke(
        "general_specialist",
        "try",
        action="mcp_invoke",
        params={
            "provider_id": "fixture_demo",
            "tool": "add_numbers",
            "arguments": {"a": 1, "b": 1},
        },
    )
    assert out["ok"] is False
    assert out["error_kind"] == "permission_denied"


def test_agent_cannot_spoof_the_requester(demo):
    """An agent must not borrow another identity, or operator context."""
    reg(provider(allowed_agents=("coding_specialist",)), replace=True)
    mcp.discover("fixture_demo")
    out = agents.invoke(
        "research_specialist",
        "borrow authority",
        action="mcp_invoke",
        params={
            "provider_id": "fixture_demo",
            "tool": "add_numbers",
            "arguments": {"a": 1, "b": 1},
            "requester": "",
        },
    )
    envelope = out["result"]["envelope"]
    assert envelope["requester"] == "research_specialist"
    assert envelope["status"] == mcp_engine.DENIED


def test_mission_to_mcp(demo):
    """mission → MCP, using the existing mission engine only."""
    from jarvis import missions

    mission_id = missions.create_mission(
        "look up tides via MCP",
        steps=[
            {
                "name": "mcp",
                "action": "mcp_step",
                "params": {
                    "provider_id": "fixture_demo",
                    "operation": "tool",
                    "tool": "lookup_doc",
                    "arguments": {"topic": "tides"},
                },
            }
        ],
        kind="mcp",
    )
    missions.run(mission_id, missions.ActionStepRunner(None))
    assert missions.status(mission_id)["state"] == missions.COMPLETED
    assert missions.checkpoints(mission_id)
    rows = mcp.history(provider_id="fixture_demo")
    assert rows[0]["status"] == mcp_engine.SUCCESS


def test_mission_cancellation_reaches_mcp(demo):
    """mission cancel → MCP invocation refused before contacting the provider."""
    from jarvis import missions
    from jarvis.missions import store as mstore

    mission_id = missions.create_mission(
        "cancelled MCP work",
        steps=[
            {
                "name": "mcp",
                "action": "mcp_step",
                "params": {
                    "provider_id": "fixture_demo",
                    "operation": "tool",
                    "tool": "slow_op",
                    "arguments": {"seconds": 30},
                },
            }
        ],
        kind="mcp",
    )
    mstore.request_cancel(mission_id)
    # Running the mission must stop at the cancelled step rather than calling
    # the provider, and must land in CANCELLED rather than COMPLETED.
    missions.run(mission_id, missions.ActionStepRunner(None))
    assert missions.status(mission_id)["state"] == missions.CANCELLED
    # The provider was never contacted at all, which is the strongest form of
    # cancellation: no slow_op invocation exists.
    assert not [r for r in mcp.history(provider_id="fixture_demo") if r["target"] == "slow_op"]

    # And a cancellation observed mid-step is reported as cancelled, not success.
    direct = mcp.call_tool(
        "fixture_demo",
        "add_numbers",
        {"a": 1, "b": 1},
        mission_id=mission_id,
        cancel_check=lambda: True,
    )
    assert direct["status"] == mcp_engine.CANCELLED
    assert direct["ok"] is False


def test_mission_recovers_after_provider_failure(demo):
    """WORKFLOW E: provider failure inside a mission ends in a truthful state."""
    from jarvis import missions

    mission_id = missions.create_mission(
        "failing MCP work",
        steps=[
            {
                "name": "mcp",
                "action": "mcp_step",
                "params": {
                    "provider_id": "fixture_demo",
                    "operation": "tool",
                    "tool": "always_fails",
                    "arguments": {},
                },
            }
        ],
        kind="mcp",
    )
    missions.run(mission_id, missions.ActionStepRunner(None))
    final = missions.status(mission_id)
    assert final["state"] != missions.COMPLETED, "a failed provider call completed the mission"
    assert mcp.history(provider_id="fixture_demo")[0]["status"] == mcp_engine.FAILED


def test_research_and_evidence_from_mcp(demo, data_dir: Path):
    """WORKFLOW B: MCP resource → evidence → claim, with provenance and no free verification."""
    from jarvis import evidence as ev

    env = mcp.read_resource("fixture_demo", "fixture://docs/tides", requester="research_specialist")
    assert env["status"] == mcp_engine.SUCCESS

    recorded = mcp.record_resource_evidence(
        env, context_id="mcp_ctx", claim_text="Tides come from gravitational gradients"
    )
    assert recorded["recorded"] is True
    assert recorded["provenance"]["chain"] == [
        "provider",
        "resource",
        "retrieved_content",
        "evidence",
        "claim",
    ]
    assert recorded["verification"] == "none"

    # Retrieval is not verification: one source cannot satisfy independence.
    verdict = ev.verify(recorded["claim_id"], method=ev.INDEPENDENT_SOURCES)
    assert verdict["result"] != "verified"


def test_failed_retrieval_never_becomes_evidence(demo):
    """Milestone 7's anti-fabrication rule holds across the MCP boundary."""
    env = mcp.read_resource(
        "fixture_demo", "fixture://does/not/exist", requester="research_specialist"
    )
    assert env["status"] != mcp_engine.SUCCESS
    recorded = mcp.record_resource_evidence(env, context_id="mcp_ctx2")
    assert recorded["recorded"] is False
    assert "retrieval" in recorded["reason"]


def test_coding_agent_uses_mcp_within_its_confinement(demo, fixture_repo: Path):
    """WORKFLOW C: Coding Agent → MCP documentation lookup, boundaries intact."""
    from jarvis.dev_agent import engine as dev_engine

    task = dev_engine.create_task("use mcp docs", str(fixture_repo))
    assert task["id"]
    env = mcp.call_tool(
        "fixture_demo", "lookup_doc", {"topic": "roche"}, requester="coding_specialist"
    )
    assert env["status"] == mcp_engine.SUCCESS

    coder = agents.get("coding_specialist")
    for forbidden in (
        "mcp_invoke_high_impact",
        "mcp_set_trust",
        "browser_use_read",
        "evidence_verify",
        "research_create",
    ):
        assert coder.permits(forbidden) is False


def test_collaboration_preserves_mcp_provenance(demo):
    """WORKFLOW D: delegation keeps requester, agent and provider identity."""
    from jarvis import collaboration

    created = collaboration.create_collaboration(
        "find reference material", initiator="analysis_specialist"
    )
    task_id = collaboration.delegate(
        created["collaboration_id"],
        requester="analysis_specialist",
        objective="look up tides",
        target="research_specialist",
    )
    assert task_id
    out = agents.invoke(
        "research_specialist",
        "look up tides",
        action="mcp_invoke",
        params={
            "provider_id": "fixture_demo",
            "tool": "lookup_doc",
            "arguments": {"topic": "tides"},
        },
    )
    envelope = out["result"]["envelope"]
    assert envelope["status"] == mcp_engine.SUCCESS
    assert envelope["requester"] == "research_specialist"
    assert envelope["provenance"]["provider"] == "fixture_demo"


def test_browser_safety_is_not_weakened_by_mcp(data_dir: Path):
    """MCP must not become a second, laxer network path."""
    from jarvis.computer_use.actions import NavigationBlocked, check_url

    with pytest.raises(NavigationBlocked):
        check_url("http://169.254.169.254/latest/meta-data/")
    with pytest.raises(defs.ProviderDefinitionError):
        defs.validate(provider(transport=defs.HTTP, command=(), url="http://169.254.169.254/mcp"))


def test_workflow_a_discovery_to_invocation(data_dir: Path):
    """WORKFLOW A: discover → inspect schema → invoke → structured result."""
    reg(provider(trust=defs.CONFIGURED))
    discovered = _call("mcp_discover", {"provider_id": "fixture_demo"})
    assert discovered["ok"] is True
    tools = _call("mcp_tools", {"provider_id": "fixture_demo"})
    add = next(t for t in tools["tools"] if t["tool"] == "add_numbers")
    assert "properties" in add["input_schema"]
    assert add["available"] is False, "discovery alone must not make a tool runnable"

    mcp_registry.set_trust("fixture_demo", defs.TRUSTED)
    result = _call(
        "mcp_invoke",
        {"provider_id": "fixture_demo", "tool": "add_numbers", "arguments": {"a": 40, "b": 2}},
    )
    assert result["ok"] is True
    assert result["envelope"]["result"]["text"] == "42"


def test_workflow_f_slow_tool_cancellation(data_dir: Path):
    """WORKFLOW F: a slow provider is bounded rather than hanging ARIA."""
    reg(provider(timeout_s=1.0))
    mcp.discover("fixture_demo")
    env = mcp.call_tool("fixture_demo", "slow_op", {"seconds": 30})
    assert env["status"] == mcp_engine.TIMEOUT
    # ARIA is immediately usable again.
    assert (
        mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1}, timeout=20)["status"]
        == mcp_engine.SUCCESS
    )


def test_no_orphan_provider_processes(demo):
    """A finished session must not leave a subprocess behind."""
    import time as _t

    before = subprocess.run(
        ["pgrep", "-fc", "demo_server.py"], capture_output=True, text=True
    ).stdout.strip()
    for _ in range(3):
        mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})
    _t.sleep(1.5)
    after = subprocess.run(
        ["pgrep", "-fc", "demo_server.py"], capture_output=True, text=True
    ).stdout.strip()
    assert after == before, f"provider processes leaked: {before} -> {after}"


def test_history_and_observability(demo):
    mcp.call_tool("fixture_demo", "add_numbers", {"a": 1, "b": 1})
    rows = mcp.history(provider_id="fixture_demo")
    assert rows and rows[0]["provider_id"] == "fixture_demo"
    out = _call("mcp_history", {"invocation_id": rows[0]["id"]})
    assert out["ok"] is True

    detail = mcp.health("fixture_demo")
    for field in (
        "provider_id",
        "trust",
        "enabled",
        "health",
        "invocations",
        "failures",
        "capabilities",
        "tool_count",
        "may_execute",
        "unavailable_reason",
    ):
        assert field in detail, field


def test_provider_registration_through_the_action_layer(data_dir: Path):
    """Regression: a provider could not be configured from the running service."""
    out = _call(
        "mcp_provider_register",
        {
            "provider_id": "live_style",
            "name": "Live Style",
            "command": [PY_BIN, str(DEMO_SERVER)],
            "allowed_agents": ["research_specialist"],
        },
    )
    assert out["ok"] is True
    # Registration never confers trust.
    assert out["provider"]["trust"] == defs.UNTRUSTED
    assert mcp.call_tool("live_style", "add_numbers", {"a": 1, "b": 1})["status"] == (
        mcp_engine.DENIED
    )
    _call("mcp_set_trust", {"provider_id": "live_style", "trust": defs.TRUSTED})
    mcp.discover("live_style")
    assert mcp.call_tool("live_style", "add_numbers", {"a": 1, "b": 1})["status"] == (
        mcp_engine.SUCCESS
    )


def test_registration_refuses_a_shell_string(data_dir: Path):
    out = _call("mcp_provider_register", {"provider_id": "shelly", "command": "rm -rf /"})
    assert out["ok"] is False
    assert out["error_kind"] == "command_form"


def test_registration_refuses_an_unapproved_binary(data_dir: Path):
    out = _call("mcp_provider_register", {"provider_id": "curly", "command": ["curl", "x"]})
    assert out["ok"] is False
    assert out["error_kind"] == "invalid_provider"


def test_registration_stores_env_as_keys_only(data_dir: Path):
    out = _call(
        "mcp_provider_register",
        {
            "provider_id": "with_env",
            "command": [PY_BIN, str(DEMO_SERVER)],
            "env": {"API_TOKEN": "sk-should-never-surface-9999"},
        },
    )
    assert out["ok"] is True
    assert out["env_keys"] == ["API_TOKEN"]
    assert "sk-should-never-surface-9999" not in str(out)
    assert "sk-should-never-surface-9999" not in mcp_store.DB_PATH.read_bytes().decode(
        "utf-8", "ignore"
    )


def test_persisted_providers_are_restored_into_a_fresh_process(data_dir: Path):
    """Regression: nothing called load_persisted, so config vanished on restart."""
    _call(
        "mcp_provider_register", {"provider_id": "survivor", "command": [PY_BIN, str(DEMO_SERVER)]}
    )
    mcp_registry.reset()
    import jarvis.mcp as mcp_pkg

    mcp_pkg._skills_loaded = False  # simulate a fresh process
    _call("mcp_provider_list", {})
    assert mcp_registry.get("survivor") is not None, "configuration did not survive"


def test_provider_removal_clears_secrets(data_dir: Path):
    _call(
        "mcp_provider_register",
        {
            "provider_id": "temporary",
            "command": [PY_BIN, str(DEMO_SERVER)],
            "env": {"TOKEN": "sk-temp-value-1234"},
        },
    )
    assert mcp_secrets.env_keys("temporary") == ["TOKEN"]
    out = _call("mcp_provider_remove", {"provider_id": "temporary"})
    assert out["ok"] is True
    assert mcp_secrets.env_keys("temporary") == []


def test_no_agent_may_configure_providers(data_dir: Path):
    """Configuration is an operator action, not something an agent can do."""
    from jarvis.specialized_agents import definitions as agent_defs

    for agent in agent_defs.BUILTIN_AGENTS:
        for action in ("mcp_provider_register", "mcp_provider_remove", "mcp_set_trust"):
            assert agent.permits(action) is False, f"{agent.id} may {action}"


def test_operator_http_routes(chat_app, data_dir: Path):
    """The operator path an agent deliberately does not have."""
    res = chat_app.post(
        "/api/mcp/providers",
        data={
            "provider_id": "route_fixture",
            "command": f'["{PY_BIN}", "{DEMO_SERVER}"]',
            "allowed_agents": '["research_specialist"]',
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["provider"]["trust"] == defs.UNTRUSTED

    listed = chat_app.get("/api/mcp/providers").json()
    assert any(p["provider_id"] == "route_fixture" for p in listed["providers"])

    trusted = chat_app.post(
        "/api/mcp/providers/route_fixture/trust", data={"trust": defs.TRUSTED}
    ).json()
    assert trusted["ok"] is True
    assert mcp_registry.get("route_fixture").may_execute() is True

    removed = chat_app.delete("/api/mcp/providers/route_fixture").json()
    assert removed["ok"] is True
    assert mcp_registry.get("route_fixture") is None


def test_operator_route_rejects_unsafe_configuration(chat_app, data_dir: Path):
    bad = chat_app.post(
        "/api/mcp/providers",
        data={
            "provider_id": "bad_one",
            "command": '["curl", "http://evil.example"]',
        },
    ).json()
    assert bad["ok"] is False
    assert bad["error_kind"] == "invalid_provider"

    ssrf = chat_app.post(
        "/api/mcp/providers",
        data={
            "provider_id": "ssrf_one",
            "transport": "http",
            "url": "http://169.254.169.254/mcp",
        },
    ).json()
    assert ssrf["ok"] is False


def test_cancellation_ends_an_in_flight_wait_promptly(data_dir: Path):
    """Regression, found live: a cancelled call still waited the full timeout.

    ARIA cannot make a remote provider stop, but it must stop waiting as soon
    as the work is cancelled rather than sitting until its own timeout.
    """
    import time as _t

    reg(provider(timeout_s=25.0))
    mcp.discover("fixture_demo")
    cancelled_at = _t.monotonic() + 1.0
    started = _t.monotonic()
    env = mcp.call_tool(
        "fixture_demo",
        "slow_op",
        {"seconds": 20},
        cancel_check=lambda: _t.monotonic() > cancelled_at,
    )
    elapsed = _t.monotonic() - started
    assert env["status"] == mcp_engine.CANCELLED
    assert env["ok"] is False
    assert elapsed < 10, f"waited {elapsed:.1f}s instead of stopping on cancellation"
    # It does not claim the provider stopped, only that ARIA did.
    assert env["provenance"]["remote_state"] == "unknown_after_cancel"


def test_failed_skill_does_not_complete_its_mission(data_dir: Path):
    """Regression, found live: a failing skill step completed the mission.

    The mission runner treats a returned dict as a completed step, so a skill
    that failed was recorded as work successfully done.
    """
    from jarvis import missions

    def boom(ctx, params):
        raise RuntimeError("skill failed")

    skill_registry.register(
        skills.SkillDefinition(
            skill_id="failing_probe", name="Failing Probe", description="always fails"
        ),
        boom,
        replace=True,
    )
    out = _call("skill_invoke", {"skill_id": "failing_probe", "inputs": {}, "mission": True})
    mission_id = out["mission_id"]
    missions.run(mission_id, missions.ActionStepRunner(None))
    final = missions.status(mission_id)
    assert final["state"] != missions.COMPLETED, "a failed skill completed its mission"
    assert final["state"] == missions.FAILED


def test_cancelled_skill_mission_lands_cancelled_not_failed(data_dir: Path):
    from jarvis import missions
    from jarvis.missions import store as mstore

    skill_registry.register(
        skills.SkillDefinition(skill_id="slow_probe", name="Slow Probe", description="slow"),
        lambda ctx, p: {"done": True},
        replace=True,
    )
    out = _call("skill_invoke", {"skill_id": "slow_probe", "inputs": {}, "mission": True})
    mission_id = out["mission_id"]
    mstore.request_cancel(mission_id)
    missions.run(mission_id, missions.ActionStepRunner(None))
    assert missions.status(mission_id)["state"] == missions.CANCELLED


def test_cancelled_mcp_call_cancels_the_mission_rather_than_failing_it(data_dir: Path):
    """Regression, found live: a cancelled MCP call landed the mission as failed.

    Cancelled is not failed. Collapsing the two reports work that was
    deliberately called off as work that broke.
    """
    from jarvis import missions
    from jarvis.missions import store as mstore

    reg(provider(timeout_s=25.0))
    mcp.discover("fixture_demo")
    mcp.ensure_mcp_skills_loaded()

    out = _call(
        "skill_invoke",
        {
            "skill_id": "mcp_tool_call",
            "mission": True,
            "inputs": {
                "provider_id": "fixture_demo",
                "tool": "slow_op",
                "arguments": {"seconds": 20},
            },
        },
    )
    mission_id = out["mission_id"]
    mstore.request_cancel(mission_id)
    missions.run(mission_id, missions.ActionStepRunner(None))

    assert missions.status(mission_id)["state"] == missions.CANCELLED
    rows = [r for r in mcp.history(provider_id="fixture_demo") if r["mission_id"] == mission_id]
    assert not [r for r in rows if r["status"] == mcp_engine.SUCCESS]


def test_cancelled_mcp_call_reports_cancelled_through_the_skill(data_dir: Path):
    reg(provider(timeout_s=25.0))
    mcp.discover("fixture_demo")
    mcp.ensure_mcp_skills_loaded()
    env = skills.execute(
        "mcp_tool_call",
        {"provider_id": "fixture_demo", "tool": "slow_op", "arguments": {"seconds": 20}},
        requester="research_specialist",
        cancel_check=lambda: True,
    )
    assert env["status"] == skills.CANCELLED
    assert env["ok"] is False


def test_mcp_skills_are_present_without_a_prior_mcp_action(data_dir: Path):
    """Regression, found live: the MCP skills only existed after an MCP action.

    A freshly restarted process answered "No such skill: mcp_tool_call" until
    something happened to touch the MCP layer first.
    """
    import jarvis.mcp as mcp_pkg

    skill_registry.reset()
    mcp_pkg._skills_loaded = False  # a fresh process

    listed = _call("skill_catalog", {})
    assert listed["ok"] is True
    ids = {r["skill_id"] for r in listed["skills"]}
    assert {"mcp_tool_call", "mcp_fetch_resource"} <= ids

    skill_registry.reset()
    mcp_pkg._skills_loaded = False
    described = _call("skill_describe", {"skill_id": "mcp_tool_call"})
    assert described["ok"] is True

    skill_registry.reset()
    mcp_pkg._skills_loaded = False
    reg(provider())
    mcp.discover("fixture_demo")
    queued = _call(
        "skill_invoke",
        {
            "skill_id": "mcp_tool_call",
            "mission": True,
            "inputs": {
                "provider_id": "fixture_demo",
                "tool": "add_numbers",
                "arguments": {"a": 1, "b": 1},
            },
        },
    )
    assert queued["ok"] is True, queued.get("message")
    assert queued["mission_id"]


def test_cwd_traversal_refused(data_dir: Path):
    """Regression, found live: a traversal cwd was accepted because it resolved."""
    with pytest.raises(defs.ProviderDefinitionError, match="must not contain"):
        defs.validate(provider(cwd="/../../etc"))
    with pytest.raises(defs.ProviderDefinitionError, match="must be absolute"):
        defs.validate(provider(cwd="relative/dir"))
    defs.validate(provider(cwd=str(data_dir)))


def test_schema_is_enforced_even_without_a_cached_discovery(data_dir: Path):
    """Regression, found live: after a restart there was no cached schema, so
    model-generated arguments went to the provider entirely unchecked."""
    reg(provider())
    # Deliberately no discover() call: this is the freshly-restarted state.
    assert mcp_registry.cached_discovery("fixture_demo") is None
    env = mcp.call_tool("fixture_demo", "add_numbers", {"a": "not a number", "b": 1})
    assert env["status"] == mcp_engine.INVALID
    assert env["error_kind"] == "schema"


def test_provider_secret_values_are_scrubbed_whatever_their_shape(data_dir: Path):
    """Regression, found live: a token that did not look credential-shaped
    survived redaction and reached the audit database in a tool result."""
    token = "sk-live-milestone11-must-never-appear-99"
    reg(provider(), persist=True)
    mcp_secrets.set_provider_env("fixture_demo", {"PROVIDER_TOKEN": token})
    mcp.discover("fixture_demo")

    env = mcp.call_tool("fixture_demo", "echo_credential", {"token": token})
    assert env["status"] == mcp_engine.SUCCESS
    assert token not in json.dumps(env), "secret survived in the envelope"

    record = mcp_store.get_invocation(env["invocation_id"])
    assert token not in json.dumps(record), "secret reached the audit record"
    assert token.encode() not in mcp_store.DB_PATH.read_bytes(), "secret reached the database"


def test_generic_redaction_still_applies(demo):
    """The shaped-secret rules keep working alongside the literal scrub."""
    env = mcp.call_tool("fixture_demo", "echo_credential", {"token": "sk-abcdefghijklmnop"})
    assert "sk-abcdefghijklmnop" not in json.dumps(env["arguments"])
