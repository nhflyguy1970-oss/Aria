"""Observable identity memory pipeline trace — evidence for encode→retrieve."""

from __future__ import annotations

from typing import Any

from acm.provenance import IngestionProvenance
from acm.semantic import extract_semantics


def trace_identity_pipeline(
    engine: Any,
    *,
    provenance: IngestionProvenance,
    utterance: str = "My name is Jeff.",
    query: str = "Who am I?",
    pin: bool = True,
) -> dict[str, Any]:
    """Run one identity fact through the full pipeline and record every stage.

    Does not redesign organs — observes existing encode / respond paths.
    """
    stages: list[dict[str, Any]] = []

    stages.append(
        {
            "stage": "natural_language_received",
            "arrived": True,
            "value": utterance,
        }
    )

    extraction = extract_semantics(utterance, kind="experience")
    stages.append(
        {
            "stage": "semantic_extraction",
            "arrived": True,
            "changed": True,
            "value": extraction.to_public(),
            "rejected": extraction.raw_fallback,
        }
    )
    stages.append(
        {
            "stage": "perspective_resolution",
            "arrived": extraction.perspective is not None,
            "value": None
            if extraction.perspective is None
            else {
                "first_person": extraction.perspective.first_person.value,
                "second_person": extraction.perspective.second_person.value,
                "reason": extraction.perspective.reason,
            },
        }
    )
    facts = [f.to_public() for f in extraction.facts]
    stages.append(
        {
            "stage": "structured_cognitive_fact",
            "arrived": bool(facts),
            "value": facts,
        }
    )

    encoded = engine.encode(utterance, pin=pin, provenance=provenance)
    identity_result = encoded.get("identity") or {}
    stages.append(
        {
            "stage": "identity_organ_input",
            "arrived": bool(extraction.facts),
            "value": {
                "facts": facts,
                "encode_kind": "experience",
                "pin": pin,
            },
        }
    )
    stages.append(
        {
            "stage": "identity_organ_storage",
            "arrived": bool(identity_result.get("identity")),
            "stored": identity_result.get("status") in ("adopted", "strengthened", "superseded"),
            "merged": identity_result.get("status") == "strengthened",
            "rewritten": identity_result.get("status") == "superseded",
            "rejected": identity_result.get("status") == "proposed",
            "value": identity_result,
        }
    )

    exp_id = str(encoded.get("experience_id") or "")
    exp = engine.store.experiences.get(exp_id) if exp_id else None
    stages.append(
        {
            "stage": "database_representation",
            "arrived": exp is not None,
            "indexed": exp is not None,
            "stored": exp is not None,
            "value": None
            if exp is None
            else {
                "experience_id": exp.id,
                "summary": exp.summary,
                "metadata": dict(exp.metadata),
            },
        }
    )

    user = engine.identity.schema_concept("user")
    record = [
        {
            "subject": "user",
            "property": a.key,
            "value": a.value,
            "confidence": a.confidence,
            "active": a.active,
            "version": a.version,
            "evidence_ids": list(a.evidence_ids),
            "storage_location": f"identity.schema.user.attributes[{a.key}]",
        }
        for a in user.attributes
        if a.active
    ]
    stages.append(
        {
            "stage": "identity_structured_record",
            "arrived": bool(record),
            "value": record,
        }
    )

    result = engine.cognitive_respond(query)
    speech = engine.speak_cognitive_result(result) if result.get("is_memory_request") else ""
    stages.append(
        {
            "stage": "remembering_retrieval",
            "arrived": bool(result.get("memory")),
            "retrieved": bool(result.get("memory")),
            "value": {
                "intent": result.get("intent"),
                "memory": result.get("memory"),
                "diagnostics": result.get("diagnostics"),
            },
        }
    )
    stages.append(
        {
            "stage": "confidence_calculation",
            "arrived": True,
            "confidence_reduced": float(result.get("confidence") or 0) < 0.7,
            "value": {
                "confidence": result.get("confidence"),
                "status": result.get("status"),
                "uncertainty": result.get("uncertainty"),
                "gate_threshold_min_known": 0.42,
                "name_attribute_confidence": next(
                    (a.confidence for a in user.attributes if a.key == "name" and a.active),
                    None,
                ),
                "schema_confidence": user.confidence,
                "reason": (
                    "User-identity confidence uses max(structured attribute confidences) "
                    "when name/role/etc. exist; schema.confidence alone is not authoritative."
                ),
            },
        }
    )
    stages.append(
        {
            "stage": "cognitive_memory_result",
            "arrived": True,
            "value": {
                "status": result.get("status"),
                "memory": result.get("memory"),
                "confidence": result.get("confidence"),
                "intent": result.get("intent"),
            },
        }
    )
    stages.append(
        {
            "stage": "faithful_language_rendering",
            "arrived": bool(speech),
            "value": speech,
        }
    )

    ok = (
        any(a.key == "name" and a.value == "Jeff" and a.active for a in user.attributes)
        and result.get("status") == "known"
        and "your name is jeff" in (result.get("memory") or "").lower()
        and "your name is jeff" in speech.lower()
        and "mentioned" not in speech.lower()
    )
    return {
        "ok": ok,
        "utterance": utterance,
        "query": query,
        "stages": stages,
        "success_criterion": "Who am I? → Your name is Jeff. (known, no mentioned pollution)",
    }


def trace_assistant_identity_pipeline(
    engine: Any,
    *,
    query: str = "Who are you?",
) -> dict[str, Any]:
    """Observe the Assistant Identity recall path (D043 / B44).

    Does not teach or mutate user identity. Asserts operational agent speech with
    no user-name bleed.
    """
    stages: list[dict[str, Any]] = []
    stages.append({"stage": "natural_language_received", "arrived": True, "value": query})

    classification = engine.classify_request(query)
    stages.append(
        {
            "stage": "intent_classification",
            "arrived": True,
            "value": classification if isinstance(classification, dict) else str(classification),
        }
    )

    route = engine.route_request(query)
    ownership = (route or {}).get("ownership") or {}
    stages.append(
        {
            "stage": "ownership",
            "arrived": ownership.get("primary_organ") == "identity",
            "value": ownership,
            "no_remembering_support": "remembering"
            not in (ownership.get("supporting_organs") or ()),
        }
    )

    rendered = engine.identity.render_assistant_identity()
    stages.append(
        {
            "stage": "identity_organ_render",
            "arrived": bool(rendered.get("answer")),
            "value": {
                "answer": rendered.get("answer"),
                "confidence": rendered.get("confidence"),
                "source": rendered.get("source"),
                "reseeded_operational_name": rendered.get("reseeded_operational_name"),
                "schemas": rendered.get("schemas"),
            },
        }
    )

    result = engine.cognitive_respond(query)
    speech = engine.speak_cognitive_result(result) if result.get("is_memory_request") else ""
    stages.append(
        {
            "stage": "cognitive_memory_result",
            "arrived": True,
            "value": {
                "intent": result.get("intent"),
                "status": result.get("status"),
                "memory": result.get("memory"),
                "confidence": result.get("confidence"),
                "diagnostics": result.get("diagnostics"),
            },
        }
    )
    stages.append(
        {
            "stage": "faithful_language_rendering",
            "arrived": bool(speech),
            "value": speech,
        }
    )

    user = engine.identity.schema_concept("user")
    user_names = {
        a.value.casefold()
        for a in user.attributes
        if a.key == "name" and a.active and a.value
    }
    agent_name = engine.identity.profile.resolved_name(engine.agent_id)
    memory = (result.get("memory") or speech or "").lower()
    bleed = any(n and n in memory for n in user_names if n != agent_name.casefold())
    ok = (
        result.get("intent") in ("assistant_identity", "identity")
        and bool(result.get("memory") or speech)
        and agent_name.lower() in memory
        and not bleed
        and "your name is" not in memory
    )
    return {
        "ok": ok,
        "query": query,
        "stages": stages,
        "user_bleed": bleed,
        "operational_name": agent_name,
        "success_criterion": (
            f"Who are you? → operational name {agent_name!r}; no user identity bleed"
        ),
    }
