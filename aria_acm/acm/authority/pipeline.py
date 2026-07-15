"""Cognitive Memory Response Pipeline — ACM before any language generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from acm.authority.classification import (
    MemoryIntent,
    classify_memory_request,
)
from acm.authority.gates import gate_status, uncertainty_label
from acm.authority.result import CognitiveMemoryResult, MemoryStatus
from acm.authority.speak import speak_cognitive_result

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine


class CognitiveResponsePipeline:
    """Formal pipeline: classify → ACM reconstruct → structured result → optional speak."""

    def __init__(self, engine: CognitiveEngine) -> None:
        self.engine = engine

    def respond(self, request: str) -> CognitiveMemoryResult:
        """Run the Memory Authority pipeline for one inbound request."""
        classification = classify_memory_request(request)
        path: list[str] = ["classify_memory_request"]

        if not classification.is_memory_request:
            path.append("bypass_non_memory")
            return CognitiveMemoryResult(
                status=MemoryStatus.NOT_MEMORY,
                is_memory_request=False,
                intent=classification.intent.value,
                memory=None,
                confidence=classification.confidence,
                language_may_speak=False,
                allow_encode_from_speech=False,
                classification=classification.to_public(),
                reasoning_path=path,
            )

        path.append(f"route:{classification.intent.value}")
        organ_payload, organ_path = self._route(classification.intent, request)
        path.extend(organ_path)

        return self._materialize(classification, organ_payload, path)

    def speak(self, result: CognitiveMemoryResult) -> str:
        """Speech only after ACM reconstruction — faithful templates."""
        if not result.language_may_speak and result.is_memory_request:
            # Still allow speak for unknown statuses (communicating uncertainty).
            pass
        return speak_cognitive_result(result)

    def _route(self, intent: MemoryIntent, request: str) -> tuple[dict[str, Any], list[str]]:
        engine = self.engine
        path: list[str] = []

        if intent == MemoryIntent.IDENTITY:
            path.append("who_am_i")
            who = engine.who_am_i()
            return {
                "memory": who.get("answer"),
                "confidence": float(who.get("confidence") or 0.0),
                "explanation_class": who.get("explanation_class") or "experience",
                "ambiguous": False,
                "concepts": who.get("central_concepts") or [],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": who,
            }, path

        if intent == MemoryIntent.LEARNING:
            path.append("learn")
            learned = engine.learn(cue=request)
            answer = learned.get("answer")
            adaptations = learned.get("adaptations") or []
            lessons = learned.get("lessons") or []
            conf = 0.75 if adaptations or lessons else 0.0
            if not answer and adaptations:
                answer = "; ".join(str(a) for a in lessons[:3]) or "Learned adaptations recorded."
            return {
                "memory": answer if adaptations or lessons else None,
                "confidence": conf,
                "explanation_class": "experience" if adaptations else "unknown",
                "ambiguous": False,
                "concepts": [],
                "cue_matched": bool(adaptations or lessons),
                "experiences": [],
                "associations": [],
                "learning": adaptations or lessons,
                "raw": learned,
            }, path

        if intent in (MemoryIntent.REFLECTION, MemoryIntent.CONFIDENCE):
            if intent == MemoryIntent.CONFIDENCE or "certain" in request.lower():
                path.append("how_certain_am_i")
                certain = engine.how_certain_am_i(request)
                return {
                    "memory": certain.get("answer"),
                    "confidence": float(certain.get("overall_confidence") or 0.0),
                    "explanation_class": "experience",
                    "ambiguous": False,
                    "concepts": [],
                    "cue_matched": True,
                    "experiences": [],
                    "associations": [],
                    "raw": certain,
                }, path
            path.append("what_do_i_think")
            thought = engine.what_do_i_think(request)
            return {
                "memory": thought.get("summary") or thought.get("answer"),
                "confidence": float(thought.get("confidence") or 0.5),
                "explanation_class": (
                    "unknown" if thought.get("insufficient_evidence") else "experience"
                ),
                "ambiguous": bool(thought.get("hypotheses")),
                "concepts": [],
                "cue_matched": not bool(thought.get("insufficient_evidence")),
                "experiences": [],
                "associations": [],
                "reflective": thought.get("outcomes") or [],
                "raw": thought,
            }, path

        if intent == MemoryIntent.RECONCILIATION:
            path.append("how_should_memory_reconcile")
            recon = engine.how_should_memory_reconcile(request)
            return {
                "memory": recon.get("answer"),
                "confidence": float((recon.get("reconciliation") or {}).get("confidence") or 0.4),
                "explanation_class": "contested",
                "ambiguous": True,
                "concepts": [],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": recon,
            }, path

        # Default cognitive remembering path (experiences, preferences, autobiography, …)
        path.append("remember")
        remembered = engine.remember(request)
        recon = remembered.reconstruction or {}
        cue = request.lower()
        cue_tokens = [t for t in cue.split() if len(t) > 2]
        memory_text = (remembered.answer or "").strip()
        # Cue grounding: memory text or primary label shares a token with the cue
        primary_label = str(recon.get("primary_label") or "")
        cue_matched = bool(memory_text) and (
            any(tok in memory_text.lower() for tok in cue_tokens)
            or any(tok in primary_label.lower() for tok in cue_tokens)
            or remembered.explanation_class.value == "preference"
            or bool(recon.get("identity_influenced"))
        )
        concepts = [
            {"id": cid}
            for cid in (remembered.activated_concept_ids or [])[:8]
        ]
        experiences = [
            {"id": eid, "summary": summary}
            for eid, summary in zip(
                recon.get("experience_ids") or [],
                recon.get("experience_summaries") or [],
                strict=False,
            )
        ]
        associations = [{"id": aid} for aid in (recon.get("association_ids") or [])[:8]]
        return {
            "memory": memory_text or None,
            "confidence": float(remembered.confidence),
            "explanation_class": remembered.explanation_class.value,
            "ambiguous": bool(remembered.ambiguous),
            "concepts": concepts,
            "cue_matched": cue_matched,
            "experiences": experiences,
            "associations": associations,
            "raw": recon,
        }, path

    def _materialize(
        self,
        classification: Any,
        organ_payload: dict[str, Any],
        path: list[str],
    ) -> CognitiveMemoryResult:
        memory_text = organ_payload.get("memory")
        if isinstance(memory_text, str):
            memory_text = memory_text.strip() or None
        conf = float(organ_payload.get("confidence") or 0.0)
        expl = str(organ_payload.get("explanation_class") or "unknown")
        ambiguous = bool(organ_payload.get("ambiguous"))
        experiences = list(organ_payload.get("experiences") or [])
        concepts = list(organ_payload.get("concepts") or [])
        associations = list(organ_payload.get("associations") or [])
        status = gate_status(
            explanation_class=expl,
            confidence=conf,
            ambiguous=ambiguous,
            has_memory_text=bool(memory_text),
            supporting_experience_count=len(experiences),
            cue_matched=bool(organ_payload.get("cue_matched")),
        )
        path.append(f"gate:{status.value}")

        # Authority: strip propositional memory when not KNOWN / CONFLICTING disclosure
        authoritative_memory = memory_text
        if status in (
            MemoryStatus.UNKNOWN,
            MemoryStatus.INSUFFICIENT_EVIDENCE,
            MemoryStatus.LOW_CONFIDENCE,
        ):
            authoritative_memory = None

        provenance: list[dict[str, Any]] = []
        for item in experiences[:6]:
            eid = item.get("id") if isinstance(item, dict) else None
            if not eid:
                continue
            try:
                prov_list = self.engine.provenance_of(str(eid))
                if isinstance(prov_list, list) and prov_list:
                    provenance.extend(prov_list[:2])
                else:
                    provenance.append({"artifact_id": eid, "origin": "experience"})
            except Exception:
                provenance.append({"artifact_id": eid, "origin": "experience"})

        result = CognitiveMemoryResult(
            status=status,
            is_memory_request=True,
            intent=classification.intent.value,
            memory=authoritative_memory if status != MemoryStatus.CONFLICTING else memory_text,
            confidence=conf,
            uncertainty=uncertainty_label(status, conf),
            explanation_class=expl,
            provenance=provenance,
            supporting_experiences=experiences,
            supporting_concepts=concepts,
            supporting_associations=associations,
            reflective_evidence=list(organ_payload.get("reflective") or []),
            learning_evidence=list(organ_payload.get("learning") or []),
            reasoning_path=path,
            ambiguous=ambiguous,
            language_may_speak=True,
            allow_encode_from_speech=False,
            classification=classification.to_public(),
            organ_payload={
                k: v for k, v in organ_payload.items() if k != "raw"
            },
        )
        path.append("cognitive_memory_result")
        result.reasoning_path = list(path)
        return result
