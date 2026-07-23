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
        """Run end-to-end Cognitive Dispatch (D038 · D039 · D040).

        Declarative teachings are encoded *before* dispatch (Teaching
        Recognition), so the reconstruction that answers the request reflects
        the updated memory. The encode passes through the full Trusted Memory
        Ingestion gate and content-level artifact protection — Teaching
        Recognition adds no bypass.
        """
        teach_path = self._teach_if_declarative(request)
        outcome = self.dispatcher.dispatch(request)
        classification = outcome.decision.classification
        organ_payload = outcome.payload
        path = teach_path + list(outcome.decision.reasoning_path)

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
        result = self._materialize(
            classification,
            organ_payload,
            path,
            outcome.decision.ownership,
            outcome.record.to_public(),
            request=request,
        )
        return result

    def _teach_if_declarative(self, request: str) -> list[str]:
        """Teaching Recognition: encode declarative user statements pre-dispatch.

        Hosts invoke ``cognitive_respond`` with inbound user conversation
        messages, so the teaching is submitted as a trusted user statement.
        ``encode`` still applies D046 ingestion policy and content-level
        artifact rejection — tool/system/infra payloads never become memory
        even here, and interrogatives never reach this encode at all.

        Read-only diagnostic mode (B07) never encodes teachings.
        """
        from acm.authority.mode import is_read_only
        from acm.authority.teaching import detect_teaching
        from acm.provenance import TRUSTED_USER_STATEMENT

        teaching = detect_teaching(request)
        if not teaching.is_teaching:
            return []
        if is_read_only():
            return ["teaching_detected", "teaching_skipped_read_only"]
        path = ["teaching_detected"]
        encode_result = self.engine.encode(request, provenance=TRUSTED_USER_STATEMENT)
        if encode_result.get("encoded"):
            path.append("teaching_encoded")
        else:
            reason = str(encode_result.get("reason") or "rejected")
            path.append(f"teaching_rejected:{reason}")
        return path

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
        request: str = "",
    ) -> CognitiveMemoryResult:
        from acm.authority.taxonomy import CognitiveIntent
        from acm.identity.rendering import (
            IdentityRenderTarget,
            is_relationship_identity_request,
            isolate_identity_text,
        )

        memory_text = sanitize_cognitive_text(organ_payload.get("memory"))
        # D044 — identity rendering isolation at CognitiveMemoryResult boundary
        intent = classification.intent
        if intent in (CognitiveIntent.USER_IDENTITY, CognitiveIntent.ASSISTANT_IDENTITY):
            if not is_relationship_identity_request(request):
                path.append("identity_render_isolate")
                if intent == CognitiveIntent.USER_IDENTITY:
                    agent = self.engine.identity.schema_concept("agent")
                    forbidden = {
                        a.value for a in agent.attributes if a.active and a.key == "name"
                    }
                    if self.engine.agent_id:
                        forbidden.add(str(self.engine.agent_id))
                    memory_text = isolate_identity_text(
                        memory_text,
                        target=IdentityRenderTarget.USER,
                        forbidden_values=forbidden,
                    )
                else:
                    user = self.engine.identity.schema_concept("user")
                    forbidden = {
                        a.value
                        for a in user.attributes
                        if a.active and a.key in ("name", "preferred_name", "location")
                    }
                    memory_text = isolate_identity_text(
                        memory_text,
                        target=IdentityRenderTarget.ASSISTANT,
                        forbidden_values=forbidden,
                    )
                    if not memory_text:
                        # Never leave assistant identity empty after isolation
                        who = self.engine.identity.render_assistant_identity()
                        memory_text = sanitize_cognitive_text(who.get("answer"))
                        organ_payload = dict(organ_payload)
                        organ_payload["confidence"] = float(who.get("confidence") or 0.95)
                        organ_payload["cue_matched"] = True
                        organ_payload["explanation_class"] = "experience"

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
