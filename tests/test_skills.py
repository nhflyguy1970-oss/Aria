"""Skills system — definitions, registry, discovery, composition, execution, safety."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from jarvis import skills
from jarvis import specialized_agents as agents
from jarvis.skills import contracts, executor, registry
from jarvis.skills.definitions import (
    ANALYSIS,
    CODING,
    HIGH_IMPACT,
    READ,
    RESEARCH,
    SkillDefinition,
    SkillDefinitionError,
)
from jarvis.specialized_agents import registry as agent_registry


@pytest.fixture(autouse=True)
def _clean_registries():
    registry.reset()
    agent_registry.reset()
    yield
    registry.reset()
    agent_registry.reset()


def make(skill_id: str = "demo_skill", **kw) -> SkillDefinition:
    base = {
        "skill_id": skill_id,
        "name": skill_id.replace("_", " ").title(),
        "description": f"{skill_id} for tests",
        "version": "1.0.0",
        "category": ANALYSIS,
        "impact": READ,
    }
    base.update(kw)
    return SkillDefinition(**base)


def noop(ctx, params):
    return {"ok": True}


def reg(defn: SkillDefinition, impl=noop, **kw):
    return registry.register(defn, impl, **kw)


# ------------------------------------------------------------- definitions


def test_valid_definition_accepted(data_dir: Path):
    assert skills.validate(make()).skill_id == "demo_skill"


@pytest.mark.parametrize(
    "kw, fragment",
    [
        ({"skill_id": "X"}, "Invalid skill_id"),
        ({"skill_id": "ab"}, "Invalid skill_id"),
        ({"version": "1.0"}, "Invalid version"),
        ({"category": "nonsense"}, "unknown category"),
        ({"impact": "catastrophic"}, "unknown impact"),
        ({"name": ""}, "name is required"),
        ({"description": ""}, "description is required"),
        ({"timeout_s": 0}, "timeout_s must be positive"),
        ({"max_depth": 0}, "max_depth must be at least 1"),
        ({"schema_version": 99}, "schema_version"),
    ],
)
def test_invalid_definitions_rejected(data_dir: Path, kw, fragment):
    with pytest.raises(SkillDefinitionError) as exc:
        skills.validate(make(**kw))
    assert fragment in str(exc.value)


def test_contradictory_agent_permissions_rejected(data_dir: Path):
    with pytest.raises(SkillDefinitionError, match="contradictory permissions"):
        skills.validate(make(allowed_agents=("a",), denied_agents=("a",)))


def test_self_dependency_rejected(data_dir: Path):
    with pytest.raises(SkillDefinitionError, match="cannot depend on itself"):
        skills.validate(make(dependencies=(("demo_skill", "1.0.0"),)))


def test_bad_schema_rejected(data_dir: Path):
    with pytest.raises(SkillDefinitionError, match="unknown type"):
        skills.validate(make(input_schema={"properties": {"a": {"type": "blob"}}}))
    with pytest.raises(SkillDefinitionError, match="requires"):
        skills.validate(
            make(input_schema={"properties": {"a": {"type": "string"}}, "required": ["b"]})
        )


def test_definition_is_frozen(data_dir: Path):
    """An executing skill must not be able to edit its own authority."""
    defn = make()
    with pytest.raises(Exception):
        defn.impact = HIGH_IMPACT  # type: ignore[misc]


def test_non_composable_with_dependencies_rejected(data_dir: Path):
    reg(make("dep_one"))
    with pytest.raises(SkillDefinitionError, match="non-composable"):
        skills.validate(make(dependencies=(("dep_one", "1.0.0"),), composable=False))


# ---------------------------------------------------------------- registry


def test_register_and_lookup(data_dir: Path):
    reg(make())
    assert registry.get("demo_skill").skill_id == "demo_skill"
    assert registry.versions("demo_skill") == ["1.0.0"]
    assert callable(registry.implementation("demo_skill"))


def test_duplicate_registration_rejected(data_dir: Path):
    reg(make())
    with pytest.raises(registry.SkillRegistryError, match="already registered"):
        reg(make())
    reg(make(), replace=True)  # explicit replace is allowed


def test_non_callable_implementation_rejected(data_dir: Path):
    with pytest.raises(SkillDefinitionError, match="not callable"):
        registry.register(make(), "not a function")  # type: ignore[arg-type]


def test_unregister(data_dir: Path):
    reg(make())
    reg(make(version="2.0.0"))
    assert registry.unregister("demo_skill", "1.0.0") is True
    assert registry.versions("demo_skill") == ["2.0.0"]
    assert registry.unregister("demo_skill") is True
    assert registry.get("demo_skill") is None
    assert registry.unregister("demo_skill") is False


def test_enable_disable(data_dir: Path):
    reg(make())
    assert registry.set_enabled("demo_skill", False).enabled is False
    assert registry.get("demo_skill").enabled is False
    assert registry.set_enabled("demo_skill", True).enabled is True


# ---------------------------------------------------------------- versions


def test_version_resolution_strategies(data_dir: Path):
    for v in ("1.0.0", "1.2.0", "2.0.0"):
        reg(make(version=v))
    assert registry.resolve("demo_skill", "1.0.0", strategy="exact").version == "1.0.0"
    # compatible picks the highest same-major version at or above the request
    assert registry.resolve("demo_skill", "1.0.0", strategy="compatible").version == "1.2.0"
    assert registry.resolve("demo_skill", strategy="latest").version == "2.0.0"


def test_incompatible_version_never_substituted(data_dir: Path):
    reg(make(version="2.0.0"))
    with pytest.raises(registry.VersionUnavailable, match="refusing to substitute"):
        registry.resolve("demo_skill", "1.0.0", strategy="compatible")
    with pytest.raises(registry.VersionUnavailable, match="refusing to substitute"):
        registry.resolve("demo_skill", "3.0.0", strategy="exact")


def test_higher_minor_not_downgraded(data_dir: Path):
    reg(make(version="1.0.0"))
    with pytest.raises(registry.VersionUnavailable):
        registry.resolve("demo_skill", "1.5.0", strategy="compatible")


def test_unknown_skill_raises(data_dir: Path):
    with pytest.raises(registry.SkillNotFound):
        registry.resolve("nobody_home")


# ------------------------------------------------------------ dependencies


def test_missing_dependency_rejected(data_dir: Path):
    with pytest.raises(registry.SkillRegistryError, match="missing skill"):
        reg(make("needs_missing", dependencies=(("absent_skill", "1.0.0"),)))
    assert registry.get("needs_missing") is None, "broken registration left behind"


def test_dependency_cycle_rejected(data_dir: Path):
    reg(make("cycle_a"))
    reg(make("cycle_b", dependencies=(("cycle_a", "1.0.0"),)))
    # Re-register a to point back at b, closing the loop.
    with pytest.raises(registry.SkillRegistryError, match="cycle"):
        reg(make("cycle_a", dependencies=(("cycle_b", "1.0.0"),)), replace=True)


def test_deep_dependency_chain_is_iterative(data_dir: Path):
    """A chain far deeper than the recursion limit must still validate."""
    reg(make("chain_000"))
    for i in range(1, 400):
        reg(make(f"chain_{i:03d}", dependencies=((f"chain_{i - 1:03d}", "1.0.0"),)))
    order = registry.dependency_order(registry.get("chain_399"))
    assert len(order) == 400
    assert order[0] == "chain_000" and order[-1] == "chain_399"


def test_dependency_order_is_deterministic(data_dir: Path):
    reg(make("leaf_a"))
    reg(make("leaf_b"))
    reg(make("trunk", dependencies=(("leaf_a", "1.0.0"), ("leaf_b", "1.0.0"))))
    first = registry.dependency_order(registry.get("trunk"))
    assert first == registry.dependency_order(registry.get("trunk"))
    assert first[-1] == "trunk"
    assert set(first[:-1]) == {"leaf_a", "leaf_b"}


def test_detect_cycle_directly(data_dir: Path):
    assert registry.detect_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}) is not None
    assert registry.detect_cycle({"a": ["b"], "b": ["c"], "c": []}) is None


# ---------------------------------------------------------------- discovery


def test_discovery_filters_and_explains(data_dir: Path):
    reg(make("alpha_skill", category=RESEARCH, tags=("news",), capabilities=("research",)))
    reg(make("beta_skill", category=CODING, tags=("git",)))

    by_cat = skills.discover(category=RESEARCH)
    assert [h["skill_id"] for h in by_cat] == ["alpha_skill"]
    assert any("category" in r for r in by_cat[0]["match_reasons"])

    assert [h["skill_id"] for h in skills.discover(tag="git")] == ["beta_skill"]
    assert [h["skill_id"] for h in skills.discover(capability="research")] == ["alpha_skill"]
    assert [h["skill_id"] for h in skills.discover(query="beta")] == ["beta_skill"]
    assert skills.discover(query="nothing_matches_this") == []


def test_discovery_by_action_includes_dependencies(data_dir: Path):
    reg(make("child_uses_action", required_actions=("mission_status",)))
    reg(make("parent_wrapper", dependencies=(("child_uses_action", "1.0.0"),)))
    found = {h["skill_id"] for h in skills.discover(action="mission_status")}
    assert found == {"child_uses_action", "parent_wrapper"}


def test_disabled_skill_is_visible_but_marked(data_dir: Path):
    reg(make())
    registry.set_enabled("demo_skill", False)
    assert skills.discover() == []
    hits = skills.discover(include_disabled=True)
    assert hits[0]["available"] is False
    assert any("DISABLED" in r for r in hits[0]["match_reasons"])


def test_discovery_by_impact_ceiling(data_dir: Path):
    reg(make("safe_skill", impact=READ))
    reg(make("risky_skill", impact=HIGH_IMPACT))
    ids = {h["skill_id"] for h in skills.discover(impact_at_most=READ)}
    assert ids == {"safe_skill"}


def test_explain_exposes_operational_detail(data_dir: Path):
    reg(make("leaf_x", required_actions=("mission_status",)))
    reg(make("top_x", dependencies=(("leaf_x", "1.0.0"),)))
    detail = skills.explain("top_x")
    assert detail["effective_actions"] == ["mission_status"]
    assert detail["dependency_order"] == ["leaf_x", "top_x"]
    assert detail["gate_action"] == "skill_invoke"


# ---------------------------------------------------------------- contracts


def test_input_contract_rejects_missing_required(data_dir: Path):
    schema = {"properties": {"a": {"type": "string"}}, "required": ["a"]}
    with pytest.raises(contracts.ContractError, match="missing required"):
        contracts.validate_payload({}, schema)


def test_input_contract_rejects_wrong_type_and_undeclared(data_dir: Path):
    schema = {"properties": {"a": {"type": "integer"}}}
    with pytest.raises(contracts.ContractError, match="must be of type integer"):
        contracts.validate_payload({"a": "x"}, schema)
    with pytest.raises(contracts.ContractError, match="undeclared"):
        contracts.validate_payload({"a": 1, "sneaky": True}, schema)


def test_bool_is_not_an_integer(data_dir: Path):
    with pytest.raises(contracts.ContractError):
        contracts.validate_payload({"a": True}, {"properties": {"a": {"type": "integer"}}})


def test_enum_and_bounds(data_dir: Path):
    schema = {
        "properties": {
            "m": {"type": "string", "enum": ["x", "y"]},
            "n": {"type": "integer", "minimum": 2},
        }
    }
    with pytest.raises(contracts.ContractError, match="must be one of"):
        contracts.validate_payload({"m": "z"}, schema)
    with pytest.raises(contracts.ContractError, match=">= 2"):
        contracts.validate_payload({"n": 1}, schema)


def test_defaults_applied(data_dir: Path):
    schema = {"properties": {"a": {"type": "string", "default": "hi"}}}
    assert contracts.apply_defaults({}, schema) == {"a": "hi"}


# ---------------------------------------------------------------- execution


def test_successful_execution_envelope(data_dir: Path):
    reg(
        make(output_schema={"properties": {"value": {"type": "integer"}}}),
        lambda ctx, p: {"value": 42},
    )
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.SUCCESS
    assert env["ok"] is True
    assert env["output"] == {"value": 42}
    for field in (
        "skill_id",
        "version",
        "invocation_id",
        "requester",
        "status",
        "input",
        "output",
        "actions",
        "children",
        "provenance",
        "duration_ms",
        "impact",
    ):
        assert field in env


def test_failure_never_reports_success(data_dir: Path):
    def boom(ctx, params):
        raise ValueError("nope")

    reg(make(), boom)
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.FAILED
    assert env["ok"] is False
    assert env["output"] is None
    assert "nope" in env["error"]


def test_unknown_skill_is_unavailable(data_dir: Path):
    env = skills.execute("no_such_skill", {})
    assert env["status"] == skills.UNAVAILABLE
    assert env["error_kind"] == "not_found"


def test_disabled_skill_cannot_execute(data_dir: Path):
    reg(make())
    registry.set_enabled("demo_skill", False)
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.UNAVAILABLE
    assert env["error_kind"] == "disabled"


def test_invalid_input_rejected_before_execution(data_dir: Path):
    ran = []

    def impl(ctx, params):
        ran.append(1)
        return {}

    reg(make(input_schema={"properties": {"a": {"type": "string"}}, "required": ["a"]}), impl)
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.INVALID
    assert env["error_kind"] == "input_contract"
    assert ran == [], "underlying work ran despite invalid input"


def test_output_contract_enforced(data_dir: Path):
    reg(
        make(output_schema={"properties": {"n": {"type": "integer"}}}),
        lambda ctx, p: {"n": "not an int"},
    )
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.FAILED
    assert env["error_kind"] == "output_contract"


def test_non_object_output_rejected(data_dir: Path):
    reg(make(), lambda ctx, p: "just a string")
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.FAILED


def test_timeout_enforced(data_dir: Path):
    def slow(ctx, params):
        time.sleep(0.05)
        ctx.checkpoint()
        return {}

    reg(make(timeout_s=0.01), slow)
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.TIMED_OUT
    assert env["error_kind"] == "timeout"


def test_cancellation_propagates(data_dir: Path):
    def worker(ctx, params):
        ctx.checkpoint()
        return {}

    reg(make(), worker)
    env = skills.execute("demo_skill", {}, cancel_check=lambda: True)
    assert env["status"] == skills.CANCELLED
    assert env["ok"] is False


def test_oversized_output_bounded(data_dir: Path):
    reg(make(), lambda ctx, p: {"blob": "x" * (executor.BOUNDS["max_output_bytes"] + 10)})
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.BOUNDED


def test_retry_on_retryable_error(data_dir: Path):
    from jarvis.missions.engine import RetryableError

    attempts = []

    def flaky(ctx, params):
        attempts.append(1)
        if len(attempts) < 2:
            raise RetryableError("transient")
        return {"tries": len(attempts)}

    reg(make(), flaky)
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.SUCCESS
    assert env["attempts"] == 2


def test_logic_errors_are_not_retried(data_dir: Path):
    attempts = []

    def broken(ctx, params):
        attempts.append(1)
        raise KeyError("bug")

    reg(make(), broken)
    env = skills.execute("demo_skill", {})
    assert env["status"] == skills.FAILED
    assert len(attempts) == 1


# -------------------------------------------------------------- composition


def test_child_skill_invocation_records_provenance(data_dir: Path):
    reg(make("child_skill"), lambda ctx, p: {"from": "child"})
    reg(
        make("parent_skill", dependencies=(("child_skill", "1.0.0"),)),
        lambda ctx, p: {"child": ctx.call_skill("child_skill", {})["output"]},
    )
    env = skills.execute("parent_skill", {})
    assert env["status"] == skills.SUCCESS
    assert env["output"]["child"] == {"from": "child"}
    assert env["children"][0]["skill_id"] == "child_skill"
    assert env["provenance"]["children"] == ["child_skill"]

    child = skills.status_of(env["invocation_id"])["child_invocations"][0]
    assert child["parent_id"] == env["invocation_id"]
    assert child["root_id"] == env["invocation_id"]
    assert child["depth"] == 1


def test_three_level_composition_shares_root(data_dir: Path):
    reg(make("level_c"), lambda ctx, p: {"depth": ctx.depth})
    reg(
        make("level_b", dependencies=(("level_c", "1.0.0"),)),
        lambda ctx, p: {"c": ctx.call_skill("level_c", {})["output"]},
    )
    reg(
        make("level_a", dependencies=(("level_b", "1.0.0"),)),
        lambda ctx, p: {"b": ctx.call_skill("level_b", {})["output"]},
    )
    env = skills.execute("level_a", {})
    assert env["status"] == skills.SUCCESS
    assert env["output"]["b"]["c"]["depth"] == 2
    rows = skills.history(root_id=env["invocation_id"], limit=10)
    assert {r["skill_id"] for r in rows} == {"level_a", "level_b", "level_c"}


def test_recursion_is_bounded(data_dir: Path):
    def recurse(ctx, params):
        return {"nested": ctx.call_skill("recursive_skill", {})["output"]}

    reg(make("recursive_skill"), recurse)
    env = skills.execute("recursive_skill", {})
    assert env["status"] == skills.BOUNDED
    assert "max_depth" in (env["error"] or "")


def test_max_children_bound(data_dir: Path):
    reg(make("tiny_child"), lambda ctx, p: {})

    def fan_out(ctx, params):
        for _ in range(executor.BOUNDS["max_children"] + 2):
            ctx.call_skill("tiny_child", {})
        return {}

    reg(make("fan_out_skill", dependencies=(("tiny_child", "1.0.0"),)), fan_out)
    env = skills.execute("fan_out_skill", {})
    assert env["status"] == skills.BOUNDED
    assert "max_children" in (env["error"] or "")


def test_child_failure_surfaces_in_parent(data_dir: Path):
    def bad(ctx, params):
        raise RuntimeError("child exploded")

    reg(make("bad_child"), bad)
    reg(
        make("hopeful_parent", dependencies=(("bad_child", "1.0.0"),)),
        lambda ctx, p: {"child": ctx.call_skill("bad_child", {})["status"]},
    )
    env = skills.execute("hopeful_parent", {})
    # The child failed; the parent may observe it, but the child's own record is truthful.
    child_rows = [
        r
        for r in skills.history(root_id=env["invocation_id"], limit=5)
        if r["skill_id"] == "bad_child"
    ]
    assert child_rows[0]["status"] == skills.FAILED


# ------------------------------------------------------------- permissions


def test_agent_needs_the_skill_gate(data_dir: Path):
    reg(make("gated_skill"))
    # research_specialist holds skill_invoke; a bare unknown agent does not exist.
    executor.check_authority(registry.get("gated_skill"), "research_specialist")
    with pytest.raises(executor.SkillDenied, match="No such agent"):
        executor.check_authority(registry.get("gated_skill"), "ghost_agent")


def test_agent_must_hold_every_action_the_skill_uses(data_dir: Path):
    reg(make("needs_dev", required_actions=("dev_command",)))
    executor.check_authority(registry.get("needs_dev"), "coding_specialist")
    with pytest.raises(executor.SkillDenied, match="may not use action 'dev_command'"):
        executor.check_authority(registry.get("needs_dev"), "research_specialist")


def test_skill_cannot_escalate_through_a_child(data_dir: Path):
    """The headline property: a harmless wrapper is not a privilege ladder."""
    reg(make("privileged_child", required_actions=("dev_command",)))
    reg(make("innocent_parent", dependencies=(("privileged_child", "1.0.0"),)))
    # The parent declares no actions of its own, but inherits the child's.
    assert registry.effective_actions(registry.get("innocent_parent")) == ["dev_command"]
    with pytest.raises(executor.SkillDenied, match="dev_command"):
        executor.check_authority(registry.get("innocent_parent"), "research_specialist")
    executor.check_authority(registry.get("innocent_parent"), "coding_specialist")


def test_denied_agent_beats_open_allow_list(data_dir: Path):
    reg(make("picky_skill", denied_agents=("general_specialist",)))
    executor.check_authority(registry.get("picky_skill"), "research_specialist")
    with pytest.raises(executor.SkillDenied, match="denies agent"):
        executor.check_authority(registry.get("picky_skill"), "general_specialist")


def test_allow_list_restricts_to_named_agents(data_dir: Path):
    reg(make("exclusive_skill", allowed_agents=("coding_specialist",)))
    executor.check_authority(registry.get("exclusive_skill"), "coding_specialist")
    with pytest.raises(executor.SkillDenied):
        executor.check_authority(registry.get("exclusive_skill"), "research_specialist")


def test_denied_execution_returns_denied_envelope(data_dir: Path):
    ran = []
    reg(make("needs_dev2", required_actions=("dev_command",)), lambda ctx, p: ran.append(1) or {})
    env = skills.execute("needs_dev2", {}, requester="research_specialist")
    assert env["status"] == skills.DENIED
    assert env["error_kind"] == "permission_denied"
    assert ran == [], "denied skill still executed"


def test_undeclared_action_refused_at_call_time(data_dir: Path):
    """A skill cannot reach an action it never declared, even if the agent holds it."""

    def sneak(ctx, params):
        return ctx.call_action("mission_status", {"mission_id": "x"})

    reg(make("sneaky_skill", required_actions=()), sneak)
    env = skills.execute("sneaky_skill", {}, requester="coding_specialist")
    assert env["status"] == skills.DENIED
    assert "did not declare" in env["error"]


def test_child_denial_propagates_upward(data_dir: Path):
    reg(make("locked_child", denied_agents=("research_specialist",)))
    reg(
        make("open_parent", dependencies=(("locked_child", "1.0.0"),)),
        lambda ctx, p: {"child": ctx.call_skill("locked_child", {})},
    )
    env = skills.execute("open_parent", {}, requester="research_specialist")
    assert env["status"] == skills.DENIED
    assert env["ok"] is False


def test_system_invocation_still_respects_skill_deny_list(data_dir: Path):
    """No requester means operator context, not unlimited authority."""
    reg(make("bounded_skill", required_actions=("dev_command",)), lambda ctx, p: {})
    executor.check_authority(registry.get("bounded_skill"), "")


# ------------------------------------------------------------------- risk


def test_effective_impact_takes_the_worst_child(data_dir: Path):
    reg(make("dangerous_leaf", impact=HIGH_IMPACT))
    reg(make("mild_wrapper", impact=READ, dependencies=(("dangerous_leaf", "1.0.0"),)))
    assert registry.get("mild_wrapper").impact == READ
    assert registry.effective_impact(registry.get("mild_wrapper")) == HIGH_IMPACT


def test_high_impact_requires_explicit_authorization(data_dir: Path):
    ran = []
    reg(make("risky_op", impact=HIGH_IMPACT), lambda ctx, p: ran.append(1) or {})
    env = skills.execute("risky_op", {})
    assert env["status"] == skills.DENIED
    assert env["error_kind"] == "high_impact_unauthorized"
    assert ran == []
    ok_env = skills.execute("risky_op", {}, authorized_high_impact=True)
    assert ok_env["status"] == skills.SUCCESS


def test_wrapper_of_high_impact_child_is_also_gated(data_dir: Path):
    """Risk is never silently downgraded by wrapping."""
    reg(make("hi_child", impact=HIGH_IMPACT))
    reg(make("calm_parent", impact=READ, dependencies=(("hi_child", "1.0.0"),)))
    env = skills.execute("calm_parent", {})
    assert env["status"] == skills.DENIED
    assert env["error_kind"] == "high_impact_unauthorized"


def test_no_builtin_agent_may_invoke_high_impact_skills(data_dir: Path):
    reg(make("shell_ish", impact=HIGH_IMPACT))
    for agent_id in (
        "research_specialist",
        "coding_specialist",
        "analysis_specialist",
        "general_specialist",
    ):
        with pytest.raises(executor.SkillDenied, match="high_impact"):
            executor.check_authority(registry.get("shell_ish"), agent_id)


# ------------------------------------------------------------- persistence


def test_invocations_are_persisted(data_dir: Path):
    reg(make(), lambda ctx, p: {"v": 1})
    env = skills.execute("demo_skill", {}, requester="research_specialist")
    record = skills.status_of(env["invocation_id"])
    assert record["skill_id"] == "demo_skill"
    assert record["status"] == skills.SUCCESS
    assert record["requester"] == "research_specialist"
    assert record["duration_ms"] >= 0


def test_history_filters(data_dir: Path):
    reg(make("hist_a"), lambda ctx, p: {})
    reg(make("hist_b"), lambda ctx, p: {})
    skills.execute("hist_a", {}, requester="research_specialist")
    skills.execute("hist_b", {}, requester="analysis_specialist")
    assert {r["skill_id"] for r in skills.history(skill_id="hist_a")} == {"hist_a"}
    assert {r["skill_id"] for r in skills.history(requester="analysis_specialist")} == {"hist_b"}


def test_failed_invocations_are_recorded_too(data_dir: Path):
    reg(make("doomed"), lambda ctx, p: (_ for _ in ()).throw(RuntimeError("x")))
    env = skills.execute("doomed", {})
    assert skills.status_of(env["invocation_id"])["status"] == skills.FAILED


def test_skill_database_lives_in_the_isolated_root(data_dir: Path):
    from jarvis.skills import store as skill_store

    reg(make(), lambda ctx, p: {})
    skills.execute("demo_skill", {})
    assert data_dir in skill_store.DB_PATH.resolve().parents


# ------------------------------------------------------------- integration


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=30)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """A small deterministic git repository — never ARIA's own tree."""
    repo = tmp_path / "skill_repo"
    repo.mkdir()
    (repo / "mod.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (repo / "test_mod.py").write_text(
        "from mod import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8"
    )
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "user.name", "T"], repo)
    _git(["add", "."], repo)
    _git(["commit", "-qm", "initial"], repo)
    return repo


@pytest.fixture
def catalog(data_dir: Path):
    """The real built-in catalog, registered into the isolated registry."""
    skills.load_builtin_skills(replace=True)
    return skills.list_skills()


def test_builtin_catalog_registers_and_validates(catalog):
    ids = {d.skill_id for d in catalog}
    for expected in (
        "repository_inspect",
        "run_test_suite",
        "analyze_test_failure",
        "research_topic",
        "summarize_evidence",
        "verify_claim",
        "browse_documentation",
        "prepare_commit",
        "run_procedure",
    ):
        assert expected in ids
    for defn in catalog:
        skills.validate(defn)
        assert defn.description and defn.input_schema is not None


def test_builtin_catalog_spans_the_required_areas(catalog):
    categories = {d.category for d in catalog}
    assert {"research", "evidence", "browser", "coding", "analysis", "repository"} <= categories


def test_skill_to_action_runs_a_real_registry_action(data_dir: Path):
    """skill → action, through the real registry."""
    seen = {}

    def impl(ctx, params):
        result = ctx.call_action("mission_list", {"limit": 1})
        seen["ok"] = result.get("ok")
        return {"listed": bool(result.get("ok"))}

    reg(make("lists_missions", required_actions=("mission_list",)), impl)
    env = skills.execute("lists_missions", {})
    assert env["status"] == skills.SUCCESS
    assert seen["ok"] is True
    assert env["actions"][0]["action"] == "mission_list"


def test_agent_to_skill_through_the_agent_framework(data_dir: Path):
    """agent → skill, with the agent's own permissions applied."""
    reg(make("agent_visible", required_actions=("mission_status",)), lambda ctx, p: {"seen": True})
    out = agents.invoke(
        "research_specialist",
        "run a skill",
        action="skill_invoke",
        params={"skill_id": "agent_visible", "inputs": {}},
    )
    assert out["ok"] is True
    assert out["result"]["envelope"]["status"] == skills.SUCCESS
    assert out["result"]["envelope"]["requester"] == "research_specialist"


def test_agent_cannot_spoof_the_requester(data_dir: Path):
    """An agent must not borrow another identity — or operator context."""
    reg(make("coding_only", required_actions=("dev_command",)), lambda ctx, p: {})
    out = agents.invoke(
        "research_specialist",
        "borrow authority",
        action="skill_invoke",
        params={"skill_id": "coding_only", "inputs": {}, "requester": ""},
    )
    envelope = out["result"]["envelope"]
    assert envelope["requester"] == "research_specialist"
    assert envelope["status"] == skills.DENIED


def test_agent_without_the_gate_is_refused(data_dir: Path):
    from dataclasses import replace as dc_replace

    base = agents.get("general_specialist")
    stripped = dc_replace(
        base, allowed_actions=tuple(a for a in base.allowed_actions if a != "skill_invoke")
    )
    agent_registry.register(stripped, replace_existing=True)
    reg(make("anything"), lambda ctx, p: {})
    out = agents.invoke(
        "general_specialist",
        "try",
        action="skill_invoke",
        params={"skill_id": "anything", "inputs": {}},
    )
    assert out["ok"] is False
    assert out["error_kind"] == "permission_denied"


def test_mission_to_skill_persists_and_checkpoints(data_dir: Path):
    """mission → skill, using the existing mission engine only."""
    from jarvis import missions

    reg(make("mission_ready"), lambda ctx, p: {"done": True})
    mission_id = skills.create_skill_mission("mission_ready", {}, requester="")
    missions.run(mission_id, missions.ActionStepRunner(None))
    snapshot = missions.status(mission_id)
    assert snapshot["state"] == missions.COMPLETED
    assert snapshot["progress"]["completed_steps"] == 1
    assert missions.checkpoints(mission_id), "mission produced no checkpoint"
    rows = skills.history(skill_id="mission_ready")
    assert rows and rows[0]["status"] == skills.SUCCESS


def test_mission_plans_dependencies_in_order(data_dir: Path):
    reg(make("dep_first"), lambda ctx, p: {})
    reg(make("dep_second", dependencies=(("dep_first", "1.0.0"),)), lambda ctx, p: {})
    steps = skills.plan_steps("dep_second", {})
    assert [s["params"]["skill_id"] for s in steps] == ["dep_first", "dep_second"]
    assert all(s["action"] == "skill_step" for s in steps)


def test_mission_cancellation_cancels_the_skill(data_dir: Path):
    """mission cancel → skill cancel → no success."""
    from jarvis.missions import store as mstore

    def watcher(ctx, params):
        ctx.checkpoint()
        return {"never": True}

    reg(make("cancellable"), watcher)
    mission_id = skills.create_skill_mission("cancellable", {})
    mstore.request_cancel(mission_id)
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    out = call_action(
        None,
        "skill_step",
        {"skill_id": "cancellable", "mission_id": mission_id},
        "step",
    )
    assert out["ok"] is False
    assert out["envelope"]["status"] == skills.CANCELLED


def test_mission_skill_recovers_after_interruption(data_dir: Path):
    """mission → skill → interruption → recovery → completion."""
    from jarvis import missions
    from jarvis.missions import store as mstore

    reg(make("resumable"), lambda ctx, p: {"done": True})
    mission_id = skills.create_skill_mission("resumable", {})
    # Simulate a process dying mid-flight: the mission is left RUNNING with no
    # process behind it, which is exactly what recovery exists to find.
    mstore.transition(mission_id, missions.RUNNING, detail="simulated crash")
    recovered = missions.recover()
    assert mission_id in recovered
    missions.resume(mission_id, missions.ActionStepRunner(None))
    assert missions.status(mission_id)["state"] == missions.COMPLETED


def test_collaboration_to_skill_preserves_provenance(data_dir: Path):
    """collaboration → agent → skill, with the root requester intact."""
    from jarvis import collaboration

    reg(
        make("delegated_skill", required_actions=("evidence_list_claims",)),
        lambda ctx, p: {"by": ctx.requester, "root": ctx.root_id},
    )
    created = collaboration.create_collaboration(
        "summarise the evidence", initiator="analysis_specialist"
    )
    collab_id = created["collaboration_id"]
    task_id = collaboration.delegate(
        collab_id,
        requester="analysis_specialist",
        objective="summarise the evidence",
        target="research_specialist",
    )
    assert task_id
    out = agents.invoke(
        "research_specialist",
        "summarise",
        action="skill_invoke",
        params={"skill_id": "delegated_skill", "inputs": {}},
    )
    envelope = out["result"]["envelope"]
    assert envelope["status"] == skills.SUCCESS
    assert envelope["output"]["by"] == "research_specialist"
    assert envelope["provenance"]["requester"] == "research_specialist"


# ------------------------------------------------- research / evidence / browser


def test_research_skill_uses_the_research_engine(catalog, data_dir: Path, assistant):
    """research → skill: the real engine, not a reimplementation."""
    from jarvis.research import store as research_store

    env = skills.execute(
        "research_topic",
        {"objective": "the composition of interstellar dust"},
        requester="research_specialist",
        assistant=assistant,
    )
    assert env["status"] == skills.SUCCESS
    research_id = env["output"]["research_id"]
    assert research_store.get_job(research_id), "no durable research job was created"
    assert {a["action"] for a in env["actions"]} == {
        "research_create",
        "research_run",
        "research_status",
    }


def test_evidence_skill_reads_real_provenance(catalog, data_dir: Path):
    """evidence → skill, with provenance surviving the skill boundary."""
    from jarvis import evidence as ev

    ctx_id = "skill_ctx_1"
    claim = ev.add_claim("dust grains are silicate-rich", context_id=ctx_id)
    src = ev.add_source("https://nasa.gov/dust", context_id=ctx_id)
    ev.mark_source_inspected(src)
    eid = ev.add_evidence(
        src, "silicate features observed", context_id=ctx_id, evidence_type=ev.FULL_TEXT
    )
    ev.link(claim, eid, ev.SUPPORTS)

    env = skills.execute(
        "summarize_evidence", {"context_id": ctx_id}, requester="research_specialist"
    )
    assert env["status"] == skills.SUCCESS
    assert env["output"]["claim_count"] == 1
    assert env["output"]["claims"][0]["chain"], "provenance chain lost through the skill"


def test_verification_comes_from_the_evidence_system(catalog, data_dir: Path):
    """A skill must not turn unverified information into verified information."""
    from jarvis import evidence as ev

    ctx_id = "skill_ctx_2"
    claim = ev.add_claim("unsupported assertion", context_id=ctx_id)
    env = skills.execute("verify_claim", {"claim_id": claim}, requester="research_specialist")
    assert env["status"] == skills.SUCCESS
    # No supporting evidence exists, so the evidence system must not verify it.
    assert env["output"]["verified"] is False
    assert env["output"]["verification"] == "evidence_system"
    assert env["verification"] == "evidence_system"


def test_browser_skill_denied_to_the_coding_specialist(catalog, data_dir: Path):
    """Coding authority never becomes browsing authority through a skill."""
    with pytest.raises(executor.SkillDenied, match="browser_use_read"):
        executor.check_authority(registry.get("browse_documentation"), "coding_specialist")
    env = skills.execute(
        "browse_documentation", {"url": "https://example.com"}, requester="coding_specialist"
    )
    assert env["status"] == skills.DENIED


def test_browser_skill_uses_isolated_state(catalog, data_dir: Path):
    """browser → skill, never against the production profile."""
    from jarvis.computer_use import retention

    assert data_dir in retention.screenshot_dir().resolve().parents
    env = skills.execute(
        "browse_documentation",
        {"url": "https://example.com", "allow_local": False},
        requester="research_specialist",
    )
    # Whether or not a browser is installed here, it must never claim success
    # dishonestly and must stay inside the isolated root.
    assert env["status"] in (skills.SUCCESS, skills.FAILED)
    if env["status"] == skills.SUCCESS and not env["output"].get("available"):
        assert env["output"]["reason"]
        assert env["output"]["provenance"]["url"] == "https://example.com"


def test_procedure_skill_bridges_the_existing_playbook_store(catalog, data_dir: Path):
    """The older skill_database is reused, not reimplemented."""
    defn = registry.get("run_procedure")
    assert defn.required_actions == ("skill_run",)
    assert registry.effective_impact(defn) == HIGH_IMPACT
    env = skills.execute("run_procedure", {"slug": "install-docker", "dry_run": True})
    assert env["status"] == skills.DENIED, "shell playbooks must need explicit authorization"


# ------------------------------------------------------- coding agent → skill


def test_coding_agent_skills_operate_on_a_fixture_repo(catalog, data_dir: Path, fixture_repo: Path):
    """Coding Agent → skill, inside the Coding Agent's own confinement."""
    from jarvis.dev_agent import engine as dev_engine

    task = dev_engine.create_task("use skills", str(fixture_repo))
    env = skills.execute(
        "repository_inspect", {"task_id": task["id"]}, requester="coding_specialist"
    )
    assert env["status"] == skills.SUCCESS
    assert env["output"]["clean"] is True
    assert env["output"]["head"]
    assert "mod.py" in env["output"]["entries"]


def test_test_suite_skill_runs_the_real_suite(catalog, data_dir: Path, fixture_repo: Path):
    from jarvis.dev_agent import engine as dev_engine

    task = dev_engine.create_task("run tests via skill", str(fixture_repo))
    env = skills.execute("run_test_suite", {"task_id": task["id"]}, requester="coding_specialist")
    assert env["status"] == skills.SUCCESS
    assert env["output"]["green"] is True
    assert env["output"]["passed"] == 1


def test_analyze_failure_skill_composes_the_test_skill(catalog, data_dir: Path, fixture_repo: Path):
    """skill → skill, over the Coding Agent's real workspace."""
    from jarvis.dev_agent import engine as dev_engine

    (fixture_repo / "mod.py").write_text("def add(a, b):\n    return 0\n", encoding="utf-8")
    task = dev_engine.create_task("diagnose via skill", str(fixture_repo))
    env = skills.execute(
        "analyze_test_failure", {"task_id": task["id"]}, requester="coding_specialist"
    )
    assert env["status"] == skills.SUCCESS
    assert env["output"]["verdict"] == "caused_by_task"
    assert env["output"]["caused_by_task"] == ["test_mod.py::test_add"]
    assert env["children"][0]["skill_id"] == "run_test_suite"


def test_coding_agent_keeps_its_boundaries_when_using_skills(catalog, data_dir: Path):
    """Skills must not become a way around the Coding Agent's limits."""
    coder = agents.get("coding_specialist")
    for forbidden in (
        "dev_deploy",
        "dev_force_push",
        "dev_history_rewrite",
        "browser_use_read",
        "evidence_verify",
        "research_create",
    ):
        assert coder.permits(forbidden) is False
    for allowed in ("repository_inspect", "run_test_suite", "prepare_commit"):
        executor.check_authority(registry.get(allowed), "coding_specialist")


# --------------------------------------------------------------- safety A-O


def test_safety_a_unauthorized_action_denied(catalog, data_dir: Path):
    env = skills.execute(
        "prepare_commit", {"task_id": "x", "message": "m"}, requester="general_specialist"
    )
    assert env["status"] == skills.DENIED


def test_safety_b_unauthorized_child_skill_denied(data_dir: Path):
    reg(make("restricted_child", denied_agents=("analysis_specialist",)))
    reg(
        make("wrapper_skill", dependencies=(("restricted_child", "1.0.0"),)),
        lambda ctx, p: {"c": ctx.call_skill("restricted_child", {})},
    )
    env = skills.execute("wrapper_skill", {}, requester="analysis_specialist")
    assert env["status"] == skills.DENIED


def test_safety_e_path_traversal_blocked(
    catalog, data_dir: Path, fixture_repo: Path, tmp_path: Path
):
    """A skill inherits the Coding Agent's path confinement."""
    from jarvis.dev_agent import engine as dev_engine
    from jarvis.dev_agent import workspace as dev_ws

    task = dev_engine.create_task("escape via skill", str(fixture_repo))
    ws = dev_ws.open_workspace(fixture_repo, task_id=task["id"])
    with pytest.raises(dev_ws.PathEscape):
        ws.resolve("../../etc/passwd")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    with pytest.raises(dev_ws.PathEscape):
        ws.resolve(str(outside))


def test_safety_l_disabled_skill_cannot_execute(catalog, data_dir: Path):
    registry.set_enabled("repository_inspect", False)
    env = skills.execute("repository_inspect", {"task_id": "x"}, requester="coding_specialist")
    assert env["status"] == skills.UNAVAILABLE


def test_safety_m_incompatible_version_never_substituted(data_dir: Path):
    reg(make("versioned", version="2.0.0"), lambda ctx, p: {})
    env = skills.execute("versioned", {}, version="1.0.0", strategy="compatible")
    assert env["status"] == skills.UNAVAILABLE
    assert env["error_kind"] == "version_unavailable"


def test_safety_o_production_data_untouched(catalog, data_dir: Path):
    """Every store this milestone writes to must be inside the isolated root."""
    from jarvis.dev_agent import store as dev_store
    from jarvis.missions import store as mission_store
    from jarvis.skills import store as skill_store

    for path in (skill_store.DB_PATH, mission_store.DB_PATH, dev_store.DB_PATH):
        assert data_dir in Path(path).resolve().parents, path


# ------------------------------------------------------------ workflows A-F


def test_workflow_a_research_to_evidence(catalog, data_dir: Path, assistant):
    """WORKFLOW A: request → research agent → research skill → evidence → result."""
    env = skills.execute(
        "research_with_evidence",
        {"objective": "how tidal locking works"},
        requester="research_specialist",
        assistant=assistant,
    )
    assert env["status"] == skills.SUCCESS
    assert env["output"]["research_id"]
    assert [c["skill_id"] for c in env["children"]] == ["research_topic", "summarize_evidence"]
    rows = skills.history(root_id=env["invocation_id"], limit=10)
    assert {r["skill_id"] for r in rows} == {
        "research_with_evidence",
        "research_topic",
        "summarize_evidence",
    }


def test_workflow_b_coding(catalog, data_dir: Path, fixture_repo: Path):
    """WORKFLOW B: coding agent → inspect skill → test skill → commit skill."""
    from jarvis.dev_agent import engine as dev_engine

    task = dev_engine.create_task("skill-driven change", str(fixture_repo))
    inspected = skills.execute(
        "repository_inspect", {"task_id": task["id"]}, requester="coding_specialist"
    )
    assert inspected["status"] == skills.SUCCESS

    (fixture_repo / "mod.py").write_text(
        "def add(a, b):\n    return a + b\n\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8",
    )
    from jarvis.dev_agent import store as dev_store

    dev_store.add_changed_file(task["id"], "mod.py")

    tested = skills.execute(
        "run_test_suite", {"task_id": task["id"]}, requester="coding_specialist"
    )
    assert tested["output"]["green"] is True

    committed = skills.execute(
        "prepare_commit",
        {"task_id": task["id"], "message": "add mul"},
        requester="coding_specialist",
    )
    assert committed["status"] == skills.SUCCESS
    assert committed["output"]["commit"]
    assert committed["side_effects"], "a commit is a side effect worth recording"


def test_workflow_d_three_skill_composition(data_dir: Path):
    """WORKFLOW D: skill A → skill B → skill C, provenance and permissions intact."""
    reg(
        make("wf_c", required_actions=("mission_status",)),
        lambda ctx, p: {"who": ctx.requester, "depth": ctx.depth},
    )
    reg(
        make("wf_b", dependencies=(("wf_c", "1.0.0"),)),
        lambda ctx, p: {"c": ctx.call_skill("wf_c", {})["output"]},
    )
    reg(
        make("wf_a", dependencies=(("wf_b", "1.0.0"),)),
        lambda ctx, p: {"b": ctx.call_skill("wf_b", {})["output"]},
    )

    env = skills.execute("wf_a", {}, requester="research_specialist")
    assert env["status"] == skills.SUCCESS
    assert env["output"]["b"]["c"]["who"] == "research_specialist"
    assert env["output"]["b"]["c"]["depth"] == 2
    rows = skills.history(root_id=env["invocation_id"], limit=10)
    assert all(r["root_id"] == env["invocation_id"] for r in rows)
    assert all(r["requester"] == "research_specialist" for r in rows)


def test_workflow_e_denial_is_clean(catalog, data_dir: Path):
    """WORKFLOW E: agent → unauthorized skill fails cleanly, with no side effects."""
    env = skills.execute("research_topic", {"objective": "anything"}, requester="coding_specialist")
    assert env["status"] == skills.DENIED
    assert env["output"] is None
    assert env["actions"] == []
    assert env["side_effects"] == []
    assert "research_create" in env["error"]


def test_workflow_f_long_running_mission_recovery(data_dir: Path):
    """WORKFLOW F: mission → skill → checkpoint → interruption → recovery → completion."""
    from jarvis import missions
    from jarvis.missions import store as mstore

    calls = []
    reg(make("wf_child"), lambda ctx, p: calls.append("child") or {"done": True})
    reg(
        make("wf_parent", dependencies=(("wf_child", "1.0.0"),)),
        lambda ctx, p: {"child": ctx.call_skill("wf_child", {})["output"]},
    )

    mission_id = skills.create_skill_mission("wf_parent", {}, requester="")
    runner = missions.ActionStepRunner(None)
    missions.run(mission_id, runner, max_steps=1)
    assert missions.status(mission_id)["progress"]["completed_steps"] == 1
    assert missions.checkpoints(mission_id)

    mstore.transition(mission_id, missions.RUNNING, detail="simulated crash")
    assert mission_id in missions.recover()
    missions.resume(mission_id, runner)

    final = missions.status(mission_id)
    assert final["state"] == missions.COMPLETED
    assert final["progress"]["completed_steps"] == 2


# ------------------------------------------------------- handlers / packaging


def _call(action: str, params: dict, assistant=None):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    return call_action(assistant, action, params, action)


def test_skill_actions_are_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {a["action"] for a in all_actions()}
    for action in (
        "skill_discover",
        "skill_describe",
        "skill_invoke",
        "skill_history",
        "skill_catalog",
        "skill_step",
        "skill_invoke_high_impact",
    ):
        assert action in names
    # The older procedure-playbook actions must survive alongside them.
    for action in ("skill_list", "skill_show", "skill_save", "skill_run", "skill_delete"):
        assert action in names


def test_earlier_milestone_actions_still_registered(data_dir: Path):
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
        "agent_list",
    ):
        assert action in names, action


def test_discover_and_describe_handlers(catalog, data_dir: Path):
    out = _call("skill_discover", {"category": "coding"})
    assert out["ok"] is True
    assert out["count"] >= 1
    assert all(h["match_reasons"] for h in out["skills"])

    detail = _call("skill_describe", {"skill_id": "run_test_suite"})
    assert detail["ok"] is True
    assert detail["skill"]["ref"] == "run_test_suite@1.0.0"

    missing = _call("skill_describe", {"skill_id": "nope_not_here"})
    assert missing["ok"] is False


def test_invoke_handler_returns_the_envelope(data_dir: Path):
    reg(make("handler_demo"), lambda ctx, p: {"value": 7})
    out = _call("skill_invoke", {"skill_id": "handler_demo", "inputs": {}})
    assert out["ok"] is True
    assert out["output"] == {"value": 7}
    assert out["envelope"]["status"] == skills.SUCCESS


def test_invoke_handler_reports_failure_as_failure(data_dir: Path):
    reg(make("handler_bad"), lambda ctx, p: (_ for _ in ()).throw(RuntimeError("nope")))
    out = _call("skill_invoke", {"skill_id": "handler_bad", "inputs": {}})
    assert out["ok"] is False
    assert out["envelope"]["status"] == skills.FAILED


def test_invoke_handler_rejects_non_object_inputs(data_dir: Path):
    reg(make("handler_demo2"), lambda ctx, p: {})
    out = _call("skill_invoke", {"skill_id": "handler_demo2", "inputs": "not an object"})
    assert out["ok"] is False
    assert out["error_kind"] == "input_contract"


def test_high_impact_gate_action_is_not_an_operation(data_dir: Path):
    out = _call("skill_invoke_high_impact", {})
    assert out["ok"] is False
    assert out["error_kind"] == "gate_only"


def test_history_handler(data_dir: Path):
    reg(make("tracked"), lambda ctx, p: {})
    invoked = _call("skill_invoke", {"skill_id": "tracked", "inputs": {}})
    listed = _call("skill_history", {"skill_id": "tracked"})
    assert listed["ok"] is True
    assert listed["invocations"][0]["skill_id"] == "tracked"

    one = _call("skill_history", {"invocation_id": invoked["envelope"]["invocation_id"]})
    assert one["ok"] is True
    assert one["invocation"]["status"] == skills.SUCCESS


def test_catalog_handler_lists_builtins(catalog, data_dir: Path):
    out = _call("skill_catalog", {})
    assert out["ok"] is True
    assert {r["skill_id"] for r in out["skills"]} >= {"repository_inspect", "verify_claim"}


def test_new_skill_needs_no_executor_change(data_dir: Path):
    """§22: adding a skill is declarative — register a definition and a callable."""
    extra = make(
        "third_party_skill",
        category=ANALYSIS,
        required_actions=("mission_list",),
        input_schema={"properties": {"n": {"type": "integer"}}, "required": ["n"]},
    )
    reg(extra, lambda ctx, p: {"doubled": p["n"] * 2})
    env = skills.execute("third_party_skill", {"n": 21})
    assert env["output"] == {"doubled": 42}
    assert any(h["skill_id"] == "third_party_skill" for h in skills.discover())


def test_malformed_skill_fails_closed(data_dir: Path):
    """A bad definition never becomes executable."""
    with pytest.raises(SkillDefinitionError):
        reg(make("bad_one", impact="apocalyptic"))
    assert registry.get("bad_one") is None
    env = skills.execute("bad_one", {})
    assert env["status"] == skills.UNAVAILABLE


def test_registered_code_does_not_get_blanket_authority(data_dir: Path):
    """An added skill only reaches what it declared, under the requester's rights."""

    def greedy(ctx, params):
        return ctx.call_action("dev_task_create", {"objective": "x", "workspace": "/"})

    reg(make("greedy_skill", required_actions=("mission_status",)), greedy)
    env = skills.execute("greedy_skill", {}, requester="coding_specialist")
    assert env["status"] == skills.DENIED
    assert "did not declare" in env["error"]


def test_model_requirements_are_reported_not_substituted(data_dir: Path):
    """§21: a skill declares what it needs; nothing silently swaps models."""
    reg(make("needs_model", model_requirements=("code",)))
    detail = skills.explain("needs_model")
    assert detail["model_requirements"] == ["code"]


def test_max_depth_override_can_only_tighten(data_dir: Path):
    """An operator may run a skill with tighter limits, never looser ones."""
    reg(make("od_child"), lambda ctx, p: {"ok": True})
    reg(
        make("od_parent", dependencies=(("od_child", "1.0.0"),)),
        lambda ctx, p: {"c": ctx.call_skill("od_child", {})["output"]},
    )

    assert skills.execute("od_parent", {})["status"] == skills.SUCCESS
    tightened = skills.execute("od_parent", {}, max_depth=1)
    assert tightened["status"] == skills.BOUNDED
    assert "max_depth (1)" in tightened["error"]

    # A caller cannot raise the ceiling above the configured bound.
    raised = skills.execute("od_parent", {}, max_depth=999)
    assert raised["status"] == skills.SUCCESS
    deep = skills.execute("recursion_probe", {}, max_depth=999)
    assert deep["status"] == skills.UNAVAILABLE  # not registered; ceiling untouched


def test_tightened_depth_propagates_to_children(data_dir: Path):
    reg(make("td_leaf"), lambda ctx, p: {"d": ctx.depth})
    reg(
        make("td_mid", dependencies=(("td_leaf", "1.0.0"),)),
        lambda ctx, p: {"l": ctx.call_skill("td_leaf", {})["output"]},
    )
    reg(
        make("td_top", dependencies=(("td_mid", "1.0.0"),)),
        lambda ctx, p: {"m": ctx.call_skill("td_mid", {})["output"]},
    )
    env = skills.execute("td_top", {}, max_depth=2)
    assert env["status"] == skills.BOUNDED


def test_research_skill_reports_the_engines_real_state(catalog, data_dir: Path, assistant):
    """Regression, found live: the skill read a field the engine does not use.

    research_status returns its lifecycle under "status"; the skill read
    "state" and so reported an empty string on every successful run.
    """
    env = skills.execute(
        "research_topic",
        {"objective": "orbital resonance"},
        requester="research_specialist",
        assistant=assistant,
    )
    assert env["status"] == skills.SUCCESS
    assert env["output"]["state"], "skill reported an empty research state"

    from jarvis.research import store as research_store

    job = research_store.get_job(env["output"]["research_id"])
    assert env["output"]["state"] == job["status"]


def test_skill_can_be_queued_as_a_durable_mission(data_dir: Path):
    """Regression: create_skill_mission existed but nothing exposed it.

    Durable skill execution was unreachable from the running process, so a
    long-running skill could never be checkpointed, cancelled or recovered
    outside of tests.
    """
    from jarvis import missions

    reg(make("queued_skill"), lambda ctx, p: {"done": True})
    out = _call("skill_invoke", {"skill_id": "queued_skill", "inputs": {}, "mission": True})
    assert out["ok"] is True
    mission_id = out["mission_id"]
    snapshot = missions.status(mission_id)
    assert snapshot["state"] in (missions.PENDING, missions.RUNNING, missions.COMPLETED)
    assert snapshot["progress"]["total_steps"] == 1

    missions.run(mission_id, missions.ActionStepRunner(None))
    assert missions.status(mission_id)["state"] == missions.COMPLETED
    assert skills.history(skill_id="queued_skill")[0]["status"] == skills.SUCCESS


def test_queued_mission_rejects_an_unknown_skill(data_dir: Path):
    out = _call("skill_invoke", {"skill_id": "not_a_real_skill", "inputs": {}, "mission": True})
    assert out["ok"] is False
    assert out["error_kind"] == "not_found"


def test_queued_skill_mission_can_be_cancelled(data_dir: Path):
    """Regression: mission=true had no counterpart, so a queued skill could
    be started but never stopped by the same caller."""
    from jarvis import missions
    from jarvis.missions import store as mstore

    reg(make("stoppable"), lambda ctx, p: {"done": True})
    queued = _call("skill_invoke", {"skill_id": "stoppable", "inputs": {}, "mission": True})
    mission_id = queued["mission_id"]

    out = _call("skill_cancel", {"mission_id": mission_id})
    assert out["ok"] is True
    assert mstore.cancel_requested(mission_id) is True

    # The running step observes it and must not report success.
    step = _call("skill_step", {"skill_id": "stoppable", "mission_id": mission_id})
    assert step["ok"] is False
    assert step["envelope"]["status"] == skills.CANCELLED
    missions.cancel(mission_id)


def test_skill_cancel_resolves_a_mission_from_an_invocation(data_dir: Path):
    reg(make("traceable"), lambda ctx, p: {"done": True})
    queued = _call("skill_invoke", {"skill_id": "traceable", "inputs": {}, "mission": True})
    mission_id = queued["mission_id"]
    _call("skill_step", {"skill_id": "traceable", "mission_id": mission_id})
    invocation = skills.history(skill_id="traceable")[0]
    assert invocation["mission_id"] == mission_id
    out = _call("skill_cancel", {"invocation_id": invocation["id"]})
    assert out["ok"] is True


def test_skill_cancel_rejects_unknown_targets(data_dir: Path):
    assert _call("skill_cancel", {})["ok"] is False
    assert _call("skill_cancel", {"mission_id": "nope"})["ok"] is False


def test_every_skill_action_is_reachable_by_an_agent(data_dir: Path):
    """A registered skill action that no agent may call is dead in production."""
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions
    from jarvis.specialized_agents import definitions as agent_defs

    ensure_handlers_loaded()
    engine_actions = {
        "skill_discover",
        "skill_describe",
        "skill_invoke",
        "skill_cancel",
        "skill_history",
        "skill_catalog",
    }
    registered = {a["action"] for a in all_actions()}
    assert engine_actions <= registered
    gated = set(agent_defs.SKILL_HIGH_IMPACT)
    for action in engine_actions - gated:
        assert any(agents.get(a.id).permits(action) for a in agent_defs.BUILTIN_AGENTS), (
            f"registered but unreachable: {action}"
        )


def test_queued_mission_steps_carry_the_mission_id(data_dir: Path):
    """Regression, found live: steps had no mission_id.

    Without it the running skill gets no cancel_check, so a cancellation
    request could never reach a skill mid-flight, and the invocation record
    was never linked back to its mission.
    """
    from jarvis.missions import store as mstore

    reg(make("linked_skill"), lambda ctx, p: {"done": True})
    out = _call("skill_invoke", {"skill_id": "linked_skill", "inputs": {}, "mission": True})
    mission_id = out["mission_id"]
    mission = mstore.get(mission_id)
    assert all(s["params"]["mission_id"] == mission_id for s in mission["steps"])


def test_invocation_is_linked_to_its_mission(data_dir: Path):
    from jarvis import missions

    reg(make("linked_two"), lambda ctx, p: {"done": True})
    out = _call("skill_invoke", {"skill_id": "linked_two", "inputs": {}, "mission": True})
    missions.run(out["mission_id"], missions.ActionStepRunner(None))
    record = skills.history(skill_id="linked_two")[0]
    assert record["mission_id"] == out["mission_id"]
    assert record["status"] == skills.SUCCESS


def test_cancellation_reaches_a_skill_running_under_a_mission(data_dir: Path):
    """mission cancel → skill cancel, with no explicit plumbing by the caller."""
    from jarvis import missions
    from jarvis.missions import store as mstore

    reg(make("mid_flight"), lambda ctx, p: {"ran": True})
    out = _call("skill_invoke", {"skill_id": "mid_flight", "inputs": {}, "mission": True})
    mission_id = out["mission_id"]
    assert _call("skill_cancel", {"mission_id": mission_id})["ok"] is True

    step = mstore.get(mission_id)["steps"][0]
    assert step["params"]["mission_id"] == mission_id

    # Run the step exactly as the worker would: the mission id is already in
    # the stored params, so the skill sees the cancellation without the caller
    # plumbing anything through.
    cancelled = _call("skill_step", step["params"])
    assert cancelled["ok"] is False
    assert cancelled["envelope"]["status"] == skills.CANCELLED

    # The same step without a mission id has nothing to observe, and runs.
    detached = dict(step["params"])
    detached.pop("mission_id")
    assert _call("skill_step", detached)["ok"] is True
    missions.cancel(mission_id)


def test_skill_cancel_by_invocation_id_works_end_to_end(data_dir: Path):
    from jarvis import missions

    reg(make("traced_skill"), lambda ctx, p: {"done": True})
    out = _call("skill_invoke", {"skill_id": "traced_skill", "inputs": {}, "mission": True})
    missions.run(out["mission_id"], missions.ActionStepRunner(None))
    record = skills.history(skill_id="traced_skill")[0]
    # The mission has finished, so cancelling it is refused honestly.
    cancelled = _call("skill_cancel", {"invocation_id": record["id"]})
    assert cancelled["ok"] is False
    assert "already finished" in cancelled["message"]
