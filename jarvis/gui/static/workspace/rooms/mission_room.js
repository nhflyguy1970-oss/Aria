/**
 * Native Mission Room (Phase 5) — quiet ops presence.
 * Not an 18-tab workstation panel. Backend /api/mission-control unchanged.
 */
(function () {
  "use strict";

  const ROOM_ID = "missionRoom";
  let _active = false;
  let _data = null;
  let _tasks = [];
  let _poll = null;

  const kit = () => window.AriaRoomKit;
  const esc = (s) => kit().esc(s);
  const api = (url, opts) => kit().fetchJson(url, opts);

  function root() {
    return document.getElementById(ROOM_ID);
  }

  function buildShell() {
    const el = kit().ensureRoot(ROOM_ID, "mission-room");
    el.setAttribute("aria-label", "Mission");
    if (el.dataset.shellBuilt === "1") return el;
    el.innerHTML = [
      kit().atmosphereHtml(),
      kit().presenceHtml("· Ops", "Listening quietly"),
      '<div class="mission-room__body">',
      '  <main class="mission-room__stage">',
      '    <div class="mission-room__hero" id="missionRoomHero"></div>',
      '    <div class="mission-room__grid" id="missionRoomGrid"></div>',
      '    <section class="mission-room__tasks" aria-label="Autonomous tasks">',
      '      <div class="mission-room__tasks-head"><h2>Tasks</h2><button type="button" data-task-act="new">New task</button></div>',
      '      <div id="missionRoomTasks"></div>',
      '    </section>',
      "  </main>",
      "</div>",
      '<button type="button" class="nr-overflow-btn" id="missionRoomOverflowBtn" aria-label="More">···</button>',
      '<div class="nr-overflow" id="missionRoomOverflow" hidden>',
      '  <button type="button" data-m-act="refresh">Refresh</button>',
      '  <button type="button" data-m-act="recover">Recover provider</button>',
      '  <button type="button" data-m-act="restart">Restart Aria</button>',
      '  <button type="button" data-m-act="repair">Guided repair</button>',
      '  <button type="button" data-m-act="integrity">Integrity</button>',
      '  <button type="button" data-m-act="chat">Ask Aria</button>',
      "</div>",
    ].join("");
    el.dataset.shellBuilt = "1";
    if (!el.parentElement) document.body.appendChild(el);
    wire(el);
    return el;
  }

  function wire(el) {
    if (el.dataset.wired) return;
    el.dataset.wired = "1";
    el.querySelector("#missionRoomOverflowBtn")?.addEventListener("click", (e) => {
      e.stopPropagation();
      const p = el.querySelector("#missionRoomOverflow");
      p.hidden = !p.hidden;
    });
    el.querySelector("#missionRoomOverflow")?.addEventListener("click", async (e) => {
      const act = e.target.closest("[data-m-act]")?.dataset.mAct;
      if (!act) return;
      el.querySelector("#missionRoomOverflow").hidden = true;
      if (act === "refresh") load();
      if (act === "recover") recoverProvider();
      if (act === "restart") restartAria();
      if (act === "repair") window.AriaActivityEngine?.start?.("repair", { confirmHighStakes: false });
      if (act === "integrity") window.AriaActivityEngine?.start?.("integrity", { confirmHighStakes: false });
      if (act === "chat") window.AriaActivityEngine?.start?.("converse", { confirmHighStakes: false });
    });
    el.querySelector(".mission-room__tasks")?.addEventListener("click", taskAction);
  }

  async function taskAction(e) {
    const button = e.target.closest("[data-task-act]");
    if (!button) return;
    const action = button.dataset.taskAct;
    const id = button.dataset.taskId;
    try {
      if (action === "new") {
        const objective = await window.ariaPrompt("What should Aria work on?", "", { title: "New task", okLabel: "Review plan" });
        if (!objective) return;
        await api("/api/agent-tasks", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ objective, project: "general" }) });
      } else if (action === "redirect") {
        const detail = await api(`/api/agent-tasks/${encodeURIComponent(id)}`);
        const current = detail.task;
        const objective = await window.ariaPrompt("Updated goal", current.objective, { title: "Redirect task", okLabel: "Next" });
        if (!objective) return;
        const raw = await window.ariaPrompt("Review remaining steps as JSON", JSON.stringify(current.steps || []),
          { title: "Redirect task", okLabel: "Propose redirect" });
        if (!raw) return;
        await api(`/api/agent-tasks/${encodeURIComponent(id)}/redirect`, { method: "POST",
          headers: { "Content-Type": "application/json" }, body: JSON.stringify({ objective, steps: JSON.parse(raw) }) });
      } else if (action === "artifact") {
        // fetch() carries the API key header (plain links would not over LAN).
        const res = await fetch(`/api/agent-tasks/${encodeURIComponent(id)}/artifact`);
        if (!res.ok) throw new Error(`Artifact unavailable (${res.status})`);
        const url = URL.createObjectURL(await res.blob());
        const link = Object.assign(document.createElement("a"), { href: url, download: `task-${id}.json` });
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        return;
      } else if (action === "reconcile") {
        const detail = await api(`/api/agent-tasks/${encodeURIComponent(id)}`);
        const index = detail.task.progress?.completed_steps || 0;
        const outcome = await window.ariaPrompt("Verified outcome: completed or not_executed", "", { title: "Reconcile operation", okLabel: "Next" });
        if (!outcome) return;
        const evidence = await window.ariaPrompt("Evidence from the external system", "", { title: "Reconcile operation", okLabel: "Next" });
        if (!evidence) return;
        const result = outcome === "completed" ? JSON.parse(await window.ariaPrompt("Observed result JSON", "{\"ok\":true}", { title: "Reconcile operation", okLabel: "Confirm" })) : null;
        await api(`/api/agent-tasks/${encodeURIComponent(id)}/reconcile`, { method: "POST",
          headers: { "Content-Type": "application/json" }, body: JSON.stringify({ step_index: index, outcome, evidence, result }) });
      } else {
        if (["approve", "deny", "cancel"].includes(action)) {
          const yes = await window.ariaConfirm(`${action} task ${id}?`, { title: "Task control", okLabel: action });
          if (!yes) return;
        }
        await api(`/api/agent-tasks/${encodeURIComponent(id)}/${action}`, { method: "POST" });
      }
      await load();
    } catch (err) {
      kit().setStatus(root(), err.message || "Task action failed");
    }
  }

  async function recoverProvider() {
    kit().setStatus(root(), "Recovering provider…");
    try {
      const out = await api("/api/provider/recover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: "OPERATOR_RECOVER", auto: true }),
      });
      kit().setStatus(root(), out.usable ? "Provider usable" : "Provider still down");
      window.showAriaToast?.(
        out.usable ? "Provider recovered" : out.operator_message || "Recovery incomplete",
        out.usable ? "ok" : "warn",
        3500,
      );
      await load();
    } catch (err) {
      kit().setStatus(root(), err.message || "Recover failed");
    }
  }

  async function restartAria() {
    const msg = "Restart Aria server now? Open work will reconnect after a few seconds.";
    if (window.ariaConfirm) {
      if (!(await window.ariaConfirm(msg, { title: "Restart Aria", okLabel: "Restart" }))) return;
    } else if (!window.confirm?.(msg)) {
      return;
    }
    kit().setStatus(root(), "Restarting…");
    try {
      await fetch("/api/jarvis/restart-server", { method: "POST" });
      window.showAriaToast?.("Aria is restarting…", "info", 4000);
    } catch (err) {
      kit().setStatus(root(), err.message || "Restart failed");
    }
  }

  function render() {
    const hero = root()?.querySelector("#missionRoomHero");
    const grid = root()?.querySelector("#missionRoomGrid");
    if (!hero || !grid) return;
    const o = _data?.overview || {};
    const status = o.platform_status || o.status || "unknown";
    const attn = Array.isArray(o.needs_attention) ? o.needs_attention : [];
    const clear = attn.length === 1 && /all clear/i.test(attn[0]);
    const ph = _data?.inference || _data?.providers || {};
    const provider =
      o.inference_provider ||
      ph.provider ||
      ph.current_provider ||
      "ollama";
    const model = o.current_model || ph.current_model || ph.model || "";

    hero.innerHTML =
      `<p class="mission-room__kicker">${esc(status)}</p>` +
      "<h1>System presence</h1>" +
      `<p class="mission-room__pulse">${
        clear || !attn.length
          ? "Everything quiet. Nothing needs you right now."
          : esc(attn.slice(0, 3).join(" · "))
      }</p>`;

    const jobs = o.active_jobs ?? _data?.jobs?.active ?? 0;
    const gpu = o.gpu || "";
    const vram = o.free_vram_mb != null ? `${o.free_vram_mb} MB free VRAM` : "";
    const ready = o.production_readiness != null ? `${o.production_readiness}% ready` : "";
    const phase = o.phase?.phase || o.phase || "";

    grid.innerHTML = [
      card("Attention", clear || !attn.length ? "All clear" : attn.slice(0, 5).join("\n")),
      card("Jobs", String(jobs)),
      card("Providers", [provider, model].filter(Boolean).join(" · ") || "—"),
      card("Hardware", [gpu, vram].filter(Boolean).join(" · ") || "—"),
      card("Readiness", [ready, phase].filter(Boolean).join(" · ") || "—"),
    ].join("");
    renderTasks();
  }

  function renderTasks() {
    const host = root()?.querySelector("#missionRoomTasks");
    if (!host) return;
    if (!_tasks.length) {
      host.innerHTML = '<p class="muted">No tasks yet. Proposed plans stay paused until owner approval.</p>';
      return;
    }
    host.innerHTML = _tasks.map((task) => {
      const id = esc(task.id);
      const state = task.error_kind === "uncertain_effect" ? "awaiting reconciliation" :
        task.display_state === "awaiting_approval" ? "awaiting approval" : task.display_state || task.state;
      const progress = task.progress || {};
      const step = task.current_step?.[0];
      const plan = (task.steps || []).map((item, n) => `<li>${n + 1}. ${esc(item.name || item.action)} ` +
        `<code>${esc(item.action)}</code> <small>${esc(JSON.stringify(item.params || {}).slice(0, 240))}</small></li>`).join("");
      const controls = task.approval === "proposed" ? ["approve", "deny"] :
        task.state === "running" || task.state === "pending" ? ["pause", "cancel"] :
        task.state === "paused" ? ["resume", "redirect", "cancel"] : [];
      if (task.error_kind === "uncertain_effect") controls.unshift("reconcile");
      return `<article class="mission-room__task"><div><strong>${esc(task.objective)}</strong> <code>${id}</code></div>` +
        `<p>${esc(state)} · ${progress.completed_steps || 0}/${progress.total_steps || 0} steps` +
        `${step ? ` · ${esc(step.name || step.action || "")}` : ""} · ${esc(task.elapsed_seconds || 0)}s elapsed</p>` +
        `${task.status_message ? `<p class="muted">${esc(task.status_message)}</p>` : ""}` +
        `${task.error ? `<p class="muted">${esc(task.error)}</p>` : ""}` +
        `${task.artifact_url ? `<button type="button" data-task-act="artifact" data-task-id="${id}">Download result and evidence</button>` : ""}` +
        `<details><summary>Review exact plan</summary><ol>${plan}</ol></details>` +
        `<div>${controls.map((act) => `<button type="button" data-task-act="${act}" data-task-id="${id}">${act}</button>`).join(" ")}</div></article>`;
    }).join("");
  }

  function card(title, body) {
    return (
      `<section class="mission-room__card"><h2>${esc(title)}</h2>` +
      `<p>${esc(body).replace(/\n/g, "<br>")}</p></section>`
    );
  }

  async function load() {
    kit().setStatus(root(), "Reading the system…");
    try {
      _data = await api("/api/mission-control");
      try {
        const taskData = await api("/api/agent-tasks?limit=50");
        _tasks = taskData.tasks || [];
      } catch (_) {
        _tasks = []; // Mission presence remains usable while owner tasks are locked.
      }
      render();
      const o = _data?.overview || {};
      const attn = o.needs_attention || [];
      const clear = attn.length === 1 && /all clear/i.test(attn[0]);
      kit().setStatus(root(), clear ? "All clear" : "Listening quietly");
    } catch (err) {
      kit().setStatus(root(), err.message || "Mission unavailable");
    }
  }

  function startPoll() {
    stopPoll();
    _poll = setInterval(() => {
      if (!_active || document.hidden) return;
      if (window.AriaHouse?.current?.() !== "mission") return;
      load();
    }, 30000);
  }

  function stopPoll() {
    if (_poll) clearInterval(_poll);
    _poll = null;
  }

  async function enter() {
    kit().exitOthers("mission");
    const el = buildShell();
    document.body.classList.add("house-room", "house-mission", "native-mission");
    document.body.dataset.room = "mission";
    window.AriaStage.mount(el, "mission");
    _active = true;
    window.AriaWorkspaceChrome?.apply?.("systems");
    await load();
    startPoll();
    try {
      window.AriaLivingFamiliarity?.recordVisit?.({ room: "mission", view: "workstation" });
    } catch (_) {
      /* ignore */
    }
    window.dispatchEvent(new CustomEvent("aria-native-room", { detail: { room: "mission", native: true } }));
  }

  function exit() {
    if (!_active) return;
    _active = false;
    stopPoll();
    document.body.classList.remove("native-mission");
  }

  window.AriaMissionRoom = {
    enter,
    exit,
    isActive: () => _active,
    version: "5.0.2-oc",
    legacyBridge: false,
  };
  window.AriaRoomKit?.register?.("mission", () => window.AriaMissionRoom);
})();
