/** Smart welcome — personalized resume card on Dashboard / startup. */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function greeting() {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  }

  function render() {
    const host = $("smartWelcomeCard");
    if (!host) return;
    const prefs = window.AriaUiPrefs?.load?.() || {};
    const recent = prefs.recentViews || [];
    const labels = window.AriaFavorites?.VIEW_LABELS || {};
    const last = recent[0];
    const health = $("statusSegProvider")?.textContent || "";
    const jobs = $("statusSegJobs")?.textContent || "";
    const firstRun = !prefs.whatsNewSeen && !recent.length;

    const actions = [];
    if (firstRun) {
      actions.push({
        label: "Start chatting",
        primary: true,
        run: () => {
          window.switchToView?.("chat");
          setTimeout(() => {
            const i = $("messageInput");
            if (i) {
              i.value = "What can you do?";
              i.focus();
            }
          }, 80);
        },
      });
      actions.push({
        label: "Open Mission Control",
        run: () => window.switchToView?.("workstation"),
      });
      actions.push({
        label: "What's New",
        run: () => window.openWhatsNew?.(true),
      });
      actions.push({
        label: "Keyboard shortcuts",
        run: () => $("shortcutsBtn")?.click(),
      });
    } else if (last && last !== "dashboard") {
      actions.push({
        label: `Resume ${labels[last] || last}`,
        primary: true,
        run: () => window.switchToView?.(last),
      });
    }
    const favs = window.AriaFavorites?.getFavorites?.() || [];
    favs.slice(0, 3).forEach((v) => {
      if (v === last) return;
      actions.push({ label: labels[v] || v, run: () => window.switchToView?.(v) });
    });
    actions.push({
      label: "Layouts",
      run: () => window.AriaLayouts?.openModal?.() || window.AriaWorkspaces?.openModal?.(),
    });

    const tips = [];
    if (firstRun) tips.push("Pin favorites, try Ctrl+K, and check Mission Control for provider health.");
    if (/degraded|unavailable/i.test(health)) tips.push("Provider needs attention — open Mission Control.");
    if (jobs && jobs !== "idle") tips.push(`Background activity: ${jobs}.`);
    const prompts = window.AriaHistory?.list?.("prompts") || [];
    if (!firstRun && prompts[0]) tips.push(`Last prompt: “${prompts[0].slice(0, 60)}${prompts[0].length > 60 ? "…" : ""}”`);

    host.innerHTML = `
      <div class="smart-welcome-head">
        <p class="smart-welcome-greet">${greeting()}.</p>
        <h3 class="smart-welcome-title">${firstRun ? "Welcome to Aria" : "Continue where you left off"}</h3>
        <p class="muted smart-welcome-sub">${tips[0] || "Your favorites and recent work are ready."}</p>
      </div>
      <div class="smart-welcome-actions"></div>
      ${tips[1] ? `<p class="muted small">${tips[1]}</p>` : ""}
    `;
    const wrap = host.querySelector(".smart-welcome-actions");
    actions.slice(0, 5).forEach((a) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = a.primary ? "apply-btn small" : "ghost-btn small";
      btn.textContent = a.label;
      btn.addEventListener("click", a.run);
      wrap?.appendChild(btn);
    });
  }

  function injectIntoDashboard() {
    const body = $("dashboardBody");
    if (!body) return;
    let card = $("smartWelcomeCard");
    if (!card) {
      card = document.createElement("section");
      card.id = "smartWelcomeCard";
      card.className = "smart-welcome-card dash-widget";
      card.dataset.widget = "smartWelcome";
      const header = body.querySelector(".dash-header-row");
      if (header) header.after(card);
      else body.prepend(card);
    }
    render();
  }

  window.AriaSmartWelcome = { render, injectIntoDashboard };

  window.addEventListener("aria-view-change", (e) => {
    if (e.detail?.view === "dashboard") setTimeout(injectIntoDashboard, 200);
  });
})();
