/**
 * LIVE acceptance test for the Deep Research / Learn topic async lifecycle.
 *
 * Not run by pytest — it talks to a running ARIA and spends real work
 * (web searches + one LLM call) and writes a knowledge brief.
 *
 *   node tests/js/live_learn_topic_acceptance.mjs <static-dir> [base-url] [message]
 *
 * It performs the real user action (POST /api/chat), then feeds the real
 * response into the real frontend handleDone() with a real fetch, so the
 * endpoints recorded are the ones a browser would actually call.
 */
import vm from "node:vm";
import fs from "node:fs";
import path from "node:path";

const STATIC_DIR = path.resolve(process.argv[2]);
const BASE = process.argv[3] || "http://127.0.0.1:8765";
const MESSAGE = process.argv[4] || "do deep research on tenkara rod action and learn about it";

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

log(`\n=== LIVE Learn Topic acceptance @ ${iso()} ===`);
log(`static dir : ${STATIC_DIR}`);
log(`base url   : ${BASE}`);
log(`message    : ${MESSAGE}\n`);

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

log(`[frontend] handing response to the real handleDone()…\n`);
ctx.handleDone_real(data, data.message || "");

const deadline = Date.now() + 15 * 60 * 1000;
while (!finalResult && Date.now() < deadline) {
  await new Promise((r) => setTimeout(r, 2000));
}

const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
const urls = [...new Set(fetched.map((f) => f.url.replace(/\/[0-9a-f]{8,}/g, "/<id>")))];
const mediaHits = fetched.filter((f) => f.url.includes("/api/media/job/"));

log(`\n=== RESULT after ${elapsed}s ===`);
log(`endpoints polled   : ${JSON.stringify(urls)}`);
log(`poll count         : ${fetched.length}`);
log(`media-endpoint hits: ${mediaHits.length}  ${mediaHits.length === 0 ? "(correct)" : "!!! WRONG REGISTRY"}`);
log(`completed          : ${Boolean(finalResult)}`);
if (finalResult) {
  log(`result.ok          : ${finalResult.ok}`);
  log(`result.type        : ${finalResult.type}`);
  log(`knowledge_path     : ${finalResult.knowledge_path}`);
  log(`result.message     :\n${String(finalResult.message || "").slice(0, 400)}`);
}
const rendered = bodyEl.allText();
log(`\nrendered warnings  : ${/Gallery|server restart|Lost track/i.test(rendered) ? "!!! " + rendered.slice(0, 300) : "none (no Gallery / no restart claim)"}`);

const pass = Boolean(finalResult) && finalResult.ok && mediaHits.length === 0
  && !/Gallery|server restart/i.test(rendered) && kind === "background_job";
log(`\nVERDICT: ${pass ? "PASS" : "FAIL"}\n`);
process.exit(pass ? 0 : 1);
