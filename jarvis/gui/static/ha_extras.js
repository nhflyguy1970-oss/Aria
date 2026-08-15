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

  function isRoomAbort(err) {
    return (
      window.AriaNet?.isRoomAbort?.(err) ||
      err?.name === "AbortError" ||
      /aborted|aria-room-leave|failed to fetch/i.test(String(err?.message || ""))
    );
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || data.detail || `Request failed (${res.status})`);
    }
    return data;
  }

  function isHaTransient(err) {
    return /home assistant disabled|home assistant is locked|unlock aria/i.test(
      String(err?.message || "")
    );
  }

  async function loadHaEntities() {
    const list = $("haEntityList");
    if (!list) return;
    const domain = $("haDomainFilter")?.value || "light";
    list.innerHTML = "<li class='muted'>Loading…</li>";
    try {
      const q = domain ? `?domain=${encodeURIComponent(domain)}&limit=60` : "?limit=60";
      const data = await fetchJson(`/api/homeassistant/entities${q}`);
      loadHaEntities._retries = 0;
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
            const res = await fetch("/api/smarthome/product/control", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                target: btn.dataset.eid,
                action: "toggle",
                confirmed: true,
                source: "ha_panel",
              }),
            });
            const data = await res.json().catch(() => ({}));
            if (data.confirm_required) {
              window.showToolConfirm?.(data);
              return;
            }
            if (!res.ok || data.ok === false) {
              throw new Error(data.message || data.detail || `Toggle failed (${res.status})`);
            }
            window.showAriaToast?.(data.message || `Toggled ${btn.dataset.eid}`, "ok", 2500);
            loadHaEntities();
          } catch (err) {
            if (isRoomAbort(err)) return;
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
            if (isRoomAbort(err)) return;
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
      // BUG-020: room thrash aborts looked like "Could not load entities: error"
      if (isRoomAbort(err)) {
        window.AriaNet?.absorbAbort?.(err, () => loadHaEntities(), 180);
        return;
      }
      // First paint can race vault visibility: status becomes Connected a beat later.
      if (isHaTransient(err) && (loadHaEntities._retries || 0) < 3) {
        loadHaEntities._retries = (loadHaEntities._retries || 0) + 1;
        list.innerHTML = "<li class='muted'>Waiting for Home Assistant…</li>";
        clearTimeout(loadHaEntities._retry);
        loadHaEntities._retry = setTimeout(() => loadHaEntities(), 350 * loadHaEntities._retries);
        return;
      }
      loadHaEntities._retries = 0;
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
