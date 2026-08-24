/**
 * Phase 6 contract harness: classify real backend chat responses with the real
 * frontend router. Reads a JSON array of responses on stdin, emits
 * [{job_id, kind, endpoint}] so pytest can compare against the backend registry.
 */
import vm from "node:vm";
import fs from "node:fs";
import path from "node:path";

const STATIC_DIR = path.resolve(process.argv[2]);
const ENDPOINTS = {
  coding_job: "/api/coding/job/",
  background_job: "/api/coding/job/",
  media_job: "/api/media/job/",
};

const sandbox = { console };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.document = {
  createElement: () => ({ className: "", appendChild() {}, addEventListener() {} }),
  getElementById: () => null,
  querySelector: () => null,
  querySelectorAll: () => [],
  documentElement: { classList: { toggle() {} } },
};
sandbox.sessionStorage = { getItem: () => null, setItem() {}, removeItem() {} };
sandbox.setTimeout = () => 0;
sandbox.fetch = async () => ({ ok: true, status: 200, json: async () => ({}) });
const ctx = vm.createContext(sandbox);
for (const f of ["coding_jobs.js", "media_jobs.js", "chat_done.js"]) {
  vm.runInContext(fs.readFileSync(path.join(STATIC_DIR, f), "utf8"), ctx, { filename: f });
}

const input = JSON.parse(fs.readFileSync(0, "utf8"));
const out = input.map((entry) => {
  const kind = ctx.resolveJobKind(entry.response);
  return {
    action: entry.action,
    kind,
    endpoint: kind ? (ENDPOINTS[kind] ?? null) : null,
    // Which pollers exist for that kind — proves the dispatch target is real.
    poller_defined: kind === "media_job"
      ? typeof ctx.pollMediaJob === "function"
      : kind === "background_job"
        ? typeof ctx.jarvisPollBackgroundJob === "function"
        : kind === "coding_job"
          ? typeof ctx.jarvisPollCodingJob === "function"
          : false,
  };
});
process.stdout.write(JSON.stringify(out, null, 2));
