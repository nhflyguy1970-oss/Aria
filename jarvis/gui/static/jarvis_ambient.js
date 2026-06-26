/** Ambient motion, voice-reactive chrome, and Life UI toggle. */
(function () {
  const LS_ALIVE = "jarvis_alive_ui";
  const LS_HUD = "jarvis_blue_theme";

  function isAlive() {
    return document.documentElement.classList.contains("jarvis-alive");
  }

  function syncHudButton(on) {
    const btn = document.getElementById("jarvisBlueToggle");
    if (!btn) return;
    btn.textContent = on ? "HUD mode on" : "HUD mode";
    btn.classList.toggle("active", on);
  }

  function setHud(on) {
    document.documentElement.classList.toggle("theme-jarvis-blue", on);
    localStorage.setItem(LS_HUD, on ? "1" : "0");
    syncHudButton(on);
  }

  function setAlive(on) {
    const html = document.documentElement;
    html.classList.toggle("jarvis-alive", on);
    localStorage.setItem(LS_ALIVE, on ? "1" : "0");
    const btn = document.getElementById("jarvisAliveToggle");
    if (btn) {
      btn.textContent = on ? "Life UI on" : "Life UI off";
      btn.classList.toggle("active", on);
      btn.title = on ? "Jarvis HUD motion and glow (on)" : "Turn Life UI back on";
    }
    const canvas = document.getElementById("jarvisAmbientCanvas");
    if (canvas) canvas.classList.toggle("hidden", !on);
    document.querySelector(".brand-icon")?.classList.toggle("brand-idle", on);
    if (on && localStorage.getItem(LS_HUD) !== "0") {
      setHud(true);
    }
  }

  function flashSystemsOnline() {
    if (!isAlive()) return;
    const html = document.documentElement;
    const flash = document.getElementById("jarvisBootFlash");
    html.classList.remove("systems-online-flash");
    flash?.classList.remove("active");
    void html.offsetWidth;
    html.classList.add("systems-online-flash");
    flash?.classList.add("active");
    window.setTimeout(() => {
      html.classList.remove("systems-online-flash");
      flash?.classList.remove("active");
    }, 2400);
  }

  function initAliveToggle() {
    const stored = localStorage.getItem(LS_ALIVE);
    const on = stored !== "0";
    setAlive(on);
    document.getElementById("jarvisAliveToggle")?.addEventListener("click", () => {
      setAlive(!isAlive());
    });
    document.getElementById("jarvisBlueToggle")?.addEventListener("click", () => {
      const next = !document.documentElement.classList.contains("theme-jarvis-blue");
      setHud(next);
    });
    if (localStorage.getItem(LS_HUD) !== "0") {
      setHud(true);
    } else {
      syncHudButton(false);
    }
  }

  function syncVoiceState() {
    const bar = document.getElementById("voiceBar");
    const state = bar?.dataset.state || "idle";
    const html = document.documentElement;
    html.dataset.voiceState = state;
    const active = state !== "idle" && state !== "muted";
    html.classList.toggle("voice-active", active);
    document.querySelector(".brand-icon")?.classList.toggle("brand-live", active);
  }

  function watchVoiceBar() {
    const bar = document.getElementById("voiceBar");
    if (!bar) return;
    syncVoiceState();
    new MutationObserver(syncVoiceState).observe(bar, {
      attributes: true,
      attributeFilter: ["data-state"],
    });
  }

  function initParticles() {
    const canvas = document.getElementById("jarvisAmbientCanvas");
    const chat = document.getElementById("chatView");
    if (!canvas || !chat) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dots = [];
    const COUNT = 88;
    const LINK_DIST = 130;
    let raf = 0;
    let last = 0;
    let scanY = 0;

    function resize() {
      const rect = chat.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function seed() {
      dots.length = 0;
      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 600;
      for (let i = 0; i < COUNT; i += 1) {
        dots.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: 1.2 + Math.random() * 2.8,
          vx: (Math.random() - 0.5) * 0.28,
          vy: (Math.random() - 0.5) * 0.18,
          a: 0.28 + Math.random() * 0.45,
        });
      }
    }

    function accentRgb() {
      const style = getComputedStyle(document.documentElement);
      const raw = style.getPropertyValue("--accent").trim() || "#4da3ff";
      if (raw.startsWith("#") && raw.length >= 7) {
        const n = parseInt(raw.slice(1, 7), 16);
        return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
      }
      return [77, 163, 255];
    }

    function frame(ts) {
      raf = requestAnimationFrame(frame);
      if (!isAlive() || chat.classList.contains("hidden") || document.hidden) return;
      if (ts - last < 28) return;
      last = ts;

      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (!w || !h) return;

      const [cr, cg, cb] = accentRgb();
      const voice = document.documentElement.dataset.voiceState || "idle";
      const boost = voice === "listening" ? 1.6 : voice === "speaking" ? 1.35 : voice === "thinking" ? 1.2 : 1;

      ctx.clearRect(0, 0, w, h);

      scanY = (scanY + 2.4 * boost) % (h + 60);
      const beam = ctx.createLinearGradient(0, scanY - 28, 0, scanY + 28);
      beam.addColorStop(0, `rgba(${cr},${cg},${cb},0)`);
      beam.addColorStop(0.45, `rgba(${cr},${cg},${cb},${0.18 * boost})`);
      beam.addColorStop(0.5, `rgba(180, 230, 255, ${0.28 * boost})`);
      beam.addColorStop(0.55, `rgba(${cr},${cg},${cb},${0.18 * boost})`);
      beam.addColorStop(1, `rgba(${cr},${cg},${cb},0)`);
      ctx.fillStyle = beam;
      ctx.fillRect(0, scanY - 28, w, 56);

      for (let i = 0; i < dots.length; i += 1) {
        const a = dots[i];
        for (let j = i + 1; j < dots.length; j += 1) {
          const b = dots[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.hypot(dx, dy);
          if (dist < LINK_DIST) {
            const la = (1 - dist / LINK_DIST) * 0.38 * boost;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(${cr},${cg},${cb},${la})`;
            ctx.lineWidth = 1.2;
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
      for (const d of dots) {
        d.x += d.vx * boost;
        d.y += d.vy * boost;
        if (d.x < 0) d.x = w;
        if (d.x > w) d.x = 0;
        if (d.y < 0) d.y = h;
        if (d.y > h) d.y = 0;
        ctx.beginPath();
        ctx.fillStyle = `rgba(${cr},${cg},${cb},${Math.min(0.95, d.a * boost)})`;
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.fillStyle = `rgba(200, 235, 255, ${0.35 * boost})`;
        ctx.arc(d.x, d.y, d.r * 0.45, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    resize();
    seed();
    window.addEventListener("resize", () => {
      resize();
      seed();
    });
    raf = requestAnimationFrame(frame);
  }

  function boot() {
    initAliveToggle();
    watchVoiceBar();
    initParticles();
  }

  window.jarvisFlashSystemsOnline = flashSystemsOnline;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
