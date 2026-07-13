# Aria Core Capability Contracts — Phase 3

Each Capability Bus verb has a contract in `aria_core.capability_contracts.CONTRACTS`.

## Required fields

| Field | Meaning |
|-------|---------|
| inputs | Expected arguments |
| outputs | Return shape |
| errors | Failure modes |
| latency_expectations | Guidance only (not SLOs enforced in Phase 3) |
| side_effects | What may change |
| observability | Where operators look |
| interruptibility | Safe to cancel? |
| recovery | Failure handling |
| future_implementation_owner | Where the organ may live later |

## Contract index

| Capability | Future owner | Side effects |
|------------|--------------|--------------|
| remember | aria_core.memory | memory write |
| recall | aria_core.memory | none |
| learn | aria_core.learning | governor + apply |
| reason | aria_core.reasoning | assistant flows |
| plan | aria_core.planning | planner store (if invoked) |
| reference | aria_core.reference | none |
| search | aria_core.knowledge | none |
| infer | aria_core.reasoning | GPU/inference |
| execute_tool | aria_core.capabilities | handler-defined |
| schedule | aria_core.runtime | none (status) |
| observe | aria_core.operations | optional metrics |
| notify | aria_core.operations | notification store |
| diagnose | aria_core.platform | none |
| repair | aria_core.platform | may restart services |
| backup | aria_core.operations | none (hint only) |
| recover | aria_core.platform | may restart services |

Authoritative machine-readable contracts: `aria_core/capability_contracts.py`.
