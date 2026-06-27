/** P4 detachable floating panels + gesture window chrome (Ada-style fist drag) */
(function () {
  const state = {
    mouseDrag: null,
    gestureDrag: null,
    sensitivity: 1.35,
    enabled: true,
  };

  const FLOAT_IDS = ["haPanel", "makerFloatPanel", "browserFloatPanel", "printerFloatPanel"];

  function panels() {
    return [...document.querySelectorAll(".floating-panel")];
  }

  function bringToFront(panel) {
    let top = 5000;
    panels().forEach((p) => {
      const z = parseInt(p.style.zIndex || "5000", 10);
      if (z >= top) top = z + 1;
    });
    panel.style.zIndex = String(top);
  }

  function floatPanel(panel) {
    if (!panel || panel.classList.contains("floating-panel")) return;
    panel.classList.add("floating-panel");
    if (panel.parentElement !== document.body) {
      document.body.appendChild(panel);
    }
    const w = panel.offsetWidth || 380;
    panel.style.left = `${Math.max(20, window.innerWidth - w - 24)}px`;
    panel.style.top = "72px";
    bringToFront(panel);
    attachMouseDrag(panel);
  }

  function dockPanel(panel) {
    if (!panel) return;
    panel.classList.remove("floating-panel", "gesture-dragging");
    panel.style.left = "";
    panel.style.top = "";
    panel.style.zIndex = "";
  }

  function toggleFloat(panelId) {
    if (!state.enabled) return;
    const panel = document.getElementById(panelId);
    if (!panel) return;
    if (panel.classList.contains("floating-panel")) dockPanel(panel);
    else floatPanel(panel);
  }

  function attachMouseDrag(panel) {
    const head =
      panel.querySelector(".float-drag-head") ||
      panel.querySelector("h2, h3, .ha-panel-head") ||
      panel;
    head.classList.add("float-drag-head");
    if (head.dataset.floatDragBound) return;
    head.dataset.floatDragBound = "1";
    head.addEventListener("mousedown", (e) => {
      if (e.button !== 0 || !panel.classList.contains("floating-panel")) return;
      bringToFront(panel);
      state.mouseDrag = {
        panel,
        ox: e.clientX - panel.offsetLeft,
        oy: e.clientY - panel.offsetTop,
      };
      e.preventDefault();
    });
  }

  function normToScreen(nx, ny) {
    const s = state.sensitivity;
    const x = Math.max(0, Math.min(1, (nx - 0.5) * s + 0.5));
    const y = Math.max(0, Math.min(1, (ny - 0.5) * s + 0.5));
    return { x: x * window.innerWidth, y: y * window.innerHeight };
  }

  function hitFloatedPanel(x, y) {
    const sorted = panels().sort(
      (a, b) => (parseInt(b.style.zIndex || "0", 10) || 0) - (parseInt(a.style.zIndex || "0", 10) || 0)
    );
    for (const p of sorted) {
      const r = p.getBoundingClientRect();
      if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) return p;
    }
    return null;
  }

  function movePanel(panel, dx, dy) {
    const left = Math.max(8, Math.min(window.innerWidth - 80, panel.offsetLeft + dx));
    const top = Math.max(8, Math.min(window.innerHeight - 48, panel.offsetTop + dy));
    panel.style.left = `${left}px`;
    panel.style.top = `${top}px`;
  }

  function gestureCursor(x, y, active) {
    const dot = document.getElementById("gestureCursor");
    if (!dot) return;
    dot.classList.toggle("hidden", !active);
    if (active) {
      dot.style.left = `${x}px`;
      dot.style.top = `${y}px`;
    }
  }

  function gestureFrame({ indexX, indexY, wristX, wristY, isFist, mode }) {
    if (!state.enabled || mode !== "control") {
      gestureCursor(0, 0, false);
      return;
    }
    const index = normToScreen(indexX, indexY);
    const wrist = normToScreen(wristX, wristY);
    gestureCursor(index.x, index.y, isFist);

    if (isFist) {
      if (!state.gestureDrag) {
        const panel = hitFloatedPanel(index.x, index.y);
        if (panel) {
          state.gestureDrag = { panel, lastX: wrist.x, lastY: wrist.y };
          bringToFront(panel);
          panel.classList.add("gesture-dragging");
        }
      } else {
        const { panel, lastX, lastY } = state.gestureDrag;
        const dx = wrist.x - lastX;
        const dy = wrist.y - lastY;
        if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) movePanel(panel, dx, dy);
        state.gestureDrag = { panel, lastX: wrist.x, lastY: wrist.y };
      }
    } else if (state.gestureDrag) {
      state.gestureDrag.panel?.classList.remove("gesture-dragging");
      state.gestureDrag = null;
    }
  }

  function gesturePinchClick(indexX, indexY, mode) {
    if (!state.enabled || mode !== "control") return;
    const { x, y } = normToScreen(indexX, indexY);
    const el = document.elementFromPoint(x, y);
    if (!el) return;
    const clickable = el.closest(
      "button, input, a, [role='button'], .ghost-btn, .apply-btn, .primary-btn, .view-tab"
    );
    if (clickable && typeof clickable.click === "function") {
      clickable.click();
      return;
    }
    document.querySelector("#toolConfirmYes")?.click();
  }

  function onGestureGrab() {
    /* legacy hook — fist drag handled in gestureFrame */
  }

  function onGestureRelease() {
    state.gestureDrag?.panel?.classList.remove("gesture-dragging");
    state.gestureDrag = null;
  }

  window.jarvisGestureGrab = onGestureGrab;
  window.jarvisGestureRelease = onGestureRelease;
  window.jarvisGestureCursor = gestureCursor;
  window.jarvisFloatingPanels = {
    gestureFrame,
    gesturePinchClick,
    floatPanel,
    toggleFloat,
    setEnabled(v) {
      state.enabled = Boolean(v);
    },
  };

  window.addEventListener("mousemove", (e) => {
    if (!state.mouseDrag) return;
    const { panel, ox, oy } = state.mouseDrag;
    panel.style.left = `${e.clientX - ox}px`;
    panel.style.top = `${e.clientY - oy}px`;
  });
  window.addEventListener("mouseup", () => {
    state.mouseDrag = null;
  });

  function initFloatingPanels() {
    fetch("/api/security/gestures/status")
      .then((r) => r.json())
      .then((d) => {
        state.enabled = d.floating_panels !== false;
        if (d.sensitivity) state.sensitivity = Number(d.sensitivity) || state.sensitivity;
      })
      .catch(() => {});

    const map = [
      ["haPanel", "haFloatBtn"],
      ["makerFloatPanel", "makerFloatBtn"],
      ["browserFloatPanel", "browserFloatBtn"],
      ["printerFloatPanel", "printerFloatBtn"],
    ];
    map.forEach(([panelId, btnId]) => {
      const btn = document.getElementById(btnId);
      if (btn) btn.addEventListener("click", () => toggleFloat(panelId));
    });

    FLOAT_IDS.forEach((id) => {
      const panel = document.getElementById(id);
      if (panel) attachMouseDrag(panel);
    });
  }

  window.initFloatingPanels = initFloatingPanels;
  document.addEventListener("DOMContentLoaded", initFloatingPanels);
})();
