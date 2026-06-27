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
      li.innerHTML = `<strong>${p.title}</strong> <span class="muted">(${p.slug})</span>`
        + (isActive ? ' <span class="ok">active</span>' : "");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn tiny";
      btn.textContent = isActive ? "Active" : "Switch";
      btn.disabled = isActive;
      btn.addEventListener("click", async () => {
        await p2Fetch("/api/projects/switch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slug: p.slug }),
        });
        loadProjects();
        window.showAriaToast?.(`Project: ${p.slug}`);
      });
      li.appendChild(document.createElement("br"));
      li.appendChild(btn);
      list.appendChild(li);
    }
    if (!(data.projects || []).length) {
      list.innerHTML = '<li class="muted">No projects yet.</li>';
    }
  } catch (e) {
    if (list) list.innerHTML = `<li class="muted">${e.message}</li>`;
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
        await p2Fetch("/api/projects/switch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slug: p.slug }),
        });
        modal.classList.add("hidden");
        sessionStorage.setItem("jarvisProjectPickerDone", "1");
        loadProjects();
      });
      pickList.appendChild(btn);
    }
    modal.classList.remove("hidden");
  } catch (_) {}
}

window.initProjects = function initProjects() {
  const root = $("projectsView");
  if (!root || root.dataset.bound === "1") return;
  root.dataset.bound = "1";
  loadProjects();
  $("projectsCreateBtn")?.addEventListener("click", async () => {
    const title = $("projectsTitleInput")?.value?.trim();
    if (!title) return;
    await p2Fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    $("projectsTitleInput").value = "";
    await p2Fetch("/api/projects/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug: title.toLowerCase().replace(/\s+/g, "-").slice(0, 48) }),
    }).catch(() => {});
    loadProjects();
  });
  $("projectsImportBtn")?.addEventListener("click", async () => {
    const path = $("projectsGitInput")?.value?.trim();
    if (!path) return;
    await p2Fetch("/api/projects/import-git", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    $("projectsGitInput").value = "";
    loadProjects();
  });
  $("projectPickerSkipBtn")?.addEventListener("click", () => {
    $("projectPickerModal")?.classList.add("hidden");
    sessionStorage.setItem("jarvisProjectPickerDone", "1");
  });
  maybeProjectPicker();
};
