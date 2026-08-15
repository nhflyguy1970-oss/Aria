# ARIA — Live Production Instance Verification

**Date:** 2026-08-15  
**Owner URL:** `http://127.0.0.1:8765/?workspace=1`  
**Conclusion:** `LIVE CERTIFIED ARIA VERIFIED`

This is a deployment-identity verification. It is not another 34-Room campaign. Owner Residency and M5 were not started.

---

## A. CERTIFICATION RESULT (already complete)

**34 / 34 Rooms certified functional**

Source: `docs/ARIA_FINAL_34_ROOM_FUNCTIONAL_VERIFICATION.md`

Documented non-defect boundaries remain: Aug 8 Journal import SKIPPED BY JEFF · Maker physical print SKIPPED BY JEFF · hardware gates · destructive leftovers not executed.

This section is the campaign result. It is not a claim about which process Jeff’s browser reaches.

---

## B. LIVE DEPLOYMENT RESULT

The process Jeff reaches at `127.0.0.1:8765` is the tray-managed owner Aria in `/media/jeff/AI/jarvis`, running the repaired working-tree code covered by that certification, using production `JARVIS_DATA_DIR=/media/jeff/AI/jarvis/data`.

Cursor does not own that process. Closing Cursor does not stop it.

---

## 1. Live PID

**1287356**

`ss` / `lsof`: `python` PID 1287356 listens on `0.0.0.0:8765`.

## 2. Parent PID

**41589** — `/media/jeff/AI/jarvis/venv/bin/python /media/jeff/AI/jarvis/main.py tray`  
Started Thu Aug 13 09:18:48 2026.  
Grandparent **1508** — `systemd --user`.

Parent chain:

`1287356 (main.py serve)` → `41589 (main.py tray)` → `1508 (systemd --user)`

Cursor (`/usr/share/cursor/cursor`, PID 25154) is not in this chain.

## 3. Launch mechanism

**Tray-managed production serve.**

- Launch command: `/media/jeff/AI/jarvis/venv/bin/python /media/jeff/AI/jarvis/main.py serve`
- Parent: `main.py tray` (same venv, same repo)
- Desktop entry: `~/.local/share/applications/aria.desktop` → `scripts/launch-jarvis.sh`
- systemd user unit `jarvis.service` exists (`ExecStart=scripts/launch-jarvis.sh`) but is **disabled** and **inactive**. It was not started (that would duplicate the live tray).
- Serve start: Sat Aug 15 16:25:15 — child of the long-lived tray after the normal tray restart (`POST /api/jarvis/restart-server` / `scripts/restart-jarvis-server.sh` USR1). That is Aria’s production restart path, not a Cursor-isolated server.

| Question | Answer |
| --- | --- |
| Cursor-launched? | **No** |
| Terminal-launched? | **No** |
| Tray-managed? | **Yes** |
| systemd unit currently active? | **No** (tray already running independently) |

## 4. Repository

`/media/jeff/AI/jarvis`

## 5. Branch

`main` (ahead of `origin/main` by 25 commits)

## 6. Commit

`c325e5576aca62f71a800641ec1cb9652e6bb5cf`  
`fix(model-runtime): prevent alternating chat failures from model residency races`

## 7. Working tree state

**Dirty.** The certified 34-Room repairs are **uncommitted working-tree changes** (and some new untracked files). They were not discarded, reset, or committed for this report.

The live process `cwd` is this repository, `PYTHONPATH` is unset, so imports and static files come from this working tree — not from a clean checkout of `c325e55` alone.

### Certification-relevant files

| File | Git |
| --- | --- |
| `jarvis/modules/graph_store.py` | modified, uncommitted |
| `jarvis/gui/extra_routes.py` | modified, uncommitted |
| `jarvis/gui/static/activity_center.js` | modified, uncommitted |
| `jarvis/gui/static/memory_browser.js` | modified, uncommitted |
| `jarvis/gui/static/connections.js` | modified, uncommitted |
| `jarvis/gui/static/view_router.js` | modified, uncommitted |
| `jarvis/gui/static/app.js` | modified, uncommitted |
| `jarvis/gui/static/mission_control.js` | modified, uncommitted |
| `jarvis/gui/static/calendar.js` | modified, uncommitted |
| `jarvis/gui/static/audit.js` | modified, uncommitted |
| `jarvis/gui/static/dashboard_home.js` | modified, uncommitted |
| `jarvis/gui/static/ha_panel.js` | modified, uncommitted |
| `jarvis/gui/static/index.html` | modified, uncommitted |
| `jarvis/gui/static/journal.js` | modified, uncommitted |
| `jarvis/gui/static/projects.js` | modified, uncommitted |
| `jarvis/calendar_schedule.py` | modified, uncommitted |
| `jarvis/home_assistant.py` | modified, uncommitted |
| `jarvis/auth.py` | modified, uncommitted |
| `jarvis/gui/static/lock_screen.js` | modified, uncommitted |
| `jarvis/gui/static/owner_experience.js` | untracked |
| `jarvis/security/owner/` (incl. `session.py`) | untracked |
| `docs/ARIA_FINAL_34_ROOM_FUNCTIONAL_VERIFICATION.md` | untracked |

Many other repo files are also modified; they are outside this identity check.

## 8. Python executable

Process `exe`: `/usr/bin/python3.12`  
Argv[0]: `/media/jeff/AI/jarvis/venv/bin/python` (venv shim)

## 9. Virtual environment

`VIRTUAL_ENV=/media/jeff/AI/jarvis/venv`

## 10. Working directory

`/media/jeff/AI/jarvis`

## 11. JARVIS_DATA_DIR

**Process environ:** `/media/jeff/AI/jarvis/data`  
**Resolved:** `/media/jeff/AI/jarvis/data`

Open file descriptors on the live PID include:

- `/media/jeff/AI/jarvis/data/acm/cognitive.db` (+ wal/shm)
- `/media/jeff/AI/jarvis/data/memory.db` (+ wal/shm)
- `/media/jeff/AI/jarvis/data/memory_vectors.db` (+ wal/shm)
- `/media/jeff/AI/jarvis/data/planner.db`
- `/media/jeff/AI/jarvis/data/logs/serve.log`

Not used: `/tmp/aria-residency`, isolated test dirs, Cursor disposable databases.

Also present in environ (not used as the owner data root):  
`JARVIS_LEGACY_DATA_DIR=/media/jeff/AI/jarvis/data`  
`JARVIS_PLATFORM_DATA_DIR=/media/jeff/AI/applications/aria/data`

## 12. Port owner

Only PID **1287356** listens on **8765** (`0.0.0.0:8765`).  
No listener on `:18765`.

## 13. Duplicate / stale processes

| PID | Port | Repository / identity | Launch | Status |
| --- | --- | --- | --- | --- |
| **1287356** | **8765** | `/media/jeff/AI/jarvis` @ working tree / `c325e55` | tray child `main.py serve` | **Jeff’s owner instance** |
| 41589 | — | same repo | `main.py tray` since Aug 13 | owns serve + PySide window |
| 1939717 | client of 8765 | same repo | `jarvis.pyside_shell http://127.0.0.1:8765` | desktop window; not a second server |
| 27514 | — | same repo | Cursor child `jarvis-mcp-server.py` | MCP only; not HTTP 8765 |
| 4579 | not 8765 | Docker `rag_api` (`python main.py`) | containerd / LibreChat | unrelated |
| 3220263 | 8188 | ComfyUI | ComfyUI `main.py` | unrelated |

Nothing was killed. No second Aria serve exists.

## 14. Browser target

Cursor browser tab `glass-browser-e4d6d093-f0ec-435b-b22a-de02d54f4542`:

- URL: `http://127.0.0.1:8765/?workspace=1`
- TCP peers: Cursor network process and PySide shell are connected to PID 1287356 on 8765
- Loaded scripts from that origin include:
  - `connections.js?v=1.0.5-browse-all`
  - `audit.js?v=5.16.166-no-autorun`
  - `activity_center.js?v=6.5.5-inbox-honest`
  - `view_router.js?v=6.4.6-hash-alias`
  - `app.js?v=5.16.165-hash-canon`
  - `memory_browser.js?v=2.0.7-briefs-parallel`

Not used: `:18765`, isolated server, Cursor preview, another repo.

## 15. Loaded repaired module paths

`ptrace` of the live PID is blocked (`yama/ptrace_scope`), so `sys.modules` could not be dumped. Load identity is proven from process cwd + unset `PYTHONPATH` + bytecode/import timing + live behavior + byte-identical static serve.

Resolved import paths for this cwd/venv (the only tree this process can import):

| Module | Path |
| --- | --- |
| `jarvis.modules.graph_store` | `/media/jeff/AI/jarvis/jarvis/modules/graph_store.py` |
| `jarvis.gui.extra_routes` | `/media/jeff/AI/jarvis/jarvis/gui/extra_routes.py` |
| `jarvis.security.owner.session` | `/media/jeff/AI/jarvis/jarvis/security/owner/session.py` |
| `jarvis.security.owner.service` | `/media/jeff/AI/jarvis/jarvis/security/owner/service.py` |
| `jarvis.home_assistant` | `/media/jeff/AI/jarvis/jarvis/home_assistant.py` |
| `jarvis.calendar_schedule` | `/media/jeff/AI/jarvis/jarvis/calendar_schedule.py` |
| `jarvis.auth` | `/media/jeff/AI/jarvis/jarvis/auth.py` |
| `jarvis.connections_services` | `/media/jeff/AI/jarvis/jarvis/connections_services.py` |
| `jarvis.integrity_product.api` | `/media/jeff/AI/jarvis/jarvis/integrity_product/api.py` |

Runtime evidence the **live PID** actually used those implementations:

| Repair | Live proof |
| --- | --- |
| Owner session / no automatic idle lock | `/api/owner-security/status`: `auto_idle_lock: false`, `idle_seconds: 0`; stayed `OWNER_UNLOCKED` across rooms |
| Front Door Lock Aria | Overlay open; `#fdLockAria` visible (`display:block`); not clicked |
| Journal Projects collision | Journal Projects tab → heading `Project journals`; hash stayed `#journal` |
| Calendar Work Schedule | `calendar.js` byte-identical on 8765 (`?v=5.17.5-search-memory`); module mtime before serve start |
| HA vault-first | While locked: entities `400 locked`. After unlock: UI `Connected · http://127.0.0.1:8123`; entities API ok |
| Connections Browse | Empty-q list-all; Overview 59/53 memgraph = Browse API 59 = UI `59 entities` |
| Knowledge Briefs hop | `openKnowledgeBriefs` → `#memory` + `#memoryKnowledgePanel` visible; Run not clicked |
| `#missionRoom` routing | From `#chat`, hash `#missionRoom` landed `#workstation`; chat hidden |
| Notifications inbox | Live `activity_center.js` contains honest empty/filter + Show unread (`?v=6.5.5-inbox-honest`) |
| Search/Fly/Documents / Mission routing | Served repaired `view_router.js` / `app.js` / `mission_control.js` byte-identical to disk |
| System Audit no auto-run | `GET /api/audit` returns `{running: false}` (status only). `extra_routes.cpython-312.pyc` written **2026-08-15 16:25:25** (9s after this serve started) |
| Home foyer abort-retry | `dashboard_home.js` byte-identical; Home smoke had no “Home unavailable / Load failed” |

Static files served by PID 1287356 were **MD5-identical** to the working-tree files (including `connections.js` and `index.html` newer than process start — Starlette serves them from disk per request).

Python repair sources were all **mtime-before** serve start 16:25:16, so this process imported the repaired versions.

## 16. Certification-to-live code comparison

| | Certification (A) | Live 8765 (B) |
| --- | --- | --- |
| Repo | `/media/jeff/AI/jarvis` | same |
| Code | repaired working tree | same working tree loaded by PID 1287356 |
| Committed? | No — repairs are uncommitted | Process does not need a commit; it loads cwd |
| Data | live owner `data/` | same `JARVIS_DATA_DIR` |
| Port | 8765 | 8765, this PID |

Mismatch that is **not** a deployment failure: HEAD commit `c325e55` does not contain the repairs. The **running process** does, because it loads the dirty tree.

## 17. Controlled restart result

This verification pass did **not** issue a second restart after Jeff unlocked.

The live serve **is already** the production-tray restart instance:

- Tray PID 41589 has been up since 2026-08-13
- Serve PID 1287356 started 2026-08-15 16:25:15 as that tray’s child
- That start matches the campaign’s `POST /api/jarvis/restart-server` (`mode=tray`) / USR1 path
- `extra_routes` bytecode was compiled at that start
- A second restart after Jeff’s unlock would have locked the house again (forbidden “repeatedly lock/unlock”)

Expected post-restart state (`OWNER_LOCKED`) was observed on this same PID **before** Jeff unlocked for this verification.

## 18. Owner unlock result

Jeff unlocked via the normal Owner UI (Master Password in the house, not chat).

After unlock:

- `OWNER_UNLOCKED`
- `session_active: true`
- `vault.unlocked: true`
- `idle_seconds: 0`
- `auto_idle_lock: false`
- `#lockScreen` hidden (`display:none`)

## 19. Independent-from-Cursor result

**Cursor does not own Aria.**

Proof: parent chain is serve → tray → `systemd --user`. Cursor’s only Aria-related child is `jarvis-mcp-server.py` (PID 27514), which is not the 8765 server.

Cursor **can be closed**. Tray + serve + PySide window remain. Jeff opens `http://127.0.0.1:8765/?workspace=1` (browser or desktop shell) and gets this same instance.

Cursor was **not** terminated (this agent would die; the tree already proves independence). systemd `jarvis.service` was **not** enabled/started (would launch a duplicate tray).

Caveat (not a live mismatch): the user unit is disabled, so a **reboot** may require the desktop shortcut / `scripts/launch-jarvis.sh` unless Jeff later enables the unit carefully (stop the current tray first).

## 20. Live owner smoke test

Performed on `http://127.0.0.1:8765/?workspace=1` against PID 1287356. No manufactured data. Lock Aria not clicked. `603973e7` not applied. Aug 8 Journal not imported. No print.

| # | Check | Result |
| --- | --- | --- |
| 1 | Front Door loads | PASS — “Where would you like to go?” |
| 2 | Owner session unlocked | PASS — `OWNER_UNLOCKED` |
| 3 | Lock Aria visible | PASS — Front Door button visible; not clicked |
| 4 | Home works | PASS — `#dashboard`; no first-paint failure |
| 5 | Journal works | PASS — Bullet Journal; Projects → Project journals |
| 6 | Health works | PASS — PHR chrome; no writes |
| 7 | Fly Tying works | PASS — library connected; catalog counts shown |
| 8 | Projects works | PASS — 2 workspaces; active `home-lab`; no QA names |
| 9 | Mission / Workstation | PASS — Mission Control console |
| 10 | Connections Browse count | PASS — 59 entities (API + UI); Overview 59/53 |
| 11 | Knowledge Briefs hop | PASS — panel on `#memory`; Run not clicked |
| 12 | HA vault-backed Connected | PASS — `Connected · http://127.0.0.1:8123` |
| 13 | Repaired nav route | PASS — `#missionRoom` → `#workstation` |
| 14 | Repaired Room function | PASS — Journal Projects collision held |
| 15 | Integrity | PASS — 100 / clean / artifacts 0 |

Evidence: `docs/evidence/exhaustive_functional_verification/LIVE_PRODUCTION_INSTANCE_SMOKE.json`

## 21. Integrity

`GET /api/integrity/score` and Integrity room UI:

**Score 100 · status `clean` · ready**

## 22. Artifact count

**0**

Sections workspace / health / projects / documents / gallery / planner / calendar / notifications / mission_control / certification: all clean. No obvious QA/test contamination in the Integrity scan. Ambiguous owner data was not deleted.

## 23. Final conclusion

### A. Certification

34 / 34 Rooms certified functional  
(`docs/ARIA_FINAL_34_ROOM_FUNCTIONAL_VERIFICATION.md`)

### B. Live deployment

The Aria Jeff will actually use on `127.0.0.1:8765` is this tray-managed process (PID 1287356), loading the same repaired working-tree code, same production data directory, same owner session contract (`UNLOCK ONCE → USE HOUSE → STAY UNLOCKED`).

# LIVE CERTIFIED ARIA VERIFIED

Meaning: the Aria instance Jeff will actually use on `127.0.0.1:8765` is running the repaired code covered by the 34-Room certification.

Stopped. No Owner Residency. No M5. No further testing unless a real mismatch or defect appears.
