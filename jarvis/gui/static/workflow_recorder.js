/** View Paths — UI navigation shortcuts only (NOT Automation workflows). */
(function () {
  "use strict";

  let recording = false;
  /** @type {{type:string,view?:string,label?:string,ts:number}[]} */
  let buffer = [];

  function $(id) {
    return document.getElementById(id);
  }

  function saved() {
    const prefs = window.AriaUiPrefs;
    let v = prefs?.get?.("viewPaths", null);
    if (!v || typeof v !== "object") {
      v = prefs?.get?.("recordedWorkflows", {});
      if (v && typeof v === "object" && Object.keys(v).length) {
        prefs?.set?.("viewPaths", v);
      }
    }
    return v && typeof v === "object" ? v : {};
  }

  function start() {
    recording = true;
    buffer = [];
    updateUi();
    window.showAriaToast?.("Recording View Path — navigate Aria views", "info", 3500);
  }

  function stop() {
    recording = false;
    updateUi();
    return buffer.slice();
  }

  function recordView(view) {
    if (!recording || !view) return;
    const last = buffer[buffer.length - 1];
    if (last?.type === "view" && last.view === view) return;
    buffer.push({
      type: "view",
      view,
      label: window.AriaFavorites?.VIEW_LABELS?.[view] || view,
      ts: Date.now(),
    });
    renderBuffer();
  }

  function save(name) {
    const steps = stop();
    const id = String(name || "").trim();
    if (!id) {
      window.showAriaToast?.("Name the View Path first", "warn", 2500);
      return;
    }
    if (steps.length < 2) {
      window.showAriaToast?.("Record at least two views", "warn", 2500);
      return;
    }
    const all = saved();
    const key = id.toLowerCase().replace(/\s+/g, "-").slice(0, 40);
    all[key] = { label: id, steps, savedAt: Date.now() };
    window.AriaUiPrefs?.set?.("viewPaths", all);
    window.AriaUiPrefs?.set?.("recordedWorkflows", all);
    window.AriaHistory?.push?.("viewPaths", key, 12);
    window.showAriaToast?.(`Saved View Path “${id}”`, "ok", 2500);
    renderList();
    buffer = [];
    renderBuffer();
  }

  async function replay(key) {
    const wf = saved()[key];
    if (!wf?.steps?.length) return;
    window.showAriaToast?.(`Running View Path “${wf.label}”…`, "info", 2000);
    for (const step of wf.steps) {
      if (step.type === "view" && step.view) {
        window.switchToView?.(step.view);
        await new Promise((r) => setTimeout(r, 350));
      }
    }
    window.showAriaToast?.(`Finished View Path “${wf.label}”`, "ok", 2500);
  }

  function remove(key) {
    const all = saved();
    delete all[key];
    window.AriaUiPrefs?.set?.("viewPaths", all);
    window.AriaUiPrefs?.set?.("recordedWorkflows", all);
    renderList();
  }

  function renderBuffer() {
    const el = $("workflowBuffer");
    if (!el) return;
    el.textContent = buffer.length
      ? buffer.map((s, i) => `${i + 1}. ${s.label || s.view}`).join(" → ")
      : "No steps yet — View Paths record navigation only";
  }

  function renderList() {
    const list = $("workflowList");
    if (!list) return;
    list.replaceChildren();
    const entries = Object.entries(saved());
    if (!entries.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "No View Paths yet. Record navigation shortcuts here — Automation Home owns schedules and rules.";
      list.appendChild(empty);
      return;
    }
    entries.forEach(([key, wf]) => {
      const row = document.createElement("div");
      row.className = "workflow-row";
      const run = document.createElement("button");
      run.type = "button";
      run.className = "ghost-btn small";
      run.textContent = wf.label || key;
      run.title = (wf.steps || []).map((s) => s.label).join(" → ");
      run.addEventListener("click", () => replay(key));
      const del = document.createElement("button");
      del.type = "button";
      del.className = "ghost-btn tiny";
      del.textContent = "×";
      del.addEventListener("click", () => remove(key));
      row.append(run, del);
      list.appendChild(row);
    });
  }

  function updateUi() {
    const btn = $("workflowRecordBtn");
    if (btn) {
      btn.textContent = recording ? "Stop recording" : "Record path";
      btn.classList.toggle("active", recording);
    }
  }

  function openModal() {
    $("workflowModal")?.classList.remove("hidden");
    renderList();
    renderBuffer();
  }

  function init() {
    window.addEventListener("aria-view-change", (e) => recordView(e.detail?.view));
    $("workflowRecordBtn")?.addEventListener("click", () => {
      if (recording) stop();
      else start();
      updateUi();
      renderBuffer();
    });
    $("workflowSaveBtn")?.addEventListener("click", () => {
      save($("workflowNameInput")?.value);
    });
    $("workflowOpenBtn")?.addEventListener("click", openModal);
    $("workflowCloseBtn")?.addEventListener("click", () => $("workflowModal")?.classList.add("hidden"));
  }

  window.AriaWorkflows = { start, stop, save, replay, openModal, isRecording: () => recording };
  window.AriaViewPaths = window.AriaWorkflows;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
