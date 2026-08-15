(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const rooms = (window.AriaWorkspaceRegistry?.rooms || []).map((r) => ({
    id: r.id, viewId: r.viewId, metaphor: r.metaphor, hero: r.hero,
    tools: r.tools || [], chromePolicy: r.chromePolicy,
  }));
  const tools = (window.AriaWorkspaceRegistry?.tools || []).map((t) => ({
    id: t.id, label: t.label, viewId: t.viewId, invoke: t.invoke, surface: t.surface,
  }));
  function inspectSurface(room) {
    const viewId = room.viewId || room.id;
    const panel = document.getElementById(viewId + "View");
    const stage = document.getElementById("ariaStage");
    const rect = panel ? panel.getBoundingClientRect() : null;
    const visibleSize = rect ? Math.round(rect.width * rect.height) : 0;
    const btns = panel ? Array.from(panel.querySelectorAll("button,[role=button],input[type=submit]")) : [];
    const inputs = panel ? Array.from(panel.querySelectorAll("input,textarea,select")) : [];
    const tabs = panel ? Array.from(panel.querySelectorAll("[role=tab],.tab,button[data-tab]")) : [];
    const textHead = ((panel && panel.innerText) || "").replace(/\s+/g, " ").trim().slice(0, 240);
    const controlSample = btns.slice(0, 25).map((b) =>
      (b.getAttribute("aria-label") || b.title || b.id || b.textContent || "").replace(/\s+/g, " ").trim().slice(0, 50)
    ).filter(Boolean);
    const failCue = /unavailable|failed to load|could not load|error|not found|coming soon|not implemented|placeholder/i.test(textHead);
    return {
      panelExists: !!panel,
      onStage: !!(stage && panel && stage.contains(panel)),
      visibleSize,
      hidden: !panel || visibleSize < 100,
      furnished: document.body.dataset.furnished === "1",
      bodyRoom: document.body.dataset.room || "",
      hash: location.hash || "",
      activity: document.body.dataset.activity || "",
      btnCount: btns.length,
      inputCount: inputs.length,
      tabCount: tabs.length,
      disabledBtnCount: btns.filter((b) => b.disabled).length,
      controlSample,
      textHead,
      failCue,
    };
  }
  const walk = [];
  const t0 = performance.now();
  for (const room of rooms) {
    const t1 = performance.now();
    let enterError = null;
    try {
      if (window.AriaFrontDoorCatalog?.goRoom) window.AriaFrontDoorCatalog.goRoom(room.id);
      else {
        window.switchToView?.(room.viewId || room.id);
        window.AriaHouse?.enter?.(room.id);
      }
    } catch (e) {
      enterError = String(e && e.message || e);
    }
    await sleep(1100);
    const surf = inspectSurface(room);
    walk.push({
      roomId: room.id, viewId: room.viewId, metaphor: room.metaphor, hero: room.hero,
      tools: room.tools, enterMs: Math.round(performance.now() - t1), enterError, ...surf,
    });
  }
  try {
    if (window.AriaFrontDoorCatalog?.goRoom) window.AriaFrontDoorCatalog.goRoom("chat");
    else window.switchToView?.("chat");
  } catch (_) {}
  return {
    living: document.documentElement.classList.contains("living-workspace") || document.body.classList.contains("living-workspace"),
    pageUrl: location.href,
    roomCount: rooms.length,
    toolCount: tools.length,
    rooms, tools, walk,
    walkTotalMs: Math.round(performance.now() - t0),
    hasGoRoom: !!window.AriaFrontDoorCatalog?.goRoom,
    hasHouse: !!window.AriaHouse,
    hasFurnish: !!window.AriaFurnish,
    bodyClass: Array.from(document.body.classList).slice(0, 20),
  };
})()
