/** Chat export + data backup controls — extracted from app.js. */
(function () {
  function activeBranchId() {
    return window.activeBranchId || "main";
  }

  function openExport(url) {
    const win = window.open(url, "_blank");
    if (!win) {
      window.showAriaToast?.("Pop-up blocked — allow pop-ups to export", "warn", 5000);
      return false;
    }
    window.showAriaToast?.("Export opened in a new tab", "ok", 2500);
    return true;
  }

  document.getElementById("exportChatBtn")?.addEventListener("click", () => {
    const params = new URLSearchParams();
    const branch = activeBranchId();
    if (branch) params.set("branch_id", branch);
    params.set("memory", "1");
    openExport(`/api/chat/export?${params}`);
  });

  document.getElementById("exportChatPdfBtn")?.addEventListener("click", () => {
    const branch = activeBranchId();
    const q = branch ? `?branch_id=${encodeURIComponent(branch)}` : "";
    openExport(`/api/chat/export/pdf${q}`);
  });

  document.getElementById("backupDataBtn")?.addEventListener("click", async () => {
    const btn = document.getElementById("backupDataBtn");
    if (btn) btn.disabled = true;
    window.showAriaToast?.("Backup starting…", "info");
    try {
      const res = await fetch("/api/admin/backup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ async: true }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        window.showAriaToast?.(data.message || "Backup failed", "err");
        return;
      }
      if (data.pending && data.job_id) {
        window.showAriaToast?.(`Backup queued (${data.job_id.slice(0, 8)}…)`, "ok");
        window.jarvisJobs?.refreshJobCenter?.();
        document.getElementById("jobCenterBtn")?.classList.add("pulse");
      } else {
        window.showAriaToast?.(data.message || "Backup complete", "ok");
      }
    } catch (e) {
      window.showAriaToast?.(String(e.message || e || "Backup failed"), "err");
    } finally {
      if (btn) btn.disabled = false;
    }
  });
})();
