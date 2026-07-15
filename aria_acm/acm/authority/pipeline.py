"""Cognitive Memory Response Pipeline — classify → dispatch → result → speak."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from acm.authority.dispatch import CognitiveDispatchEngine
from acm.authority.gates import gate_status, uncertainty_label
from acm.authority.handlers import sanitize_cognitive_text
from acm.authority.result import CognitiveMemoryResult, MemoryStatus
from acm.authority.speak import speak_cognitive_result
from acm.authority.taxonomy import ORGAN_NONE

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine


class CognitiveResponsePipeline:
    """Formal pipeline: intent → ownership → dispatch → organ terminate → speak."""

    def __init__(self, engine: CognitiveEngine) -> None:
        self.engine = engine
        self.dispatcher = CognitiveDispatchEngine(engine)

    def respond(self, request: str) -> CognitiveMemoryResult:
        """Run end-to-end Cognitive Dispatch (D038 · D039 · D040)."""
        outcome = self.dispatcher.dispatch(request)
        classification = outcome.decision.classification
        organ_payload = outcome.payload
        path = list(outcome.decision.reasoning_path)

        non_cognitive = (
            classification.is_memory_request is False
            or outcome.decision.ownership.primary_organ == ORGAN_NONE
        )
        if non_cognitive:
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
                organ_payload={"ownership": outcome.decision.ownership.to_public()},
                diagnostics=outcome.record.to_public(),
            )

        path.append("cognitive_dispatch_complete")
        return self._materialize(
            classification,
            organ_payload,
            path,
            outcome.decision.ownership,
            outcome.record.to_public(),
        )

    def speak(self, result: CognitiveMemoryResult) -> str:
        """Speech only after ACM reconstruction — faithful templates."""
        if not result.language_may_speak and result.is_memory_request:
            pass
        return speak_cognitive_result(result)

    def _materialize(
        self,
        classification: Any,
        organ_payload: dict[str, Any],
        path: list[str],
        ownership: Any = None,
        diagnostics: dict[str, Any] | None = None,
    ) -> CognitiveMemoryResult:
        memory_text = sanitize_cognitive_text(organ_payload.get("memory"))
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
        if getattr(classification, "uncertain", False) and status == MemoryStatus.KNOWN:
            if conf < 0.75 or not organ_payload.get("cue_matched"):
                status = MemoryStatus.LOW_CONFIDENCE
                path.append("uncertain_classification_cap")
        path.append(f"gate:{status.value}")

        terminated = str(
            (diagnostics or {}).get("terminated_at")
            or organ_payload.get("terminated_at")
            or (ownership.primary_organ if ownership is not None else "")
        )
        if terminated and terminated not in ("", ORGAN_NONE):
            path.append(f"terminated_at:{terminated}")

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

        diag = dict(diagnostics or {})
        diag.setdefault("intent", classification.intent.value)
        diag.setdefault(
            "primary_organ",
            ownership.primary_organ if ownership is not None else "",
        )
        diag.setdefault(
            "supporting_organs",
            list(ownership.supporting_organs) if ownership is not None else [],
        )
        diag["confidence"] = conf
        diag["uncertainty"] = uncertainty_label(status, conf)
        diag["provenance_count"] = len(provenance)
        diag["infrastructure_role"] = diag.get("infrastructure_role") or "substrate_only"

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
            classification={
                **classification.to_public(),
                "ownership": ownership.to_public() if ownership is not None else {},
            },
            organ_payload={
                k: v
                for k, v in organ_payload.items()
                if k not in ("raw", "dispatch")
            },
            diagnostics=diag,
        )
        path.append("cognitive_memory_result")
        result.reasoning_path = list(path)
        return result
