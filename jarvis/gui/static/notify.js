/** Desktop notification helper — preserves Notifications/Activity wrappers. */
(function () {
  "use strict";

  function notifyDesktop(title, body) {
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted") {
      new Notification(title, { body });
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission().then((p) => {
        if (p === "granted") new Notification(title, { body });
      });
    }
  }

  // Never clobber an existing wrapped jarvisNotify from Notifications / Activity Center.
  if (typeof window.jarvisNotify === "function") {
    if (!window.__ariaDesktopNotifyRaw) {
      // If already wrapped, keep raw if previously saved; else save current only if unwrapped
      if (!window.jarvisNotify._ariaActivityWrapped && !window.jarvisNotify._ariaNotificationsWrapped) {
        window.__ariaDesktopNotifyRaw = window.jarvisNotify;
      }
    }
    // Install raw under a stable name for the pipeline; leave wrapped handler in place
    if (!window.__ariaDesktopNotifyRaw) {
      window.__ariaDesktopNotifyRaw = notifyDesktop;
    }
  } else {
    window.__ariaDesktopNotifyRaw = notifyDesktop;
    window.jarvisNotify = notifyDesktop;
  }
})();
