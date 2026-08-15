/** Aria outcome mutation — never toast success without verify.
 * Architectural rule (Batch A): HTTP 200 / res.ok alone is not success.
 */
(function () {
  "use strict";

  /**
   * @param {object} opts
   * @param {() => Promise<Response>} opts.request
   * @param {(data: any, res: Response) => Promise<boolean>|boolean} [opts.verify]
   * @param {string} [opts.successToast]
   * @param {string} [opts.failToast]
   * @param {"ok"|"warn"|"err"|"info"} [opts.successTone]
   * @returns {Promise<{ok:boolean, res?:Response, data?:any, error?:string}>}
   */
  async function ariaMutate(opts) {
    const {
      request,
      verify,
      successToast,
      failToast,
      successTone = "ok",
    } = opts || {};
    try {
      const res = await request();
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        const msg =
          (typeof data.message === "string" && data.message) ||
          data.detail ||
          failToast ||
          `Request failed (${res.status})`;
        window.showAriaToast?.(String(msg), "err", 5000);
        return { ok: false, res, data, error: String(msg) };
      }
      if (typeof verify === "function") {
        const ok = await verify(data, res);
        if (!ok) {
          const msg = failToast || "Action reported success but outcome could not be verified";
          window.showAriaToast?.(msg, "err", 5000);
          return { ok: false, res, data, error: msg };
        }
      }
      if (successToast) window.showAriaToast?.(successToast, successTone, 3000);
      return { ok: true, res, data };
    } catch (err) {
      const msg = err?.message || failToast || "Request failed";
      window.showAriaToast?.(String(msg), "err", 5000);
      return { ok: false, error: String(msg) };
    }
  }

  window.ariaMutate = ariaMutate;
})();
