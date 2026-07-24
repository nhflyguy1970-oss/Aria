/** Desktop notification helper — extracted from app.js. */
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
window.jarvisNotify = notifyDesktop;

})();
