/** P2 project workspace UI */

function $(id) {
  return document.getElementById(id);
}

async function p2Fetch(url, opts = {}) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || res.statusText);
  return data;
}

async function loadProjects() {
  const list = $("projectsList");
  const activeEl = $("projectsActive");
  if (!list) return;
  try {
    const data = await p2Fetch("/api/projects");
    if (activeEl) {
      activeEl.textContent = data.active
        ? `Active: ${data.active}`
        : "No active project — pick one or create below.";
    }
    list.innerHTML = "";
    for (const p of data.projects || []) {
      const li = document.createElement("li");
      li.className = "planner-list-item";
      const isActive = p.slug === data.active;
      const title = document.createElement("strong");
      title.textContent = p.title || p.slug || "Untitled project";
      const slug = document.createElement("span");
      slug.className = "muted";
      slug.textContent = ` (${p.slug || "?"})`;
      li.append(title, slug);
      if (isActive) {
        const active = document.createElement("span");
        active.className = "ok";
        active.textContent = " active";
        li.append(active);
      }
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn tiny";
      btn.textContent = isActive ? "Active" : "Switch";
      btn.disabled = isActive;
      btn.addEventListener("click", async () => {
        try {
          await p2Fetch("/api/projects/switch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ slug: p.slug }),
          });
          loadProjects();
          window.showAriaToast?.(`Project: ${p.slug}`, "ok", 2500);
        } catch (err) {
          window.showAriaToast?.(err.message || "Switch failed", "err", 5000);
        }
      });
      li.appendChild(document.createElement("br"));
      li.appendChild(btn);
      list.appendChild(li);
    }
    if (!(data.projects || []).length) {
      list.innerHTML =
        '<li class="muted">No projects yet. <button type="button" class="ghost-btn tiny" id="projectsEmptyCreateBtn">Create project</button> or <button type="button" class="ghost-btn tiny" id="projectsEmptyChatBtn">ask Chat</button></li>';
      list.querySelector("#projectsEmptyCreateBtn")?.addEventListener("click", () => {
        $("projectsTitleInput")?.focus();
      });
      list.querySelector("#projectsEmptyChatBtn")?.addEventListener("click", () => {
        window.switchToView?.("chat");
        window.jarvisSendToChat?.("Create a new project named ");
      });
    }
  } catch (e) {
    if (list) {
      list.replaceChildren();
      const error = document.createElement("li");
      error.className = "muted";
      error.textContent = e.message || "Could not load projects";
      list.appendChild(error);
    }
    window.showAriaToast?.(e.message || "Could not load projects", "err", 5000);
  }
}

async function maybeProjectPicker() {
  if (sessionStorage.getItem("jarvisProjectPickerDone")) return;
  try {
    const data = await p2Fetch("/api/projects");
    if (data.active || !(data.projects || []).length) {
      sessionStorage.setItem("jarvisProjectPickerDone", "1");
      return;
    }
    const modal = $("projectPickerModal");
    const pickList = $("projectPickerList");
    if (!modal || !pickList) return;
    pickList.innerHTML = "";
    for (const p of data.projects) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn";
      btn.textContent = `${p.title} (${p.slug})`;
      btn.addEventListener("click", async () => {
        try {
          await p2Fetch("/api/projects/switch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ slug: p.slug }),
          });
          modal.classList.add("hidden");
          sessionStorage.setItem("jarvisProjectPickerDone", "1");
          window.showAriaToast?.(`Active project: ${p.title || p.slug}`, "ok", 3000);
          loadProjects();
        } catch (err) {
          window.showAriaToast?.(err.message || "Could not switch project", "err", 5000);
        }
      });
      pickList.appendChild(btn);
    }
    modal.classList.remove("hidden");
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not load project picker", "err", 5000);
  }
}

window.initProjects = function initProjects() {
  const root = $("projectsView");
  if (!root || root.dataset.bound === "1") return;
  root.dataset.bound = "1";
  loadProjects();
  $("projectsOpenMemoryBtn")?.addEventListener("click", () => window.switchToView?.("memory"));
  $("projectsOpenCodingBtn")?.addEventListener("click", () => window.switchToView?.("chat"));
  $("projectsOpenDocumentsBtn")?.addEventListener("click", () => window.switchToView?.("documents"));
  $("projectsCreateBtn")?.addEventListener("click", async () => {
    const title = $("projectsTitleInput")?.value?.trim();
    if (!title) return;
    try {
      const created = await p2Fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      $("projectsTitleInput").value = "";
      const slug = created?.project?.slug || created?.slug;
      if (!slug) throw new Error("Create succeeded but no project slug returned");
      await p2Fetch("/api/projects/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug }),
      });
      window.showAriaToast?.(`Active project: ${created?.project?.title || title}`, "ok", 3500);
      loadProjects();
    } catch (err) {
      window.showAriaToast?.(err.message || "Could not create project", "err", 5000);
    }
  });
  $("projectsImportBtn")?.addEventListener("click", async () => {
    const path = $("projectsGitInput")?.value?.trim();
    if (!path) return;
    try {
      await p2Fetch("/api/projects/import-git", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
      $("projectsGitInput").value = "";
      window.showAriaToast?.("Project imported", "ok", 3500);
      loadProjects();
    } catch (err) {
      window.showAriaToast?.(err.message || "Import failed", "err", 5000);
    }
  });
  $("projectPickerSkipBtn")?.addEventListener("click", () => {
    $("projectPickerModal")?.classList.add("hidden");
    sessionStorage.setItem("jarvisProjectPickerDone", "1");
  });
  maybeProjectPicker();
};
