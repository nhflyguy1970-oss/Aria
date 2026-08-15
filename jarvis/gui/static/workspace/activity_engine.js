/**
 * Activity Engine — primary interaction model for Living Workspace.
 * Composes Rooms + Tools; inspectable recipes; never magical.
 */
(function () {
  "use strict";

  let _current = null;
  let _history = [];

  function registry() {
    return window.AriaWorkspaceRegistry;
  }

  function enterRoom(roomId) {
    const room = registry()?.room(roomId);
    if (!room) return false;
    const view = room.viewId || roomId;
    try {
      /* switchToView owns hash, house enter, and place identity.
         A second AriaHouse.enter here aborted the Room's own inits
         and left location.hash on the previous Room. */
      window.switchToView?.(view);
    } catch (_) {
      /* adapter */
    }
    return true;
  }

  function setToolTray(toolIds) {
    const el = document.getElementById("wsToolTray");
    if (!el) return;
    const tools = (toolIds || []).map((id) => registry()?.tool(id)).filter(Boolean);
    if (!tools.length) {
      el.innerHTML = "";
      el.classList.add("hidden");
      return;
    }
    el.classList.remove("hidden");
    el.innerHTML = tools
      .map(
        (t) =>
          `<button type="button" class="ws-tool-chip" data-tool="${t.id}" title="${t.label}">${t.label}</button>`
      )
      .join("");
  }

  function start(activityId, { confirmHighStakes = true } = {}) {
    const act = registry()?.activity(activityId);
    if (!act) {
      window.showAriaToast?.(`Unknown activity: ${activityId}`, "warn");
      return null;
    }

    const high = act.id === "repair" || act.id === "doctor_visit";
    if (high && confirmHighStakes) {
      const msg = `${act.title}\n\nRecipe:\n${act.recipe}\n\nContinue?`;
      // Living Workspace must not use the browser confirm() — it blocks the house.
      if (window.ariaConfirm) {
        // start() is sync for callers; kick async confirm then re-enter without re-prompt.
        window.ariaConfirm(msg, { title: act.title, okLabel: "Continue" }).then((ok) => {
          if (ok) start(activityId, { confirmHighStakes: false });
        });
        return null;
      }
      if (!window.confirm?.(msg)) return null;
    }

    if (_current) _history.push(_current.id);
    _current = act;

    document.body.dataset.activity = act.id;
    document.body.dataset.workspace = "1";

    window.AriaWorkspaceChrome?.apply?.(act.chromePolicy);
    enterRoom(act.primaryRoom);
    // Tools appear for the activity — empty in Living Room converse
    setToolTray(act.id === "converse" ? [] : act.tools || []);

    const label = document.getElementById("wsActivityLabel");
    if (label) label.textContent = act.id === "converse" ? "Aria" : act.title;
    const recipe = document.getElementById("wsActivityRecipe");
    if (recipe) {
      recipe.textContent = act.recipe;
      recipe.title = act.recipe;
    }

    window.dispatchEvent(
      new CustomEvent("aria-activity-change", {
        detail: { activity: act, previous: _history[_history.length - 1] || null },
      })
    );

    // Immersion: never toast when entering the Living Room
    if (act.id !== "converse") {
      window.showAriaToast?.(`${act.title}`, "ok", 1800);
    }
    return act;
  }

  function inspect() {
    return _current
      ? {
          id: _current.id,
          title: _current.title,
          recipe: _current.recipe,
          primaryRoom: _current.primaryRoom,
          tools: _current.tools,
          chromePolicy: _current.chromePolicy,
        }
      : null;
  }

  function stop() {
    const prev = _current;
    _current = null;
    delete document.body.dataset.activity;
    setToolTray([]);
    const label = document.getElementById("wsActivityLabel");
    if (label) label.textContent = "Aria";
    const recipe = document.getElementById("wsActivityRecipe");
    if (recipe) recipe.textContent = "Open the Front Door · Ctrl+K";
    window.dispatchEvent(
      new CustomEvent("aria-activity-change", { detail: { activity: null, previous: prev?.id } })
    );
    return prev;
  }

  function current() {
    return _current;
  }

  window.AriaActivityEngine = {
    start,
    stop,
    inspect,
    current,
    history: () => _history.slice(),
    list: () => registry()?.activities || [],
  };
})();
