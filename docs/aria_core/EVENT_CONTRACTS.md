# Aria Core Event Contracts — Phase 4

Machine-readable contracts: `aria_core/event_contracts.py`.

## Required fields

Purpose · Publisher · Subscribers · Payload · Ordering · Reliability · Replay support · Version

## Replay (Phase 4)

Replay means **re-reading the in-memory ring buffer**. There is no durable event log re-delivery yet.

## Index

All types in `aria_core.event_types.ALL_EVENT_TYPES` have contracts.
