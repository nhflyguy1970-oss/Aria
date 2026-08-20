"""Live certification: pruning orphan nodes must work on the graph backend
this deployment actually runs.

`NOT (n)--()` is a Neo4j-ism. Memgraph rejects the anonymous pattern outright
("Not yet implemented: atom expression '(n)--()'"), so /api/connections/prune
returned 500 every time it was used.
"""

from __future__ import annotations

import inspect
import re


def _query_only(src: str) -> str:
    """The Cypher, without the comment that explains why it changed."""
    return "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))


def _bolt_prune_source() -> str:
    from jarvis.modules import graph_store

    bolt = next(
        cls
        for name, cls in vars(graph_store).items()
        if inspect.isclass(cls) and hasattr(cls, "prune_orphans") and "Bolt" in name
    )
    return inspect.getsource(bolt.prune_orphans)


def test_the_prune_query_avoids_the_unsupported_pattern():
    src = _query_only(_bolt_prune_source())
    assert not re.search(r"NOT\s*\(n\)--\(\)", src), "the Memgraph-incompatible pattern is back"


def test_the_prune_query_counts_incident_relationships_instead():
    src = _bolt_prune_source()
    assert "OPTIONAL MATCH (n)-[r]-()" in src
    assert "count(r)" in src
    assert "DETACH DELETE n" in src


def test_the_namespace_filter_is_preserved():
    src = _bolt_prune_source()
    assert "$namespace" in src and "n.namespace" in src
