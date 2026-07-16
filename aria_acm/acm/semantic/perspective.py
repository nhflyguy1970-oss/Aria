"""Conversational perspective resolution — user vs assistant vs third party."""

from __future__ import annotations

import re

from acm.semantic.model import PerspectiveResolution, PerspectiveSubject
from acm.semantic.strip import has_remember_instruction

_USER_REFERENT = re.compile(
    r"\b(user'?s?\s+name|the\s+user\s+is|about\s+the\s+user)\b",
    re.I,
)
_ASSISTANT_ADDRESS = re.compile(
    r"\b(you\s+are|your\s+name\s+is|call\s+yourself)\b",
    re.I,
)
_FIRST_PERSON = re.compile(r"\b(i|i'?m|me|my|mine|myself)\b", re.I)
_SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself)\b", re.I)


def resolve_perspective(
    text: str,
    *,
    kind: str = "experience",
    speaker: str | None = None,
) -> PerspectiveResolution:
    """Determine who first-person / second-person refer to.

    Rules (host-independent):
    - Explicit speaker="user"|"assistant" wins.
    - "please remember" / teaching cues → first person = user (autobiographical teaching).
    - "you are" / "your name" → second person = assistant; subject for those facts = assistant.
    - kind=="identity" without teaching cues → first person = assistant (self-encode compat).
    - Otherwise first person defaults to user (human conversational autobiography).
    """
    t = text or ""
    hint = (speaker or "").strip().lower() or None

    if hint in ("user", "human"):
        return PerspectiveResolution(
            first_person=PerspectiveSubject.USER,
            second_person=PerspectiveSubject.ASSISTANT,
            speaker_hint="user",
            reason="explicit_speaker_user",
        )
    if hint in ("assistant", "agent", "self"):
        return PerspectiveResolution(
            first_person=PerspectiveSubject.ASSISTANT,
            second_person=PerspectiveSubject.USER,
            speaker_hint="assistant",
            reason="explicit_speaker_assistant",
        )

    if _USER_REFERENT.search(t):
        return PerspectiveResolution(
            first_person=PerspectiveSubject.USER,
            second_person=PerspectiveSubject.ASSISTANT,
            speaker_hint=hint,
            reason="user_referent_language",
        )

    if has_remember_instruction(t):
        return PerspectiveResolution(
            first_person=PerspectiveSubject.USER,
            second_person=PerspectiveSubject.ASSISTANT,
            speaker_hint=hint,
            reason="remember_instruction_teaching",
        )

    if kind == "identity" and not _ASSISTANT_ADDRESS.search(t):
        # Self-encode path used by existing identity tests / agent autobiography
        return PerspectiveResolution(
            first_person=PerspectiveSubject.ASSISTANT,
            second_person=PerspectiveSubject.USER,
            speaker_hint=hint,
            reason="identity_kind_self_encode",
        )

    if kind in ("preference", "experience", "") or kind not in ("identity",):
        # Conversational default: human first-person
        if _FIRST_PERSON.search(t) or not _ASSISTANT_ADDRESS.search(t):
            return PerspectiveResolution(
                first_person=PerspectiveSubject.USER,
                second_person=PerspectiveSubject.ASSISTANT,
                speaker_hint=hint,
                reason="conversational_default_user",
            )

    return PerspectiveResolution(
        first_person=PerspectiveSubject.USER,
        second_person=PerspectiveSubject.ASSISTANT,
        speaker_hint=hint,
        reason="default_user",
    )


def subject_for_first_person(perspective: PerspectiveResolution) -> PerspectiveSubject:
    return perspective.first_person


def subject_for_second_person(perspective: PerspectiveResolution) -> PerspectiveSubject:
    return perspective.second_person
