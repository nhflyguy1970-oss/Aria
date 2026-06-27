/** Smart home extras — Kasa discovery, room filters, scene presets (Ada parity). */
(function () {
  const $ = (id) => document.getElementById(id);

  let kasaDevices = [];
  let roomGroups = {};
  let activeRoom = "All";

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
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
          const r = await fetchJson("/api/kasa/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target: btn.dataset.target, action: btn.dataset.action }),
          });
          if (!r.ok) window.showAriaToast?.(r.message || "Control failed", "err");
          await refreshKasa();
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
    } catch (_) {
      line.textContent = "Kasa: unavailable";
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
      if (!r.ok) alert(r.error || "Discover failed");
      await refreshKasa();
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
            if (!r.ok) alert(r.message || "Scene failed");
            await refreshKasa();
          } finally {
            btn.disabled = false;
          }
        });
      });
    } catch (_) {
      wrap.innerHTML = "<span class=\"muted\">Could not load presets</span>";
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
