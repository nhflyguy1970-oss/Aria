"""Choosing between permitted local and cloud models — explainably.

Ranking order (earlier criteria always dominate later ones):

  1. privacy and authorization — local-only requests never see a cloud
     candidate; a cloud candidate needs cloud enabled, a permitted provider,
     credentials and an active owner authorization covering the role
  2. capabilities — tools, vision, … as the model/provider reports them
  3. measured correctness — accuracy on ARIA's own workload benchmark for the
     role's category (``data/model_quality.json``); unmeasured ranks below
     measured
  4. availability — installed locally / provider circuit closed
  5. context — the request must fit the model's context window
  6. latency — measured p50
  7. cost — estimated per-call cost from the operator's price table

The default conversation stays local: cloud candidates are only *considered*
for automatic selection when the operator turns on ``auto_escalate`` in
``data/cloud_routing.json``. An explicitly requested cloud model goes through
the gateway's own checks; nothing here can override privacy or cloud-disable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.inference import boundary

QUALITY_FILE = DATA_DIR / "model_quality.json"
ROUTING_FILE = DATA_DIR / "cloud_routing.json"

# ARIA role → benchmark category it is judged on.
ROLE_CATEGORY = {
    "conversation": "reasoning",
    "general": "reasoning",
    "reasoning": "reasoning",
    "planning": "reasoning",
    "router": "routing",
    "tool_calling": "tool_routing",
    "summarization": "memory",
    "research": "evidence",
    "web_research": "evidence",
    "coder": "coding",
    "coding": "coding",
    "vision": "vision",
}


def _load(path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def routing_config() -> dict[str, Any]:
    return {"auto_escalate": False, "candidates": {}, "quality": {}, **_load(ROUTING_FILE)}


def measured(model: str, category: str) -> dict[str, Any] | None:
    """Benchmark accuracy/latency for a model on a category, if measured."""
    by_model = (_load(QUALITY_FILE).get("by_model") or {}).get(model) or {}
    cat = (by_model.get("categories") or {}).get(category)
    if cat:
        return cat
    declared = (routing_config().get("quality") or {}).get(model) or {}
    if category in declared:
        return {"accuracy": float(declared[category]), "p50_ms": None, "declared": True}
    return None


@dataclass
class Candidate:
    model: str
    locality: str
    eligible: bool = True
    excluded_by: str = ""
    accuracy: float | None = None
    p50_ms: float | None = None
    est_cost_usd: float | None = None
    notes: list[str] = field(default_factory=list)

    def sort_key(self) -> tuple:
        return (
            0 if self.accuracy is not None else 1,  # measured before unmeasured
            -(self.accuracy or 0.0),
            self.p50_ms if self.p50_ms is not None else 1e9,
            self.est_cost_usd if self.est_cost_usd is not None else 0.0,
        )


@dataclass
class Decision:
    chosen: Candidate | None
    candidates: list[Candidate]
    explanation: list[str]


def choose(
    role: str,
    *,
    needs: set[str] | None = None,
    privacy: str = boundary.STANDARD,
    context_tokens: int = 0,
    include_cloud: bool | None = None,
) -> Decision:
    needs = set(needs or ())
    category = ROLE_CATEGORY.get(role, "reasoning")
    config = routing_config()
    consider_cloud = config.get("auto_escalate") if include_cloud is None else include_cloud
    explanation = [f"role={role} judged on '{category}'; needs={sorted(needs) or 'none'}"]
    pool: list[Candidate] = []

    # ---- local candidate(s)
    try:
        local = boundary.local_fallback(role)
        pool.append(Candidate(model=local, locality=boundary.LOCAL))
    except boundary.ProviderUnavailable as exc:
        explanation.append(f"no installed local model: {exc}")

    # ---- cloud candidates (operator-listed, never hardcoded)
    for model in (config.get("candidates") or {}).get(role, []) if consider_cloud else []:
        pool.append(Candidate(model=model, locality=boundary.CLOUD))
    if not consider_cloud:
        explanation.append("cloud not considered for automatic selection (auto_escalate off)")

    for cand in pool:
        _evaluate(cand, role, category, needs, privacy, context_tokens)

    eligible = sorted((c for c in pool if c.eligible), key=Candidate.sort_key)
    for c in pool:
        if not c.eligible:
            explanation.append(f"{c.model}: excluded — {c.excluded_by}")
    chosen = eligible[0] if eligible else None
    if chosen:
        acc = f"{chosen.accuracy:.0%}" if chosen.accuracy is not None else "unmeasured"
        explanation.append(
            f"chose {chosen.model} ({chosen.locality}; {category} accuracy {acc}"
            + (f"; p50 {chosen.p50_ms:.0f} ms" if chosen.p50_ms else "")
            + (f"; ~${chosen.est_cost_usd:.4f}" if chosen.est_cost_usd else "")
            + ")"
        )
        for other in eligible[1:]:
            explanation.append(f"ranked below: {other.model} ({other.locality})")
    else:
        explanation.append("no eligible model")
    return Decision(chosen, pool, explanation)


def _evaluate(cand: Candidate, role: str, category: str, needs: set[str], privacy: str, ctx: int) -> None:
    def exclude(reason: str) -> None:
        cand.eligible = False
        cand.excluded_by = reason

    # 1. privacy and authorization
    if cand.locality == boundary.CLOUD:
        refusal = boundary.cloud_refusal(cand.model, privacy=privacy)
        if refusal:
            return exclude(refusal)
        from jarvis.inference import cloud_policy
        from jarvis.inference.providers import circuit_open, has_credentials, split_model

        provider, _ = split_model(cand.model)
        if not has_credentials(provider):
            return exclude(f"no {provider} API credential")
        if cloud_policy.active_authorization(provider, role) is None:
            return exclude("no active owner authorization for this role")
        # 4. availability (checked early for cloud: cheap and decisive)
        if circuit_open(provider):
            return exclude(f"{provider} temporarily unavailable (circuit open)")
        cand.est_cost_usd = cloud_policy.estimate_cost(cand.model, max(ctx, 1), 1024)
        if cand.est_cost_usd is None:
            return exclude("no price configured")
    # 2. capabilities
    caps = boundary.model_capabilities(cand.model)
    if needs and caps is not None and not needs <= set(caps):
        return exclude(f"lacks {', '.join(sorted(needs - set(caps)))}")
    if needs and caps is None:
        cand.notes.append("capabilities unknown")
    # 3. measured correctness
    m = measured(cand.model, category)
    if m:
        cand.accuracy = m.get("accuracy")
        cand.p50_ms = m.get("p50_ms")
        if m.get("declared"):
            cand.notes.append("operator-declared quality (not measured locally)")
    # 5. context
    if cand.locality == boundary.CLOUD and ctx:
        from jarvis.inference.providers import discovered_model

        window = (discovered_model(cand.model) or {}).get("context_window")
        if window and ctx > int(window):
            return exclude(f"needs {ctx} tokens; window {window}")


def import_benchmark(summary_path: str) -> dict[str, Any]:
    """Adopt a Phase 3 benchmark summary as ARIA's measured model quality."""
    from jarvis.live_data_guard import assert_live_write_allowed

    data = json.loads(open(summary_path, encoding="utf-8").read())
    out = {"source": summary_path, "by_model": data.get("by_model") or {}}
    assert_live_write_allowed(QUALITY_FILE)
    QUALITY_FILE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return {"models": len(out["by_model"])}
