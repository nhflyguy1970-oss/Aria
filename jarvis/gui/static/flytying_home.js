/** Fly Tying Home — inventory-first overview, recovery, profiles, voice bench. */
(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  function isRoomAbort(err) {
    return !!(
      window.AriaNet?.isRoomAbort?.(err) ||
      err?.name === "AbortError" ||
      /aborted|aria-room-leave/i.test(String(err?.message || err?.reason || ""))
    );
  }

  function flyViewActive() {
    return (
      document.body.classList.contains("house-flytying") ||
      /^#?flytying\b/i.test(location.hash || "") ||
      !!document.getElementById("flytyingView")?.offsetParent
    );
  }

  async function loadFlytyingHome() {
    const panel = $("flytyingHomePanel");
    if (!panel) return;
    const gen = (loadFlytyingHome._gen = (loadFlytyingHome._gen || 0) + 1);
    try {
      const [home, profiles] = await Promise.all([
        fetch("/api/flytying/product/home").then((r) => r.json()),
        fetch("/api/flytying/product/profiles").then((r) => r.json()).catch(() => ({ profiles: [] })),
      ]);
      if (gen !== loadFlytyingHome._gen) return;
      const recovery = home.recovery || {};
      const card = $("flytyingRecoveryCard");
      if (card) {
        if (!recovery.ready) {
          card.classList.remove("hidden");
          const steps = (recovery.steps || [])
            .map((s) => `<li>${s.done ? "✓" : "○"} ${esc(s.label)} — <span class="muted">${esc(s.detail)}</span></li>`)
            .join("");
          card.innerHTML = `<strong>Connect your pattern library</strong><p class="muted small">${esc(recovery.hint || "")}</p><ol class="tiny">${steps}</ol>`;
        } else {
          card.classList.add("hidden");
          card.innerHTML = "";
        }
      }
      const inv = home.inventory || {};
      if ($("flytyingHomeInvStatus")) {
        $("flytyingHomeInvStatus").textContent = `${inv.count || 0} materials · ${inv.low_stock?.length || 0} low stock · ${(inv.queue || []).length} in queue`;
      }
      const low = $("flytyingHomeLowStock");
      if (low) {
        const rows = inv.low_stock || [];
        low.innerHTML = rows.length
          ? rows.slice(0, 5).map((i) => `<li>${esc(i.name || i.what)}</li>`).join("")
          : "<li class='muted'>No low-stock flags</li>";
      }
      const potd = home.pattern_of_the_day || {};
      if ($("flytyingHomePotd")) {
        $("flytyingHomePotd").textContent = potd.ok
          ? `Pattern of the day: ${potd.name || ""} (${potd.type || ""})`
          : potd.message || "Pattern of the day unavailable";
      }
      const sess = home.session;
      if ($("flytyingHomeSession")) {
        $("flytyingHomeSession").textContent = sess
          ? `Session: ${sess.recipe_name || sess.recipe_id || sess.id} · step ${(sess.step_idx || 0) + 1}`
          : "No active tying session";
      }
      const hatch = home.hatch || {};
      if ($("flytyingHomeHatch")) {
        const hats = (hatch.hatches || []).slice(0, 4).join(", ");
        $("flytyingHomeHatch").textContent = hats
          ? `${hatch.region || ""} · ${hats}`
          : "Seasonal hatch loading…";
      }
      const sel = $("flytyingProfileSelect");
      if (sel && !(sel.dataset.bound === "1")) {
        sel.dataset.bound = "1";
        (profiles.profiles || []).forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.textContent = p.name + (p.builtin ? "" : " *");
          if (p.id === profiles.active) opt.selected = true;
          sel.appendChild(opt);
        });
      }
    } catch (err) {
      if (gen !== loadFlytyingHome._gen) return;
      if (isRoomAbort(err)) {
        if (flyViewActive()) {
          clearTimeout(loadFlytyingHome._retry);
          loadFlytyingHome._retry = setTimeout(() => {
            if (flyViewActive()) loadFlytyingHome();
          }, 160);
        }
        return;
      }
      if ($("flytyingHomeInvStatus")) $("flytyingHomeInvStatus").textContent = err.message || "Home failed";
    }
  }

  function bindHome() {
    const root = $("flytyingView");
    if (!root || root.dataset.homeBound === "1") return;
    root.dataset.homeBound = "1";
    $("flytyingHomeSuggestBtn")?.addEventListener("click", () => {
      $("flytyingMaterialsBtn")?.click();
    });
    $("flytyingHomeFocusInvBtn")?.addEventListener("click", () => {
      const d = $("flytyingInvDetails");
      if (d) d.open = true;
      const what = $("flytyingInvWhat");
      const box = $("flytyingInvDetails") || $("flytyingMaterialsSummary")?.closest(".flytying-materials-box");
      try {
        (box || what)?.scrollIntoView?.({ block: "center", behavior: "smooth" });
      } catch (_) {
        /* ignore */
      }
      what?.focus();
    });
    $("flytyingStartSessionBtn")?.addEventListener("click", async () => {
      const id = window._flytyingSelectedId || "";
      const name = window._flytyingSelectedName || "";
      try {
        const res = await fetch("/api/flytying/product/sessions/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ recipe_id: id, recipe_name: name }),
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.message || "Session failed");
        window.showAriaToast?.("Tying session started", "ok");
        loadFlytyingHome();
      } catch (e) {
        window.showAriaToast?.(e.message || "Session failed", "err");
      }
    });
    $("flytyingProfileActivateBtn")?.addEventListener("click", async () => {
      const id = $("flytyingProfileSelect")?.value;
      if (!id) return;
      await fetch(`/api/flytying/product/profiles/${encodeURIComponent(id)}/activate`, { method: "POST" });
      window.showAriaToast?.("Fly Tying profile applied", "ok");
      loadFlytyingHome();
    });
    async function voiceBench(action) {
      try {
        const res = await fetch("/api/flytying/product/voice/bench", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action, speak: true }),
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || data.message || "Voice bench failed");
        window.showAriaToast?.(data.step_text || data.message || action, "ok", 2500);
        loadFlytyingHome();
      } catch (e) {
        window.showAriaToast?.(e.message || "Voice bench failed", "err");
      }
    }
    $("flytyingVoiceNextBtn")?.addEventListener("click", () => voiceBench("next"));
    $("flytyingVoiceRepeatBtn")?.addEventListener("click", () => voiceBench("repeat"));
    document.addEventListener("keydown", (e) => {
      if (!document.getElementById("flytyingView") || document.getElementById("flytyingView").classList.contains("hidden")) return;
      if (e.target && /input|textarea|select/i.test(e.target.tagName)) return;
      if (e.key === "/" && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        $("flytyingSearchInput")?.focus();
      }
      if (e.key === "n" && !e.ctrlKey && !e.metaKey) voiceBench("next");
      if (e.key === "p" && !e.ctrlKey && !e.metaKey) voiceBench("previous");
    });
  }

  const prevInit = window.initFlytying;
  window.initFlytying = function initFlytyingWrapped() {
    if (typeof prevInit === "function") prevInit();
    bindHome();
    loadFlytyingHome();
  };
  window.loadFlytyingHome = loadFlytyingHome;
})();
