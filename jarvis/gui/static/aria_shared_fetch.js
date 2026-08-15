/**
 * Shared GET coalesce + short TTL for duplicate room init fetches (SYS-P02).
 * Identical in-flight URLs share one network request; optional ttlMs caches briefly.
 */
(function () {
  "use strict";

  /** @type {Map<string, Promise<any>>} */
  const inflight = new Map();
  /** @type {Map<string, { at: number, value: any }>} */
  const cache = new Map();

  /**
   * @param {string} url
   * @param {{ ttlMs?: number, signal?: AbortSignal }} [opts]
   */
  async function getJson(url, opts = {}) {
    const key = String(url || "");
    const ttlMs = Math.max(0, Number(opts.ttlMs) || 0);
    if (ttlMs > 0) {
      const hit = cache.get(key);
      if (hit && Date.now() - hit.at < ttlMs) {
        return typeof structuredClone === "function" ? structuredClone(hit.value) : JSON.parse(JSON.stringify(hit.value));
      }
    }
    let p = inflight.get(key);
    if (!p) {
      p = (async () => {
        const res = await fetch(key, { cache: "no-store", signal: opts.signal });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const err = new Error(data.error || data.message || `HTTP ${res.status}`);
          err.status = res.status;
          err.data = data;
          throw err;
        }
        if (ttlMs > 0) cache.set(key, { at: Date.now(), value: data });
        return data;
      })().finally(() => {
        inflight.delete(key);
      });
      inflight.set(key, p);
    }
    const data = await p;
    return typeof structuredClone === "function" ? structuredClone(data) : JSON.parse(JSON.stringify(data));
  }

  /**
   * Home foyer payload — coalesces duplicate /api/dashboard/home callers.
   * @param {{ category?: string, stale_ok?: boolean, ttlMs?: number, signal?: AbortSignal }} [opts]
   */
  function dashboardHome(opts = {}) {
    const category = String(opts.category || "").trim();
    const stale = opts.stale_ok !== false;
    const q = new URLSearchParams();
    if (category) q.set("category", category);
    if (stale) q.set("stale_ok", "true");
    const qs = q.toString();
    const url = qs ? `/api/dashboard/home?${qs}` : "/api/dashboard/home";
    return getJson(url, { ttlMs: opts.ttlMs ?? 2500, signal: opts.signal });
  }

  window.AriaSharedFetch = {
    getJson,
    dashboardHome,
    version: "3a.1",
  };
})();
