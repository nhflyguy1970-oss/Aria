/** P3 Maker lab — CAD generation, STL viewer, printer panel */
(function () {
  const $ = (id) => document.getElementById(id);
  let viewer = null;
  let selectedModelId = "";

  async function engFetch(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || data.error || res.statusText);
    return data;
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  async function refreshCadStatus() {
    const el = $("cadStatusLine");
    if (!el) return;
    try {
      const st = await engFetch("/api/engineering/cad_status");
      const parts = [];
      if (st.openscad) parts.push("OpenSCAD");
      if (st.build123d) parts.push("build123d");
      if (st.meshy) parts.push("Meshy");
      const sl = st.slicer || {};
      const slicers = (sl.slicers || []).map((s) => s.label).join(", ");
      el.textContent = `CAD: ${parts.join(" · ") || "not installed"}${slicers ? ` · Slicer: ${slicers}` : ""}`;
    } catch (e) {
      el.textContent = `CAD status: ${e.message}`;
    }
  }

  async function loadModels() {
    const list = $("cadModelList");
    if (!list) return;
    try {
      const data = await engFetch("/api/engineering/models");
      list.innerHTML = "";
      const models = data.models || [];
      if (!models.length) {
        list.innerHTML = "<li class='muted'>No models yet — generate or Hello cube</li>";
      }
      for (const m of models) {
        const li = document.createElement("li");
        li.className = "planner-list-item";
        li.innerHTML = `<button type="button" class="ghost-btn small cad-model-btn" data-id="${esc(m.id)}">${esc(m.name || m.id)}</button> <span class="muted">${esc(m.backend || "")}</span>`;
        list.appendChild(li);
      }
      list.querySelectorAll(".cad-model-btn").forEach((btn) => {
        btn.addEventListener("click", () => selectModel(btn.dataset.id));
      });
      if (!selectedModelId && models.length) selectModel(models[0].id);
    } catch (e) {
      list.innerHTML = `<li class="muted">${esc(e.message)}</li>`;
    }
  }

  function selectModel(id) {
    selectedModelId = id;
    const log = $("cadGenLog");
    if (log) log.textContent = `Selected model ${id}`;
    loadStlViewer(id);
  }

  function loadStlViewer(modelId) {
    const wrap = $("cadViewer");
    if (!wrap || !modelId || typeof THREE === "undefined") return;
    wrap.innerHTML = "";
    const w = wrap.clientWidth || 400;
    const h = 280;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 2000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    wrap.appendChild(renderer.domElement);
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(1, 2, 3);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x666666));
    const loader = new THREE.STLLoader();
    loader.load(`/api/engineering/models/${encodeURIComponent(modelId)}/stl`, (geom) => {
      geom.center();
      geom.computeVertexNormals();
      const mesh = new THREE.Mesh(geom, new THREE.MeshPhongMaterial({ color: 0x4ade80, specular: 0x111111 }));
      scene.add(mesh);
      const box = new THREE.Box3().setFromObject(mesh);
      const size = box.getSize(new THREE.Vector3()).length();
      camera.position.set(size, size, size);
      camera.lookAt(0, 0, 0);
      function animate() {
        requestAnimationFrame(animate);
        mesh.rotation.y += 0.005;
        renderer.render(scene, camera);
      }
      animate();
      viewer = { scene, camera, renderer, mesh };
    });
  }

  async function generateCad() {
    const prompt = $("cadPromptInput")?.value?.trim();
    if (!prompt) return;
    const log = $("cadGenLog");
    if (log) log.textContent = "Generating…";
    try {
      const data = await engFetch("/api/engineering/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, backend: $("cadBackendSelect")?.value || "auto" }),
      });
      if (log) {
        const v = data.verify || {};
        log.textContent = data.message || `Done — ${v.triangles || "?"} triangles`;
      }
      await loadModels();
      if (data.model?.id) selectModel(data.model.id);
    } catch (e) {
      if (log) log.textContent = e.message;
    }
  }

  async function helloCube() {
    const log = $("cadGenLog");
    if (log) log.textContent = "Hello cube…";
    try {
      const data = await engFetch("/api/engineering/hello-cube", { method: "POST" });
      if (log) log.textContent = "10mm cube ready";
      await loadModels();
      if (data.model?.id) selectModel(data.model.id);
    } catch (e) {
      if (log) log.textContent = e.message;
    }
  }

  async function sliceSelected() {
    if (!selectedModelId) return;
    const log = $("cadGenLog");
    if (log) log.textContent = "Slicing…";
    try {
      const data = await engFetch("/api/engineering/slice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: selectedModelId }),
      });
      if (log) log.textContent = `G-code: ${data.gcode_path}`;
      wrap.dataset.lastGcode = data.gcode_path;
    } catch (e) {
      if (log) log.textContent = e.message;
    }
  }

  const wrap = { dataset: {} };

  async function refreshPrinter() {
    const line = $("printerStatusLine");
    try {
      const st = await engFetch("/api/engineering/printer/status");
      if (line) {
        line.textContent = st.ok
          ? `${st.printer?.name || "Printer"} — ${st.state} · bed ${st.bed_c}°C · nozzle ${st.nozzle_c}°C`
          : (st.message || st.error || "No printer");
      }
    } catch (e) {
      if (line) line.textContent = e.message;
    }
  }

  async function addPrinter() {
    const host = $("printerHostInput")?.value?.trim();
    if (!host) return;
    await engFetch("/api/engineering/printers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: $("printerNameInput")?.value || "Printer", host }),
    });
    await refreshPrinter();
  }

  async function discoverPrinters() {
    const list = $("printerDiscoverList");
    try {
      const data = await engFetch("/api/engineering/printers/discover", { method: "POST" });
      if (list) {
        list.innerHTML = (data.printers || []).map((p) =>
          `<li><button type="button" class="ghost-btn small printer-pick-btn" data-host="${esc(p.host)}">${esc(p.name)} — ${esc(p.host)}</button></li>`
        ).join("") || "<li class='muted'>None found on LAN</li>";
        list.querySelectorAll(".printer-pick-btn").forEach((btn) => {
          btn.addEventListener("click", () => {
            if ($("printerHostInput")) $("printerHostInput").value = btn.dataset.host;
          });
        });
      }
    } catch (e) {
      if (list) list.innerHTML = `<li class="muted">${esc(e.message)}</li>`;
    }
  }

  async function startPrint() {
    const gcode = wrap.dataset.lastGcode || "";
    if (!gcode) {
      alert("Slice a model first.");
      return;
    }
    const bed = $("printBedConfirm")?.checked;
    const fil = $("printFilamentConfirm")?.checked;
    const log = $("cadGenLog");
    try {
      const data = await engFetch("/api/engineering/print", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gcode_path: gcode, bed_confirmed: bed, filament_confirmed: fil }),
      });
      if (log) log.textContent = data.message || `Queued ${data.job_id}`;
    } catch (e) {
      if (log) log.textContent = e.message;
    }
  }

  async function iterateCad() {
    const prompt = $("cadIterateInput")?.value?.trim();
    const log = $("cadGenLog");
    if (!selectedModelId) {
      if (log) log.textContent = "Select a model first";
      return;
    }
    if (!prompt) return;
    if (log) log.textContent = "Iterating…";
    try {
      const data = await engFetch("/api/engineering/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: selectedModelId, prompt }),
      });
      if (log) log.textContent = data.message || "Iterate done";
      await loadModels();
      const mid = data.model?.id || data.model_id || selectedModelId;
      if (mid) selectModel(mid);
    } catch (e) {
      if (log) log.textContent = e.message;
      window.showAriaToast?.(`Iterate failed: ${e.message}`, "err");
    }
  }

  async function clearGallery() {
    const log = $("cadGenLog");
    try {
      const data = await engFetch("/api/engineering/models/clear", { method: "POST" });
      selectedModelId = "";
      if (log) log.textContent = data.message || "Gallery cleared";
      await loadModels();
      const wrap = $("cadViewer");
      if (wrap) wrap.innerHTML = "";
    } catch (e) {
      if (log) log.textContent = e.message;
      window.showAriaToast?.(`Clear failed: ${e.message}`, "err");
    }
  }

  function exportSelected() {
    const log = $("cadGenLog");
    if (!selectedModelId) {
      if (log) log.textContent = "Select a model to export";
      window.showAriaToast?.("Select a model first", "warn");
      return;
    }
    window.open(`/api/engineering/models/${encodeURIComponent(selectedModelId)}/stl`, "_blank");
    if (log) log.textContent = `Downloading STL for ${selectedModelId}`;
  }

  function initMakerLab() {
    $("cadRefreshBtn")?.addEventListener("click", () => { refreshCadStatus(); loadModels(); });
    $("cadGenerateBtn")?.addEventListener("click", generateCad);
    $("cadHelloCubeBtn")?.addEventListener("click", helloCube);
    $("cadSliceBtn")?.addEventListener("click", sliceSelected);
    $("cadIterateBtn")?.addEventListener("click", iterateCad);
    $("cadClearBtn")?.addEventListener("click", clearGallery);
    $("cadExportBtn")?.addEventListener("click", exportSelected);
    $("printerRefreshBtn")?.addEventListener("click", refreshPrinter);
    $("printerAddBtn")?.addEventListener("click", addPrinter);
    $("printerDiscoverBtn")?.addEventListener("click", discoverPrinters);
    $("printStartBtn")?.addEventListener("click", startPrint);
    refreshCadStatus();
    loadModels();
    refreshPrinter();
  }

  window.initMakerLab = initMakerLab;
})();
