"""Deep Research Engine — planning, collection, evidence, citations, synthesis.

Layered on the persistent mission system: missions provide execution,
checkpoints, pause/resume, cancellation, retry and crash recovery, while this
package owns research-specific durable state.
"""

from jarvis.research.engine import (
    PHASES,
    create_research,
    decompose,
    mission_steps,
    report,
    run_phase,
    status,
)
from jarvis.research.store import (
    CONTRADICTS,
    FACT,
    INFERENCE,
    SUPPORTS,
    VERIFIES,
    canonical_url,
    get_job,
    list_jobs,
)

__all__ = [
    "CONTRADICTS",
    "FACT",
    "INFERENCE",
    "PHASES",
    "SUPPORTS",
    "VERIFIES",
    "canonical_url",
    "create_research",
    "decompose",
    "get_job",
    "list_jobs",
    "mission_steps",
    "report",
    "run_phase",
    "status",
]
