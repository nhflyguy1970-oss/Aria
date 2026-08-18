"""Evidence & Verification — provenance, independence, contradictions, anti-fabrication."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import jarvis.evidence.verify as verify  # module, not the re-exported function
from jarvis import evidence as ev
from jarvis import missions
from jarvis import specialized_agents as agents
from jarvis.evidence import store
from jarvis.missions import store as mstore
from jarvis.specialized_agents import registry

# jarvis.evidence re-exports verify() as a function, which shadows the module
# attribute, so the module itself is fetched explicitly for its constants.
verify = importlib.import_module("jarvis.evidence.verify")

REPO_ROOT = Path(__file__).resolve().parents[1]
CTX = "ctx1"


@pytest.fixture(autouse=True)
def _clean_registry():
    registry.reset()
    yield
    registry.reset()


def _inspected_source(url, title="T", ctx=CTX) -> str:
    sid = ev.add_source(url, context_id=ctx, title=title)
    ev.mark_source_inspected(sid)
    return sid


def _claim_with(support_urls, contradict_urls=(), ctx=CTX, inspected=True) -> str:
    cid = ev.add_claim("the test claim", context_id=ctx)
    for u in support_urls:
        sid = _inspected_source(u, ctx=ctx) if inspected else ev.add_source(u, context_id=ctx)
        kind = ev.FULL_TEXT if inspected else ev.SNIPPET
        eid = ev.add_evidence(sid, f"supporting text from {u}", context_id=ctx, evidence_type=kind)
        ev.link(cid, eid, ev.SUPPORTS)
    for u in contradict_urls:
        sid = _inspected_source(u, ctx=ctx) if inspected else ev.add_source(u, context_id=ctx)
        kind = ev.FULL_TEXT if inspected else ev.SNIPPET
        eid = ev.add_evidence(
            sid, f"contradicting text from {u}", context_id=ctx, evidence_type=kind
        )
        ev.link(cid, eid, ev.CONTRADICTS)
    return cid


# ------------------------------------------------------------------ sources


def test_source_recorded_as_discovered_not_inspected(data_dir: Path):
    sid = ev.add_source("https://nasa.gov/a", context_id=CTX, title="NASA")
    src = ev.get_source(sid)
    assert src["access_state"] == ev.DISCOVERED
    assert src["domain"] == "nasa.gov"
    assert src["tier"] >= 1


def test_source_deduplicated_by_canonical_url(data_dir: Path):
    a = ev.add_source("https://www.NASA.gov/a/", context_id=CTX)
    b = ev.add_source("http://nasa.gov/a#frag", context_id=CTX)
    assert a == b
    assert len(ev.sources(CTX)) == 1


def test_invalid_source_rejected(data_dir: Path):
    with pytest.raises(ev.EvidenceError):
        ev.add_source("   ", context_id=CTX)


def test_source_inspection_and_unavailability(data_dir: Path):
    sid = ev.add_source("https://nasa.gov/a", context_id=CTX)
    ev.mark_source_inspected(sid)
    assert ev.get_source(sid)["access_state"] == ev.INSPECTED
    other = ev.add_source("https://blocked.example.com/x", context_id=CTX)
    ev.mark_source_unavailable(other, "403 forbidden")
    assert ev.get_source(other)["access_state"] == ev.UNAVAILABLE
    assert "403" in ev.get_source(other)["error"]


def test_source_metadata_preserved(data_dir: Path):
    sid = ev.add_source(
        "https://nasa.gov/a", context_id=CTX, title="T", publisher="NASA", published_at="2020-01-01"
    )
    src = ev.get_source(sid)
    assert src["publisher"] == "NASA" and src["published_at"] == "2020-01-01"


# ----------------------------------------------------------------- evidence


def test_evidence_requires_a_recorded_source(data_dir: Path):
    with pytest.raises(ev.EvidenceError, match="recorded source"):
        ev.add_evidence("src_does_not_exist", "text", context_id=CTX)


def test_evidence_requires_an_excerpt(data_dir: Path):
    sid = ev.add_source("https://nasa.gov/a", context_id=CTX)
    with pytest.raises(ev.EvidenceError):
        ev.add_evidence(sid, "   ", context_id=CTX)


def test_snippet_evidence_is_not_marked_inspected(data_dir: Path):
    """A search snippet must never read as full-source inspection."""
    sid = _inspected_source("https://nasa.gov/a")
    eid = ev.add_evidence(sid, "snippet", context_id=CTX, evidence_type=ev.SNIPPET)
    assert ev.get_evidence(eid)["inspected"] == 0


def test_full_text_from_inspected_source_is_inspected(data_dir: Path):
    sid = _inspected_source("https://nasa.gov/a")
    eid = ev.add_evidence(sid, "body", context_id=CTX, evidence_type=ev.FULL_TEXT)
    assert ev.get_evidence(eid)["inspected"] == 1


def test_full_text_from_unavailable_source_rejected(data_dir: Path):
    """A failed fetch cannot become full-source evidence."""
    sid = ev.add_source("https://blocked.example.com/x", context_id=CTX)
    ev.mark_source_unavailable(sid, "timeout")
    with pytest.raises(ev.EvidenceError, match="could not be retrieved"):
        ev.add_evidence(sid, "invented body", context_id=CTX, evidence_type=ev.FULL_TEXT)


def test_evidence_from_uninspected_source_is_not_inspected(data_dir: Path):
    sid = ev.add_source("https://nasa.gov/a", context_id=CTX)
    eid = ev.add_evidence(sid, "snippet only", context_id=CTX, evidence_type=ev.FULL_TEXT)
    assert ev.get_evidence(eid)["inspected"] == 0, "uninspected source produced inspected evidence"


def test_unknown_evidence_type_rejected(data_dir: Path):
    sid = _inspected_source("https://nasa.gov/a")
    with pytest.raises(ev.EvidenceError):
        ev.add_evidence(sid, "x", context_id=CTX, evidence_type="hearsay")


def test_evidence_records_provenance_string(data_dir: Path):
    sid = _inspected_source("https://nasa.gov/a")
    eid = ev.add_evidence(sid, "body", context_id=CTX, evidence_type=ev.FULL_TEXT)
    assert "nasa.gov" in ev.get_evidence(eid)["provenance"]


# ------------------------------------------------------------------- claims


def test_claim_created_as_proposed(data_dir: Path):
    cid = ev.add_claim("water boils at 100C", context_id=CTX)
    assert ev.get_claim(cid)["status"] == ev.store.PROPOSED


def test_claim_deduplicated_by_normalized_text(data_dir: Path):
    a = ev.add_claim("Water Boils At 100C?", context_id=CTX)
    b = ev.add_claim("water boils at 100c", context_id=CTX)
    assert a == b


def test_empty_claim_rejected(data_dir: Path):
    with pytest.raises(ev.EvidenceError):
        ev.add_claim("  ", context_id=CTX)


def test_link_requires_real_claim_and_evidence(data_dir: Path):
    sid = _inspected_source("https://nasa.gov/a")
    eid = ev.add_evidence(sid, "b", context_id=CTX, evidence_type=ev.FULL_TEXT)
    cid = ev.add_claim("c", context_id=CTX)
    with pytest.raises(ev.EvidenceError):
        ev.link("clm_missing", eid, ev.SUPPORTS)
    with pytest.raises(ev.EvidenceError):
        ev.link(cid, "evd_missing", ev.SUPPORTS)
    with pytest.raises(ev.EvidenceError):
        ev.link(cid, eid, "vibes")


def test_all_relation_types_supported(data_dir: Path):
    sid = _inspected_source("https://nasa.gov/a")
    cid = ev.add_claim("relations", context_id=CTX)
    for rel in ev.RELATIONS:
        eid = ev.add_evidence(sid, f"text for {rel}", context_id=CTX, evidence_type=ev.FULL_TEXT)
        ev.link(cid, eid, rel)
    assert {r["relation"] for r in ev.claim_evidence(cid)} == set(ev.RELATIONS)


# -------------------------------------------------------------- independence


def test_same_source_is_not_independent(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a"])
    rows = [r for r in ev.claim_evidence(cid) if r["relation"] == ev.SUPPORTS]
    assert ev.independence(rows)["level"] == store.NOT_INDEPENDENT


def test_same_domain_is_not_independent(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nasa.gov/b"])
    rows = [r for r in ev.claim_evidence(cid) if r["relation"] == ev.SUPPORTS]
    indep = ev.independence(rows)
    assert indep["distinct_sources"] == 2
    assert indep["level"] == store.NOT_INDEPENDENT, "same publisher counted as corroboration"


def test_distinct_domains_are_independent(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    rows = [r for r in ev.claim_evidence(cid) if r["relation"] == ev.SUPPORTS]
    assert ev.independence(rows)["level"] == store.INDEPENDENT


def test_http_https_variants_are_one_source(data_dir: Path):
    ev.add_source("https://nasa.gov/a", context_id=CTX)
    ev.add_source("http://www.nasa.gov/a/", context_id=CTX)
    assert len(ev.sources(CTX)) == 1


def test_no_evidence_is_not_independent(data_dir: Path):
    assert ev.independence([])["level"] == store.NOT_INDEPENDENT


# ------------------------------------------------------------- verification


def test_independent_sources_verification(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    out = ev.verify(cid, method=ev.INDEPENDENT_SOURCES)
    assert out["result"] == verify.VERIFIED
    assert out["confidence"] == verify.HIGH
    assert ev.get_claim(cid)["status"] == store.VERIFIED


def test_single_source_cannot_be_verified(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a"])
    out = ev.verify(cid)
    assert out["result"] == verify.SUPPORTED
    assert out["confidence"] != verify.HIGH
    assert ev.get_claim(cid)["status"] == store.SUPPORTED


def test_same_domain_cannot_be_verified(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nasa.gov/b"])
    out = ev.verify(cid)
    assert out["result"] != verify.VERIFIED
    assert out["independence"]["level"] == store.NOT_INDEPENDENT


def test_contradiction_makes_claim_contested(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"], ["https://blog.example.com/c"])
    out = ev.verify(cid)
    assert out["result"] == verify.CONTESTED
    assert out["confidence"] in (verify.LOW, verify.MODERATE)
    assert ev.get_claim(cid)["status"] == store.CONTESTED


def test_only_contradicting_evidence(data_dir: Path):
    cid = _claim_with([], ["https://blog.example.com/c"])
    out = ev.verify(cid, method=ev.CONTRADICTION_ANALYSIS)
    assert out["result"] == verify.CONTRADICTED
    assert ev.get_claim(cid)["status"] == store.CONTRADICTED


def test_insufficient_evidence(data_dir: Path):
    cid = ev.add_claim("nothing supports this", context_id=CTX)
    out = ev.verify(cid)
    assert out["result"] == verify.INSUFFICIENT
    assert out["confidence"] == verify.NONE
    assert ev.get_claim(cid)["status"] == store.UNRESOLVED


def test_direct_inspection_method(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"], inspected=True)
    out = ev.verify(cid, method=ev.DIRECT_INSPECTION)
    assert out["result"] == verify.VERIFIED
    snippet_claim = _claim_with(["https://x.gov/a"], ctx="ctx2", inspected=False)
    out2 = ev.verify(snippet_claim, method=ev.DIRECT_INSPECTION)
    assert out2["result"] == verify.INSUFFICIENT, "snippets counted as direct inspection"


def test_source_quality_method(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a"])
    out = ev.verify(cid, method=ev.SOURCE_QUALITY)
    assert out["method"] == ev.SOURCE_QUALITY
    assert "tier" in out["explanation"]


def test_cross_source_consistency_method(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    out = ev.verify(cid, method=ev.CROSS_SOURCE_CONSISTENCY)
    assert out["result"] == verify.SUPPORTED


def test_unknown_method_rejected(data_dir: Path):
    cid = ev.add_claim("x", context_id=CTX)
    with pytest.raises(ev.EvidenceError):
        ev.verify(cid, method="vibes")


def test_verification_is_recorded_with_method_and_inputs(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    ev.verify(cid, verifier="analysis_specialist", model="test-model")
    rows = ev.verifications(cid)
    assert rows[-1]["method"] == ev.INDEPENDENT_SOURCES
    assert rows[-1]["verifier"] == "analysis_specialist"
    assert rows[-1]["model"] == "test-model"
    assert rows[-1]["inputs"]["evidence"]


def test_verification_is_deterministic(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    first = ev.verify(cid, record=False)
    for _ in range(4):
        again = ev.verify(cid, record=False)
        assert again["result"] == first["result"]
        assert again["confidence"] == first["confidence"]


def test_verify_unknown_claim(data_dir: Path):
    with pytest.raises(ev.EvidenceError):
        ev.verify("clm_missing")


# --------------------------------------------------------------- confidence


def test_confidence_is_explainable(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    out = ev.verify(cid, record=False)
    f = out["factors"]
    assert f["supporting_evidence"] == 2
    assert f["contradicting_evidence"] == 0
    assert f["independent_sources"] == 2
    assert out["confidence_reason"]


def test_strong_contradiction_never_high_confidence(data_dir: Path):
    cid = _claim_with(
        ["https://nasa.gov/a"], ["https://a.example.com/x", "https://b.example.com/y"]
    )
    out = ev.verify(cid, record=False)
    assert out["confidence"] == verify.LOW


def test_model_assertion_does_not_corroborate(data_dir: Path):
    """A model saying so is not independent evidence."""
    cid = ev.add_claim("model says so", context_id=CTX)
    s1 = _inspected_source("https://nasa.gov/a")
    e1 = ev.add_evidence(cid and s1, "real body", context_id=CTX, evidence_type=ev.FULL_TEXT)
    ev.link(cid, e1, ev.SUPPORTS)
    s2 = _inspected_source("https://nih.gov/b")
    e2 = ev.add_evidence(
        s2, "the model asserts it", context_id=CTX, evidence_type=ev.MODEL_ASSERTION
    )
    ev.link(cid, e2, ev.SUPPORTS)
    out = ev.verify(cid, record=False)
    assert out["factors"]["excluded_non_corroborating"] == 1
    assert out["result"] != verify.VERIFIED, "model assertion counted as corroboration"


# ------------------------------------------------------------- contradictions


def test_conflicts_are_persisted_pairwise(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a"], ["https://blog.example.com/c"])
    ev.verify(cid)
    rows = ev.conflicts(cid)
    assert rows
    assert rows[0]["resolution"] == "unresolved"
    assert "supports" in rows[0]["explanation"]


def test_both_sides_of_a_conflict_survive(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a"], ["https://blog.example.com/c"])
    ev.verify(cid)
    rels = {r["relation"] for r in ev.claim_evidence(cid)}
    assert ev.SUPPORTS in rels and ev.CONTRADICTS in rels


def test_contested_claim_creates_unresolved_issue(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a"], ["https://blog.example.com/c"])
    ev.verify(cid)
    assert any("contested" in u["text"] for u in ev.unresolved(CTX))


# --------------------------------------------------------------- provenance


def test_provenance_traces_claim_to_source_to_verification(data_dir: Path):
    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    ev.verify(cid)
    prov = ev.provenance(cid)
    assert prov["claim"]["id"] == cid
    assert len(prov["chain"]) == 2
    for hop in prov["chain"]:
        assert hop["source"]["url"]
        assert hop["source"]["access_state"] == ev.INSPECTED
        assert hop["evidence"]["provenance"]
    assert prov["verifications"]


def test_provenance_unknown_claim(data_dir: Path):
    assert ev.provenance("clm_missing") is None


# ------------------------------------------------------- research integration


def test_research_produces_verified_evidence_claims(data_dir: Path, monkeypatch):
    from jarvis.research import engine as rengine
    from jarvis.research import store as rstore

    monkeypatch.setattr(
        rengine,
        "_default_search",
        lambda q, n: [
            {"url": "https://nasa.gov/a", "title": "A", "snippet": "supports"},
            {"url": "https://nih.gov/b", "title": "B", "snippet": "also supports"},
        ],
    )
    monkeypatch.setattr(rengine, "_default_fetch", lambda u: "agreeing body")
    rid = rengine.create_research("water boils at 100C")["research_id"]
    for phase in rengine.PHASES:
        rengine.run_phase(rid, phase)

    assert rstore.get_job(rid)["status"] == "completed"
    claims = rengine._evidence_claims(rid)
    assert claims and claims[0]["verification"]["result"] == verify.VERIFIED
    assert claims[0]["status"] == store.VERIFIED
    assert ev.sources(rid) and ev.evidence(rid)


def test_research_contradiction_survives_into_evidence_layer(data_dir: Path, monkeypatch):
    from jarvis.research import engine as rengine

    monkeypatch.setattr(
        rengine,
        "_default_search",
        lambda q, n: [
            {"url": "https://nasa.gov/a", "title": "A", "snippet": "supports"},
            {"url": "https://blog.example.com/c", "title": "C", "snippet": "this is false, a myth"},
        ],
    )
    # Research uses the fetched body as evidence when inspection succeeds, so the
    # contradiction has to live in the retrieved content, not just the snippet.
    monkeypatch.setattr(
        rengine,
        "_default_fetch",
        lambda u: "this is false, a myth, refuted" if "blog.example" in u else "supporting body",
    )
    rid = rengine.create_research("contested topic")["research_id"]
    for phase in rengine.PHASES:
        rengine.run_phase(rid, phase)
    claims = rengine._evidence_claims(rid)
    assert claims[0]["status"] in (store.CONTESTED, store.CONTRADICTED)
    assert claims[0]["conflicts"] >= 1


def test_research_unretrievable_source_not_marked_inspected(data_dir: Path, monkeypatch):
    from jarvis.research import engine as rengine

    monkeypatch.setattr(
        rengine,
        "_default_search",
        lambda q, n: [{"url": "https://blocked.example.com/x", "title": "X", "snippet": "snip"}],
    )

    def failing_fetch(url):
        raise RuntimeError("blocked")

    monkeypatch.setattr(rengine, "_default_fetch", failing_fetch)
    rid = rengine.create_research("unreachable")["research_id"]
    for phase in rengine.PHASES:
        rengine.run_phase(rid, phase)
    srcs = ev.sources(rid)
    assert srcs and srcs[0]["access_state"] == ev.UNAVAILABLE
    assert all(e["inspected"] == 0 for e in ev.evidence(rid))
    claims = rengine._evidence_claims(rid)
    assert claims[0]["status"] != store.VERIFIED


def test_existing_research_tables_still_readable(data_dir: Path, monkeypatch):
    """Backward compatibility: Milestone 4 structures are untouched."""
    from jarvis.research import engine as rengine
    from jarvis.research import store as rstore

    monkeypatch.setattr(
        rengine,
        "_default_search",
        lambda q, n: [{"url": "https://nasa.gov/a", "title": "A", "snippet": "s"}],
    )
    monkeypatch.setattr(rengine, "_default_fetch", lambda u: "body")
    rid = rengine.create_research("compat")["research_id"]
    for phase in rengine.PHASES:
        rengine.run_phase(rid, phase)
    assert rstore.claims(rid) and rstore.sources(rid) and rstore.evidence(rid)
    assert rstore.get_job(rid)["synthesis"].startswith("# Research:")


# ---------------------------------------------------------- agent permissions


def test_agent_evidence_permissions_are_split(data_dir: Path):
    assert agents.get("research_specialist").permits("evidence_add") is True
    assert agents.get("research_specialist").permits("evidence_verify") is True
    assert agents.get("analysis_specialist").permits("evidence_verify") is True
    assert agents.get("analysis_specialist").permits("evidence_add") is False
    assert agents.get("general_specialist").permits("evidence_verify") is False
    assert agents.get("general_specialist").permits("evidence_provenance") is True


def test_coding_specialist_has_no_evidence_authority(data_dir: Path):
    coding = agents.get("coding_specialist")
    for action in ("evidence_add", "evidence_verify", "evidence_claim_add", "evidence_provenance"):
        assert coding.permits(action) is False, action


def test_specialist_cannot_verify_without_permission(data_dir: Path):
    out = agents.invoke("general_specialist", "verify it", action="evidence_verify")
    assert out["ok"] is False
    assert out["error_kind"] == "permission_denied"


def test_specialist_cannot_fabricate_evidence_without_permission(data_dir: Path):
    out = agents.invoke("analysis_specialist", "add evidence", action="evidence_add")
    assert out["ok"] is False
    assert out["error_kind"] == "permission_denied"


# -------------------------------------------------------- collaboration


def test_evidence_survives_delegation(data_dir: Path):
    from jarvis.collaboration import engine as cengine
    from jarvis.collaboration import store as cstore

    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    ev.verify(cid)
    collab = cengine.create_collaboration("evidence handoff", initiator="analysis_specialist")
    tid = cengine.delegate(
        collab["collaboration_id"],
        requester="analysis_specialist",
        objective="report provenance",
        target="research_specialist",
        action="evidence_provenance",
        params={"claim_id": cid},
    )["id"]
    task = cengine.execute_task(tid)
    assert task["status"] == cstore.TASK_SUCCESS
    prov = task["result"]["output"]["provenance"]
    assert prov["claim"]["id"] == cid
    assert len(prov["chain"]) == 2
    assert prov["verifications"], "verification lost through delegation"


def test_conflicts_survive_delegation(data_dir: Path):
    from jarvis.collaboration import engine as cengine

    cid = _claim_with(["https://nasa.gov/a"], ["https://blog.example.com/c"])
    ev.verify(cid)
    collab = cengine.create_collaboration("conflict handoff", initiator="analysis_specialist")
    tid = cengine.delegate(
        collab["collaboration_id"],
        requester="analysis_specialist",
        objective="show conflicts",
        target="research_specialist",
        action="evidence_conflicts",
        params={"claim_id": cid},
    )["id"]
    task = cengine.execute_task(tid)
    assert task["result"]["output"]["conflicts"], "contradiction lost through delegation"


# ------------------------------------------------------------ missions


def test_evidence_work_checkpoints_in_a_mission(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    sid = _inspected_source("https://nasa.gov/a")
    cid = ev.add_claim("mission claim", context_id=CTX)
    steps = [
        {
            "name": "evidence",
            "action": "evidence_add",
            "params": {
                "source_id": sid,
                "excerpt": "body",
                "context_id": CTX,
                "evidence_type": ev.FULL_TEXT,
            },
        },
        {"name": "verify", "action": "evidence_verify", "params": {"claim_id": cid}},
    ]
    mid = missions.create_mission("evidence mission", steps=steps)
    missions.run(mid, lambda s, c: call_action(None, s["action"], s["params"], ""))
    assert missions.get(mid)["state"] == mstore.COMPLETED
    assert len(mstore.checkpoints(mid)) == 2
    assert ev.verifications(cid)


# ------------------------------------------------------------ handlers


def test_evidence_actions_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {s["action"] for s in all_actions()}
    for action in (
        "evidence_source_add",
        "evidence_add",
        "evidence_claim_add",
        "evidence_link",
        "evidence_claim_get",
        "evidence_list_claims",
        "evidence_verify",
        "evidence_provenance",
        "evidence_conflicts",
    ):
        assert action in names, f"{action} not registered"


def test_handler_round_trip(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    s1 = call_action(
        None, "evidence_source_add", {"url": "https://nasa.gov/a", "context_id": CTX}, ""
    )
    s2 = call_action(
        None, "evidence_source_add", {"url": "https://nih.gov/b", "context_id": CTX}, ""
    )
    assert s1["ok"] and s2["ok"]
    ev.mark_source_inspected(s1["source_id"])
    ev.mark_source_inspected(s2["source_id"])

    c = call_action(None, "evidence_claim_add", {"text": "handler claim", "context_id": CTX}, "")
    assert c["ok"] is True
    for s in (s1, s2):
        e = call_action(
            None,
            "evidence_add",
            {
                "source_id": s["source_id"],
                "excerpt": "body",
                "context_id": CTX,
                "evidence_type": ev.FULL_TEXT,
            },
            "",
        )
        assert e["ok"] is True
        assert (
            call_action(
                None,
                "evidence_link",
                {
                    "claim_id": c["claim_id"],
                    "evidence_id": e["evidence_id"],
                    "relation": ev.SUPPORTS,
                },
                "",
            )["ok"]
            is True
        )

    v = call_action(None, "evidence_verify", {"claim_id": c["claim_id"]}, "")
    assert v["ok"] is True
    assert v["verification"]["result"] == verify.VERIFIED

    p = call_action(None, "evidence_provenance", {"claim_id": c["claim_id"]}, "")
    assert p["ok"] is True and len(p["provenance"]["chain"]) == 2

    g = call_action(None, "evidence_claim_get", {"claim_id": c["claim_id"]}, "")
    assert g["ok"] is True and g["claim"]["status"] == store.VERIFIED


def test_handler_rejects_fabricated_evidence(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    out = call_action(None, "evidence_add", {"source_id": "src_nope", "excerpt": "invented"}, "")
    assert out["ok"] is False
    assert out["error_kind"] == "evidence_integrity"


# ------------------------------------------------------ isolation / reload


def test_evidence_store_is_isolated(data_dir: Path):
    ev.add_claim("isolation", context_id=CTX)
    assert data_dir in store.DB_PATH.resolve().parents


def test_module_reload_durability(data_dir: Path):
    import importlib

    cid = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"])
    ev.verify(cid)
    importlib.reload(store)
    assert store.get_claim(cid)["status"] == store.VERIFIED
    assert store.verifications(cid)


def test_contexts_do_not_interfere(data_dir: Path):
    a = _claim_with(["https://nasa.gov/a", "https://nih.gov/b"], ctx="ctxA")
    b = _claim_with(["https://blog.example.com/c"], ctx="ctxB")
    ev.verify(a)
    ev.verify(b)
    assert ev.get_claim(a)["status"] == store.VERIFIED
    assert ev.get_claim(b)["status"] == store.SUPPORTED
    assert {s["context_id"] for s in ev.sources("ctxA")} == {"ctxA"}
    assert {s["context_id"] for s in ev.sources("ctxB")} == {"ctxB"}


# ------------------------------------------------------ crash recovery

_CRASH = """
import os, sys
sys.path.insert(0, {repo!r})
os.environ["JARVIS_DATA_DIR"] = {data_dir!r}
from unittest.mock import MagicMock
sys.modules.setdefault("ollama", MagicMock())

from jarvis import evidence as ev

ctx = {ctx!r}
cid = {cid!r}
sid = ev.add_source("https://nih.gov/b", context_id=ctx)
ev.mark_source_inspected(sid)
eid = ev.add_evidence(sid, "second body", context_id=ctx, evidence_type=ev.FULL_TEXT)
ev.link(cid, eid, ev.SUPPORTS)
# Evidence is durable now. Die before verification runs.
os._exit(9)
"""


def test_evidence_survives_real_process_crash(data_dir: Path, tmp_path: Path):
    ctx = "crashctx"
    cid = ev.add_claim("crash claim", context_id=ctx)
    s1 = ev.add_source("https://nasa.gov/a", context_id=ctx)
    ev.mark_source_inspected(s1)
    e1 = ev.add_evidence(s1, "first body", context_id=ctx, evidence_type=ev.FULL_TEXT)
    ev.link(cid, e1, ev.SUPPORTS)

    script = tmp_path / "crash_evidence.py"
    script.write_text(
        textwrap.dedent(_CRASH).format(
            repo=str(REPO_ROOT), data_dir=str(data_dir), ctx=ctx, cid=cid
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["JARVIS_DATA_DIR"] = str(data_dir)
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=120, env=env
    )
    assert proc.returncode == 9, f"child did not crash: {proc.stderr[-1500:]}"

    # Both evidence items survived; nothing was verified yet.
    rows = ev.claim_evidence(cid)
    assert len(rows) == 2, "evidence lost in the crash"
    assert ev.get_claim(cid)["status"] == store.PROPOSED
    assert not ev.verifications(cid)

    # Re-adding the same evidence does not duplicate provenance.
    before = len(ev.evidence(ctx))
    ev.link(cid, e1, ev.SUPPORTS)
    assert len(ev.evidence(ctx)) == before

    out = ev.verify(cid)
    assert out["result"] == verify.VERIFIED
    assert len(ev.claim_evidence(cid)) == 2
