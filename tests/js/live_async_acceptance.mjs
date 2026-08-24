/**
 * LIVE acceptance test for any queued ARIA capability's async lifecycle.
 *
 * Not run by pytest — it talks to a running ARIA and spends real work
 * (web searches, LLM calls, GPU time) and writes real artifacts.
 *
 *   node tests/js/live_async_acceptance.mjs <static-dir> [base-url] [message] [expected-kind]
 *
 * It performs the real user action (POST /api/chat), then feeds the real
 * response into the real frontend handleDone() with a real fetch, so the
 * endpoints recorded are the ones a browser would actually call.
 *
 * expected-kind is background_job (default) or media_job. The pass criteria
 * follow from it: each kind must poll its own registry's endpoint and must not
 * touch the other's, and a media result must name a real artifact on disk.
 */
import vm from "node:vm";
import fs from "node:fs";
import path from "node:path";

const STATIC_DIR = path.resolve(process.argv[2]);
const BASE = process.argv[3] || "http://127.0.0.1:8765";
const MESSAGE = process.argv[4] || "do deep research on tenkara rod action and learn about it";
const EXPECT_KIND = process.argv[5] || "background_job";
const EXPECT_ENDPOINT = EXPECT_KIND === "media_job" ? "/api/media/job/" : "/api/coding/job/";
const FORBIDDEN_ENDPOINT = EXPECT_KIND === "media_job" ? "/api/coding/job/" : "/api/media/job/";

const log = (...a) => console.log(...a);
const iso = () => new Date().toISOString();
const fetched = [];

function makeEl() {
  const el = {
    className: "", textContent: "", html: "", children: [], _idx: {}, style: {}, dataset: {},
    querySelector(sel) {
      if (el._idx[sel]) return el._idx[sel];
      if (typeof sel === "string" && sel.startsWith(".") && el.html.includes(sel.slice(1))) return makeEl();
      return null;
    },
    querySelectorAll: () => [],
    appendChild(c) {
      el.children.push(c);
      String(c.className || "").split(/\s+/).filter(Boolean).forEach((t) => { el._idx["." + t] = c; });
      return c;
    },
    insertAdjacentHTML(_p, h) { el.html += h; },
    closest: () => el,
    addEventListener() {},
    classList: { toggle() {}, add() {}, remove() {}, contains: () => false },
    allText() {
      return el.html + el.children.map((c) => (c.html || "") + (c.textContent || "")).join(" ");
    },
  };
  return el;
}

const bodyEl = makeEl();
const msgEl = makeEl();
msgEl._idx[".msg-body"] = bodyEl;

const sandbox = { console };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.document = {
  createElement: () => makeEl(),
  getElementById: () => makeEl(),
  querySelector: () => msgEl,
  querySelectorAll: () => [],
  documentElement: { classList: { toggle() {}, add() {}, remove() {} } },
};
const store = new Map();
sandbox.sessionStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
};
sandbox.setTimeout = setTimeout;
sandbox.clearTimeout = clearTimeout;
sandbox.requestAnimationFrame = (fn) => setTimeout(fn, 0);
// Real network, against the live server, recording every URL.
sandbox.fetch = async (url, opts) => {
  const full = String(url).startsWith("http") ? String(url) : BASE + String(url);
  fetched.push({ t: iso(), url: String(url) });
  return fetch(full, opts);
};
sandbox.escapeHtml = (t) => String(t == null ? "" : t);
sandbox.formatMessage = (t) => String(t == null ? "" : t);
sandbox.isNativeApp = () => false;
sandbox.showAriaToast = (m, k) => log(`  [toast:${k}] ${m}`);
sandbox.addMessage = () => ({ body: makeEl() });
sandbox.resolveMetaType = (d) => d.type || d.result_type;

const ctx = vm.createContext(sandbox);
for (const f of ["coding_jobs.js", "media_jobs.js", "chat_done.js"]) {
  vm.runInContext(fs.readFileSync(path.join(STATIC_DIR, f), "utf8"), ctx, { filename: f });
}

let finalResult = null;
ctx.handleDone_real = ctx.handleDone;
ctx.handleDone = (result) => { finalResult = result; };

log(`\n=== LIVE async acceptance @ ${iso()} ===`);
log(`static dir : ${STATIC_DIR}`);
log(`base url   : ${BASE}`);
log(`message    : ${MESSAGE}`);
log(`expect     : ${EXPECT_KIND} via ${EXPECT_ENDPOINT}\n`);

const form = new FormData();
form.append("message", MESSAGE);
form.append("stream", "false");

const t0 = Date.now();
log(`[${iso()}] POST /api/chat …`);
const res = await fetch(`${BASE}/api/chat`, { method: "POST", body: form });
const data = await res.json();
log(`[${iso()}] HTTP ${res.status}`);
log(`  job_id  : ${data.job_id}`);
log(`  type    : ${data.type}`);
log(`  pending : ${data.pending}`);
log(`  action  : ${data.action}`);
log(`  module  : ${data.module}`);
log(`  message : ${String(data.message || "").split("\n")[0]}`);

const kind = ctx.resolveJobKind(data);
log(`\n[frontend] resolveJobKind -> ${kind}`);

// Fail fast when the request never became a job. Waiting for a completion that
// can never arrive just burns the timeout and tells you nothing.
if (!data.job_id || !kind) {
  log(`\n=== RESULT ===`);
  log(`no job was created — the request did not route to a queued action`);
  log(`  action  : ${data.action}`);
  log(`  type    : ${data.type}`);
  log(`  pending : ${data.pending}`);
  log(`  message : ${String(data.message || "").slice(0, 300)}`);
  log(`\nVERDICT: FAIL (no job handle)\n`);
  process.exit(1);
}
if (kind !== EXPECT_KIND) {
  log(`\n=== RESULT ===`);
  log(`job kind mismatch: expected ${EXPECT_KIND}, got ${kind}`);
  log(`\nVERDICT: FAIL (wrong job kind)\n`);
  process.exit(1);
}

log(`[frontend] handing response to the real handleDone()…\n`);
ctx.handleDone_real(data, data.message || "");

const deadline = Date.now() + 15 * 60 * 1000;
let lastNote = 0;
while (!finalResult && Date.now() < deadline) {
  await new Promise((r) => setTimeout(r, 2000));
  if (Date.now() - lastNote > 30000) {
    lastNote = Date.now();
    log(`  … still waiting (${((Date.now() - t0) / 1000).toFixed(0)}s, ${fetched.length} polls)`);
  }
}
if (!finalResult) log(`\n!!! deadline reached without completion`);

const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
const urls = [...new Set(fetched.map((f) => f.url.replace(/\/[0-9a-f]{8,}/g, "/<id>")))];
const rightHits = fetched.filter((f) => f.url.includes(EXPECT_ENDPOINT));
const wrongHits = fetched.filter((f) => f.url.includes(FORBIDDEN_ENDPOINT));

log(`\n=== RESULT after ${elapsed}s ===`);
log(`endpoints polled   : ${JSON.stringify(urls)}`);
log(`poll count         : ${fetched.length}`);
log(`correct-registry   : ${rightHits.length} hits on ${EXPECT_ENDPOINT}`);
log(`wrong-registry     : ${wrongHits.length} hits on ${FORBIDDEN_ENDPOINT}  ${wrongHits.length === 0 ? "(correct)" : "!!! WRONG REGISTRY"}`);
log(`completed          : ${Boolean(finalResult)}`);
let artifact = null;
if (finalResult) {
  log(`result.ok          : ${finalResult.ok}`);
  log(`result.type        : ${finalResult.type}`);
  artifact = finalResult.image_path || finalResult.video_path || finalResult.audio_path
    || finalResult.output_path || finalResult.knowledge_path || null;
  log(`artifact           : ${artifact}`);
  if (finalResult.image_name) log(`image_name         : ${finalResult.image_name}`);
  log(`result.message     :\n${String(finalResult.message || "").slice(0, 400)}`);
}
// A media capability is only certified when a real file exists on disk.
let artifactOnDisk = null;
if (EXPECT_KIND === "media_job" && artifact) {
  const p = path.isAbsolute(artifact) ? artifact : path.join(process.env.HOME || "", artifact);
  artifactOnDisk = fs.existsSync(artifact) ? artifact : (fs.existsSync(p) ? p : null);
  log(`artifact on disk   : ${artifactOnDisk || "!!! NOT FOUND"}`);
  if (artifactOnDisk) {
    log(`artifact bytes     : ${fs.statSync(artifactOnDisk).size}`);
  }
}
const rendered = bodyEl.allText();
log(`\nrendered warnings  : ${/server restart|Lost track/i.test(rendered) ? "!!! " + rendered.slice(0, 300) : "none (no restart claim, no lost-job claim)"}`);

const noFalseClaim = !/server restart/i.test(rendered)
  && (EXPECT_KIND === "media_job" || !/Gallery/i.test(rendered));
const pass = Boolean(finalResult) && finalResult.ok
  && wrongHits.length === 0 && rightHits.length > 0
  && noFalseClaim && kind === EXPECT_KIND
  && (EXPECT_KIND !== "media_job" || Boolean(artifactOnDisk));
log(`\nVERDICT: ${pass ? "PASS" : "FAIL"}\n`);
process.exit(pass ? 0 : 1);
