/** HA entity browser + scene composer — extracted from movie_tiers.js. */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || data.detail || `Request failed (${res.status})`);
    }
    return data;
  }

  async function loadHaEntities() {
    const list = $("haEntityList");
    if (!list) return;
    const domain = $("haDomainFilter")?.value || "light";
    list.innerHTML = "<li class='muted'>Loading…</li>";
    try {
      const q = domain ? `?domain=${encodeURIComponent(domain)}&limit=60` : "?limit=60";
      const data = await fetchJson(`/api/homeassistant/entities${q}`);
      const ents = data.entities || [];
      const isScene = domain === "scene";
      list.innerHTML = ents.length
        ? ents
            .map((e) => {
              const id = e.entity_id || "";
              const name = e.attributes?.friendly_name || id;
              const st = e.state || "?";
              const chatBtn = `<button type="button" class="ghost-btn tiny ha-ent-chat" data-eid="${escapeHtml(id)}" title="Insert in chat">Chat</button>`;
              const actBtn = isScene
                ? `<button type="button" class="ghost-btn tiny ha-ent-scene" data-eid="${escapeHtml(id)}">Activate</button>`
                : `<button type="button" class="ghost-btn tiny ha-ent-toggle" data-eid="${escapeHtml(id)}">${escapeHtml(st)}</button>`;
              return `<li><span>${escapeHtml(name)}</span><code>${escapeHtml(id)}</code>${actBtn}${chatBtn}</li>`;
            })
            .join("")
        : `<li class='muted'>No ${domain || "entities"} found — add integrations in HA.</li>`;
      list.querySelectorAll(".ha-ent-toggle").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            const res = await fetch("/api/homeassistant/toggle", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ entity_id: btn.dataset.eid, action: "toggle" }),
            });
            const data = await res.json().catch(() => ({}));
            if (data.confirm_required) {
              window.showToolConfirm?.(data);
              return;
            }
            if (!res.ok || data.ok === false) {
              throw new Error(data.message || data.detail || `Toggle failed (${res.status})`);
            }
            window.showAriaToast?.(`Toggled ${btn.dataset.eid}`, "ok", 2500);
            loadHaEntities();
          } catch (err) {
            window.showAriaToast?.(err.message || "Toggle failed", "err", 5000);
          }
        });
      });
      list.querySelectorAll(".ha-ent-scene").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            const res = await fetch("/api/homeassistant/scene", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ entity_id: btn.dataset.eid }),
            });
            const data = await res.json().catch(() => ({}));
            if (data.confirm_required) {
              window.showToolConfirm?.(data);
              return;
            }
            if (!res.ok || data.ok === false) {
              throw new Error(data.message || data.detail || `Scene failed (${res.status})`);
            }
            window.showAriaToast?.(`Activated ${btn.dataset.eid}`, "ok", 2500);
            loadHaEntities();
          } catch (err) {
            window.showAriaToast?.(err.message || "Scene failed", "err", 5000);
          }
        });
      });
      list.querySelectorAll(".ha-ent-chat").forEach((btn) => {
        btn.addEventListener("click", () => {
          const input = $("messageInput");
          if (input) {
            input.value = `${isScene ? "activate scene" : "toggle"} ${btn.dataset.eid}`;
            input.focus();
          }
        });
      });
    } catch (err) {
      list.innerHTML = `<li class='muted'>Could not load entities: ${escapeHtml(err.message || "error")}</li>`;
      window.showAriaToast?.(err.message || "Could not load HA entities", "err", 5000);
    }
  }

  function initHaExtras() {
    $("haDomainFilter")?.addEventListener("change", loadHaEntities);
    $("haEntitiesRefreshBtn")?.addEventListener("click", loadHaEntities);
    $("haSceneSaveBtn")?.addEventListener("click", async () => {
      const scene = $("haSceneComposerInput")?.value?.trim();
      if (!scene) return;
      try {
        const res = await fetch("/api/homeassistant/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ leave_scene: scene }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          throw new Error(data.message || data.detail || `Save failed (${res.status})`);
        }
        if ($("haLeaveSceneInput")) $("haLeaveSceneInput").value = scene;
        window.showAriaToast?.(`Leave scene set to ${scene}`, "ok", 3000);
      } catch (err) {
        window.showAriaToast?.(err.message || "Could not save leave scene", "err", 5000);
      }
    });
    $("haSetupWizardBtn")?.addEventListener("click", () => $("haSetupModal")?.classList.remove("hidden"));
    $("haSetupCloseBtn")?.addEventListener("click", () => $("haSetupModal")?.classList.add("hidden"));
    loadHaEntities();
  }

  window.loadHaEntities = loadHaEntities;
  window.initHaExtras = initHaExtras;

  document.addEventListener("DOMContentLoaded", () => {
    initHaExtras();
  });
})();
