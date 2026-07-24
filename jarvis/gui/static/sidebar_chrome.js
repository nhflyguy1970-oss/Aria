/** Sidebar layout + mobile drawer — extracted from app.js. */
(function () {
  "use strict";

function resetSidebarLayout() {
  localStorage.removeItem("jarvis_sidebar_collapsed");
  document.querySelectorAll(".sidebar-section.collapsed").forEach((sec) => {
    sec.classList.remove("collapsed");
    const head = sec.querySelector(".sidebar-section-head");
    if (head) head.setAttribute("aria-expanded", "true");
  });
  document.body.classList.remove("mobile-sidebar-open");
}

document.getElementById("mobileMenuBtn")?.addEventListener("click", () => {
  document.body.classList.toggle("mobile-sidebar-open");
});
document.querySelector(".sidebar-backdrop")?.addEventListener("click", () => {
  document.body.classList.remove("mobile-sidebar-open");
});

document.getElementById("resetLayoutBtn")?.addEventListener("click", () => {
  resetSidebarLayout();
  if (statusText) statusText.textContent = "Sidebar expanded — all sections visible";
});

  window.resetSidebarLayout = resetSidebarLayout;
})();
