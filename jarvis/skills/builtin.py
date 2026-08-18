"""The built-in skill catalog.

Every skill here performs real work through an existing ARIA subsystem. None of
them reimplements one: research goes to the research engine, verification to the
evidence system, repository and test work to the Coding Agent, browsing to
computer use, and procedure playbooks to the existing skill_database.
"""

from __future__ import annotations

from typing import Any

from jarvis.skills import registry
from jarvis.skills.definitions import (
    ANALYSIS,
    BROWSER,
    CODING,
    EVIDENCE,
    HIGH_IMPACT,
    LOW_IMPACT,
    MODIFY,
    PROCEDURE,
    READ,
    REPOSITORY,
    RESEARCH,
    SkillDefinition,
)
from jarvis.skills.executor import SkillContext, SkillDenied

# --------------------------------------------------------------- repository


REPOSITORY_INSPECT = SkillDefinition(
    skill_id="repository_inspect",
    name="Inspect Repository",
    description="Report a coding task's repository state: branch, head, dirty files, layout.",
    purpose="Give an agent a grounded picture of a workspace before it changes anything.",
    version="1.0.0",
    category=REPOSITORY,
    tags=("git", "repository", "inspect", "coding"),
    capabilities=("repository", "inspection"),
    required_actions=("dev_command",),
    impact=READ,
    input_schema={
        "type": "object",
        "properties": {"task_id": {"type": "string"}},
        "required": ["task_id"],
    },
    output_schema={
        "type": "object",
        "properties": {"branch": {"type": "string"}, "head": {"type": "string"}},
    },
    preconditions=("an open coding task owns the workspace",),
    postconditions=("no files are modified",),
    side_effects=(),
)


def _repository_inspect(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    task_id = params["task_id"]
    status = ctx.call_action("dev_command", {"task_id": task_id, "argv": ["git", "status", "-sb"]})
    head = ctx.call_action(
        "dev_command", {"task_id": task_id, "argv": ["git", "log", "-1", "--oneline"]}
    )
    listing = ctx.call_action("dev_command", {"task_id": task_id, "argv": ["ls"]})
    if not status.get("ok"):
        raise RuntimeError(status.get("message") or "git status failed")
    status_text = (status.get("output") or "").strip()
    branch = ""
    for line in status_text.splitlines():
        if line.startswith("##"):
            branch = line[2:].split("...")[0].strip()
            break
    dirty = [ln.strip() for ln in status_text.splitlines() if ln and not ln.startswith("##")]
    return {
        "branch": branch,
        "head": (head.get("output") or "").strip().splitlines()[0] if head.get("ok") else "",
        "dirty": dirty,
        "entries": [e for e in (listing.get("output") or "").split() if e],
        "clean": not dirty,
    }


# ------------------------------------------------------------------- testing


RUN_TEST_SUITE = SkillDefinition(
    skill_id="run_test_suite",
    name="Run Test Suite",
    description="Run a coding task's test suite in its confined workspace and summarise results.",
    purpose="One reusable way to find out whether a workspace is green.",
    version="1.0.0",
    category=CODING,
    tags=("tests", "pytest", "coding"),
    capabilities=("testing",),
    required_actions=("dev_command",),
    impact=LOW_IMPACT,
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "test_cmd": {"type": "array", "default": ["pytest", "-q"]},
        },
        "required": ["task_id"],
    },
    output_schema={
        "type": "object",
        "properties": {"green": {"type": "boolean"}, "passed": {"type": "integer"}},
    },
    side_effects=("runs the project's test command",),
)


def _run_test_suite(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    from jarvis.dev_agent import commands

    argv = list(params.get("test_cmd") or ["pytest", "-q"])
    result = ctx.call_action("dev_command", {"task_id": params["task_id"], "argv": argv})
    output = result.get("output") or result.get("message") or ""
    summary = commands.parse_test_output(output)
    ctx.record_side_effect(f"ran {' '.join(argv)}")
    return {
        "command": argv,
        "exit_code": result.get("exit_code"),
        "ran": result.get("exit_code") is not None,
        **summary,
    }


ANALYZE_TEST_FAILURE = SkillDefinition(
    skill_id="analyze_test_failure",
    name="Analyse Test Failure",
    description="Run the suite and separate failures this task caused from pre-existing ones.",
    purpose="Stop an agent from 'fixing' tests that were already red before it started.",
    version="1.0.0",
    category=CODING,
    tags=("tests", "diagnosis", "coding"),
    capabilities=("testing", "debugging"),
    required_actions=(),
    dependencies=(("run_test_suite", "1.0.0"),),
    impact=READ,
    input_schema={
        "type": "object",
        "properties": {"task_id": {"type": "string"}, "test_cmd": {"type": "array"}},
        "required": ["task_id"],
    },
    output_schema={"type": "object", "properties": {"verdict": {"type": "string"}}},
)


def _analyze_test_failure(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    from jarvis.dev_agent import store as dev_store

    child = ctx.call_skill(
        "run_test_suite",
        {"task_id": params["task_id"], "test_cmd": params.get("test_cmd") or ["pytest", "-q"]},
        version="1.0.0",
    )
    tests = child.get("output") or {}
    failing = set(tests.get("failing_tests") or [])
    task = dev_store.get(params["task_id"]) or {}
    baseline = set(task.get("baseline_failures") or [])
    caused = sorted(failing - baseline)
    pre_existing = sorted(failing & baseline)
    if tests.get("green"):
        verdict = "clean"
    elif caused:
        verdict = "caused_by_task"
    elif pre_existing:
        verdict = "pre_existing"
    else:
        verdict = "unrunnable" if tests.get("errors") else "clean"
    return {
        "verdict": verdict,
        "caused_by_task": caused,
        "pre_existing": pre_existing,
        "green": bool(tests.get("green")),
        "tests": tests,
    }


PREPARE_COMMIT = SkillDefinition(
    skill_id="prepare_commit",
    name="Prepare Commit",
    description="Commit a coding task's own changed files, leaving unrelated work alone.",
    purpose="Reuse the Coding Agent's commit discipline from anywhere.",
    version="1.0.0",
    category=CODING,
    tags=("git", "commit", "coding"),
    capabilities=("repository",),
    required_actions=("dev_task_commit",),
    impact=MODIFY,
    input_schema={
        "type": "object",
        "properties": {"task_id": {"type": "string"}, "message": {"type": "string"}},
        "required": ["task_id", "message"],
    },
    output_schema={"type": "object", "properties": {"commit": {"type": "string"}}},
    side_effects=("creates a git commit in the task's workspace",),
)


def _prepare_commit(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    result = ctx.call_action(
        "dev_task_commit", {"task_id": params["task_id"], "message": params["message"]}
    )
    if not result.get("ok"):
        raise RuntimeError(result.get("message") or "commit failed")
    ctx.record_side_effect(f"committed {result.get('commit', '')[:10]}")
    return {"commit": result.get("commit") or "", "files": result.get("files") or []}


# ------------------------------------------------------------------ research


RESEARCH_TOPIC = SkillDefinition(
    skill_id="research_topic",
    name="Research Topic",
    description="Start and run a deep research job through ARIA's research engine.",
    purpose="Make the research engine reusable as one composable step.",
    version="1.0.0",
    category=RESEARCH,
    tags=("research", "search", "synthesis"),
    capabilities=("research", "search"),
    required_actions=("research_create", "research_run", "research_status"),
    impact=LOW_IMPACT,
    input_schema={
        "type": "object",
        "properties": {"objective": {"type": "string", "maxLength": 2000}},
        "required": ["objective"],
    },
    output_schema={"type": "object", "properties": {"research_id": {"type": "string"}}},
    side_effects=("creates a durable research job",),
)


def _research_topic(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    created = ctx.call_action("research_create", {"objective": params["objective"]})
    if not created.get("ok"):
        raise RuntimeError(created.get("message") or "could not create research")
    research_id = created.get("research_id") or ""
    ctx.record_side_effect(f"created research {research_id}")
    ctx.call_action("research_run", {"research_id": research_id})
    status = ctx.call_action("research_status", {"research_id": research_id})
    snapshot = status.get("research") or {}
    # The research engine reports its lifecycle under "status"; reading "state"
    # here silently produced an empty field on every successful run.
    return {
        "research_id": research_id,
        "objective": params["objective"],
        "state": snapshot.get("status") or snapshot.get("state") or "",
        "phase": snapshot.get("phase") or "",
        "confidence": snapshot.get("confidence") or "",
        "provenance": {"research_id": research_id},
    }


# ------------------------------------------------------------------ evidence


SUMMARIZE_EVIDENCE = SkillDefinition(
    skill_id="summarize_evidence",
    name="Summarise Evidence",
    description="List the claims in a context with their provenance chains.",
    purpose="Read the evidence layer without being able to write to it.",
    version="1.0.0",
    category=EVIDENCE,
    tags=("evidence", "provenance", "summary"),
    capabilities=("evidence", "summarization"),
    required_actions=("evidence_list_claims", "evidence_provenance"),
    impact=READ,
    input_schema={
        "type": "object",
        "properties": {
            "context_id": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["context_id"],
    },
    output_schema={"type": "object", "properties": {"claims": {"type": "array"}}},
)


def _summarize_evidence(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    listed = ctx.call_action("evidence_list_claims", {"context_id": params["context_id"]})
    claims = listed.get("claims") or []
    limit = int(params.get("limit") or 10)
    chains = []
    for claim in claims[:limit]:
        claim_id = claim.get("id") if isinstance(claim, dict) else str(claim)
        if not claim_id:
            continue
        prov = ctx.call_action("evidence_provenance", {"claim_id": claim_id})
        chains.append(
            {
                "claim_id": claim_id,
                "text": (claim.get("text") if isinstance(claim, dict) else ""),
                "chain": (prov.get("provenance") or {}).get("chain") or [],
            }
        )
    return {
        "context_id": params["context_id"],
        "claim_count": len(claims),
        "claims": chains,
        "provenance": {"context_id": params["context_id"]},
    }


VERIFY_CLAIM = SkillDefinition(
    skill_id="verify_claim",
    name="Verify Claim",
    description="Verify a claim using ARIA's evidence verification system.",
    purpose="Expose verification as a skill without inventing a second notion of truth.",
    version="1.0.0",
    category=EVIDENCE,
    tags=("evidence", "verification"),
    capabilities=("evidence", "verification"),
    required_actions=("evidence_verify",),
    impact=LOW_IMPACT,
    input_schema={
        "type": "object",
        "properties": {"claim_id": {"type": "string"}, "method": {"type": "string"}},
        "required": ["claim_id"],
    },
    output_schema={"type": "object", "properties": {"verified": {"type": "boolean"}}},
    side_effects=("records a verification against the claim",),
)


def _verify_claim(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    payload = {"claim_id": params["claim_id"]}
    if params.get("method"):
        payload["method"] = params["method"]
    result = ctx.call_action("evidence_verify", payload)
    if not result.get("ok"):
        raise RuntimeError(result.get("message") or "verification failed")
    verification = result.get("verification") or {}
    # The verification state is whatever the evidence system decided. A skill
    # must never upgrade unverified information by asserting it here.
    return {
        "claim_id": params["claim_id"],
        "verified": bool(verification.get("verified")),
        "method": verification.get("method") or params.get("method") or "",
        "confidence": verification.get("confidence"),
        "verification": "evidence_system",
        "provenance": {"claim_id": params["claim_id"], "verified_by": "jarvis.evidence.verify"},
    }


RESEARCH_WITH_EVIDENCE = SkillDefinition(
    skill_id="research_with_evidence",
    name="Research With Evidence",
    description="Research a topic, then summarise the evidence recorded for it.",
    purpose="A composed skill: research first, then read back its provenance.",
    version="1.0.0",
    category=RESEARCH,
    tags=("research", "evidence", "composition"),
    capabilities=("research", "evidence", "synthesis"),
    required_actions=(),
    dependencies=(("research_topic", "1.0.0"), ("summarize_evidence", "1.0.0")),
    impact=LOW_IMPACT,
    input_schema={
        "type": "object",
        "properties": {"objective": {"type": "string"}},
        "required": ["objective"],
    },
    output_schema={"type": "object", "properties": {"research_id": {"type": "string"}}},
)


def _research_with_evidence(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    research = ctx.call_skill("research_topic", {"objective": params["objective"]})
    research_id = (research.get("output") or {}).get("research_id") or ""
    evidence = ctx.call_skill("summarize_evidence", {"context_id": research_id})
    summary = evidence.get("output") or {}
    return {
        "research_id": research_id,
        "state": (research.get("output") or {}).get("state") or "",
        "claim_count": summary.get("claim_count", 0),
        "claims": summary.get("claims") or [],
        "provenance": {
            "research_id": research_id,
            "child_invocations": [research["invocation_id"], evidence["invocation_id"]],
        },
    }


# ------------------------------------------------------------------- browser


BROWSE_DOCUMENTATION = SkillDefinition(
    skill_id="browse_documentation",
    name="Browse Documentation",
    description="Open an isolated browser session, read a page, and return its text.",
    purpose="Reuse computer use for read-only reference lookups, with provenance.",
    version="1.0.0",
    category=BROWSER,
    tags=("browser", "documentation", "read"),
    capabilities=("browsing", "research"),
    # The browser gate is a permission token rather than a registry action, so
    # it is declared here and enforced twice: once by check_authority and again
    # inside computer_use itself.
    required_actions=(),
    required_permissions=("browser_use_read",),
    impact=READ,
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "owner": {"type": "string", "default": "skill"},
            "allow_local": {"type": "boolean", "default": False},
        },
        "required": ["url"],
    },
    output_schema={"type": "object", "properties": {"url": {"type": "string"}}},
    side_effects=("opens and closes a browser session",),
)


def _browse_documentation(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    from jarvis import computer_use as cu

    ctx.checkpoint()
    session = cu.open_session(owner=params.get("owner") or "skill", task_id=ctx.invocation_id)
    session_id = session["id"] if isinstance(session, dict) else str(session)
    ctx.record_side_effect(f"opened browser session {session_id}")
    try:
        nav = cu.perform(
            session_id,
            "navigate",
            {"url": params["url"]},
            agent_id=ctx.requester,
            allow_local=bool(params.get("allow_local")),
        )
        if not nav.get("ok"):
            kind = nav.get("error_kind") or ""
            if kind in ("permission_denied", "policy"):
                raise SkillDenied(nav.get("error") or "browser navigation denied")
            return {
                "url": params["url"],
                "available": False,
                "reason": nav.get("error_kind") or "navigation_failed",
                "detail": nav.get("error") or "",
                "provenance": {"session_id": session_id, "url": params["url"]},
            }
        ctx.checkpoint()
        extract = cu.perform(
            session_id,
            "extract_text",
            {},
            agent_id=ctx.requester,
            allow_local=bool(params.get("allow_local")),
        )
        text = (extract.get("result") or {}).get("text", "") if extract.get("ok") else ""
        return {
            "url": params["url"],
            "available": True,
            "title": (nav.get("result") or {}).get("title", ""),
            "text": text[:8000],
            "provenance": {
                "session_id": session_id,
                "url": params["url"],
                "captured_by": "jarvis.computer_use",
            },
        }
    finally:
        try:
            cu.close_session(session_id)
        except Exception:  # noqa: BLE001 - cleanup must not mask the result
            pass


# ----------------------------------------------------------------- procedure


RUN_PROCEDURE = SkillDefinition(
    skill_id="run_procedure",
    name="Run Procedure Playbook",
    description="Execute a saved procedure playbook from ARIA's skill database.",
    purpose="Bridge the existing playbook store into the skills layer rather than "
    "reimplementing it.",
    version="1.0.0",
    category=PROCEDURE,
    tags=("procedure", "playbook", "ops"),
    capabilities=("procedure",),
    required_actions=("skill_run",),
    # Playbook steps are shell commands, so this is the most consequential
    # thing the catalog can do and is gated accordingly.
    impact=HIGH_IMPACT,
    input_schema={
        "type": "object",
        "properties": {
            "slug": {"type": "string"},
            "dry_run": {"type": "boolean", "default": True},
        },
        "required": ["slug"],
    },
    output_schema={"type": "object", "properties": {"slug": {"type": "string"}}},
    side_effects=("may run shell commands defined by the playbook",),
)


def _run_procedure(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    result = ctx.call_action(
        "skill_run", {"skill": params["slug"], "dry_run": bool(params.get("dry_run", True))}
    )
    ctx.record_side_effect(f"ran playbook {params['slug']} (dry_run={params.get('dry_run', True)})")
    return {
        "slug": params["slug"],
        "dry_run": bool(params.get("dry_run", True)),
        "ok": bool(result.get("ok")),
        "summary": (result.get("message") or "")[:2000],
    }


# ------------------------------------------------------------------ analysis


SUMMARIZE_FINDINGS = SkillDefinition(
    skill_id="summarize_findings",
    name="Summarise Findings",
    description="Turn a set of claims into a compact structured summary with counts.",
    purpose="A deterministic analysis step usable by any agent that can read evidence.",
    version="1.0.0",
    category=ANALYSIS,
    tags=("analysis", "summary", "evidence"),
    capabilities=("analysis", "summarization"),
    required_actions=(),
    dependencies=(("summarize_evidence", "1.0.0"),),
    impact=READ,
    input_schema={
        "type": "object",
        "properties": {"context_id": {"type": "string"}},
        "required": ["context_id"],
    },
    output_schema={"type": "object", "properties": {"claim_count": {"type": "integer"}}},
)


def _summarize_findings(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    child = ctx.call_skill("summarize_evidence", {"context_id": params["context_id"]})
    summary = child.get("output") or {}
    claims = summary.get("claims") or []
    supported = [c for c in claims if c.get("chain")]
    return {
        "context_id": params["context_id"],
        "claim_count": summary.get("claim_count", 0),
        "with_provenance": len(supported),
        "without_provenance": len(claims) - len(supported),
        "provenance": {"child_invocation": child["invocation_id"]},
    }


CATALOG: tuple[tuple[SkillDefinition, Any], ...] = (
    (REPOSITORY_INSPECT, _repository_inspect),
    (RUN_TEST_SUITE, _run_test_suite),
    (ANALYZE_TEST_FAILURE, _analyze_test_failure),
    (PREPARE_COMMIT, _prepare_commit),
    (RESEARCH_TOPIC, _research_topic),
    (SUMMARIZE_EVIDENCE, _summarize_evidence),
    (VERIFY_CLAIM, _verify_claim),
    (RESEARCH_WITH_EVIDENCE, _research_with_evidence),
    (SUMMARIZE_FINDINGS, _summarize_findings),
    (BROWSE_DOCUMENTATION, _browse_documentation),
    (RUN_PROCEDURE, _run_procedure),
)


def load_builtin_skills(*, replace: bool = True) -> list[str]:
    """Register the catalog. Dependencies are registered before their dependents."""
    loaded = []
    for defn, impl in CATALOG:
        registry.register(defn, impl, replace=replace)
        loaded.append(defn.ref())
    return loaded
