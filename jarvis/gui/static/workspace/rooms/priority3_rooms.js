/**
 * Phase 5 Priority 3 + remaining flagships — native Rooms:
 * Memory, Voice, Repair, Integrity, Automation, Providers,
 * Home Automation, Home (foyer), Calendar.
 */
(function () {
  "use strict";
  const kit = () => window.AriaRoomKit;
  if (!kit()?.defineRoom) return;

  function card(ctx, title, body) {
    return `<section class="nr-card"><h2>${ctx.esc(title)}</h2><p>${ctx.esc(body)}</p></section>`;
  }

  /* Memory */
  kit().defineRoom({
    id: "memory",
    global: "AriaMemoryRoom",
    rootId: "memoryRoom",
    className: "memory-room",
    houseClass: "house-memory",
    bodyNativeClass: "native-memory",
    place: "· Memory archive",
    label: "Memory",
    buildBody: () =>
      '<main class="nr-stage">' +
      '<div class="nr-hero" data-mem-hero></div>' +
      '<form class="nr-form" data-mem-form autocomplete="off">' +
      '<input name="content" placeholder="Remember something…" required />' +
      '<button type="submit">Remember</button></form>' +
      '<label class="nr-search"><span class="visually-hidden">Search memory</span>' +
      '<input type="search" data-mem-q placeholder="Search what Aria knows…" /></label>' +
      '<ul class="nr-list" data-mem-list></ul>' +
      "</main>",
    wire: (ctx) => {
      ctx.root.querySelector("[data-mem-form]")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const content = String(new FormData(e.target).get("content") || "").trim();
        if (!content) return;
        ctx.setStatus("Encoding…");
        try {
          const out = await ctx.api("/api/memory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content, type: "fact", namespace: "profile" }),
          });
          e.target.reset();
          const entry = out.entry || { content };
          const items = ctx.root._memItems || [];
          items.unshift(entry);
          ctx.root._memItems = items;
          renderMemoryList(ctx, items);
          const q = ctx.root.querySelector("[data-mem-q]");
          if (q) q.value = "";
          ctx.setStatus("Remembered");
          window.showAriaToast?.("Remembered", "ok", 2000);
        } catch (err) {
          ctx.setStatus(err.message || "Could not remember");
        }
      });
      let t;
      ctx.root.querySelector("[data-mem-q]")?.addEventListener("input", (e) => {
        clearTimeout(t);
        t = setTimeout(() => filterMemory(ctx, e.target.value.trim()), 220);
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Remembering…");
      try {
        const [d, all] = await Promise.all([
          ctx.api("/api/memory/home"),
          ctx.api("/api/memory/all?limit=48").catch(() => ({ entries: [] })),
        ]);
        const about = d.about_you || d.beliefs || [];
        const entries = all.entries || all.items || [];
        const merged = [];
        const seen = new Set();
        for (const m of [...entries, ...about]) {
          const key = m.id || m.content || m.summary || JSON.stringify(m).slice(0, 80);
          if (seen.has(key)) continue;
          seen.add(key);
          merged.push(m);
        }
        ctx.root._memItems = merged;
        ctx.root.querySelector("[data-mem-hero]").innerHTML =
          "<h1>What Aria knows</h1>" +
          `<p class="nr-pulse">${ctx.esc(d.philosophy?.body || d.philosophy || "Personal history — not a note dump.")}</p>`;
        renderMemoryList(ctx, merged);
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Memory unavailable");
      }
    },
  });

  function renderMemoryList(ctx, about) {
    const ul = ctx.root.querySelector("[data-mem-list]");
    if (!ul) return;
    ul.innerHTML = about.length
      ? about
          .slice(0, 24)
          .map((m) => {
            const t = m.summary || m.text || m.content || m.title || m.belief || JSON.stringify(m).slice(0, 120);
            return `<li><div class="nr-row"><span class="nr-row-title">${ctx.esc(String(t).slice(0, 200))}</span></div></li>`;
          })
          .join("")
      : '<li class="nr-empty">Nothing encoded yet — familiarity grows with time.</li>';
  }

  function filterMemory(ctx, q) {
    const all = ctx.root._memItems || [];
    if (!q) {
      renderMemoryList(ctx, all);
      return;
    }
    const qq = q.toLowerCase();
    const filtered = all.filter((m) => {
      const t = String(m.summary || m.text || m.content || m.title || m.belief || "").toLowerCase();
      return t.includes(qq);
    });
    renderMemoryList(ctx, filtered);
    ctx.setStatus(filtered.length ? `${filtered.length} matches` : "No matches");
  }

  /* Voice */
  kit().defineRoom({
    id: "voice",
    global: "AriaVoiceRoom",
    rootId: "voiceRoom",
    className: "voice-room",
    houseClass: "house-voice",
    bodyNativeClass: "native-voice",
    place: "· Presence",
    label: "Voice",
    buildBody: () =>
      '<main class="nr-stage"><div class="nr-hero" data-voice-hero></div><div class="nr-grid" data-voice-grid></div></main>',
    load: async (ctx) => {
      ctx.setStatus("Tuning presence…");
      let status = {};
      try {
        status = await ctx.api("/api/voice/home");
      } catch (_) {
        try {
          status = await ctx.api("/api/audio/status");
        } catch (_2) {
          status = {};
        }
      }
      ctx.root.querySelector("[data-voice-hero]").innerHTML =
        "<h1>Speaking</h1>" +
        '<p class="nr-pulse">Voice lives here when you want to talk — not as a permanent toolbar.</p>';
      ctx.root.querySelector("[data-voice-grid]").innerHTML = [
        card(ctx, "Mode", status.mode || status.duplex || status.status || "Ready when you are"),
        card(ctx, "Backend", status.backend || status.stt || status.tts || "—"),
      ].join("");
      ctx.setStatus("Listening quietly");
    },
  });

  /* Repair — restoration bench (uses integrity + mission signals; not workstation panel) */
  kit().defineRoom({
    id: "repair",
    global: "AriaRepairRoom",
    rootId: "repairRoom",
    className: "repair-room",
    houseClass: "house-repair",
    bodyNativeClass: "native-repair",
    place: "· Restoration bench",
    label: "Repair",
    chrome: "systems",
    overflowHtml:
      '<button type="button" data-nr-act="refresh">Refresh</button>' +
      '<button type="button" data-nr-act="scan">Scan</button>' +
      '<button type="button" data-nr-act="integrity">Integrity</button>' +
      '<button type="button" data-nr-act="mission">Mission</button>',
    onOverflow: async (act) => {
      if (act === "scan") {
        if (window.AriaGuidedRepair?.scanAndShow) {
          await window.AriaGuidedRepair.scanAndShow();
        } else {
          window.showAriaToast?.("Guided Repair is not loaded", "err", 4000);
        }
      }
      if (act === "integrity") window.AriaActivityEngine?.start?.("integrity", { confirmHighStakes: false });
      if (act === "mission") window.AriaActivityEngine?.start?.("systems", { confirmHighStakes: false });
    },
    buildBody: () =>
      '<main class="nr-stage"><div class="nr-hero" data-repair-hero></div><div class="nr-grid" data-repair-grid></div></main>',
    load: async (ctx) => {
      ctx.setStatus("Examining evidence…");
      try {
        const [mc, integ, repairHome] = await Promise.all([
          ctx.api("/api/mission-control").catch(() => ({})),
          ctx.api("/api/integrity/home").catch(() => ({})),
          ctx.api("/api/repair/home").catch(() => ({})),
        ]);
        const attn = mc.overview?.needs_attention || [];
        const clear = attn.length === 1 && /all clear/i.test(attn[0]);
        const issues = repairHome.issues || repairHome.repair_queue || [];
        const issueLine = issues.length
          ? issues
              .slice(0, 3)
              .map((i) => i.title || i.summary || i.id)
              .filter(Boolean)
              .join(" · ")
          : "";
        ctx.root.querySelector("[data-repair-hero]").innerHTML =
          "<h1>Evidence</h1>" +
          `<p class="nr-pulse">${
            issueLine
              ? ctx.esc(issueLine)
              : clear
                ? "Nothing urgent. The bench is quiet."
                : ctx.esc((attn || []).slice(0, 3).join(" · ") || "Check integrity for details.")
          }</p>`;
        ctx.root.querySelector("[data-repair-grid]").innerHTML = [
          card(ctx, "Integrity", `${integ.score?.overall ?? integ.status ?? "—"} · ${integ.state || integ.status || ""}`),
          card(ctx, "Open repairs", String(issues.length || repairHome.active_issues || 0)),
          card(ctx, "Platform", mc.overview?.platform_status || "—"),
          card(ctx, "Attention", clear && !issues.length ? "All clear" : (attn || []).slice(0, 4).join("\n") || issueLine || "—"),
        ].join("");
        ctx.setStatus(issues.length || !clear ? "Listening quietly" : "All clear");
      } catch (err) {
        ctx.setStatus(err.message || "Repair unavailable");
      }
    },
  });

  function integrityListItems(d) {
    const score = d?.score || {};
    const deductions = score.deductions || d?.deductions || [];
    const findings = (d?.last_scan && d.last_scan.findings) || d?.findings || [];
    if (deductions.length) return deductions;
    return findings;
  }

  function cacheIntegrityHome(d) {
    const score = d?.score || {};
    const items = integrityListItems(d).map((x) => ({
      title: x.title || x.message || "Item",
    }));
    try {
      sessionStorage.setItem(
        "aria.integrity.home",
        JSON.stringify({
          overall: score.overall,
          state: d?.state || score.status || "",
          items,
          at: Date.now(),
        })
      );
    } catch (_) {
      /* ignore */
    }
  }

  function paintIntegrityTruth(ctx, hero, ul, d) {
    const score = (d && d.score) || {};
    const items = integrityListItems(d);
    if (hero) {
      hero.innerHTML =
        "<h1>Truth</h1>" +
        `<p class="nr-pulse">Score ${ctx.esc(String(score.overall ?? "—"))} · ${ctx.esc(d.state || score.status || "")}</p>`;
    }
    if (!ul) return;
    ul.innerHTML = items.length
      ? items
          .slice(0, 12)
          .map((x) => `<li><div class="nr-row"><span class="nr-row-title">${ctx.esc(x.title || x.message || "Item")}</span></div></li>`)
          .join("")
      : '<li class="nr-empty">No deductions on record.</li>';
  }

  /* Integrity */
  kit().defineRoom({
    id: "integrity",
    global: "AriaIntegrityRoom",
    rootId: "integrityRoom",
    className: "integrity-room",
    houseClass: "house-integrity",
    bodyNativeClass: "native-integrity",
    place: "· Quiet caretaker",
    label: "Integrity",
    chrome: "systems",
    overflowHtml:
      '<button type="button" data-nr-act="refresh">Refresh</button>' +
      '<button type="button" data-nr-act="repair">Repair</button>',
    onOverflow: async (act) => {
      if (act === "repair") window.AriaActivityEngine?.start?.("repair", { confirmHighStakes: false });
    },
    buildBody: () =>
      '<main class="nr-stage"><div class="nr-hero" data-int-hero></div><ul class="nr-list" data-int-list></ul></main>',
    load: async (ctx) => {
      const hero = ctx.root.querySelector("[data-int-hero]");
      const ul = ctx.root.querySelector("[data-int-list]");
      // Instant last-known Truth so Jeff never stares at an empty caretaker while
      // the network is in flight (or wedged behind other room fetches).
      let cached = null;
      try {
        cached = JSON.parse(sessionStorage.getItem("aria.integrity.home") || "null");
      } catch (_) {
        cached = null;
      }
      if (cached) {
        // Never flash Checking when we already know last Truth.
        ctx.setStatus("Listening quietly");
      } else {
        ctx.setStatus("Checking truth…");
      }
      if (cached && hero && (!hero.innerHTML.trim() || /Reading the house|Gathering integrity|Refreshing|Score\s/i.test(hero.innerHTML + (ul?.innerHTML || "")))) {
        hero.innerHTML =
          "<h1>Truth</h1>" +
          `<p class="nr-pulse">Score ${ctx.esc(String(cached.overall ?? "—"))} · ${ctx.esc(cached.state || "")}</p>`;
        if (ul && !ul.querySelector(".nr-row")) {
          const cachedItems = Array.isArray(cached.items) ? cached.items : [];
          ul.innerHTML = cachedItems.length
            ? cachedItems
                .slice(0, 12)
                .map((x) => `<li><div class="nr-row"><span class="nr-row-title">${ctx.esc(x.title || "Item")}</span></div></li>`)
                .join("")
            : '<li class="nr-empty">Gathering integrity…</li>';
        }
      } else if (hero && !hero.innerHTML.trim()) {
        hero.innerHTML =
          "<h1>Truth</h1><p class=\"nr-pulse muted\">Reading the house…</p>";
      }
      if (ul && !ul.innerHTML.trim()) {
        ul.innerHTML = '<li class="nr-empty">Gathering integrity…</li>';
      }
      try {
        const d = await ctx.api("/api/integrity/home", { timeoutMs: 15000 });
        if (!ctx.active()) return;
        cacheIntegrityHome(d);
        paintIntegrityTruth(ctx, hero, ul, d);
        ctx.setStatus("Listening quietly");
      } catch (err) {
        if (err?.aborted && !err?.timedOut) {
          if (ctx.active() && /Score\s/i.test(hero?.innerHTML || "")) {
            ctx.setStatus("Listening quietly");
          }
          return;
        }
        if (!ctx.active()) return;
        // One quiet retry — room thrash may have aborted the first attempt.
        if (!err?.timedOut) {
          try {
            const d2 = await ctx.api("/api/integrity/home", { timeoutMs: 12000 });
            if (!ctx.active()) return;
            cacheIntegrityHome(d2);
            paintIntegrityTruth(ctx, hero, ul, d2);
            ctx.setStatus("Listening quietly");
            return;
          } catch (err2) {
            if (err2?.aborted && !err2?.timedOut) {
              if (ctx.active() && /Score\s/i.test(hero?.innerHTML || "")) {
                ctx.setStatus("Listening quietly");
              }
              return;
            }
            err = err2;
          }
        }
        if (hero && !/Score\s/i.test(hero.innerHTML || "")) {
          hero.innerHTML =
            "<h1>Truth</h1><p class=\"nr-pulse\">Couldn’t finish this check</p>";
        }
        if (ul && !ul.querySelector(".nr-row")) {
          const msg = err?.timedOut
            ? err.message || "That check took too long"
            : window.AriaNet?.isRoomAbort?.(err)
              ? "Gathering integrity…"
              : err.message || "Integrity unavailable";
          ul.innerHTML = `<li class="nr-empty">${ctx.esc(msg)}</li>`;
        }
        ctx.setStatus(
          err?.timedOut
            ? err.message || "That check took too long"
            : window.AriaNet?.isRoomAbort?.(err)
              ? "Listening quietly"
              : err.message || "Integrity unavailable"
        );
      }
    },
  });

  /* Automation */
  kit().defineRoom({
    id: "automation",
    global: "AriaAutomationRoom",
    rootId: "automationRoom",
    className: "automation-room",
    houseClass: "house-automation",
    bodyNativeClass: "native-automation",
    place: "· Automation loft",
    label: "Automation",
    chrome: "standard",
    buildBody: () =>
      '<main class="nr-stage">' +
      '<div class="nr-hero" data-auto-hero></div>' +
      '<div class="nr-grid" data-auto-grid></div>' +
      '<section class="nr-section"><h2>Pipelines</h2><ul class="nr-list" data-auto-list></ul></section>' +
      "</main>",
    wire: (ctx) => {
      ctx.root.querySelector("[data-auto-list]")?.addEventListener("click", async (e) => {
        const btn = e.target.closest("[data-auto-run]");
        if (!btn) return;
        const id = btn.dataset.autoRun;
        if (!id) return;
        if (!window.ariaConfirm) {
          if (!window.confirm?.(`Run pipeline ${id}?`)) return;
        } else if (!(await window.ariaConfirm(`Run pipeline ${id}?`, { title: "Run pipeline", okLabel: "Run" }))) {
          return;
        }
        ctx.setStatus("Running…");
        try {
          const out = await ctx.api(`/api/automation/pipelines/${encodeURIComponent(id)}/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
          });
          window.showAriaToast?.(out.message || "Pipeline started", out.ok === false ? "warn" : "ok", 3500);
          ctx.setStatus("Listening quietly");
        } catch (err) {
          ctx.setStatus(err.message || "Run failed");
        }
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Checking the loft…");
      try {
        const [d, pipes] = await Promise.all([
          ctx.api("/api/automation/home"),
          ctx.api("/api/automation/pipelines").catch(() => ({ pipelines: [] })),
        ]);
        const idn = d.identity || {};
        ctx.root.querySelector("[data-auto-hero]").innerHTML =
          "<h1>Skills & schedules</h1>" +
          `<p class="nr-pulse">${ctx.esc(idn.automation || d.philosophy || "Work that runs when you need it.")}</p>`;
        ctx.root.querySelector("[data-auto-grid]").innerHTML = [
          card(ctx, "Skills", idn.skills || "—"),
          card(ctx, "Rules", idn.rules || "—"),
          card(ctx, "Workflows", idn.workflows || "—"),
        ].join("");
        const list = pipes.pipelines || pipes.items || pipes.results || [];
        const ul = ctx.root.querySelector("[data-auto-list]");
        ul.innerHTML = list.length
          ? list
              .slice(0, 16)
              .map((p) => {
                const id = p.id || p.pipeline_id || "";
                const name = p.name || p.title || id || "Pipeline";
                return (
                  `<li><div class="nr-row"><span class="nr-row-title">${ctx.esc(name)}</span>` +
                  `<span class="nr-row-meta">${ctx.esc(p.status || p.schedule || "")}</span>` +
                  `<span class="nr-row-actions"><button type="button" class="nr-mini" data-auto-run="${ctx.esc(id)}">Run</button></span>` +
                  `</div></li>`
                );
              })
              .join("")
          : '<li class="nr-empty">No pipelines yet.</li>';
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Automation unavailable");
      }
    },
  });

  /* Providers */
  kit().defineRoom({
    id: "providers",
    global: "AriaProvidersRoom",
    rootId: "providersRoom",
    className: "providers-room",
    houseClass: "house-providers",
    bodyNativeClass: "native-providers",
    place: "· Provider bay",
    label: "Providers",
    chrome: "standard",
    buildBody: () =>
      '<main class="nr-stage"><div class="nr-hero" data-prov-hero></div><div class="nr-grid" data-prov-grid></div></main>',
    load: async (ctx) => {
      ctx.setStatus("Checking models…");
      try {
        const d = await ctx.api("/api/models/home");
        ctx.root.querySelector("[data-prov-hero]").innerHTML =
          "<h1>Models</h1>" +
          `<p class="nr-pulse">${ctx.esc(d.philosophy || "Configure here. Mission watches health.")}</p>`;
        const roles = d.roles || d.assignments || d.models || [];
        const grid = ctx.root.querySelector("[data-prov-grid]");
        if (Array.isArray(roles) && roles.length) {
          grid.innerHTML = roles
            .slice(0, 8)
            .map((r) => card(ctx, r.role || r.name || "Role", r.model || r.id || JSON.stringify(r).slice(0, 80)))
            .join("");
        } else {
          grid.innerHTML = [
            card(ctx, "Product", d.title || "Models"),
            card(ctx, "Status", d.status || "Configured"),
          ].join("");
        }
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Providers unavailable");
      }
    },
  });

  /* Home automation — full HA panel via AriaFurnish (homeAutomationView) */
  kit().defineRoom({
    id: "home_automation",
    global: "AriaHomeAutoRoom",
    rootId: "homeAutoRoom",
    className: "home-auto-room",
    houseClass: "house-home-auto",
    bodyNativeClass: "native-home-auto",
    place: "· Home control",
    label: "Home",
    viewId: "homeAutomation",
    buildBody: () =>
      '<main class="nr-stage"><div class="nr-hero" data-ha-hero></div><div class="nr-grid" data-ha-grid></div></main>',
    load: async (ctx) => {
      ctx.setStatus("Sensing the house…");
      let d = {};
      try {
        d = await ctx.api("/api/smarthome/product/home");
      } catch (_) {
        try {
          d = await ctx.api("/api/smarthome/home");
        } catch (_2) {
          try {
            d = await ctx.api("/api/dashboard/home");
          } catch (_3) {
            d = {};
          }
        }
      }
      const health = d.health || d.connection || {};
      const connected = !!(health.connected || d.connected);
      const statusLine = connected
        ? health.message || d.status || "Home Assistant connected"
        : health.message || d.status || d.state || "Home Assistant not connected";
      ctx.root.querySelector("[data-ha-hero]").innerHTML =
        "<h1>Environment</h1>" +
        `<p class="nr-pulse">${ctx.esc(d.philosophy || d.greeting?.welcome || "Lights, scenes, and Home Assistant — when the house needs you.")}</p>`;
      ctx.root.querySelector("[data-ha-grid]").innerHTML = [
        card(ctx, "Status", statusLine),
        card(ctx, "Note", "Open this room’s furnished panel for controls, token, and scenes."),
      ].join("");
      ctx.setStatus("Listening quietly");
    },
  });

  /* Home foyer */
  kit().defineRoom({
    id: "home",
    global: "AriaHomeRoom",
    rootId: "homeRoom",
    className: "home-room",
    houseClass: "house-home",
    bodyNativeClass: "native-home",
    place: "· Foyer",
    label: "Home",
    viewId: "dashboard",
    chrome: "standard",
    overflowHtml:
      '<button type="button" data-nr-act="refresh">Refresh</button>' +
      '<button type="button" data-nr-act="chat">Talk with Aria</button>' +
      '<button type="button" data-nr-act="search">Search</button>',
    onOverflow: async (act) => {
      if (act === "search") window.AriaActivityEngine?.start?.("search", { confirmHighStakes: false });
    },
    buildBody: () =>
      '<main class="nr-stage"><div class="nr-hero" data-home-hero></div><div class="nr-grid" data-home-grid></div></main>',
    load: async (ctx) => {
      ctx.setStatus("Coming home…");
      try {
        const d = window.AriaSharedFetch?.dashboardHome
          ? await window.AriaSharedFetch.dashboardHome({ stale_ok: true, ttlMs: 2500 })
          : await ctx.api("/api/dashboard/home?stale_ok=true");
        const g = d.greeting || {};
        ctx.root.querySelector("[data-home-hero]").innerHTML =
          `<p class="nr-kicker">${ctx.esc(g.date || "")}</p>` +
          `<h1>${ctx.esc(g.greeting || g.welcome || "Welcome")}</h1>` +
          `<p class="nr-pulse">${ctx.esc(g.welcome && g.greeting !== g.welcome ? g.welcome : "Orientation without a dashboard wall.")}</p>`;
        const weather = d.weather?.summary || d.weather?.text || d.weather?.condition || "";
        const attn = d.attention || d.needs_attention || [];
        ctx.root.querySelector("[data-home-grid]").innerHTML = [
          card(ctx, "Weather", weather || "—"),
          card(ctx, "Attention", Array.isArray(attn) && attn.length ? attn.slice(0, 3).join(" · ") : "All quiet"),
        ].join("");
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Home unavailable");
      }
    },
  });

  /* Calendar */
  kit().defineRoom({
    id: "calendar",
    global: "AriaCalendarRoom",
    rootId: "calendarRoom",
    className: "calendar-room",
    houseClass: "house-calendar",
    bodyNativeClass: "native-calendar",
    place: "· Wall calendar",
    label: "Calendar",
    overflowHtml:
      '<button type="button" data-nr-act="refresh">Refresh</button>' +
      '<button type="button" data-nr-act="planner">Planner</button>',
    onOverflow: async (act) => {
      if (act === "planner") window.AriaActivityEngine?.start?.("planning", { confirmHighStakes: false });
    },
    buildBody: () =>
      '<main class="nr-stage"><div class="nr-hero" data-cal-hero></div><ul class="nr-list" data-cal-list></ul></main>',
    load: async (ctx) => {
      ctx.setStatus("Checking the week…");
      let events = [];
      try {
        const plan = await ctx.api("/api/planner");
        events = plan.events_today || plan.events || [];
        ctx.root.querySelector("[data-cal-hero]").innerHTML =
          "<h1>The week</h1>" +
          `<p class="nr-pulse">${events.length ? `${events.length} on today’s slate` : "A clear wall — nothing scheduled in view."}</p>`;
      } catch (_) {
        ctx.root.querySelector("[data-cal-hero]").innerHTML =
          "<h1>The week</h1><p class=\"nr-pulse\">Calendar stays calm. Planner holds the day.</p>";
      }
      const ul = ctx.root.querySelector("[data-cal-list]");
      ul.innerHTML = events.length
        ? events
            .map((e) => `<li><div class="nr-row"><span class="nr-row-title">${ctx.esc(e.title || e.text || e.name || "Event")}</span><span class="nr-row-meta">${ctx.esc(e.when || e.start || e.time || "")}</span></div></li>`)
            .join("")
        : '<li class="nr-empty">Nothing on the wall for today.</li>';
      ctx.setStatus("Listening quietly");
    },
  });
})();
