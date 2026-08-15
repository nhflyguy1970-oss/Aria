"""Owner Security Vault — M1 session + M2 provider credential dual-read.

Secrets never enter ACM. Master password never stored. Recovery is deliberate.
M2 copies authorized provider keys into the vault; jarvis.env is retained.
"""

from __future__ import annotations

from jarvis.security.owner.service import OwnerSecurityService, get_owner_security

__all__ = ["OwnerSecurityService", "get_owner_security"]
