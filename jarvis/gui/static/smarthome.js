/** Smart home extras — Kasa discovery, room filters, scene presets (Ada parity). */
(function () {
  const $ = (id) => document.getElementById(id);

  let kasaDevices = [];
  let roomGroups = {};
  let activeRoom = "All";

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
      const detail = data.message || data.error || data.detail;
      throw new Error(
        typeof detail === "string" && detail ? detail : `Request failed (${res.status})`,
      );
    }
    return data;
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  function groupByRoom(devices) {
    const keywords = {
      Office: ["office", "desk", "work", "pc", "monitor"],
      "Living Room": ["living", "lounge", "tv", "sofa"],
      Kitchen: ["kitchen", "cook", "dining"],
      Bedroom: ["bed", "sleep", "night"],
      Bathroom: ["bath", "shower"],
    };
    const groups = {};
    for (const dev of devices) {
      const alias = (dev.alias || dev.host || "").toLowerCase();
      let matched = false;
      for (const [room, keys] of Object.entries(keywords)) {
        if (keys.some((k) => alias.includes(k))) {
          groups[room] = groups[room] || [];
          groups[room].push(dev);
          matched = true;
          break;
        }
      }
      if (!matched) {
        groups.Other = groups.Other || [];
        groups.Other.push(dev);
      }
    }
    return groups;
  }

  function renderRoomFilters() {
    const wrap = $("kasaRoomFilters");
    if (!wrap) return;
    const rooms = ["All", ...Object.keys(roomGroups).sort()];
    wrap.innerHTML = rooms
      .map(
        (r) =>
          `<button type="button" class="ghost-btn tiny kasa-room-btn${r === activeRoom ? " active" : ""}" data-room="${esc(r)}">${esc(r)}</button>`
      )
      .join("");
    wrap.querySelectorAll(".kasa-room-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        activeRoom = btn.dataset.room || "All";
        renderRoomFilters();
        renderDeviceList();
      });
    });
  }

  function devicesForRoom() {
    if (activeRoom === "All") return kasaDevices;
    return roomGroups[activeRoom] || [];
  }

  function renderDeviceList() {
    const list = $("kasaDeviceList");
    if (!list) return;
    const devs = devicesForRoom();
    if (!devs.length) {
      list.innerHTML = "<li class=\"muted\">No devices in this room — click Discover</li>";
      return;
    }
    list.innerHTML = devs
      .map((d) => {
        const alias = d.alias || d.host;
        const on = d.is_on ? "on" : "off";
        return (
          `<li class="kasa-device-row">`
          + `<strong>${esc(alias)}</strong> `
          + `<span class="muted">${esc(d.host)}</span> `
          + `<span class="kasa-state ${on}">${on}</span> `
          + `<button type="button" class="ghost-btn tiny kasa-toggle" data-target="${esc(alias)}" data-action="${d.is_on ? "off" : "on"}">${d.is_on ? "Off" : "On"}</button>`
          + `</li>`
        );
      })
      .join("");
    list.querySelectorAll(".kasa-toggle").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await fetchJson("/api/kasa/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target: btn.dataset.target, action: btn.dataset.action }),
          });
          window.showAriaToast?.(
            `${btn.dataset.action === "on" ? "On" : "Off"}: ${btn.dataset.target}`,
            "ok",
            2000,
          );
          await refreshKasa();
        } catch (err) {
          window.showAriaToast?.(err?.message || "Kasa control failed", "err", 5000);
        } finally {
          btn.disabled = false;
        }
      });
    });
  }

  async function refreshKasa() {
    const line = $("kasaStatusLine");
    try {
      const st = await fetchJson("/api/kasa/status");
      const enabled = st.enabled ? "enabled" : "disabled";
      const pkg = st.available ? "python-kasa OK" : "install python-kasa";
      kasaDevices = st.devices || [];
      roomGroups = groupByRoom(kasaDevices);
      line.textContent = `Kasa: ${enabled} · ${pkg} · ${kasaDevices.length} device(s) · ${st.online_count || 0} on`;
      renderRoomFilters();
      renderDeviceList();
    } catch (err) {
      if (isRoomAbort(err)) {
        window.AriaNet?.absorbAbort?.(err, () => refreshKasa(), 180);
        return;
      }
      line.textContent = "Kasa: unavailable";
      // Optional Kasa stack — quiet status, not a hard failure toast.
      console.info("[smarthome] Kasa unavailable:", err?.message || err);
    }
  }

  async function discoverKasa() {
    const btn = $("kasaDiscoverBtn");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Discovering…";
    }
    try {
      const r = await fetchJson("/api/kasa/discover", { method: "POST" });
      if (!r.ok) {
        const msg = r.error || r.message || "Discover failed";
        window.showAriaToast?.(msg, "err", 5000);
      } else {
        window.showAriaToast?.(
          `Discovered ${r.devices?.length ?? r.count ?? "Kasa"} device(s)`,
          "ok",
          3000
        );
      }
      await refreshKasa();
    } catch (err) {
      window.showAriaToast?.(err?.message || "Discover failed", "err", 5000);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Discover Kasa";
      }
    }
  }

  async function loadScenePresets() {
    const wrap = $("scenePresetsBtns");
    if (!wrap) return;
    try {
      const r = await fetchJson("/api/scenes/presets");
      const presets = r.presets || [];
      if (!presets.length) {
        wrap.innerHTML = "<span class=\"muted\">No presets in data/scene_presets.json</span>";
        return;
      }
      wrap.innerHTML = presets
        .map(
          (p) =>
            `<button type="button" class="ghost-btn small scene-preset-btn" data-preset="${esc(p.id)}">`
            + `${esc(p.label || p.id)}</button>`
        )
        .join("");
      wrap.querySelectorAll(".scene-preset-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.preset;
          btn.disabled = true;
          try {
            const r = await fetchJson(`/api/scenes/presets/${encodeURIComponent(id)}/activate`, {
              method: "POST",
            });
            window.showAriaToast?.(r.message || "Scene", r.ok ? "ok" : "warn");
            if (!r.ok) window.showAriaToast?.(r.message || "Scene failed", "err", 5000);
            else window.showAriaToast?.(r.message || "Scene applied", "ok", 2500);
            await refreshKasa();
          } catch (err) {
            window.showAriaToast?.(err?.message || "Scene failed", "err", 5000);
          } finally {
            btn.disabled = false;
          }
        });
      });
    } catch (err) {
      // BUG-020: enter thrash aborted /api/scenes/presets → false "Could not load presets".
      if (isRoomAbort(err)) {
        window.AriaNet?.absorbAbort?.(err, () => loadScenePresets(), 180);
        return;
      }
      wrap.innerHTML = "<span class=\"muted\">Could not load presets</span>";
      window.showAriaToast?.(err?.message || "Could not load scene presets", "err", 4000);
    }
  }

  function initSmarthomeExtras() {
    $("kasaDiscoverBtn")?.addEventListener("click", discoverKasa);
    $("kasaRefreshBtn")?.addEventListener("click", refreshKasa);
    refreshKasa();
    loadScenePresets();
  }

  window.initSmarthomeExtras = initSmarthomeExtras;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSmarthomeExtras);
  } else {
    initSmarthomeExtras();
  }
})();
