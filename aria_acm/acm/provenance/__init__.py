"""Provenance package — engineering lineage, not a cognitive organ."""

from acm.provenance.ingestion import (
    TRUSTED_USER_CORRECTION,
    TRUSTED_USER_STATEMENT,
    TRUSTED_USER_TEACHING,
    HostOperation,
    IngestionActor,
    IngestionDecision,
    IngestionProvenance,
    MessageRole,
    evaluate_ingestion,
)
from acm.provenance.legacy_cleanup import (
    classify_untrusted_artifact,
    cleanup_legacy_contamination,
)
from acm.provenance.model import ProvenanceRecord, ProvenanceSource, stamp_provenance

__all__ = [
    "HostOperation",
    "IngestionActor",
    "IngestionDecision",
    "IngestionProvenance",
    "MessageRole",
    "ProvenanceRecord",
    "ProvenanceSource",
    "TRUSTED_USER_CORRECTION",
    "TRUSTED_USER_STATEMENT",
    "TRUSTED_USER_TEACHING",
    "classify_untrusted_artifact",
    "cleanup_legacy_contamination",
    "evaluate_ingestion",
    "stamp_provenance",
]
