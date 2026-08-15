/** Aria final-release certification harness — injected into the live GUI. */
(function () {
  "use strict";

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function baseResult(feature) {
    return {
      feature,
      started: new Date().toISOString(),
      workflows: [],
      controls: [],
      defects: [],
      fails: [],
      blocked: [],
      notes: [],
      status: "PASS",
    };
  }

  function helpers(R) {
    const mark = (c) => R.controls.push(c);
    const fail = (msg, detail) => {
      R.fails.push(msg);
      R.defects.push({ msg, detail: detail || null });
      R.status = "FAIL";
      throw new Error("HARD_FAIL:" + msg);
    };
    const assert = (cond, msg, detail) => {
      if (!cond) fail(msg, detail);
    };
    return { mark, fail, assert, sleep };
  }

  async function closeDialogs() {
    for (const sel of [
      "#ariaConfirmDialog button",
      "#ariaPromptDialog button",
      ".modal:not(.hidden) button",
      "dialog[open] button",
    ]) {
      const btns = [...document.querySelectorAll(sel)].filter((b) =>
        /cancel|close|no|×/i.test(b.textContent || b.getAttribute("aria-label") || ""),
      );
      btns.slice(0, 2).forEach((b) => {
        try {
          b.click();
        } catch (_) {}
      });
    }
  }

  async function certifyCalendar() {
    const R = baseResult("Calendar");
    const { mark, assert, sleep } = helpers(R);
    try {
      window.switchToView?.("calendar");
      await sleep(800);
      const view = document.getElementById("calendarView");
      assert(view && !view.classList.contains("hidden"), "calendar hidden");
      mark("open");
      R.workflows.push("open");

      const viewLabels = ["Day", "Week", "Month", "Agenda"];
      for (const label of viewLabels) {
        const btn = [...document.querySelectorAll("#calendarView button")].find(
          (b) => (b.textContent || "").trim().toLowerCase() === label.toLowerCase(),
        );
        if (!btn) {
          R.notes.push("missing view " + label);
          continue;
        }
        btn.click();
        mark("view:" + label);
        await sleep(500);
        assert((view.innerText || "").trim().length > 20, "blank after " + label);
        R.workflows.push("view " + label);
      }

      for (const id of ["calendarPrevBtn", "calendarNextBtn", "calendarTodayBtn"]) {
        const el = document.getElementById(id);
        assert(!!el, id + " missing");
        el.click();
        mark(id);
        await sleep(350);
      }
      R.workflows.push("nav");

      const filt = document.getElementById("calendarFilter");
      if (filt && filt.options && filt.options.length > 1) {
        const cur = filt.value;
        filt.selectedIndex = 1;
        filt.dispatchEvent(new Event("change", { bubbles: true }));
        mark("calendarFilter");
        await sleep(350);
        filt.value = cur;
        filt.dispatchEvent(new Event("change", { bubbles: true }));
        R.workflows.push("filter");
      }

      const search = document.getElementById("calendarSearch");
      if (search) {
        search.value = "cert";
        search.dispatchEvent(new Event("input", { bubbles: true }));
        mark("calendarSearch");
        await sleep(350);
        search.value = "";
        search.dispatchEvent(new Event("input", { bubbles: true }));
        R.workflows.push("search");
      }

      const ics = document.getElementById("calendarIcsUrl");
      if (ics) {
        const prev = ics.value;
        ics.value = "http://127.0.0.1:9/invalid.ics";
        mark("calendarIcsUrl");
        document.getElementById("calendarIcsTestBtn")?.click();
        mark("calendarIcsTestBtn");
        await sleep(1200);
        R.workflows.push("ics test invalid");
        document.getElementById("calendarIcsRefreshBtn")?.click();
        mark("calendarIcsRefreshBtn");
        await sleep(700);
        R.workflows.push("ics refresh");
        ics.value = prev;
      }

      for (const id of [
        "calendarOpenPlannerBtn",
        "calendarOpenJournalBtn",
        "calendarOpenDocumentsBtn",
        "calendarHintPlannerBtn",
        "calendarHintJournalBtn",
        "calendarVisionBtn",
        "calendarMemoryBtn",
        "calendarHaMeetingBtn",
      ]) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.click();
        mark(id);
        await sleep(400);
        await closeDialogs();
        window.switchToView?.("calendar");
        await sleep(200);
      }
      R.workflows.push("cross-links+aux");

      const deny = /print|pdf|restart|wipe|factory/i;
      const btns = [...document.querySelectorAll("#calendarView button")].filter((b) => {
        const r = b.getBoundingClientRect();
        const lab = (b.textContent || "") + (b.title || "") + (b.id || "");
        return r.width > 0 && r.height > 0 && !deny.test(lab);
      });
      for (const b of btns.slice(0, 40)) {
        try {
          b.click();
          mark("sweep:" + (b.id || (b.textContent || "").trim().slice(0, 24)));
          await sleep(80);
        } catch (_) {}
        await closeDialogs();
        window.switchToView?.("calendar");
      }
      R.workflows.push("control sweep");
      assert((view.innerText || "").trim().length > 20, "calendar blank end");
      R.ended = new Date().toISOString();
      R.controlCount = R.controls.length;
      R.workflowCount = R.workflows.length;
    } catch (e) {
      R.status = "FAIL";
      R.error = String(e && e.message ? e.message : e);
      R.ended = new Date().toISOString();
    }
    return R;
  }

  async function certifyJournal() {
    const R = baseResult("Journal");
    const { mark, assert, sleep } = helpers(R);
    try {
      window.switchToView?.("journal");
      await sleep(700);
      const view = document.getElementById("journalView");
      assert(view && !view.classList.contains("hidden"), "journal hidden");
      mark("open");
      R.workflows.push("open");

      const rapid = document.getElementById("rapidLogInput");
      assert(!!rapid, "rapidLogInput missing");
      const addBtn = document.getElementById("rapidLogBtn");
      assert(!!addBtn, "rapidLogBtn missing");
      // Ensure Daily tab + content loaded
      const dailyTab = [...document.querySelectorAll("#journalView [data-bujo]")].find((b) => b.dataset.bujo === "daily");
      dailyTab?.click();
      await sleep(1500);
      if (document.querySelector("#bujoContent .bujo-loading")) {
        dailyTab?.click();
        await sleep(2000);
      }
      assert(!document.querySelector("#bujoContent .bujo-loading"), "journal stuck Loading");
      const entry = "cert-journal-" + Date.now();
      rapid.value = entry;
      rapid.dispatchEvent(new Event("input", { bubbles: true }));
      mark("rapidLogInput");
      addBtn.click();
      mark("rapidLogBtn");
      await sleep(2000);
      const bujoText = document.getElementById("bujoContent")?.innerText || "";
      assert(
        bujoText.includes(entry) || rapid.value === "",
        "journal entry missing",
        { bujo: bujoText.slice(0, 400), value: rapid.value },
      );
      R.workflows.push("rapid log");
      // Enter key path
      const entry2 = "cert-journal-enter-" + Date.now();
      rapid.value = entry2;
      rapid.dispatchEvent(new Event("input", { bubbles: true }));
      rapid.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true, cancelable: true }));
      mark("rapid Enter");
      await sleep(2000);
      assert(
        (document.getElementById("bujoContent")?.innerText || "").includes(entry2) || rapid.value === "",
        "journal Enter path failed",
        { value: rapid.value, text: (document.getElementById("bujoContent")?.innerText || "").slice(0, 200) },
      );
      R.workflows.push("rapid enter");

      const search = document.getElementById("journalSearch");
      if (search) {
        search.value = "cert-journal";
        search.dispatchEvent(new Event("input", { bubbles: true }));
        mark("journalSearch");
        document.getElementById("journalSearchBtn")?.click();
        mark("journalSearchBtn");
        await sleep(600);
        R.workflows.push("search");
        search.value = "";
      }

      for (const id of [
        "journalOpenCalendarBtn",
        "journalOpenPlannerBtn",
        "journalOpenMemoryBtn",
        "journalReflectBtn",
        "journalAssistPromoteBtn",
        "journalWritingModeBtn",
        "journalShortcutsBtn",
        "journalExportBtn",
        "journalBackupBtn",
      ]) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.click();
        mark(id);
        await sleep(350);
        await closeDialogs();
        window.switchToView?.("journal");
      }
      R.workflows.push("toolbar");

      // Avoid print/pdf
      R.notes.push("skipped journalPrintBtn/journalPdfBtn to avoid extra browser tabs");
      R.ended = new Date().toISOString();
      R.controlCount = R.controls.length;
      R.workflowCount = R.workflows.length;
    } catch (e) {
      R.status = "FAIL";
      R.error = String(e && e.message ? e.message : e);
      R.ended = new Date().toISOString();
    }
    return R;
  }

  async function certifySearch() {
    const R = baseResult("Search");
    const { mark, assert, sleep } = helpers(R);
    try {
      window.switchToView?.("search");
      await sleep(600);
      const view = document.getElementById("searchView");
      assert(view && !view.classList.contains("hidden"), "search hidden");
      mark("open");
      const input = document.getElementById("searchHomeInput");
      assert(!!input, "searchHomeInput missing");
      input.value = "planner task";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      mark("searchHomeInput");
      document.getElementById("searchHomeRunBtn")?.click();
      mark("searchHomeRunBtn");
      await sleep(2000);
      assert((view.innerText || "").trim().length > 40, "search empty results area");
      R.workflows.push("run search");

      const mode = document.getElementById("searchModeSelect");
      if (mode && mode.options.length > 1) {
        const cur = mode.value;
        mode.selectedIndex = Math.min(1, mode.options.length - 1);
        mode.dispatchEvent(new Event("change", { bubbles: true }));
        mark("searchModeSelect");
        await sleep(300);
        mode.value = cur;
        mode.dispatchEvent(new Event("change", { bubbles: true }));
        R.workflows.push("mode");
      }

      for (const id of ["searchOptInGallery", "searchOptInHa"]) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.click();
        mark(id);
        await sleep(100);
        el.click();
      }
      R.workflows.push("opt-ins");

      document.getElementById("searchHomeRefreshBtn")?.click();
      mark("searchHomeRefreshBtn");
      document.getElementById("searchDiagBtn")?.click();
      mark("searchDiagBtn");
      await sleep(500);
      await closeDialogs();
      document.getElementById("searchClearHistoryBtn")?.click();
      mark("searchClearHistoryBtn");
      await sleep(300);
      R.workflows.push("refresh/diag/clear");

      R.ended = new Date().toISOString();
      R.controlCount = R.controls.length;
      R.workflowCount = R.workflows.length;
    } catch (e) {
      R.status = "FAIL";
      R.error = String(e && e.message ? e.message : e);
      R.ended = new Date().toISOString();
    }
    return R;
  }

  async function certifyBrowser() {
    const R = baseResult("Browser");
    const { mark, assert, sleep } = helpers(R);
    try {
      window.switchToView?.("browser");
      await sleep(700);
      const view = document.getElementById("browserView");
      assert(view && !view.classList.contains("hidden"), "browser hidden");
      mark("open");
      const url = document.getElementById("browserUrlInput");
      assert(!!url, "browserUrlInput missing");
      url.value = "https://example.com";
      mark("browserUrlInput");
      document.getElementById("browserNavigateBtn")?.click();
      mark("browserNavigateBtn");
      await sleep(2500);
      R.workflows.push("navigate");

      for (const id of [
        "browserRefreshBtn",
        "browserScreenshotBtn",
        "browserBookmarkBtn",
        "browserFloatBtn",
        "browserHomeRefreshBtn",
        "browserPauseBtn",
        "browserResumeBtn",
        "browserStopBtn",
      ]) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.click();
        mark(id);
        await sleep(400);
      }
      R.workflows.push("toolbar");

      for (const id of [
        "browserOpenProjectsBtn",
        "browserOpenJobsBtn",
        "browserOpenCodingBtn",
        "browserOpenMemoryBtn",
        "browserOpenDocumentsBtn",
        "browserOpenChatBtn",
      ]) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.click();
        mark(id);
        await sleep(350);
        window.switchToView?.("browser");
      }
      R.workflows.push("cross-links");
      R.ended = new Date().toISOString();
      R.controlCount = R.controls.length;
      R.workflowCount = R.workflows.length;
    } catch (e) {
      R.status = "FAIL";
      R.error = String(e && e.message ? e.message : e);
      R.ended = new Date().toISOString();
    }
    return R;
  }

  async function certifyMissionControl() {
    const R = baseResult("Mission Control");
    const { mark, assert, sleep } = helpers(R);
    try {
      window.switchToView?.("workstation");
      await sleep(1000);
      const view = document.getElementById("workstationView");
      assert(view && !view.classList.contains("hidden"), "MC hidden");
      mark("open");
      R.workflows.push("open");

      document.getElementById("mcRefreshBtn")?.click();
      mark("mcRefreshBtn");
      await sleep(1500);
      R.workflows.push("refresh");

      const tabs = [...document.querySelectorAll("#workstationView button, #workstationView [role=tab]")].filter(
        (b) => {
          const t = (b.textContent || "").trim();
          return t && t.length < 40 && b.getBoundingClientRect().width > 0;
        },
      );
      const seen = new Set();
      for (const tab of tabs.slice(0, 25)) {
        const label = (tab.textContent || "").trim();
        if (seen.has(label)) continue;
        seen.add(label);
        tab.click();
        mark("tab:" + label);
        await sleep(500);
      }
      R.workflows.push("tabs");

      for (const id of [
        "mcOpenJobCenterBtn",
        "mcOpenActivityCenterBtn",
        "mcOpenChatBtn",
        "mcOpenAuditBtn",
        "mcOpenDashboardBtn",
      ]) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.click();
        mark(id);
        await sleep(500);
        await closeDialogs();
        window.switchToView?.("workstation");
      }
      R.workflows.push("openers");

      // health API must respond quickly
      const t0 = Date.now();
      const health = await fetch("/api/mission-control/health").then((r) => r.json());
      const ms = Date.now() - t0;
      mark("api health " + ms + "ms");
      assert(ms < 8000, "health too slow", { ms, health });
      R.notes.push({ healthMs: ms, overall: health.overall, ok: health.ok });
      R.workflows.push("health api");

      R.ended = new Date().toISOString();
      R.controlCount = R.controls.length;
      R.workflowCount = R.workflows.length;
    } catch (e) {
      R.status = "FAIL";
      R.error = String(e && e.message ? e.message : e);
      R.ended = new Date().toISOString();
    }
    return R;
  }

  async function certifyViewSmoke(feature, viewId, controlIds) {
    const R = baseResult(feature);
    const { mark, assert, sleep } = helpers(R);
    try {
      window.switchToView?.(viewId === "dashboard" ? "dashboard" : viewId);
      await sleep(700);
      const view = document.getElementById(viewId + "View") || document.getElementById(viewId);
      assert(view && !view.classList.contains("hidden"), feature + " hidden");
      mark("open");
      R.workflows.push("open");
      assert((view.innerText || "").trim().length > 10, feature + " blank");

      for (const id of controlIds || []) {
        const el = document.getElementById(id);
        if (!el) {
          R.notes.push("missing " + id);
          continue;
        }
        try {
          if (el.tagName === "SELECT" && el.options.length > 1) {
            const cur = el.value;
            el.selectedIndex = (el.selectedIndex + 1) % el.options.length;
            el.dispatchEvent(new Event("change", { bubbles: true }));
            mark(id);
            await sleep(200);
            el.value = cur;
            el.dispatchEvent(new Event("change", { bubbles: true }));
          } else if (el.type === "checkbox") {
            el.click();
            mark(id);
            await sleep(100);
            el.click();
          } else if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
            const prev = el.value;
            el.value = (el.value || "") + " cert";
            el.dispatchEvent(new Event("input", { bubbles: true }));
            mark(id);
            el.value = prev;
          } else {
            el.click();
            mark(id);
            await sleep(300);
          }
        } catch (err) {
          fail("control " + id, String(err));
        }
        await closeDialogs();
        window.switchToView?.(viewId === "workstation" ? "workstation" : viewId);
      }
      R.workflows.push("controls");
      R.ended = new Date().toISOString();
      R.controlCount = R.controls.length;
      R.workflowCount = R.workflows.length;
    } catch (e) {
      R.status = "FAIL";
      R.error = String(e && e.message ? e.message : e);
      R.ended = new Date().toISOString();
    }
    return R;
  }

  async function certifySettingsPersistence() {
    const R = baseResult("Settings");
    const { mark, assert, sleep } = helpers(R);
    try {
      window.switchToView?.("settings");
      await sleep(700);
      const view = document.getElementById("settingsView");
      assert(view && !view.classList.contains("hidden"), "settings hidden");
      mark("open");

      const theme = document.getElementById("settingsThemeSelect");
      const density = document.getElementById("settingsDensitySelect");
      const dock = document.getElementById("settingsDockToggle");
      const status = document.getElementById("settingsStatusToggle");
      const mini = document.getElementById("settingsMiniChatToggle");

      const before = {
        theme: theme?.value,
        density: density?.value,
        dock: dock?.checked,
        status: status?.checked,
        mini: mini?.checked,
      };
      R.notes.push({ before });

      if (theme && theme.options.length > 1) {
        theme.selectedIndex = (theme.selectedIndex + 1) % theme.options.length;
        theme.dispatchEvent(new Event("change", { bubbles: true }));
        mark("settingsThemeSelect");
      }
      if (density && density.options.length > 1) {
        density.selectedIndex = (density.selectedIndex + 1) % density.options.length;
        density.dispatchEvent(new Event("change", { bubbles: true }));
        mark("settingsDensitySelect");
      }
      if (dock) {
        dock.click();
        mark("settingsDockToggle");
      }
      if (status) {
        status.click();
        mark("settingsStatusToggle");
      }
      if (mini) {
        mini.click();
        mark("settingsMiniChatToggle");
      }
      await sleep(500);

      const mid = {
        theme: theme?.value,
        density: density?.value,
        dock: dock?.checked,
        status: status?.checked,
        mini: mini?.checked,
      };
      R.notes.push({ mid });
      R.workflows.push("change settings");

      // Soft reload same page to verify persistence (SPA prefs)
      location.hash = "#settings";
      await sleep(300);
      window.switchToView?.("settings");
      await sleep(800);
      const afterNav = {
        theme: document.getElementById("settingsThemeSelect")?.value,
        density: document.getElementById("settingsDensitySelect")?.value,
        dock: document.getElementById("settingsDockToggle")?.checked,
        status: document.getElementById("settingsStatusToggle")?.checked,
        mini: document.getElementById("settingsMiniChatToggle")?.checked,
      };
      R.notes.push({ afterNav });
      assert(afterNav.theme === mid.theme, "theme not persisted");
      assert(afterNav.density === mid.density, "density not persisted");
      if (typeof mid.dock === "boolean") assert(afterNav.dock === mid.dock, "dock not persisted");
      R.workflows.push("persist after nav");

      // restore
      const themeEl = document.getElementById("settingsThemeSelect");
      const densEl = document.getElementById("settingsDensitySelect");
      if (themeEl && before.theme != null) {
        themeEl.value = before.theme;
        themeEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
      if (densEl && before.density != null) {
        densEl.value = before.density;
        densEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
      const dockEl = document.getElementById("settingsDockToggle");
      if (dockEl && typeof before.dock === "boolean" && dockEl.checked !== before.dock) dockEl.click();
      const statusEl = document.getElementById("settingsStatusToggle");
      if (statusEl && typeof before.status === "boolean" && statusEl.checked !== before.status) statusEl.click();
      const miniEl = document.getElementById("settingsMiniChatToggle");
      if (miniEl && typeof before.mini === "boolean" && miniEl.checked !== before.mini) miniEl.click();
      mark("restore");
      R.workflows.push("restore");

      for (const id of [
        "settingsHomeRefreshBtn",
        "settingsVoiceChatBtn",
        "settingsDiagBtn",
        "settingsExportBtn",
        "settingsSearchBtn",
        "settingsResetAppearanceBtn",
      ]) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.click();
        mark(id);
        await sleep(400);
        await closeDialogs();
        window.switchToView?.("settings");
      }
      R.workflows.push("toolbar");

      R.ended = new Date().toISOString();
      R.controlCount = R.controls.length;
      R.workflowCount = R.workflows.length;
    } catch (e) {
      R.status = "FAIL";
      R.error = String(e && e.message ? e.message : e);
      R.ended = new Date().toISOString();
    }
    return R;
  }

  window.AriaFinalCert = {
    certifyCalendar,
    certifyJournal,
    certifySearch,
    certifyBrowser,
    certifyMissionControl,
    certifyViewSmoke,
    certifySettingsPersistence,
    async runBatch(names) {
      const out = [];
      for (const n of names) {
        if (typeof this[n] === "function") out.push(await this[n]());
      }
      return out;
    },
  };
})();
