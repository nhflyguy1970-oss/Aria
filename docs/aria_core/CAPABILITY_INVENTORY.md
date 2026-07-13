# Aria Core — Capability Inventory (SSOT)

**Version:** 2.0 Phase 1
**Rule:** Aria must never become less capable.
**Profiles:** standard · uncensored (same intelligence)

**Count:** 98 capabilities

| id | layer | risk | protected | owner |
|----|-------|------|-----------|-------|
| `chat-assistant` | Intelligence | Critical | True | `jarvis/assistant.py` |
| `aria-uncensored` | Intelligence | High | True | `jarvis/config.py` |
| `nlu-routing` | Intelligence | Critical | True | `jarvis/nlu` |
| `inference-llm` | Intelligence | Critical | True | `jarvis/llm.py` |
| `memory-hierarchy` | Intelligence | Critical | True | `jarvis/modules/memory.py` |
| `knowledge-rag` | Intelligence | High | True | `jarvis/knowledge` |
| `personalization` | Intelligence | Medium | True | `jarvis/personalization` |
| `planning-agents` | Intelligence | High | True | `jarvis/agents` |
| `context-builder` | Intelligence | High | True | `jarvis/context` |
| `learning-sources` | Intelligence | High | True | `jarvis/learning_governor.py` |
| `coding-agent` | Capability | Critical | True | `jarvis/coding_agent.py` |
| `voice-stt-tts` | Capability | High | True | `jarvis/stt.py` |
| `audio-studio` | Capability | Medium | True | `jarvis/song_studio.py` |
| `vision-media` | Capability | High | True | `jarvis/comfyui.py` |
| `fly-tying` | Capability | Medium | True | `jarvis/flytying` |
| `home-smarthome` | Capability | High | True | `jarvis/home_assistant.py` |
| `web-research` | Capability | Medium | True | `jarvis/web_search.py` |
| `journal-briefing` | Capability | High | True | `jarvis/morning_briefing.py` |
| `engineering-cad` | Capability | Medium | True | `jarvis/engineering` |
| `data-analysis` | Capability | Low | False | `jarvis/modules/data.py` |
| `tools-runner` | Capability | High | True | `jarvis/tools` |
| `projects-workspace` | Capability | Medium | True | `jarvis/project_registry.py` |
| `browser-automation` | Capability | Medium | True | `jarvis/extensions/browser` |
| `world-state-presence` | Capability | Low | False | `jarvis/world_state.py` |
| `gpu-vram` | Capability | High | True | `jarvis/vram_guard.py` |
| `rag-search` | Capability | High | True | `aiplatform/retrieval` |
| `plat-agents-tools-workflows` | Capability | High | True | `aiplatform/agents` |
| `gui-8765` | Interface | Critical | True | `jarvis/gui` |
| `tray-daemon` | Interface | Critical | True | `jarvis/daemon.py` |
| `cli-aria-workstation` | Interface | Critical | True | `jarvis/application/cli.py` |
| `rest-api` | Interface | Critical | True | `jarvis/gui/server.py` |
| `desktop-launchers` | Interface | High | True | `jarvis/desktop` |
| `mcp-cursor` | Interface | High | True | `scripts/jarvis-mcp-server.py` |
| `mc-web-ui` | Interface | High | True | `aiplatform/mission_control/static` |
| `mc-desktop` | Interface | High | True | `aiplatform/mission_control/desktop` |
| `mc-server` | Interface | Critical | True | `aiplatform/mission_control/server.py` |
| `external-interfaces` | Interface | Low | True | `jarvis/interfaces` |
| `app-aria-primary` | Application | Critical | True | `jarvis/application/host.py` |
| `app-flytying` | Application | Medium | True | `jarvis/extensions/flytying` |
| `app-home` | Application | High | True | `jarvis/extensions/smarthome` |
| `app-coding` | Application | Critical | True | `jarvis/coding_agent.py` |
| `app-research` | Application | Medium | True | `jarvis/knowledge` |
| `app-engineering` | Application | Medium | True | `jarvis/engineering` |
| `app-journal` | Application | High | True | `jarvis/modules/journal.py` |
| `extensions-system` | Application | High | True | `jarvis/extensibility` |
| `behaviors-framework` | Application | High | True | `jarvis/behaviors` |
| `handler-registry` | Application | Critical | True | `jarvis/handlers/registry.py` |
| `session-chat-history` | Application | High | True | `jarvis/chat_sessions.py` |
| `feature-flags` | Application | Medium | True | `jarvis/feature_flags.py` |
| `app-registry-platform` | Application | High | True | `aiplatform/applications` |
| `app-host-contract` | Application | Critical | True | `aiplatform/applications/host.py` |
| `app-migration-framework` | Application | High | True | `aiplatform/applications/migration` |
| `attachment-layers` | Application | Critical | True | `jarvis/platform_*.py` |
| `ws-lifecycle` | Platform | Critical | True | `aiplatform/workstation` |
| `ws-doctor-acceptance` | Platform | High | True | `aiplatform/workstation/acceptance.py` |
| `ws-repair-platform` | Platform | High | True | `aiplatform/workstation/repair.py` |
| `ws-backup-delegation` | Platform | Critical | True | `aiplatform/workstation/cli.py` |
| `infra-runtime-docker` | Infrastructure | Critical | True | `aiplatform/runtime` |
| `infra-services` | Infrastructure | High | True | `aiplatform/services` |
| `plat-config-secrets` | Platform | Critical | True | `aiplatform/config` |
| `plat-doctor` | Platform | High | True | `aiplatform/doctor` |
| `plat-plugins` | Platform | High | True | `aiplatform/plugins` |
| `plat-cli` | Platform | High | True | `aiplatform/cli.py` |
| `service-lifecycle-aria` | Infrastructure | High | True | `jarvis/services.py` |
| `background-jobs` | Infrastructure | High | True | `jarvis/background_jobs.py` |
| `network-security-base` | Infrastructure | High | True | `jarvis/auth.py` |
| `observability` | Infrastructure | Low | False | `jarvis/metrics.py` |
| `mc-aggregator` | Operational | Critical | True | `aiplatform/mission_control/aggregator.py` |
| `mc-overview` | Operational | High | True | `aggregator` |
| `mc-operational-advisor` | Operational | Medium | True | `aiplatform/mission_control/operational_advisor.py` |
| `mc-performance-lab` | Operational | High | True | `aiplatform/mission_control/performance_lab.py` |
| `mc-release-dashboard` | Operational | High | True | `aiplatform/mission_control/release_dashboard.py` |
| `mc-production-smoke` | Operational | High | True | `aiplatform/mission_control/production_smoke.py` |
| `mc-production-confidence` | Operational | High | True | `aiplatform/mission_control/production_confidence.py` |
| `mc-ci-monitor` | Operational | Medium | True | `aiplatform/mission_control/ci_monitor.py` |
| `mc-startup-pipeline` | Operational | Critical | True | `aiplatform/mission_control/startup_pipeline.py` |
| `mc-session-recorder` | Operational | Medium | True | `aiplatform/mission_control/session_recorder.py` |
| `mc-timeline` | Operational | Medium | True | `aiplatform/mission_control/timeline.py` |
| `mc-routing-log` | Operational | High | True | `aiplatform/mission_control/routing_log.py` |
| `mc-intent-analytics` | Operational | Medium | True | `aiplatform/mission_control/intent_analytics.py` |
| `mc-diagnostics` | Operational | High | True | `aiplatform/mission_control/diagnostics.py` |
| `mc-recovery` | Operational | High | True | `aggregator recovery` |
| `mc-activity-notifications` | Operational | Medium | True | `aiplatform/mission_control/activity.py` |
| `mc-bug-report-exports` | Operational | Medium | True | `aiplatform/mission_control/bug_report.py` |
| `mc-endurance` | Operational | Medium | True | `aiplatform/mission_control/endurance.py` |
| `backup-restore-repair-aria` | Operational | Critical | True | `jarvis/application/standalone/workstation_impl` |
| `automation-scheduler` | Operational | High | True | `jarvis/proactive_scheduler.py` |
| `security-pin` | Operational | High | True | `jarvis/security` |
| `operations-behavior` | Operational | High | True | `jarvis/behaviors/operations` |
| `first-run-install` | Operational | High | True | `application/standalone/workstation_impl` |
| `system-audit` | Operational | Medium | True | `jarvis/system_audit_engine.py` |
| `intel-memory-platform` | Intelligence | High | True | `aiplatform/memory` |
| `intel-knowledge-platform` | Intelligence | Medium | True | `aiplatform/knowledge` |
| `intel-intelligence-pipeline` | Intelligence | High | True | `aiplatform/intelligence` |
| `intel-vectorstore` | Intelligence | High | True | `aiplatform/vectorstore` |
| `runtime-client` | Platform | High | True | `jarvis/runtime_client.py` |
| `mission-control-embed` | Platform | High | True | `jarvis/mission_control.py` |
| `platform-attachment` | Platform | High | True | `jarvis/platform_attachment.py` |

## Related

- Behavioral Contract: `docs/aria_core/BEHAVIORAL_CONTRACT.json`
- Phase 1 notes: `docs/aria_core/PHASE1.md`

Nothing may leave this inventory until its replacement passes validation.
