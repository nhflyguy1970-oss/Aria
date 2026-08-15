# ARIA Execution State Closure

Generated: 2026-08-10T21:56:10.063080+00:00

- Applicable states: **111**
- PASS: **109**
- FAIL: **2**
- UNTESTED: **0**

| ID | Room | State | Executed | Status | Bug | Evidence |
|---|---|---|---|---|---|---|
| STATE-001 | chat | DEFAULT | yes | PASS | — | by_state/STATE-001.json |
| STATE-002 | chat | LOADING | yes | PASS | — | by_state/STATE-002.json |
| STATE-003 | chat | SUCCESS | yes | PASS | — | by_state/STATE-003.json |
| STATE-004 | chat | ERROR | yes | PASS | — | by_state/STATE-004.json |
| STATE-005 | chat | CANCELLING | yes | FAIL | BUG-005 | by_state/STATE-005.json |
| STATE-006 | chat | CANCELLED | yes | FAIL | BUG-005 | by_state/STATE-006.json |
| STATE-007 | chat | MODAL | yes | PASS | — | by_state/STATE-007.json |
| STATE-008 | chat | EMPTY | yes | PASS | — | by_state/STATE-008.json |
| STATE-009 | flytying | DEFAULT | yes | PASS | — | by_state/STATE-009.json |
| STATE-010 | flytying | TAB | yes | PASS | — | by_state/STATE-010.json |
| STATE-011 | flytying | EDITING | yes | PASS | — | by_state/STATE-011.json |
| STATE-012 | flytying | EMPTY | yes | PASS | — | by_state/STATE-012.json |
| STATE-013 | flytying | SEARCH RESULTS | yes | PASS | — | by_state/STATE-013.json |
| STATE-014 | flytying | NO RESULTS | yes | PASS | — | by_state/STATE-014.json |
| STATE-015 | flytying | SUCCESS | yes | PASS | — | by_state/STATE-015.json |
| STATE-016 | flytying | ERROR | yes | PASS | — | by_state/STATE-016.json |
| STATE-017 | planner | DEFAULT | yes | PASS | — | by_state/STATE-017.json |
| STATE-018 | planner | EDITING | yes | PASS | — | by_state/STATE-018.json |
| STATE-019 | planner | EMPTY | yes | PASS | — | by_state/STATE-019.json |
| STATE-020 | planner | SUCCESS | yes | PASS | — | by_state/STATE-020.json |
| STATE-021 | planner | ERROR | yes | PASS | — | by_state/STATE-021.json |
| STATE-022 | planner | MODAL | yes | PASS | — | by_state/STATE-022.json |
| STATE-023 | memory | DEFAULT | yes | PASS | — | by_state/STATE-023.json |
| STATE-024 | memory | SEARCH RESULTS | yes | PASS | — | by_state/STATE-024.json |
| STATE-025 | memory | NO RESULTS | yes | PASS | — | by_state/STATE-025.json |
| STATE-026 | memory | EMPTY | yes | PASS | — | by_state/STATE-026.json |
| STATE-027 | memory | SUCCESS | yes | PASS | — | by_state/STATE-027.json |
| STATE-028 | memory | ERROR | yes | PASS | — | by_state/STATE-028.json |
| STATE-029 | memory | EDITING | yes | PASS | — | by_state/STATE-029.json |
| STATE-030 | documents | DEFAULT | yes | PASS | — | by_state/STATE-030.json |
| STATE-031 | documents | SEARCH RESULTS | yes | PASS | — | by_state/STATE-031.json |
| STATE-032 | documents | NO RESULTS | yes | PASS | — | by_state/STATE-032.json |
| STATE-033 | documents | EMPTY | yes | PASS | — | by_state/STATE-033.json |
| STATE-034 | documents | ERROR | yes | PASS | — | by_state/STATE-034.json |
| STATE-035 | documents | LOADING | yes | PASS | — | by_state/STATE-035.json |
| STATE-036 | gallery | DEFAULT | yes | PASS | — | by_state/STATE-036.json |
| STATE-037 | gallery | LOADING | yes | PASS | — | by_state/STATE-037.json |
| STATE-038 | gallery | SUCCESS | yes | PASS | — | by_state/STATE-038.json |
| STATE-039 | gallery | ERROR | yes | PASS | — | by_state/STATE-039.json |
| STATE-040 | gallery | EMPTY | yes | PASS | — | by_state/STATE-040.json |
| STATE-041 | providers | DEFAULT | yes | PASS | — | by_state/STATE-041.json |
| STATE-042 | providers | TAB | yes | PASS | — | by_state/STATE-042.json |
| STATE-043 | providers | EDITING | yes | PASS | — | by_state/STATE-043.json |
| STATE-044 | providers | LOADING | yes | PASS | — | by_state/STATE-044.json |
| STATE-045 | providers | ERROR | yes | PASS | — | by_state/STATE-045.json |
| STATE-046 | providers | SUCCESS | yes | PASS | — | by_state/STATE-046.json |
| STATE-047 | settings | DEFAULT | yes | PASS | — | by_state/STATE-047.json |
| STATE-048 | settings | EDITING | yes | PASS | — | by_state/STATE-048.json |
| STATE-049 | settings | SUCCESS | yes | PASS | — | by_state/STATE-049.json |
| STATE-050 | home_automation | DEFAULT | yes | PASS | — | by_state/STATE-050.json |
| STATE-051 | home_automation | SEARCH RESULTS | yes | PASS | — | by_state/STATE-051.json |
| STATE-052 | home_automation | EMPTY | yes | PASS | — | by_state/STATE-052.json |
| STATE-053 | home_automation | ERROR | yes | PASS | — | by_state/STATE-053.json |
| STATE-054 | home_automation | LOADING | yes | PASS | — | by_state/STATE-054.json |
| STATE-055 | home_automation | NO RESULTS | yes | PASS | — | by_state/STATE-055.json |
| STATE-056 | coding | DEFAULT | yes | PASS | — | by_state/STATE-056.json |
| STATE-057 | coding | EDITING | yes | PASS | — | by_state/STATE-057.json |
| STATE-058 | coding | LOADING | yes | PASS | — | by_state/STATE-058.json |
| STATE-059 | coding | ERROR | yes | PASS | — | by_state/STATE-059.json |
| STATE-060 | coding | MODAL | yes | PASS | — | by_state/STATE-060.json |
| STATE-061 | mission | DEFAULT | yes | PASS | — | by_state/STATE-061.json |
| STATE-062 | mission | LOADING | yes | PASS | — | by_state/STATE-062.json |
| STATE-063 | mission | SUCCESS | yes | PASS | — | by_state/STATE-063.json |
| STATE-064 | mission | ERROR | yes | PASS | — | by_state/STATE-064.json |
| STATE-065 | activity | DEFAULT | yes | PASS | — | by_state/STATE-065.json |
| STATE-066 | activity | MODAL | yes | PASS | — | by_state/STATE-066.json |
| STATE-067 | activity | EMPTY | yes | PASS | — | by_state/STATE-067.json |
| STATE-068 | activity | ERROR | yes | PASS | — | by_state/STATE-068.json |
| STATE-069 | audio | DEFAULT | yes | PASS | — | by_state/STATE-069.json |
| STATE-070 | audio | LOADING | yes | PASS | — | by_state/STATE-070.json |
| STATE-071 | audio | ERROR | yes | PASS | — | by_state/STATE-071.json |
| STATE-072 | audio | SUCCESS | yes | PASS | — | by_state/STATE-072.json |
| STATE-073 | audio | EMPTY | yes | PASS | — | by_state/STATE-073.json |
| STATE-074 | journal | DEFAULT | yes | PASS | — | by_state/STATE-074.json |
| STATE-075 | journal | EDITING | yes | PASS | — | by_state/STATE-075.json |
| STATE-076 | journal | EMPTY | yes | PASS | — | by_state/STATE-076.json |
| STATE-077 | journal | SUCCESS | yes | PASS | — | by_state/STATE-077.json |
| STATE-078 | journal | LOADING | yes | PASS | — | by_state/STATE-078.json |
| STATE-079 | calendar | DEFAULT | yes | PASS | — | by_state/STATE-079.json |
| STATE-080 | calendar | EMPTY | yes | PASS | — | by_state/STATE-080.json |
| STATE-081 | calendar | LOADING | yes | PASS | — | by_state/STATE-081.json |
| STATE-082 | calendar | MODAL | yes | PASS | — | by_state/STATE-082.json |
| STATE-083 | automation | DEFAULT | yes | PASS | — | by_state/STATE-083.json |
| STATE-084 | automation | EDITING | yes | PASS | — | by_state/STATE-084.json |
| STATE-085 | automation | EMPTY | yes | PASS | — | by_state/STATE-085.json |
| STATE-086 | automation | ERROR | yes | PASS | — | by_state/STATE-086.json |
| STATE-087 | automation | SUCCESS | yes | PASS | — | by_state/STATE-087.json |
| STATE-088 | browser | DEFAULT | yes | PASS | — | by_state/STATE-088.json |
| STATE-089 | browser | LOADING | yes | PASS | — | by_state/STATE-089.json |
| STATE-090 | browser | ERROR | yes | PASS | — | by_state/STATE-090.json |
| STATE-091 | browser | SUCCESS | yes | PASS | — | by_state/STATE-091.json |
| STATE-092 | repair | DEFAULT | yes | PASS | — | by_state/STATE-092.json |
| STATE-093 | repair | LOADING | yes | PASS | — | by_state/STATE-093.json |
| STATE-094 | repair | EMPTY | yes | PASS | — | by_state/STATE-094.json |
| STATE-095 | repair | SUCCESS | yes | PASS | — | by_state/STATE-095.json |
| STATE-096 | repair | ERROR | yes | PASS | — | by_state/STATE-096.json |
| STATE-097 | integrity | DEFAULT | yes | PASS | — | by_state/STATE-097.json |
| STATE-098 | integrity | LOADING | yes | PASS | — | by_state/STATE-098.json |
| STATE-099 | integrity | SUCCESS | yes | PASS | — | by_state/STATE-099.json |
| STATE-100 | integrity | ERROR | yes | PASS | — | by_state/STATE-100.json |
| STATE-101 | voice | DEFAULT | yes | PASS | — | by_state/STATE-101.json |
| STATE-102 | voice | LOADING | yes | PASS | — | by_state/STATE-102.json |
| STATE-103 | voice | ERROR | yes | PASS | — | by_state/STATE-103.json |
| STATE-104 | video | DEFAULT | yes | PASS | — | by_state/STATE-104.json |
| STATE-105 | video | LOADING | yes | PASS | — | by_state/STATE-105.json |
| STATE-106 | video | ERROR | yes | PASS | — | by_state/STATE-106.json |
| STATE-107 | video | EMPTY | yes | PASS | — | by_state/STATE-107.json |
| STATE-108 | health | DEFAULT | yes | PASS | — | by_state/STATE-108.json |
| STATE-109 | health | LOADING | yes | PASS | — | by_state/STATE-109.json |
| STATE-110 | health | EMPTY | yes | PASS | — | by_state/STATE-110.json |
| STATE-111 | health | ERROR | yes | PASS | — | by_state/STATE-111.json |
