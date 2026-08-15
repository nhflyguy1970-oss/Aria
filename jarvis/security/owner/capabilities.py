"""Normative capability catalog — Rooms request; Security authorizes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Risk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Capability:
    id: str
    risk: Risk
    description: str
    rooms: frozenset[str]  # rooms that may request (not auto-grant)


# Derived from existing Aria products — not an invented mega-IAM.
CAPABILITIES: dict[str, Capability] = {
    c.id: c
    for c in (
        Capability("owner.unlock", Risk.CRITICAL, "Unlock owner vault/session", frozenset({"security"})),
        Capability("owner.lock", Risk.LOW, "Lock owner session", frozenset({"security", "*"})),
        Capability("owner.step_up", Risk.HIGH, "Elevate for high-risk ops", frozenset({"security", "health", "journal", "integrations"})),
        Capability("owner.recovery", Risk.CRITICAL, "Recover vault with recovery key", frozenset({"security"})),
        Capability("security.read", Risk.LOW, "Read security status", frozenset({"security", "mission"})),
        Capability("security.modify", Risk.CRITICAL, "Change security settings", frozenset({"security"})),
        Capability("vault.meta.read", Risk.LOW, "Read non-secret vault metadata", frozenset({"security", "integrations"})),
        Capability("vault.secret.use", Risk.MEDIUM, "Use secret without revealing", frozenset({"integrations", "ha", "lan", "coding", "automation", "engineering", "voice", "models"})),
        Capability("vault.secret.migrate", Risk.MEDIUM, "Copy env secret into vault (no reveal)", frozenset({"security", "integrations"})),
        Capability("vault.secret.reveal", Risk.HIGH, "Reveal secret in UI", frozenset({"security", "integrations"})),
        Capability("vault.secret.write", Risk.HIGH, "Write/rotate vault secret", frozenset({"security", "integrations"})),
        Capability("journal.read", Risk.LOW, "Read journal", frozenset({"journal"})),
        Capability("journal.write", Risk.LOW, "Write journal", frozenset({"journal"})),
        Capability("journal.export", Risk.HIGH, "Portable encrypted export", frozenset({"journal"})),
        Capability("journal.import", Risk.HIGH, "Portable encrypted import", frozenset({"journal"})),
        Capability("health.read", Risk.MEDIUM, "Read health record", frozenset({"health"})),
        Capability("health.write", Risk.HIGH, "Write health record", frozenset({"health"})),
        Capability("health.export", Risk.HIGH, "Export PHR / encrypted backup", frozenset({"health"})),
        Capability("health.delete", Risk.CRITICAL, "Delete health data", frozenset({"health"})),
        Capability("integrations.read", Risk.LOW, "Read integration status", frozenset({"integrations", "providers"})),
        Capability("integrations.modify", Risk.HIGH, "Modify integrations/secrets", frozenset({"integrations", "providers"})),
        Capability("ha.read", Risk.LOW, "Read Home Assistant state", frozenset({"ha", "home"})),
        Capability("ha.actuate", Risk.MEDIUM, "Actuate HA devices", frozenset({"ha", "home"})),
        Capability("git.read", Risk.LOW, "Read git status", frozenset({"coding"})),
        Capability("git.write", Risk.HIGH, "Git write / push", frozenset({"coding"})),
        Capability("browser.credentials.use", Risk.MEDIUM, "Use browser profile", frozenset({"browser"})),
        Capability("automation.read", Risk.LOW, "Read automation config", frozenset({"automation"})),
        Capability("automation.modify", Risk.HIGH, "Modify automation secrets", frozenset({"automation"})),
        Capability("actions.execute", Risk.MEDIUM, "Execute tools/actions", frozenset({"coding", "tools", "*"})),
        Capability("uncensored.enable", Risk.HIGH, "Enable uncensored mode", frozenset({"security", "chat"})),
    )
}


@dataclass
class AuthDecision:
    ok: bool
    capability: str
    risk: str
    reason: str
    step_up_required: bool = False
    locked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "capability": self.capability,
            "risk": self.risk,
            "reason": self.reason,
            "step_up_required": self.step_up_required,
            "locked": self.locked,
        }


def catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": c.id,
            "risk": c.risk.value,
            "description": c.description,
            "rooms": sorted(c.rooms),
        }
        for c in sorted(CAPABILITIES.values(), key=lambda x: x.id)
    ]


def authorize(
    capability_id: str,
    *,
    owner_unlocked: bool,
    step_up_valid: bool,
    room: str | None = None,
) -> AuthDecision:
    cap = CAPABILITIES.get(capability_id)
    if not cap:
        return AuthDecision(
            ok=False,
            capability=capability_id,
            risk="UNKNOWN",
            reason="Unknown capability",
        )
    if room and "*" not in cap.rooms and room not in cap.rooms:
        return AuthDecision(
            ok=False,
            capability=capability_id,
            risk=cap.risk.value,
            reason=f"Room {room!r} may not request {capability_id}",
        )

    # Unlock/recovery are allowed while locked (auth boundary).
    if capability_id in ("owner.unlock", "owner.recovery"):
        return AuthDecision(ok=True, capability=capability_id, risk=cap.risk.value, reason="auth boundary")

    if capability_id == "owner.lock":
        return AuthDecision(ok=True, capability=capability_id, risk=cap.risk.value, reason="always allowed")

    if not owner_unlocked:
        return AuthDecision(
            ok=False,
            capability=capability_id,
            risk=cap.risk.value,
            reason="Owner locked — unlock Aria first",
            locked=True,
        )

    if cap.risk in (Risk.HIGH, Risk.CRITICAL) and not step_up_valid:
        # security.read / vault.meta.read are LOW; HIGH needs step-up
        if cap.risk == Risk.CRITICAL or capability_id in (
            "vault.secret.reveal",
            "vault.secret.write",
            "journal.export",
            "journal.import",
            "health.export",
            "health.delete",
            "health.write",
            "integrations.modify",
            "git.write",
            "automation.modify",
            "security.modify",
            "uncensored.enable",
        ):
            return AuthDecision(
                ok=False,
                capability=capability_id,
                risk=cap.risk.value,
                reason="Step-up authentication required",
                step_up_required=True,
            )

    return AuthDecision(ok=True, capability=capability_id, risk=cap.risk.value, reason="authorized")
