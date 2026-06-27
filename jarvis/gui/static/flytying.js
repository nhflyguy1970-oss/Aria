/** Fly Tying workspace — recipes, images, videos, dedicated streaming chat. */
(function () {
  function recipeKey(r) {
    if (!r) return "";
    return r.recipe_id || r.id || r.name || "";
  }

  function imgTag(url, className, alt = "") {
    if (!url) return "";
    return `<img class="${className}" src="${esc(url)}" alt="${esc(alt)}" loading="lazy" onerror="this.style.display='none'" />`;
  }
  const CHAT_KEY = "flytying_chat_v1";
  const EXPECTED_API_VERSION = 3;
  let _bound = false;
  let _recipes = [];
  let _videos = [];
  let _selectedId = "";
  let _selectedVideoKey = "";
  let _chat = [];
  let _streaming = false;
  let _chatAbort = null;
  let _lastSearchMode = "";
  let _favorites = new Set();
  let _compare = new Set();
  let _queue = [];
  let _currentRecipe = null;
  let _stepMode = false;
  let _stepIdx = 0;
  let _inventory = [];
  let _invSortCol = "what";
  let _invSortDir = 1;
  let _editingId = "";
  let _pendingBarcode = "";
  let _scanStream = null;
  let _scanDetector = null;
  let _scanRaf = 0;
  let _scanInterval = 0;
  let _scanBusy = false;
  let _lastScanCode = "";
  let _lastScanAt = 0;
  const RECIPE_PAGE = 40;
  let _recipeOffset = 0;
  let _recipeTotal = 0;
  const _recipeCache = new Map();

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  function fmt(text) {
    return esc(text || "").replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    let data = {};
    try {
      data = await res.json();
    } catch (_) {}
    if (!res.ok) {
      const msg = data.message || data.detail || res.statusText || `HTTP ${res.status}`;
      const err = new Error(typeof msg === "string" ? msg : "Request failed");
      err.status = res.status;
      throw err;
    }
    return data;
  }

  async function fetchRecipeRows(q, type, limit, offset = 0) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (type) params.set("type", type);
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    if ($("flytyingFavoritesOnly")?.checked) params.set("favorites_only", "true");
    const minQ = parseFloat($("flytyingMinQuality")?.value || "0");
    if (minQ > 0) params.set("min_quality", String(minQ));
    const cacheKey = params.toString();
    if (_recipeCache.has(cacheKey)) return _recipeCache.get(cacheKey);
    const data = await fetchJson(`/api/flytying/recipes?${params}`);
    _recipeCache.set(cacheKey, data);
    return data;
  }

  function isFavorite(id) {
    return _favorites.has(id);
  }

  async function loadUserState() {
    try {
      const data = await fetchJson("/api/flytying/user");
      _favorites = new Set(data.favorites || []);
      _queue = data.queue || [];
      _inventory = (data.inventory?.length ? data.inventory : materialsToInventory(data.materials || [])).map(
        (row, i) => normalizeInventoryItem(row, i),
      );
      renderInventory();
      renderQueue();
    } catch (_) {}
  }

  function composeMaterialName(item) {
    const what = (item?.what || "").trim();
    const legacy = (item?.name || "").trim();
    if (!what) return legacy;
    const color = (item?.color || "").trim();
    const size = (item?.size || "").trim();
    const brand = (item?.brand || "").trim();
    const lead = [color, size].filter(Boolean);
    let desc = [...lead, what].join(" ");
    if (brand && !desc.toLowerCase().includes(brand.toLowerCase())) desc = `${desc} (${brand})`;
    return desc;
  }

  function normalizeInventoryItem(raw, idx) {
    const row = { ...(raw || {}) };
    if (!row.what && row.name) row.what = String(row.name);
    row.name = composeMaterialName(row) || String(row.name || "").trim();
    if (!row.id) {
      const slug = row.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 24) || String(idx);
      row.id = `local-${idx}-${slug}`;
    }
    return row;
  }

  function materialsToInventory(materials) {
    return (materials || []).map((name, i) =>
      normalizeInventoryItem({ what: String(name || "").trim(), name: String(name || "").trim(), source: "manual" }, i),
    );
  }

  function applyInventoryResponse(data) {
    if (Array.isArray(data?.inventory)) {
      _inventory = data.inventory.map((row, i) => normalizeInventoryItem(row, i));
    } else if (Array.isArray(data?.materials)) {
      _inventory = materialsToInventory(data.materials);
    }
    renderInventory();
    syncMaterialsSummary();
  }

  function parseBulkLine(line) {
    const raw = (line || "").trim();
    if (!raw) return null;
    const m = raw.match(/^(?:(.+?)\s+)?(?:size\s+)?(\d{1,2}(?:\/\d)?|\d+\/\d)\s+(.+)$/i);
    if (m) {
      return {
        color: (m[1] || "").trim(),
        size: (m[2] || "").trim(),
        what: (m[3] || "").trim(),
      };
    }
    return { what: raw, color: "", size: "", brand: "", notes: "" };
  }

  async function persistInventoryRows(rows, opts = {}) {
    const payload = rows.map((r) => normalizeInventoryItem(r, 0));
    try {
      const data = await fetchJson("/api/flytying/materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: payload, replace: true }),
      });
      applyInventoryResponse(data);
      return data;
    } catch (e) {
      if (e.status !== 404 && e.status !== 400 && e.status !== 405) throw e;
      const names = payload.map((r) => composeMaterialName(r) || r.name).filter(Boolean);
      return persistMaterialsList(names, { replace: !!opts.replace || true });
    }
  }

  async function persistMaterialsList(names, opts = {}) {
    const data = await fetchJson("/api/flytying/materials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ materials: names, replace: !!opts.replace }),
    });
    applyInventoryResponse(data);
    syncMaterialsSummary();
    return data;
  }

  function readEntryFields() {
    return {
      what: ($("flytyingInvWhat")?.value || "").trim(),
      color: ($("flytyingInvColor")?.value || "").trim(),
      size: ($("flytyingInvSize")?.value || "").trim(),
      brand: ($("flytyingInvBrand")?.value || "").trim(),
      notes: ($("flytyingInvNotes")?.value || "").trim(),
    };
  }

  function clearEntryFields() {
    ["flytyingInvWhat", "flytyingInvColor", "flytyingInvSize", "flytyingInvBrand", "flytyingInvNotes"].forEach((id) => {
      const el = $(id);
      if (el) el.value = "";
    });
    $("flytyingInvWhat")?.focus();
  }

  function inventoryMaterialText() {
    return _inventory.map((i) => composeMaterialName(i)).filter(Boolean).join(", ");
  }

  function syncMaterialsSummary() {
    const box = $("flytyingMaterialsSummary");
    if (box && document.activeElement !== box) {
      box.value = inventoryMaterialText();
    }
  }

  function materialsTextForSuggest() {
    const box = $("flytyingMaterialsSummary");
    const raw = (box?.value || "").trim();
    if (raw) return raw;
    return inventoryMaterialText();
  }

  async function saveMaterialsFromSummary() {
    const raw = ($("flytyingMaterialsSummary")?.value || "").trim();
    const status = $("flytyingChatStatus");
    if (!raw) {
      if (status) status.textContent = "Enter materials or use the inventory table";
      return;
    }
    const lines = raw
      .split(/\n+/)
      .flatMap((line) => line.split(/[,;]+/))
      .map((s) => s.trim())
      .filter(Boolean);
    if (status) status.textContent = "Saving…";
    try {
      const rows = lines.map((line, i) => normalizeInventoryItem(parseBulkLine(line) || { what: line }, i));
      await persistInventoryRows(rows, { replace: true });
      if (status) status.textContent = `Saved ${rows.length} material${rows.length === 1 ? "" : "s"}`;
    } catch (e) {
      if (status) status.textContent = e.message || "Could not save";
    }
  }

  function sortedInventory() {
    const col = _invSortCol || "what";
    const dir = _invSortDir || 1;
    return _inventory.slice().sort((a, b) => {
      const av = String(a[col] || composeMaterialName(a) || "").toLowerCase();
      const bv = String(b[col] || composeMaterialName(b) || "").toLowerCase();
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return 0;
    });
  }

  function renderInventoryCell(value, field, item, editing) {
    const id = esc(item.id || "");
    if (!editing) return `<td class="flytying-inv-cell" data-field="${field}">${esc(value || "")}</td>`;
    return `<td><input type="text" class="flytying-inv-edit" data-id="${id}" data-field="${field}" value="${esc(value || "")}" /></td>`;
  }

  function renderInventory() {
    const body = $("flytyingInventoryBody");
    const countEl = $("flytyingInventoryCount");
    document.querySelectorAll(".flytying-sort-btn").forEach((btn) => {
      const col = btn.dataset.col || "";
      const active = col === _invSortCol ? (_invSortDir === 1 ? " ▲" : " ▼") : "";
      btn.textContent =
        (col === "what" ? "What" : col === "color" ? "Color" : col === "size" ? "Size" : "Brand") + active;
    });
    if (countEl) {
      countEl.textContent = _inventory.length
        ? `${_inventory.length} record${_inventory.length === 1 ? "" : "s"}`
        : "No records — add a row above or import lines.";
    }
    if (!body) return;
    const rows = sortedInventory();
    if (!rows.length) {
      body.innerHTML = `<tr class="flytying-inv-empty"><td colspan="6" class="muted small">No materials yet.</td></tr>`;
      return;
    }
    body.innerHTML = rows
      .map((item) => {
        const id = esc(item.id || "");
        const editing = _editingId && String(item.id) === String(_editingId);
        const what = (item.what || item.name || "").trim();
        const actions = editing
          ? `<button type="button" class="ghost-btn tiny flytying-inv-save" data-id="${id}">Save</button> <button type="button" class="ghost-btn tiny flytying-inv-cancel">Cancel</button>`
          : `<button type="button" class="ghost-btn tiny flytying-inv-edit" data-id="${id}">Edit</button> <button type="button" class="ghost-btn tiny flytying-inv-remove" data-id="${id}">×</button>`;
        return `<tr class="flytying-inv-row${editing ? " editing" : ""}" data-id="${id}">${renderInventoryCell(what, "what", item, editing)}${renderInventoryCell(item.color, "color", item, editing)}${renderInventoryCell(item.size, "size", item, editing)}${renderInventoryCell(item.brand, "brand", item, editing)}${renderInventoryCell(item.notes, "notes", item, editing)}<td class="flytying-inv-actions">${actions}</td></tr>`;
      })
      .join("");
    body.querySelectorAll("button.flytying-inv-edit").forEach((btn) => {
      btn.addEventListener("click", () => {
        _editingId = btn.dataset.id || "";
        renderInventory();
      });
    });
    body.querySelectorAll(".flytying-inv-remove").forEach((btn) => {
      btn.addEventListener("click", () => removeInventoryItem(btn.dataset.id));
    });
    body.querySelectorAll(".flytying-inv-save").forEach((btn) => {
      btn.addEventListener("click", () => saveInventoryEdit(btn.dataset.id));
    });
    body.querySelectorAll(".flytying-inv-cancel").forEach((btn) => {
      btn.addEventListener("click", () => {
        _editingId = "";
        renderInventory();
      });
    });
  }

  async function addStructuredItem(fields) {
    const payload = { ...fields, source: "manual" };
    try {
      return await fetchJson("/api/flytying/materials/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (e) {
      if (e.status !== 404) throw e;
      const entry = normalizeInventoryItem({ ...fields, name: composeMaterialName(fields) }, _inventory.length);
      const key = entry.name.toLowerCase();
      if (_inventory.some((i) => composeMaterialName(i).toLowerCase() === key)) {
        return { ok: true, merged: true, inventory: _inventory };
      }
      await persistInventoryRows([..._inventory, entry]);
      return { ok: true, item: entry, inventory: _inventory };
    }
  }

  async function addManualItem() {
    const fields = readEntryFields();
    const status = $("flytyingChatStatus");
    if (!fields.what) {
      if (status) status.textContent = "What is required (e.g. hook, thread, dubbing)";
      $("flytyingInvWhat")?.focus();
      return;
    }
    const label = composeMaterialName(fields);
    if (_inventory.some((i) => composeMaterialName(i).toLowerCase() === label.toLowerCase())) {
      if (status) status.textContent = "Already in inventory";
      return;
    }
    if (status) status.textContent = "Adding…";
    try {
      const data = await addStructuredItem(fields);
      applyInventoryResponse(data);
      clearEntryFields();
      if (status) status.textContent = `Added: ${label}`;
    } catch (e) {
      if (status) status.textContent = e.message || "Could not add material";
    }
  }

  async function saveInventoryEdit(itemId) {
    if (!itemId) return;
    const body = $("flytyingInventoryBody");
    const row = body?.querySelector(`.flytying-inv-row[data-id="${itemId}"]`);
    if (!row) return;
    const fields = {};
    row.querySelectorAll(".flytying-inv-edit").forEach((input) => {
      fields[input.dataset.field] = input.value.trim();
    });
    if (!fields.what) {
      const status = $("flytyingChatStatus");
      if (status) status.textContent = "What is required";
      return;
    }
    const status = $("flytyingChatStatus");
    if (status) status.textContent = "Saving…";
    try {
      let data;
      try {
        data = await fetchJson(`/api/flytying/materials/item/${encodeURIComponent(itemId)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(fields),
        });
      } catch (e) {
        if (e.status !== 404 && e.status !== 405) throw e;
        const rows = _inventory.map((item) => {
          if (String(item.id) !== String(itemId)) return item;
          return normalizeInventoryItem({ ...item, ...fields }, 0);
        });
        await persistInventoryRows(rows);
        data = { ok: true, inventory: _inventory };
      }
      _editingId = "";
      applyInventoryResponse(data);
      if (status) status.textContent = "Saved";
    } catch (e) {
      if (status) status.textContent = e.message || "Could not save";
    }
  }

  async function addBulkLines() {
    const raw = ($("flytyingBulkInput")?.value || "").trim();
    if (!raw) return;
    const lines = raw
      .split(/\n+/)
      .flatMap((line) => line.split(/[,;]+/))
      .map((s) => s.trim())
      .filter(Boolean);
    if (!lines.length) return;
    const status = $("flytyingChatStatus");
    if (status) status.textContent = `Importing ${lines.length} lines…`;
    try {
      const seen = new Set(_inventory.map((i) => composeMaterialName(i).toLowerCase()).filter(Boolean));
      const rows = _inventory.slice();
      let added = 0;
      for (const line of lines) {
        const fields = parseBulkLine(line);
        if (!fields?.what) continue;
        const label = composeMaterialName(fields);
        const low = label.toLowerCase();
        if (seen.has(low)) continue;
        seen.add(low);
        rows.push(normalizeInventoryItem({ ...fields, source: "manual" }, rows.length));
        added += 1;
      }
      if (!added) {
        if (status) status.textContent = "Those materials are already in inventory";
        return;
      }
      await persistInventoryRows(rows);
      const bulk = $("flytyingBulkInput");
      if (bulk) bulk.value = "";
      if (status) status.textContent = `Imported ${added} record${added === 1 ? "" : "s"} (${_inventory.length} total)`;
    } catch (e) {
      if (status) status.textContent = e.message || "Could not import materials";
    }
  }

  async function removeInventoryItem(itemId) {
    if (!itemId) return;
    const status = $("flytyingChatStatus");
    try {
      const data = await fetchJson(`/api/flytying/materials/item/${encodeURIComponent(itemId)}`, { method: "DELETE" });
      if (_editingId === itemId) _editingId = "";
      applyInventoryResponse(data);
      if (status) status.textContent = "Removed from inventory";
    } catch (e) {
      if (e.status !== 404) {
        if (status) status.textContent = e.message;
        return;
      }
      const rows = _inventory.filter((i) => String(i.id || "") !== String(itemId));
      await persistInventoryRows(rows);
      if (_editingId === itemId) _editingId = "";
      if (status) status.textContent = "Removed from inventory";
    }
  }

  function setInventorySort(col) {
    if (_invSortCol === col) _invSortDir = _invSortDir === 1 ? -1 : 1;
    else {
      _invSortCol = col;
      _invSortDir = 1;
    }
    renderInventory();
  }

  function setScanStatus(msg) {
    const el = $("flytyingScanModalStatus");
    if (el) el.textContent = msg || "";
    const chat = $("flytyingChatStatus");
    if (chat && msg && !$("flytyingScanModal")?.classList.contains("hidden")) return;
    if (chat && msg) chat.textContent = msg;
  }

  async function processBarcode(raw, opts = {}) {
    const code = (raw || "").trim();
    if (!code) return;
    const now = Date.now();
    if (code === _lastScanCode && now - _lastScanAt < 2500 && !opts.force) return;
    _lastScanCode = code;
    _lastScanAt = now;
    const input = $("flytyingScanInput");
    if (input) input.value = code;
    setScanStatus(`Looking up ${code}…`);
    try {
      const data = await fetchJson("/api/flytying/materials/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ barcode: code, name: opts.name || "", brand: opts.brand || "" }),
      });
      if (data.needs_name) {
        _pendingBarcode = code;
        const modal = $("flytyingNameBarcodeModal");
        const codeEl = $("flytyingNameBarcodeCode");
        const nameEl = $("flytyingNameBarcodeName");
        const brandEl = $("flytyingNameBarcodeBrand");
        if (codeEl) codeEl.textContent = `Barcode: ${code}`;
        if (nameEl) {
          nameEl.value = "";
          nameEl.focus();
        }
        if (brandEl) brandEl.value = "";
        modal?.classList.remove("hidden");
        setScanStatus(data.message || "Name this barcode to add it.");
        return;
      }
      _inventory = data.inventory?.length ? data.inventory.map((row, i) => normalizeInventoryItem(row, i)) : _inventory;
      renderInventory();
      const item = data.item || {};
      setScanStatus(`Added: ${item.name || code}`);
      closeNameBarcodeModal();
    } catch (e) {
      setScanStatus(e.message);
    }
  }

  function closeNameBarcodeModal() {
    $("flytyingNameBarcodeModal")?.classList.add("hidden");
    _pendingBarcode = "";
  }

  async function savePendingBarcode() {
    const name = ($("flytyingNameBarcodeName")?.value || "").trim();
    const brand = ($("flytyingNameBarcodeBrand")?.value || "").trim();
    if (!name || !_pendingBarcode) return;
    await processBarcode(_pendingBarcode, { name, brand, force: true });
  }

  const SCAN_FORMATS = ["ean_13", "ean_8", "upc_a", "upc_e", "code_128", "code_39", "qr_code"];

  async function getBarcodeDetector() {
    if (!("BarcodeDetector" in window)) {
      throw new Error("Barcode scan needs Chrome or Edge, or type the code manually");
    }
    return new BarcodeDetector({ formats: SCAN_FORMATS });
  }

  async function stopCameraScan() {
    if (_scanRaf) cancelAnimationFrame(_scanRaf);
    _scanRaf = 0;
    if (_scanInterval) clearInterval(_scanInterval);
    _scanInterval = 0;
    _scanBusy = false;
    _scanDetector = null;
    const video = $("flytyingScanVideo");
    if (video) video.srcObject = null;
    if (_scanStream) {
      _scanStream.getTracks().forEach((t) => t.stop());
      _scanStream = null;
    }
    $("flytyingScanModal")?.classList.add("hidden");
  }

  async function startCameraScan() {
    const modal = $("flytyingScanModal");
    const video = $("flytyingScanVideo");
    if (!modal || !video) return;
    modal.classList.remove("hidden");
    if (!("BarcodeDetector" in window)) {
      setScanStatus("Camera scan needs Chrome or Edge. Type the barcode in the field or use a USB scanner.");
      return;
    }
    try {
      setScanStatus("Starting camera…");
      _scanDetector = new BarcodeDetector({ formats: SCAN_FORMATS });
      _scanStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 } },
        audio: false,
      });
      video.srcObject = _scanStream;
      await video.play();
      setScanStatus("Point at UPC/EAN or QR on package…");
      const tick = async () => {
        if (_scanBusy || !video.videoWidth || !_scanDetector) return;
        _scanBusy = true;
        try {
          const codes = await _scanDetector.detect(video);
          if (codes && codes.length) {
            await processBarcode(codes[0].rawValue || "");
          }
        } catch (_) {}
        _scanBusy = false;
      };
      _scanInterval = setInterval(tick, 280);
      tick();
    } catch (e) {
      setScanStatus(`Camera error: ${e.message}`);
    }
  }

  async function scanFromPhoto(file) {
    if (!file) return;
    setScanStatus("Reading photo…");
    if ("BarcodeDetector" in window) {
      try {
        const detector = new BarcodeDetector({ formats: SCAN_FORMATS });
        const bitmap = await createImageBitmap(file);
        const codes = await detector.detect(bitmap);
        bitmap.close();
        if (codes && codes.length) {
          await processBarcode(codes[0].rawValue || "", { force: true });
          return;
        }
      } catch (_) {}
    }
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/flytying/materials/scan-image", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.message || "Scan failed");
      if (data.barcode) await processBarcode(data.barcode, { force: true });
      else setScanStatus(data.message || "No barcode found in photo");
    } catch (e) {
      setScanStatus(e.message);
    }
  }

  async function printMaterialLabel() {
    const name = readEntryFields().what || composeMaterialName(_inventory[0] || {}) || "";
    if (!name) {
      setScanStatus("Enter a material name first (or scan one in).");
      return;
    }
    try {
      const data = await fetchJson("/api/flytying/materials/label", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (data.label_url) window.open(data.label_url, "_blank", "noopener");
    } catch (e) {
      setScanStatus(e.message);
    }
  }

  function renderQueue() {
    const list = $("flytyingQueueList");
    if (!list) return;
    if (!_queue.length) {
      list.innerHTML = "";
      return;
    }
    list.innerHTML =
      `<li class="flytying-queue-label muted small">Tying queue (${_queue.length})</li>` +
      _queue
        .map(
          (q) =>
            `<li><button type="button" class="flytying-queue-btn" data-id="${esc(q.recipe_id)}">${esc(q.name || q.recipe_id)}</button></li>`
        )
        .join("");
    list.querySelectorAll(".flytying-queue-btn").forEach((btn) => {
      btn.addEventListener("click", () => selectRecipe(btn.dataset.id));
    });
  }

  async function toggleFavorite(id, name) {
    if (!id) return;
    try {
      const data = await fetchJson("/api/flytying/favorites/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_id: id }),
      });
      _favorites = new Set(data.favorites || []);
      loadRecipes();
      if (_selectedId === id) selectRecipe(id, { skipVideo: true });
    } catch (_) {}
  }

  async function addToQueue(id, name) {
    if (!id) return;
    try {
      const data = await fetchJson("/api/flytying/queue/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_id: id, name: name || "" }),
      });
      _queue = data.queue || [];
      renderQueue();
    } catch (_) {}
  }

  function updateCompareToolbar() {
    const n = _compare.size;
    $("flytyingCompareBtn")?.toggleAttribute("disabled", n < 2);
    $("flytyingExportBtn")?.toggleAttribute("disabled", !_currentRecipe);
    $("flytyingPrintBtn")?.toggleAttribute("disabled", !_currentRecipe);
  }

  function renderInstructions(data) {
    const section = $("flytyingStepsSection");
    if (!section) return;
    const steps = data.steps || [];
    const stepBtn = $("flytyingStepModeBtn");
    if (stepBtn) {
      stepBtn.textContent = _stepMode ? "All steps" : "Step mode";
      stepBtn.disabled = !steps.length;
    }
    if (!steps.length) {
      section.innerHTML = `<h4>Instructions</h4><ol class="flytying-steps"><li class="muted">No steps listed for this pattern.</li></ol>`;
      return;
    }
    if (!_stepMode) {
      section.innerHTML = `<h4>Instructions</h4><ol class="flytying-steps">${steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>`;
      return;
    }
    const idx = Math.max(0, Math.min(_stepIdx, steps.length - 1));
    section.innerHTML = `
      <h4>Instructions <span class="muted small">· step ${idx + 1} of ${steps.length}</span></h4>
      <div class="flytying-step-box">
        <p class="flytying-step-text">${fmt(steps[idx])}</p>
        <div class="flytying-step-nav">
          <button type="button" class="ghost-btn small" id="flytyingStepPrev"${idx <= 0 ? " disabled" : ""}>← Prev</button>
          <button type="button" class="ghost-btn small" id="flytyingStepNext"${idx >= steps.length - 1 ? " disabled" : ""}>Next →</button>
        </div>
      </div>`;
    $("flytyingStepPrev")?.addEventListener("click", () => {
      _stepIdx = Math.max(0, _stepIdx - 1);
      renderInstructions(data);
    });
    $("flytyingStepNext")?.addEventListener("click", () => {
      _stepIdx = Math.min(steps.length - 1, _stepIdx + 1);
      renderInstructions(data);
    });
    section.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function loadChat() {
    try {
      const raw = sessionStorage.getItem(CHAT_KEY);
      _chat = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(_chat)) _chat = [];
    } catch (_) {
      _chat = [];
    }
  }

  function saveChat() {
    sessionStorage.setItem(CHAT_KEY, JSON.stringify(_chat.slice(-40)));
  }

  function renderChat() {
    const box = $("flytyingChatMessages");
    if (!box) return;
    if (!_chat.length) {
      box.innerHTML =
        '<p class="muted flytying-chat-empty">Ask about patterns, materials, or say <strong>design a caddis emerger for spring creeks</strong>.</p>';
      return;
    }
    box.innerHTML = _chat
      .map((m, i) => {
        const role = m.role === "assistant" ? "assistant" : "user";
        const streaming = m.streaming ? " streaming" : "";
        return `<div class="flytying-chat-bubble flytying-chat-${role}${streaming}" data-idx="${i}"><div class="flytying-chat-role">${role === "assistant" ? "ARIA" : "You"}</div><div class="flytying-chat-body">${fmt(m.content)}</div></div>`;
      })
      .join("");
    box.scrollTop = box.scrollHeight;
  }

  function updateStreamingBubble(text) {
    const box = $("flytyingChatMessages");
    if (!box) return;
    const bubble = box.querySelector(".flytying-chat-bubble.streaming .flytying-chat-body");
    if (bubble) bubble.innerHTML = fmt(text);
    box.scrollTop = box.scrollHeight;
  }

  function videoKey(v) {
    return `${v.provider || ""}:${v.video_id || ""}:${v.watch_url || ""}:${v.recipe_id || ""}`;
  }

  function customVideoKey(v) {
    return `${v.provider || ""}:${v.video_id || v.watch_url || ""}`;
  }

  function searchModeLabel(mode) {
    if (mode === "hybrid") return "keyword + semantic";
    if (mode === "semantic") return "semantic";
    if (mode === "keyword") return "keyword";
    if (mode === "browse") return "browse";
    return mode || "";
  }

  function showVideo(video) {
    const player = $("flytyingVideoPlayer");
    if (!player || !video) {
      player?.classList.add("hidden");
      return;
    }
    _selectedVideoKey = videoKey(video);
    document.querySelectorAll(".flytying-video-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.vkey === _selectedVideoKey);
    });
    player.classList.remove("hidden");
    if (video.provider === "youtube" && video.video_id) {
      player.classList.remove("flytying-video-article");
      player.innerHTML = `<iframe src="https://www.youtube.com/embed/${esc(video.video_id)}?rel=0" title="${esc(video.title || video.recipe_name || "Fly tying video")}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
      return;
    }
    if (video.provider === "vimeo" && video.video_id) {
      player.classList.remove("flytying-video-article");
      player.innerHTML = `<iframe src="https://player.vimeo.com/video/${esc(video.video_id)}" title="${esc(video.title || video.recipe_name || "Fly tying video")}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>`;
      return;
    }
    player.classList.add("flytying-video-article");
    const url = video.watch_url || "";
    const label = video.provider === "flyfishfood" ? "Fly Fish Food" : "Tutorial";
    player.innerHTML = `<p><strong>${esc(video.recipe_name || video.title || label)}</strong></p><p class="muted">${esc(label)} — open in a new tab to watch.</p><p><a href="${esc(url)}" target="_blank" rel="noopener" class="apply-btn small">Open tutorial</a></p>`;
  }

  function providerLabel(v) {
    if (v.provider === "flyfishfood") return "Fly Fish Food";
    if (v.provider === "vimeo") return "Vimeo";
    if (v.custom) return "Custom";
    return "YouTube";
  }

  function renderVideoList() {
    const list = $("flytyingVideoList");
    if (!list) return;
    const q = ($("flytyingVideoSearch")?.value || "").trim().toLowerCase();
    const filtered = _videos.filter((v) => {
      if (!q) return true;
      const blob = `${v.recipe_name || ""} ${v.title || ""} ${v.fly_type || ""} ${v.provider || ""}`.toLowerCase();
      return blob.includes(q);
    });
    if (!filtered.length) {
      list.innerHTML = '<li class="muted">No videos found</li>';
      return;
    }
    list.innerHTML = filtered
      .slice(0, 60)
      .map((v, idx) => {
        const vkey = videoKey(v);
        const thumb =
          v.thumbnail && (v.provider === "youtube" || v.thumbnail.startsWith("http"))
            ? `<img class="flytying-video-thumb" src="${esc(v.thumbnail)}" alt="" loading="lazy" />`
            : '<span class="flytying-video-thumb"></span>';
        const label = providerLabel(v);
        const delBtn = v.custom
          ? `<button type="button" class="flytying-video-del" data-ckey="${esc(customVideoKey(v))}" title="Remove custom video">×</button>`
          : "";
        return `<li class="flytying-video-item">${delBtn}<button type="button" class="flytying-video-btn${vkey === _selectedVideoKey ? " active" : ""}" data-vidx="${idx}" data-vkey="${esc(vkey)}" data-recipe="${esc(v.recipe_id || v.recipe_name || "")}">${thumb}<span class="flytying-video-meta"><span class="flytying-video-provider">${esc(label)}</span><span>${esc(v.recipe_name || v.title)}</span></span></button></li>`;
      })
      .join("");
    list.querySelectorAll(".flytying-video-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.dataset.vidx || "0", 10);
        const v = filtered[idx];
        if (v) {
          showVideo(v);
          if (v.recipe_id || v.recipe_name) selectRecipe(v.recipe_id || v.recipe_name, { skipVideo: true });
        }
      });
    });
    list.querySelectorAll(".flytying-video-del").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        deleteCustomVideo(btn.dataset.ckey || "");
      });
    });
  }

  async function deleteCustomVideo(key) {
    if (!key) return;
    const status = $("flytyingChatStatus");
    if (status) status.textContent = "Removing video…";
    try {
      await fetchJson("/api/flytying/videos/custom", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key }),
      });
      await loadVideos();
      if (status) status.textContent = "Video removed";
    } catch (e) {
      if (status) status.textContent = e.message;
    }
  }

  async function loadVideos() {
    try {
      const data = await fetchJson("/api/flytying/videos?limit=120");
      _videos = data.results || [];
      renderVideoList();
    } catch (_) {
      const list = $("flytyingVideoList");
      if (list) list.innerHTML = '<li class="muted">Videos unavailable</li>';
    }
  }

  async function refreshStatus() {
    const el = $("flytyingStatus");
    if (!el) return;
    try {
      const st = await fetchJson("/api/flytying/status");
      const types = st.types || {};
      const typeBits = Object.entries(types)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([k, v]) => `${k} ${v}`)
        .join(" · ");
      const lib = st.library || {};
      const libBit = lib.recipe_files ? ` · library ${lib.recipe_files} docs` : "";
      const bfBit = st.blackfly_import ? "Blackfly ✓" : "Blackfly ✗";
      const semBit = st.semantic_usable ? "semantic" : "keyword only";
      const modeBit = st.index_note ? ` · ${st.index_note}` : "";
      const apiWarn =
        st.api_version && st.api_version < EXPECTED_API_VERSION
          ? " · restart ARIA for latest fly tying API"
          : "";
      const enable = st.blackfly_enablement || {};
      const hint = enable.hint || "";
      const srcLabel =
        st.recipe_source === "gold"
          ? `${st.gold_count || st.record_count || 0} gold`
          : `${st.record_count || 0} scraped`;
      el.textContent = st.ok
        ? `${srcLabel} · ${bfBit} · ${semBit} · index ${st.index_built ? "on" : "off"}${typeBits ? " · " + typeBits : ""}${libBit}${modeBit}${apiWarn}${hint ? " · ⚠ " + hint : ""}`
        : "Dataset not ready — set JARVIS_FLYTYING_ROOT in data/jarvis.env";
      const warnEl = $("flytyingDataWarn");
      if (warnEl) {
        const gold = Number(st.gold_count || 0);
        const scraped = Number(st.scraped_count || st.record_count || 0);
        const root = st.root || (st.blackfly_enablement || {}).project_root || "";
        const onStub = st.recipe_source !== "gold" && gold < 50 && scraped < 150;
        if (onStub) {
          warnEl.classList.remove("hidden");
          warnEl.innerHTML =
            `<strong>Limited pattern library (${scraped} scraped, no gold).</strong> ` +
            `Your full Blackfly library (~271+ recipes) lives at <code>/media/jeff/C/fly_fishing_project</code>. ` +
            `Mount that drive, add <code>export JARVIS_FLYTYING_ROOT="/media/jeff/C/fly_fishing_project"</code> to ` +
            `<code>data/jarvis.env</code>, restart ARIA, then click <strong>Rebuild</strong>.` +
            (root ? ` <span class="muted">(currently: ${esc(root)})</span>` : "");
        } else if (!st.ok) {
          warnEl.classList.remove("hidden");
          warnEl.textContent =
            "Fly tying data not found. Set JARVIS_FLYTYING_ROOT in data/jarvis.env to your Blackfly project folder.";
        } else {
          warnEl.classList.add("hidden");
          warnEl.textContent = "";
        }
      }
      const potd = $("flytyingPatternOfDay");
      const pod = st.pattern_of_the_day || {};
      if (potd && pod.name) {
        potd.innerHTML = `Pattern of the day: <button type="button" class="linkish flytying-potd-btn" data-id="${esc(pod.recipe_id || pod.name)}">${esc(pod.name)}</button>`;
        potd.querySelector(".flytying-potd-btn")?.addEventListener("click", (e) => {
          selectRecipe(e.target.dataset.id);
        });
      }
      const hatchEl = $("flytyingHatchBanner");
      const hatch = st.hatch || {};
      if (hatchEl && hatch.hatches?.length) {
        hatchEl.textContent = `Season (${hatch.region}, month ${hatch.month}): ${hatch.hatches.join(", ")} — ${hatch.notes || ""}`;
      }
    } catch (e) {
      el.textContent = `Unavailable — ${e.message}`;
    }
  }

  async function loadModelSelect() {
    const sel = $("flytyingModelSelect");
    if (!sel) return;
    try {
      const data = await fetchJson("/api/flytying/model");
      const current = data.saved || data.model || "qwen2.5:7b";
      const options = [
        ["qwen2.5:7b", "qwen2.5:7b (recipes — recommended)"],
        ["qwen2.5:14b", "qwen2.5:14b (design & new patterns)"],
        ["qwen2.5:3b", "qwen2.5:3b (fast)"],
      ];
      sel.innerHTML = options
        .map(([v, label]) => `<option value="${esc(v)}"${v === current ? " selected" : ""}>${esc(label)}</option>`)
        .join("");
      if (!options.some(([v]) => v === current) && current) {
        sel.innerHTML += `<option value="${esc(current)}" selected>${esc(current)}</option>`;
      }
    } catch (_) {
      sel.innerHTML = '<option value="qwen2.5:7b">qwen2.5:7b</option>';
    }
  }

  async function saveModel() {
    const sel = $("flytyingModelSelect");
    if (!sel) return;
    try {
      await fetchJson("/api/flytying/model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: sel.value }),
      });
    } catch (_) {}
  }

  function renderRecipeListItems() {
    const list = $("flytyingRecipeList");
    if (!list) return;
    list.innerHTML = _recipes
      .map((r) => {
        const id = r.recipe_id || r.name;
        const active = id === _selectedId ? " active" : "";
        const fav = isFavorite(id) ? " favorited" : "";
        const thumb = r.thumbnail ? imgTag(r.thumbnail, "flytying-recipe-thumb") : "";
        const qBadge = r.quality_score ? `<span class="flytying-q">${Math.round(r.quality_score)}</span>` : "";
        return `<li class="flytying-recipe-item"><button type="button" class="flytying-fav-btn${fav}" data-id="${esc(id)}" title="Favorite">★</button><label class="flytying-cmp-check"><input type="checkbox" class="flytying-cmp-input" data-id="${esc(id)}" /></label><button type="button" class="flytying-recipe-btn${active}" data-id="${esc(id)}" data-name="${esc(r.name)}">${thumb}<span><span>${esc(r.name)}</span><span class="flytying-recipe-meta">${esc(r.type || "")} · ${r.steps_count || 0} steps ${esc(r.hook_size || "")} ${qBadge}</span></span></button></li>`;
      })
      .join("");
    const hasMore = _recipes.length < _recipeTotal;
    if (hasMore) {
      list.insertAdjacentHTML(
        "beforeend",
        `<li class="flytying-recipe-more"><button type="button" id="flytyingLoadMoreBtn" class="ghost-btn small">Load more (${_recipes.length} / ${_recipeTotal})</button></li>`,
      );
      $("flytyingLoadMoreBtn")?.addEventListener("click", () => loadRecipes({ reset: false }));
    }
    list.querySelectorAll(".flytying-recipe-btn").forEach((btn) => {
      btn.addEventListener("click", () => selectRecipe(btn.dataset.id || btn.dataset.name));
    });
    list.querySelectorAll(".flytying-fav-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleFavorite(btn.dataset.id);
      });
    });
    list.querySelectorAll(".flytying-cmp-input").forEach((inp) => {
      inp.checked = _compare.has(inp.dataset.id);
      inp.addEventListener("change", () => {
        if (inp.checked) _compare.add(inp.dataset.id);
        else _compare.delete(inp.dataset.id);
        updateCompareToolbar();
      });
    });
  }

  async function loadRecipes(opts = {}) {
    const reset = opts.reset !== false;
    if (reset) _recipeOffset = 0;
    const q = ($("flytyingSearchInput")?.value || "").trim();
    const type = $("flytyingTypeFilter")?.value || "";
    const list = $("flytyingRecipeList");
    const hint = $("flytyingSearchHint");
    if (!list) return;
    if (reset) list.innerHTML = '<li class="muted">Loading…</li>';
    else $("flytyingLoadMoreBtn")?.replaceWith(Object.assign(document.createElement("li"), { className: "muted", textContent: "Loading more…" }));
    if (hint && reset) hint.textContent = q ? "Searching…" : "";
    try {
      const pageLimit = q ? 80 : RECIPE_PAGE;
      const data = await fetchRecipeRows(q, type, pageLimit, _recipeOffset);
      const rows = data.results || [];
      _recipeTotal = data.total ?? rows.length;
      _recipes = reset ? rows : _recipes.concat(rows);
      _recipeOffset = _recipes.length;
      _lastSearchMode = data.search_mode || "";
      if (!_recipes.length) {
        const filterNote = type ? ` No matches for type “${type}” — try All types.` : "";
        const restartNote =
          q && !type && !data.search_mode ? " Restart ARIA if this persists (fly tying API may be outdated)." : "";
        list.innerHTML = `<li class="muted">No patterns found.${filterNote}${restartNote}</li>`;
        if (hint) hint.textContent = q ? `0 results for “${q}”` : "";
        return;
      }
      const modeNote = _lastSearchMode ? ` · ${searchModeLabel(_lastSearchMode)}` : "";
      if (hint) {
        hint.textContent = q
          ? `${_recipeTotal} result${_recipeTotal === 1 ? "" : "s"} for “${q}”${type ? ` (${type})` : ""}${modeNote}`
          : `${_recipeTotal} patterns · showing ${_recipes.length}`;
      }
      renderRecipeListItems();
      if (q && _recipes[0]) {
        selectRecipe(_recipes[0].recipe_id || _recipes[0].name);
      } else if (!_selectedId) {
        const detail = $("flytyingRecipeDetail");
        if (detail) detail.innerHTML = '<p class="muted">Select a pattern to view materials and steps.</p>';
      }
    } catch (e) {
      list.innerHTML = `<li class="muted">${esc(e.message)}</li>`;
    }
  }

  function recipeImagesHtml(data) {
    const imgs = data.images || [];
    const urls = imgs.length
      ? imgs
      : (data.image_urls || []).map((url) => ({ url, kind: "remote", label: "" }));
    const filtered = urls.filter((img) => {
      const url = String(img.url || img || "");
      return url.startsWith("/api/flytying/images/") || !url.includes("midcurrent.com/gear/");
    });
    if (!filtered.length) return '<p class="muted">No images for this pattern.</p>';
    return `<div class="flytying-image-grid">${filtered
      .slice(0, 8)
      .map((img) => {
        const url = img.url || img;
        const href = String(url).startsWith("/") ? url : url;
        return `<a href="${esc(href)}" target="_blank" rel="noopener" class="flytying-img-link">${imgTag(url, "", img.label || "")}</a>`;
      })
      .join("")}</div>`;
  }

  async function selectRecipe(idOrName, opts = {}) {
    _selectedId = idOrName || "";
    if (!opts.preserveStepMode) {
      _stepMode = false;
      _stepIdx = 0;
    }
    document.querySelectorAll(".flytying-recipe-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.id === _selectedId || b.dataset.name === _selectedId);
    });
    const detail = $("flytyingRecipeDetail");
    if (!detail) return;
    detail.innerHTML = '<p class="muted">Loading recipe…</p>';
    try {
      const data = await fetchJson(`/api/flytying/recipes/${encodeURIComponent(idOrName)}`);
      _currentRecipe = data;
      updateCompareToolbar();
      const subs = data.substitutions || {};
      const subHtml = Object.keys(subs).length
        ? `<section><h4>Substitutions</h4><ul class="flytying-steps">${Object.entries(subs)
            .map(([m, alts]) => `<li><strong>${esc(m)}</strong>: ${esc(alts.join(", "))}</li>`)
            .join("")}</ul></section>`
        : "";
      const similar = (data.similar || [])
        .map(
          (s) =>
            `<button type="button" class="ghost-btn small flytying-similar-btn" data-id="${esc(s.recipe_id || s.name)}">${esc(s.name)}</button>`
        )
        .join(" ");
      const mats = (data.materials || []).map((m) => `<li>${esc(m)}</li>`).join("");
      const videos = data.videos || [];
      const videoBtns = videos.length
        ? `<div class="flytying-recipe-videos">${videos
            .map((v, i) => {
              const label = providerLabel(v);
              return `<button type="button" class="ghost-btn small flytying-play-video-btn" data-vidx="${i}">Play ${esc(label)}</button>`;
            })
            .join(" ")}</div>`
        : "";
      const favOn = isFavorite(data.recipe_id || data.name);
      detail.innerHTML = `
        <header class="flytying-detail-head">
          <h3>${esc(data.name)}</h3>
          <p class="muted">${esc(data.type || "")}${data.hook ? " · hook " + esc(data.hook) : ""}${data.quality_score ? " · Q" + esc(String(Math.round(data.quality_score))) : ""}</p>
          <div class="flytying-recipe-actions">
            <button type="button" class="ghost-btn small" id="flytyingFavRecipeBtn">${favOn ? "★ Favorited" : "☆ Favorite"}</button>
            <button type="button" class="ghost-btn small" id="flytyingQueueRecipeBtn">+ Queue</button>
            <button type="button" class="ghost-btn small" id="flytyingStepModeBtn">Step mode</button>
          </div>
          ${data.source_url ? `<p class="flytying-source"><a href="${esc(data.source_url)}" target="_blank" rel="noopener">Source</a></p>` : ""}
          ${videoBtns}
        </header>
        ${recipeImagesHtml(data)}
        <section><h4>Materials</h4><ul class="flytying-steps">${mats || "<li class='muted'>—</li>"}</ul></section>
        ${subHtml}
        <section id="flytyingStepsSection"><h4>Instructions</h4><ol class="flytying-steps"><li class="muted">…</li></ol></section>
        ${similar ? `<section><h4>Similar</h4><div class="flytying-similar-row">${similar}</div></section>` : ""}
        <section><h4>Your notes</h4><textarea id="flytyingNoteInput" rows="2" placeholder="Bench notes…"></textarea><button type="button" class="ghost-btn small" id="flytyingSaveNoteBtn">Save note</button></section>
        <button type="button" class="ghost-btn small" id="flytyingAskRecipeBtn">Ask ARIA about this pattern</button>
      `;
      $("flytyingFavRecipeBtn")?.addEventListener("click", () => toggleFavorite(data.recipe_id || data.name, data.name));
      $("flytyingQueueRecipeBtn")?.addEventListener("click", () => addToQueue(data.recipe_id || data.name, data.name));
      $("flytyingStepModeBtn")?.addEventListener("click", () => {
        if (!(data.steps || []).length) return;
        _stepMode = !_stepMode;
        if (_stepMode) _stepIdx = 0;
        renderInstructions(data);
      });
      renderInstructions(data);
      $("flytyingSaveNoteBtn")?.addEventListener("click", async () => {
        const note = ($("flytyingNoteInput")?.value || "").trim();
        await fetchJson("/api/flytying/notes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ recipe_id: data.recipe_id || data.name, note }),
        });
      });
      const noteEl = $("flytyingNoteInput");
      if (noteEl) noteEl.value = data.user_note || "";
      detail.querySelectorAll(".flytying-similar-btn").forEach((btn) => {
        btn.addEventListener("click", () => selectRecipe(btn.dataset.id));
      });
      detail.querySelectorAll(".flytying-play-video-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const idx = parseInt(btn.dataset.vidx || "0", 10);
          const v = videos[idx];
          if (v) showVideo({ ...v, recipe_name: data.name, recipe_id: data.recipe_id });
        });
      });
      if (!opts.skipVideo && videos.length) {
        showVideo({ ...videos[0], recipe_name: data.name, recipe_id: data.recipe_id });
      }
      $("flytyingAskRecipeBtn")?.addEventListener("click", () => {
        const input = $("flytyingChatInput");
        if (input) {
          input.value = `Walk me through tying the ${data.name} step by step.`;
          input.focus();
        }
      });
    } catch (e) {
      detail.innerHTML = `<p class="muted">${esc(e.message)}</p>`;
    }
  }

  async function sendChat() {
    if (_streaming) return;
    const input = $("flytyingChatInput");
    const text = (input?.value || "").trim();
    if (!text) return;
    const model = $("flytyingModelSelect")?.value || "";
    input.value = "";
    _chat.push({ role: "user", content: text });
    _chat.push({ role: "assistant", content: "", streaming: true });
    saveChat();
    renderChat();
    const status = $("flytyingChatStatus");
    if (status) status.textContent = "Thinking…";
    _streaming = true;
    $("flytyingCancelChatBtn")?.classList.remove("hidden");
    _chatAbort = new AbortController();

    let answer = "";
    let modelUsed = "";
    try {
      const res = await fetch("/api/flytying/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: _chat.filter((m) => !m.streaming), model, stream: true }),
        signal: _chatAbort.signal,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || res.statusText);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          let event;
          try {
            event = JSON.parse(line.slice(5).trim());
          } catch (_) {
            continue;
          }
          if (event.type === "token" && event.content) {
            answer += event.content;
            updateStreamingBubble(answer);
          } else if (event.type === "recipes" && event.recipes?.length) {
            const first = event.recipes[0];
            if (first) selectRecipe(recipeKey(first), { skipVideo: true });
          } else if (event.type === "done") {
            if (!answer) answer = event.answer || "";
            modelUsed = event.model || "";
            if (!event.ok && event.message) throw new Error(event.message);
            if (event.recipes?.length && !answer) {
              const first = event.recipes[0];
              if (first) selectRecipe(recipeKey(first), { skipVideo: true });
            }
          }
        }
      }
      _chat = _chat.filter((m) => !m.streaming);
      _chat.push({ role: "assistant", content: answer || "(no response)" });
      saveChat();
      renderChat();
      if (status) status.textContent = modelUsed ? `Model: ${modelUsed}` : "";
    } catch (e) {
      _chat = _chat.filter((m) => !m.streaming);
      const msg = e.name === "AbortError" ? "Stopped." : `Error: ${e.message}`;
      _chat.push({ role: "assistant", content: msg });
      saveChat();
      renderChat();
      if (status) status.textContent = e.name === "AbortError" ? "" : "";
    } finally {
      _streaming = false;
      _chatAbort = null;
      $("flytyingCancelChatBtn")?.classList.add("hidden");
    }
  }

  function cancelChat() {
    if (_chatAbort) _chatAbort.abort();
  }

  async function suggestFromMaterials() {
    const raw = materialsTextForSuggest();
    if (!raw) {
      const status = $("flytyingChatStatus");
      if (status) status.textContent = "Add materials first (list above or inventory table)";
      $("flytyingMaterialsSummary")?.focus();
      return;
    }
    const model = $("flytyingModelSelect")?.value || "";
    const status = $("flytyingChatStatus");
    const explain = $("flytyingMaterialsExplain")?.checked;
    if (status) status.textContent = explain ? "Matching materials (with explanation)…" : "Matching materials…";
    try {
      const data = await fetchJson("/api/flytying/from-materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ materials_text: raw, model, explain: !!explain }),
      });
      const matches = (data.matches || [])
        .slice(0, 5)
        .map((m) => `• **${m.name}** (${m.type || "?"}) — matched: ${(m.matched_materials || []).join(", ")}`)
        .join("\n");
      const userMsg = `Materials I have: ${raw}`;
      const assistantMsg = `${data.answer || ""}${matches ? "\n\n**Library matches:**\n" + matches : ""}`.trim();
      _chat.push({ role: "user", content: userMsg });
      _chat.push({ role: "assistant", content: assistantMsg });
      saveChat();
      renderChat();
      if (status) status.textContent = data.model ? `Model: ${data.model}` : "";
      if (data.matches?.[0]) selectRecipe(recipeKey(data.matches[0]));
    } catch (e) {
      if (status) status.textContent = e.message;
    }
  }

  function clearChat() {
    _chat = [];
    saveChat();
    renderChat();
    const status = $("flytyingChatStatus");
    if (status) status.textContent = "";
  }

  async function addCustomVideo() {
    const input = $("flytyingCustomVideoUrl");
    const url = (input?.value || "").trim();
    if (!url) return;
    const status = $("flytyingChatStatus");
    if (status) status.textContent = "Resolving video…";
    try {
      const data = await fetchJson("/api/flytying/videos/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (input) input.value = "";
      await loadVideos();
      const first = (data.videos || [])[0];
      if (first) showVideo(first);
      if (status) status.textContent = data.message || "Video added";
    } catch (e) {
      if (status) status.textContent = e.message;
    }
  }


  async function loadSeasonal() {
    try {
      const data = await fetchJson("/api/flytying/seasonal?limit=12");
      _recipes = data.results || [];
      _lastSearchMode = "seasonal";
      const list = $("flytyingRecipeList");
      const hint = $("flytyingSearchHint");
      if (hint) hint.textContent = `Seasonal picks (${(data.hatch || {}).month || "?"})`;
      if (!list) return;
      if (!_recipes.length) {
        list.innerHTML = '<li class="muted">No seasonal matches</li>';
        return;
      }
      list.innerHTML = _recipes
        .map((r) => {
          const id = r.recipe_id || r.name;
          return `<li><button type="button" class="flytying-recipe-btn" data-id="${esc(id)}">${esc(r.name)}<span class="flytying-recipe-meta">${esc(r.type || "")}</span></button></li>`;
        })
        .join("");
      list.querySelectorAll(".flytying-recipe-btn").forEach((btn) => {
        btn.addEventListener("click", () => selectRecipe(btn.dataset.id));
      });
      if (_recipes[0]) selectRecipe(_recipes[0].recipe_id || _recipes[0].name);
    } catch (e) {
      $("flytyingSearchHint").textContent = e.message;
    }
  }

  async function showLibraryHealth() {
    try {
      const h = await fetchJson("/api/flytying/health");
      alert(
        `Library health\n` +
          `Total: ${h.total}\n` +
          `With images: ${h.with_images} (${h.image_pct}%)\n` +
          `With videos: ${h.with_videos} (${h.video_pct}%)\n` +
          `Avg quality: ${h.avg_quality}\n` +
          `Duplicate name groups: ${h.duplicate_name_groups}\n` +
          `Aliases loaded: ${h.alias_count}`
      );
    } catch (e) {
      alert(e.message);
    }
  }

  async function rebuildGold() {
    if (!confirm("Rebuild gold dataset and semantic index? This may take a while.")) return;
    const status = $("flytyingChatStatus");
    if (status) status.textContent = "Rebuilding gold…";
    try {
      await fetchJson("/api/flytying/gold/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ build_index: true }),
      });
      if (status) status.textContent = "Gold rebuild complete";
      refreshStatus();
      loadRecipes();
    } catch (e) {
      if (status) status.textContent = e.message;
    }
  }

  async function exportCurrentRecipe() {
    if (!_currentRecipe) return;
    const id = _currentRecipe.recipe_id || _currentRecipe.name;
    const data = await fetchJson(`/api/flytying/recipes/${encodeURIComponent(id)}/export?format=markdown`);
    const blob = new Blob([data.content || ""], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${(_currentRecipe.name || "pattern").replace(/\W+/g, "-")}.md`;
    a.click();
  }

  function printCurrentRecipe() {
    if (!_currentRecipe) return;
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(`<pre>${esc(_currentRecipe.formatted || _currentRecipe.name)}</pre>`);
    w.document.close();
    w.print();
  }

  async function runCompare() {
    const ids = [..._compare];
    if (ids.length < 2) return;
    const panel = $("flytyingComparePanel");
    if (!panel) return;
    panel.classList.remove("hidden");
    panel.innerHTML = '<p class="muted">Comparing…</p>';
    try {
      const data = await fetchJson("/api/flytying/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_ids: ids }),
      });
      panel.innerHTML = `<div class="flytying-compare-md">${fmt(data.markdown || "")}</div><button type="button" class="ghost-btn small" id="flytyingCompareClose">Close</button>`;
      $("flytyingCompareClose")?.addEventListener("click", () => {
        panel.classList.add("hidden");
      });
    } catch (e) {
      panel.innerHTML = `<p class="muted">${esc(e.message)}</p>`;
    }
  }

  function clearRecipeFilters() {
    const input = $("flytyingSearchInput");
    const type = $("flytyingTypeFilter");
    if (input) input.value = "";
    if (type) type.value = "";
    $("flytyingFavoritesOnly") && ($("flytyingFavoritesOnly").checked = false);
    $("flytyingMinQuality") && ($("flytyingMinQuality").value = "");
    if (_searchTimer) clearTimeout(_searchTimer);
    loadRecipes();
  }

  function toggleVideosPanel() {
    const panel = $("flytyingVideosPanel");
    const btn = $("flytyingVideosToggle");
    if (!panel || !btn) return;
    const collapsed = panel.classList.toggle("collapsed");
    btn.textContent = collapsed ? "Show" : "Hide";
    btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
  }

  let _searchTimer = null;

  function scheduleRecipeSearch() {
    if (_searchTimer) clearTimeout(_searchTimer);
    _searchTimer = setTimeout(() => loadRecipes(), 280);
  }

  function bindOnce() {
    if (_bound) return;
    _bound = true;
    $("flytyingClearFiltersBtn")?.addEventListener("click", clearRecipeFilters);
    $("flytyingVideosToggle")?.addEventListener("click", toggleVideosPanel);
    $("flytyingCancelChatBtn")?.addEventListener("click", cancelChat);
    $("flytyingSearchBtn")?.addEventListener("click", loadRecipes);
    $("flytyingSearchInput")?.addEventListener("input", scheduleRecipeSearch);
    $("flytyingSearchInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        if (_searchTimer) clearTimeout(_searchTimer);
        loadRecipes();
      }
    });
    $("flytyingTypeFilter")?.addEventListener("change", loadRecipes);
    $("flytyingVideoSearch")?.addEventListener("input", renderVideoList);
    $("flytyingAddVideoBtn")?.addEventListener("click", addCustomVideo);
    $("flytyingCustomVideoUrl")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        addCustomVideo();
      }
    });
    $("flytyingChatForm")?.addEventListener("submit", (e) => {
      e.preventDefault();
      sendChat();
    });
    $("flytyingMaterialsBtn")?.addEventListener("click", suggestFromMaterials);
    $("flytyingSaveMaterialsBtn")?.addEventListener("click", saveMaterialsFromSummary);
    $("flytyingManualAddBtn")?.addEventListener("click", addManualItem);
    $("flytyingBulkAddBtn")?.addEventListener("click", addBulkLines);
    document.querySelectorAll(".flytying-sort-btn").forEach((btn) => {
      btn.addEventListener("click", () => setInventorySort(btn.dataset.col || "what"));
    });
    ["flytyingInvWhat", "flytyingInvColor", "flytyingInvSize", "flytyingInvBrand", "flytyingInvNotes"].forEach((id) => {
      $(id)?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          addManualItem();
        }
      });
    });
    $("flytyingLabelBtn")?.addEventListener("click", printMaterialLabel);
    $("flytyingCameraScanBtn")?.addEventListener("click", startCameraScan);
    $("flytyingScanModalClose")?.addEventListener("click", stopCameraScan);
    $("flytyingScanPhotoBtn")?.addEventListener("click", () => $("flytyingScanPhotoFile")?.click());
    $("flytyingScanPhotoFile")?.addEventListener("change", (e) => {
      const f = e.target.files && e.target.files[0];
      if (f) scanFromPhoto(f);
      e.target.value = "";
    });
    $("flytyingScanInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        processBarcode(e.target.value, { force: true });
      }
    });
    $("flytyingNameBarcodeSave")?.addEventListener("click", savePendingBarcode);
    $("flytyingNameBarcodeCancel")?.addEventListener("click", closeNameBarcodeModal);
    $("flytyingNameBarcodeName")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        savePendingBarcode();
      }
    });
    $("flytyingFavoritesOnly")?.addEventListener("change", loadRecipes);
    $("flytyingMinQuality")?.addEventListener("change", loadRecipes);
    $("flytyingSeasonalBtn")?.addEventListener("click", loadSeasonal);
    $("flytyingHealthBtn")?.addEventListener("click", showLibraryHealth);
    $("flytyingRebuildBtn")?.addEventListener("click", rebuildGold);
    $("flytyingCompareBtn")?.addEventListener("click", runCompare);
    $("flytyingExportBtn")?.addEventListener("click", exportCurrentRecipe);
    $("flytyingPrintBtn")?.addEventListener("click", printCurrentRecipe);
    $("flytyingClearChatBtn")?.addEventListener("click", clearChat);
    $("flytyingModelSelect")?.addEventListener("change", saveModel);
    $("flytyingRefreshBtn")?.addEventListener("click", () => {
      _recipeCache.clear();
      refreshStatus();
      loadRecipes();
      loadVideos();
    });
  }

  async function initFlytying() {
    bindOnce();
    loadChat();
    renderChat();
    await loadUserState();
    await Promise.all([refreshStatus(), loadModelSelect(), loadRecipes(), loadVideos()]);
    const hash = (location.hash || "").match(/flytying\/([^/?]+)/);
    if (hash && hash[1]) selectRecipe(decodeURIComponent(hash[1]));
  }

  window.initFlytying = initFlytying;
  window.selectFlytyingPattern = function (idOrName) {
    if (window.switchToView) window.switchToView("flytying");
    else document.querySelector('.view-tab[data-view="flytying"]')?.click();
    setTimeout(() => selectRecipe(idOrName), 300);
  };
})();
