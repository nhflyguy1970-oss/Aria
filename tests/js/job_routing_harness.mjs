/**
 * Behavioural harness for chat job routing (see tests/test_chat_job_routing.py).
 *
 * Loads the real static JS in a vm context with stubbed browser globals, drives
 * handleDone/the pollers, and records which endpoints were actually fetched.
 * Prints {"results": [{name, ok, detail}, ...]} as JSON.
 */
import vm from "node:vm";
import fs from "node:fs";
import path from "node:path";

const STATIC_DIR = path.resolve(process.argv[2]);
const settle = () => new Promise((r) => setImmediate(r));

function makeEl() {
  const el = {
    className: "", textContent: "", html: "", children: [], _idx: {},
    style: {}, dataset: {}, type: "",
    querySelector(sel) {
      if (el._idx[sel]) return el._idx[sel];
      if (typeof sel === "string" && sel.startsWith(".") && el.html.includes(sel.slice(1))) {
        return makeEl();
      }
      return null;
    },
    querySelectorAll() { return []; },
    appendChild(c) {
      el.children.push(c);
      String(c.className || "").split(/\s+/).filter(Boolean).forEach((t) => { el._idx["." + t] = c; });
      return c;
    },
    insertAdjacentHTML(_pos, h) { el.html += h; },
    closest() { return el; },
    addEventListener() {},
    classList: { toggle() {}, add() {}, remove() {}, contains() { return false; } },
    // Everything rendered anywhere in this element tree, for assertions.
    allText() {
      return el.html + el.children.map((c) => (c.html || "") + (c.textContent || "")).join(" ");
    },
  };
  return el;
}

function buildSandbox() {
  const fetches = [];
  const timers = [];
  const store = new Map();
  const sandbox = {
    console,
    __clock: 1_000_000,
    __fetches: fetches,
    __timers: timers,
    __responder: null,
    __handleDoneCalls: [],
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;

  sandbox.document = {
    createElement: () => makeEl(),
    getElementById: () => makeEl(),
    querySelector: () => sandbox.__lastMessageEl || makeEl(),
    querySelectorAll: () => [],
    documentElement: { classList: { toggle() {}, add() {}, remove() {} } },
  };
  sandbox.sessionStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
  sandbox.setTimeout = (fn) => { timers.push(fn); return timers.length; };
  sandbox.clearTimeout = () => {};
  sandbox.requestAnimationFrame = (fn) => { timers.push(fn); return timers.length; };
  sandbox.fetch = async (url, opts) => {
    fetches.push(String(url));
    const r = sandbox.__responder ? sandbox.__responder(String(url), opts) : null;
    const body = r?.body ?? { ok: true, done: false, message: "working" };
    return {
      ok: r?.status ? r.status < 400 : true,
      status: r?.status ?? 200,
      json: async () => body,
    };
  };
  return vm.createContext(sandbox);
}

function load(ctx, name) {
  const file = path.join(STATIC_DIR, name);
  vm.runInContext(fs.readFileSync(file, "utf8"), ctx, { filename: file });
}

function newCtx() {
  const ctx = buildSandbox();
  vm.runInContext("Date.now = () => globalThis.__clock;", ctx);
  load(ctx, "coding_jobs.js");
  load(ctx, "media_jobs.js");
  load(ctx, "chat_done.js");
  // Renderer + chrome stubs the pollers/handleDone reach for.
  ctx.handleDone_real = ctx.handleDone;
  ctx.escapeHtml = (t) => String(t == null ? "" : t);
  ctx.formatMessage = (t) => String(t == null ? "" : t);
  ctx.isNativeApp = () => false;
  ctx.showAriaToast = () => {};
  ctx.addMessage = () => ({ body: makeEl() });
  ctx.resolveMetaType = (d) => d.type || d.result_type;
  return ctx;
}

async function drain(ctx, maxSteps = 12) {
  for (let i = 0; i < maxSteps; i += 1) {
    await settle();
    if (!ctx.__timers.length) break;
    const batch = ctx.__timers.splice(0, ctx.__timers.length);
    for (const fn of batch) { try { fn(); } catch (e) { /* surfaced via assertions */ } }
  }
  await settle();
}

const results = [];
const check = (name, ok, detail) => results.push({ name, ok: Boolean(ok), detail: String(detail) });
// Pollers absent on pre-fix code must surface as failed checks, not a crash.
function callPoller(ctx, name, ...args) {
  if (typeof ctx[name] !== "function") {
    check(`${name}_exists`, false, `${name} is not defined`);
    return false;
  }
  ctx[name](...args);
  return true;
}

/* ---- Routing kind resolution (pure) ---------------------------------- */
{
  const ctx = newCtx();
  // Missing entirely on pre-fix code — report as failures rather than crashing.
  const kind = (d) => {
    try { return ctx.resolveJobKind ? ctx.resolveJobKind(d) : "<resolveJobKind missing>"; }
    catch (e) { return `<threw: ${e.message}>`; }
  };
  check(
    "resolve_background_job",
    kind({ pending: true, type: "background_job", job_id: "abc123" }) === "background_job",
    kind({ pending: true, type: "background_job", job_id: "abc123" }),
  );
  check("resolve_coding_job", kind({ pending: true, type: "coding_job", job_id: "c1" }) === "coding_job",
    kind({ pending: true, type: "coding_job", job_id: "c1" }));
  check("resolve_media_job", kind({ pending: true, type: "media_job", job_id: "m1" }) === "media_job",
    kind({ pending: true, type: "media_job", job_id: "m1" }));
  check("resolve_untyped_pending_stays_media", kind({ pending: true, job_id: "img1" }) === "media_job",
    kind({ pending: true, job_id: "img1" }));
  check("resolve_streamed_result_type", kind({ type: "done", result_type: "background_job", job_id: "b2" }) === "background_job",
    kind({ type: "done", result_type: "background_job", job_id: "b2" }));
  check("resolve_coding_queue_hint", kind({ pending: true, queue: "coding", job_id: "br1" }) === "background_job",
    kind({ pending: true, queue: "coding", job_id: "br1" }));
  check("resolve_no_job_id", kind({ pending: true }) === null, kind({ pending: true }));
  check("resolve_not_a_job", kind({ job_id: "x", ok: true }) === null, kind({ job_id: "x", ok: true }));
}

/* ---- Test 1: Learn Topic must not hit the media endpoint -------------- */
{
  const ctx = newCtx();
  ctx.__responder = () => ({ status: 200, body: { ok: true, done: false, message: "Researching…" } });
  ctx.handleDone_real(
    { ok: true, pending: true, type: "background_job", job_id: "abc123", message: "Learn topic queued" },
    "Learn topic queued",
  );
  await drain(ctx, 3);
  const urls = ctx.__fetches;
  check("t1_no_media_endpoint", !urls.some((u) => u.includes("/api/media/job/abc123")), JSON.stringify(urls));
  check("t1_uses_coding_endpoint", urls.some((u) => u.includes("/api/coding/job/abc123")), JSON.stringify(urls));
}

/* ---- Test 2: coding jobs unchanged ------------------------------------ */
{
  const ctx = newCtx();
  ctx.__responder = () => ({ status: 200, body: { ok: true, done: false, message: "Coding…" } });
  ctx.handleDone_real(
    { ok: true, pending: true, type: "coding_job", job_id: "code1", message: "Coding agent queued" },
    "Coding agent queued",
  );
  await drain(ctx, 3);
  const urls = ctx.__fetches;
  check("t2_coding_endpoint", urls.some((u) => u.includes("/api/coding/job/code1")), JSON.stringify(urls));
  check("t2_no_media_endpoint", !urls.some((u) => u.includes("/api/media/job/")), JSON.stringify(urls));
}

/* ---- Test 3: media jobs unchanged ------------------------------------- */
{
  const ctx = newCtx();
  ctx.__responder = () => ({ status: 200, body: { ok: true, done: false, message: "Rendering…" } });
  ctx.handleDone_real(
    { ok: true, pending: true, type: "media_job", job_id: "img9", message: "Image queued" },
    "Image queued",
  );
  await drain(ctx, 3);
  check("t3_media_endpoint", ctx.__fetches.some((u) => u.includes("/api/media/job/img9")), JSON.stringify(ctx.__fetches));

  // Legacy untyped image producers (image_generation/gallery/video) must still work.
  const ctx2 = newCtx();
  ctx2.__responder = () => ({ status: 200, body: { ok: true, done: false, message: "Rendering…" } });
  ctx2.handleDone_real({ ok: true, pending: true, job_id: "untyped1", action: "generate_image" }, "queued");
  await drain(ctx2, 3);
  check("t3_untyped_media_endpoint", ctx2.__fetches.some((u) => u.includes("/api/media/job/untyped1")),
    JSON.stringify(ctx2.__fetches));
}

/* ---- Test 4: background completion renders the result ----------------- */
{
  const ctx = newCtx();
  const done = {
    ok: true,
    done: true,
    message: "Complete",
    result: {
      ok: true,
      module: "general",
      type: "knowledge_learned",
      message: "**Learned about:** fishing forecasting\nSaved to `knowledge/fishing.md` (11 web source(s)).",
    },
  };
  ctx.__responder = () => ({ status: 200, body: done });
  const calls = [];
  ctx.handleDone = (result) => { calls.push(result); };
  const msgEl = makeEl();
  const bodyEl = makeEl();
  msgEl._idx[".msg-body"] = bodyEl;
  callPoller(ctx, "jarvisPollBackgroundJob", "bg-done-1", msgEl);
  await drain(ctx, 6);

  check("t4_result_rendered", calls.length === 1 && /Learned about/.test(calls[0]?.message || ""),
    JSON.stringify(calls.map((c) => c.message)));
  const before = ctx.__fetches.length;
  await drain(ctx, 4);
  check("t4_polling_stopped", ctx.__fetches.length === before, `${before} -> ${ctx.__fetches.length}`);
  check("t4_not_tracked_after_done", !ctx.activeMediaJobs.has("background-bg-done-1"),
    JSON.stringify([...ctx.activeMediaJobs]));
  const rendered = bodyEl.allText();
  check("t4_no_gallery_reference", !/Gallery/i.test(rendered), rendered.slice(0, 200));
  check("t4_no_restart_claim", !/server restart/i.test(rendered), rendered.slice(0, 200));
}

/* ---- Test 5: a 404 must not claim a server restart -------------------- */
{
  // Media poller.
  const ctx = newCtx();
  ctx.__responder = () => ({ status: 404, body: { ok: false, message: "Job not found" } });
  const msgEl = makeEl();
  const bodyEl = makeEl();
  msgEl._idx[".msg-body"] = bodyEl;
  callPoller(ctx, "pollMediaJob", "gone-media", msgEl);
  await settle();
  ctx.__clock += 20_000; // push past the 8s grace window
  await drain(ctx, 6);
  const mediaText = bodyEl.allText();
  check("t5_media_no_restart_claim", mediaText.length > 0 && !/server restart/i.test(mediaText), mediaText.slice(0, 200));

  // Background poller.
  const ctx2 = newCtx();
  ctx2.__responder = () => ({ status: 404, body: { ok: false, message: "Job not found" } });
  const msgEl2 = makeEl();
  const bodyEl2 = makeEl();
  msgEl2._idx[".msg-body"] = bodyEl2;
  callPoller(ctx2, "jarvisPollBackgroundJob", "gone-bg", msgEl2);
  await settle();
  ctx2.__clock += 20_000;
  await drain(ctx2, 6);
  const bgText = bodyEl2.allText();
  check("t5_background_no_restart_claim", bgText.length > 0 && !/server restart/i.test(bgText), bgText.slice(0, 200));
  check("t5_background_no_gallery", !/Gallery/i.test(bgText), bgText.slice(0, 200));
}

process.stdout.write(JSON.stringify({ results }, null, 2));
