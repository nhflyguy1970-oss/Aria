# Aria Engineering Law — Capability-Driven Development

This is one of the highest engineering rules inside Aria.

Aria is no longer in a feature race, architecture phase, or rewrite phase. Aria is becoming a mature personal AI operating system.

## Golden rule

**Aria should grow because Jeff's life grows — not because the codebase grows.**

The measure of success is not the number of features. It is whether Jeff increasingly forgets there are separate products and simply says: **"I'll ask Aria."**

## Origin of every capability

Every new capability must originate from one of:

1. Jeff discovers real friction.
2. Jeff repeatedly performs the same manual task.
3. A capability is required to support an existing flagship product.
4. A capability naturally completes another capability.

## Forbidden origins

Do not add features because they would be cool, the architecture could support them, we might need them someday, another AI has them, or someone else requested them.

Before writing code, answer: what problem, who, how often, can existing systems solve it, does it belong in an existing product, would Jeff naturally expect it? If not — do not implement.

## Expand, don't proliferate

Expand flagship products (Health, ACM, Documents, Coding, Mission Control, Fly Tying). Put cross-cutting needs in platform services (Execution Law, Guided Repair, Mission Control, Search, Auth, Notifications, Certification, **Production Integrity**). Prefer a 10-line repair over a rewrite. Freeze mature products except for bugs, real friction, performance, security, or reliability.

**Production Integrity** is a permanent platform safeguard: Jeff must never see QA/smoke/cert/demo artifacts in the live workspace. Scans never auto-delete — Guided Repair recommends; Jeff approves. See `.cursor/rules/production-integrity.mdc`.

## Cursor enforcement

Agents follow this law via `.cursor/rules/capability-driven-development.mdc` and `.cursor/rules/production-integrity.mdc` (`alwaysApply: true`).
