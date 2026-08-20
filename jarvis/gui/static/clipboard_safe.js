/** Clipboard writes that cannot fail silently.
 *
 * navigator.clipboard.writeText rejects whenever the browser withholds
 * permission, the page is not a secure context, or there was no user gesture.
 * Unguarded call sites turned that into an unhandled rejection: the copy did
 * not happen and the user was told nothing.
 */
(function () {
  async function ariaCopy(text, label) {
    const value = String(text == null ? "" : text);
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        throw new Error("clipboard unavailable");
      }
      await navigator.clipboard.writeText(value);
      window.showAriaToast?.(label ? `${label} copied` : "Copied", "ok", 1800);
      return true;
    } catch (err) {
      // Last resort: a hidden textarea still works where the async API is blocked.
      try {
        const ta = document.createElement("textarea");
        ta.value = value;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand && document.execCommand("copy");
        document.body.removeChild(ta);
        if (ok) {
          window.showAriaToast?.(label ? `${label} copied` : "Copied", "ok", 1800);
          return true;
        }
      } catch (_) {
        /* fall through to the honest failure below */
      }
      window.showAriaToast?.(
        label ? `Could not copy ${label}` : "Could not copy to the clipboard",
        "err",
        3500,
      );
      return false;
    }
  }
  window.ariaCopy = ariaCopy;
})();
