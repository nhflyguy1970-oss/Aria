# Memory Retrieval Behavior

Canonical reference for Everyday / Daily Use memory behavior.
Owner: `aria_core.memory` (Memory Manager). Storage: `jarvis.modules.memory` (unchanged schema).

## Memory classes

| Class | Type / tags | Recall | Search | Summary | Planning / Behavior | Diagnostics |
|-------|-------------|--------|--------|---------|---------------------|-------------|
| User facts | `fact` | Yes | Yes | Yes | Context only | Yes |
| Preferences | `preference` | Yes | Yes | Yes | Strategy if style | Yes |
| Profile | `namespace=profile` | Summary | Rare | Yes | Prompt | Yes |
| Notes | `note` (non-journal) | List | Yes | Limited | Context | Yes |
| Journal | `journal*` / “From bullet journal” | No (fact Q) | Demoted | No | No | Yes |
| Strategies | `strategy` | No | No | No | System rules | Yes |
| Telemetry / tool-outcome | tags | No | No | No | No | Yes |
| Conversation Trace | observability | No | No | No | No | Yes |
| Superseded | tag `superseded` | No | No | No | No | Yes |

## Retrieval precedence

1. Imperative memory verbs (`remember` / `forget` / `update`) short-circuit routing.
2. Fact questions (`What is my…`, `What do you know about X?`) → spoken answer from top **fact/preference**, journal excluded.
3. Explicit search → ranked list; keyword + focus + type; journal megablobs demoted.
4. Preference / about-me summary → profile + learned preferences + facts.

## Update precedence

`Actually…` / `Update…` / `Change…` → `memory_correct`.

- Topic hint derived from the new fact (`favorite coffee`, `favorite color`, …).
- Prior active entries on that topic are **superseded** (tag) or deleted.
- Recall always returns the newest active value.
- Historical / superseded entries remain for diagnostics only.

## Search ranking

Scores recorded per query (Conversation Trace / Memory panel — no contents):

- keyword_score
- semantic_score (when no keyword hits)
- recency_score
- focus_score (short topic facts beat long journal blobs)
- type_boost (preference > fact > note ≫ journal)

Winner = highest composite score.

## Summary policy

`What do you know about me?` and preference questions summarize:

- Profile summary / interests
- Learned preferences
- Key user facts

Not journal dumps, strategies, or telemetry.

## Forget policy

`Forget …` uses precise topic matching. Distinctive tokens required (`coffee` ≠ `color`).

## Duplicate resolution

Multiple active facts for one topic → supersede on update. Soft `superseded` tag keeps history without schema change.

## Fallback behavior

Backend / empty-model failures never show raw `Model qwen… returned empty` to users.
User sees a graceful retry message; underlying detail is recorded for Trace / events only.

## Instrumentation

Every ranked retrieval emits a decision with candidate counts, winner id/type, reject reasons, ranking latency — contents omitted.
