/** P4 webcam preview + gesture overlay (MediaPipe Hands in Chrome / WebEngine) */
(function () {
  const $ = (id) => document.getElementById(id);
  const DEFAULT_THRESHOLDS = { pinchMax: 0.05, palmMin: 0.12 };
  let initialized = false;
  let stream = null;
  let mode = "off";
  let serverEnabled = false;
  let cpuThrottle = false;
  let frameSkip = 0;
  let calibrating = false;
  let lastGesture = "";
  let gestureCooldown = 0;
  let wasPinching = false;
  let thresholds = { ...DEFAULT_THRESHOLDS };
  let calibSamples = { pinch: [], fist: [], palm: [] };
  let savedCalibration = null;

  function applyCalibration(cal) {
    if (!cal || typeof cal !== "object") return;
    if (typeof cal.pinchMax === "number" && cal.pinchMax > 0) thresholds.pinchMax = cal.pinchMax;
    if (typeof cal.palmMin === "number" && cal.palmMin > 0) thresholds.palmMin = cal.palmMin;
  }

  function calibCaptured() {
    return {
      pinch: calibSamples.pinch.length > 0,
      fist: calibSamples.fist.length > 0,
      palm: calibSamples.palm.length > 0,
    };
  }

  function formatCalibStatus(cal) {
    if (!cal || typeof cal !== "object") return "";
    const caps = cal.captured
      ? Object.entries(cal.captured)
          .filter(([, v]) => v)
          .map(([k]) => k)
      : [];
    if (caps.length) return `Calibrated: ${caps.join(", ")}`;
    if (cal.at) return `Last calibration: ${new Date(cal.at).toLocaleString()}`;
    return "";
  }

  function updateCalibSteps(active) {
    const steps = $("gestureCalibSteps");
    if (!steps) return;
    if (!active) {
      steps.textContent = formatCalibStatus(savedCalibration);
      return;
    }
    const need = ["pinch", "fist", "palm"];
    const done = need.filter((k) => calibSamples[k].length > 0);
    const pending = need.filter((k) => !done.includes(k));
    steps.textContent = done.length
      ? `Captured: ${done.join(", ")}${pending.length ? ` — still need: ${pending.join(", ")}` : ""}`
      : "Perform pinch, fist, and palm in front of the camera…";
  }

  function buildCalibrationPayload() {
    const captured = calibCaptured();
    const pinchMax = captured.pinch
      ? Math.min(0.12, Math.max(0.03, Math.max(...calibSamples.pinch) * 1.15))
      : thresholds.pinchMax;
    const palmMin = captured.palm
      ? Math.max(0.06, Math.min(0.2, Math.min(...calibSamples.palm) * 0.85))
      : thresholds.palmMin;
    return { pinchMax, palmMin, captured, at: Date.now() };
  }

  function isFingerFolded(lm, tipIdx, mcpIdx) {
    const tip = lm[tipIdx];
    const mcp = lm[mcpIdx];
    const wrist = lm[0];
    const distTip = Math.hypot(tip.x - wrist.x, tip.y - wrist.y);
    const distMcp = Math.hypot(mcp.x - wrist.x, mcp.y - wrist.y);
    return distTip < distMcp;
  }

  function detectGestures(lm) {
    const thumb = lm[4];
    const index = lm[8];
    const pinchDist = Math.hypot(thumb.x - index.x, thumb.y - index.y);
    const isPinch = pinchDist < thresholds.pinchMax;
    const isFist =
      isFingerFolded(lm, 8, 5) &&
      isFingerFolded(lm, 12, 9) &&
      isFingerFolded(lm, 16, 13) &&
      isFingerFolded(lm, 20, 17);
    const isPalm = lm[9].y < lm[0].y && pinchDist > thresholds.palmMin && !isFist;
    return { isPinch, isFist, isPalm, index, wrist: lm[0], pinchDist };
  }

  function recordCalibSample(g) {
    if (g.isPinch) calibSamples.pinch.push(g.pinchDist);
    if (g.isFist) calibSamples.fist.push(1);
    if (g.isPalm) calibSamples.palm.push(g.pinchDist);
    updateCalibSteps(true);
  }

  async function refreshGpuMode() {
    try {
      const r = await fetch("/api/environment");
      const d = await r.json();
      const free = d?.gpu?.free_vram_mb;
      cpuThrottle = mode === "cpu" || (typeof free === "number" && free < 1200);
      frameSkip = cpuThrottle ? 4 : 0;
    } catch (_) {
      cpuThrottle = mode === "cpu";
      frameSkip = cpuThrottle ? 4 : 0;
    }
  }

  async function loadSettings() {
    try {
      const r = await fetch("/api/security/gestures/status");
      const d = await r.json();
      mode = d.mode || "off";
      serverEnabled = Boolean(d.gestures_enabled);
      applyCalibration(d.calibration);
      savedCalibration = d.calibration || null;
      if ($("gestureModeSelect")) $("gestureModeSelect").value = mode;
      if (!calibrating) updateCalibSteps(false);
      const hint = $("presenceStatus");
      if (hint && serverEnabled && mode === "off") {
        hint.textContent = "Gestures enabled — pick Control mode to move floating panels";
      }
    } catch (_) {
      try {
        const r = await fetch("/api/security/gestures/settings");
        const d = await r.json();
        mode = d.mode || "off";
        applyCalibration(d.calibration);
      savedCalibration = d.calibration || null;
        if ($("gestureModeSelect")) $("gestureModeSelect").value = mode;
        if (!calibrating) updateCalibSteps(false);
      } catch (_2) {}
    }
    refreshGpuMode();
  }

  async function saveSettings() {
    const m = $("gestureModeSelect")?.value || "off";
    await fetch("/api/security/gestures/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: m }),
    });
    mode = m;
    refreshGpuMode();
  }

  function cameraErrorHint(e) {
    const name = e?.name || "";
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      return "Camera blocked — allow camera in your desktop shell or browser site settings, then retry.";
    }
    if (name === "NotFoundError" || name === "DevicesNotFoundError") {
      return "No camera found — plug in a webcam or check JARVIS_CAMERA_DEVICE for server capture.";
    }
    if (name === "NotReadableError" || name === "TrackStartError") {
      return "Camera busy — stop another app using the webcam, or start Presence camera first, then retry.";
    }
    return e?.message || String(e);
  }

  window.jarvisCameraErrorHint = cameraErrorHint;

  async function releaseOtherCapture() {
    try {
      stopCamera();
      await window.jarvisEndCloudLive?.();
    } catch (_) {}
  }

  window.jarvisReleaseOtherCapture = releaseOtherCapture;

  async function startCamera() {
    const video = $("presenceVideo");
    if (!video) return;
    if (stream) {
      if ($("presenceStatus")) $("presenceStatus").textContent = "Camera already on";
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      if ($("presenceStatus")) {
        $("presenceStatus").textContent = "Camera API unavailable in this shell — restart ARIA window after update.";
      }
      return;
    }
    await releaseOtherCapture();
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      video.srcObject = stream;
      await video.play();
      if ($("presenceStatus")) $("presenceStatus").textContent = "Camera on — fist drag · pinch click";
    } catch (e) {
      if ($("presenceStatus")) $("presenceStatus").textContent = `Camera: ${cameraErrorHint(e)}`;
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    const video = $("presenceVideo");
    if (video) video.srcObject = null;
    if ($("presenceStatus")) $("presenceStatus").textContent = "Camera off";
    window.jarvisGestureCursor?.(0, 0, false);
  }

  function onGestureName(name) {
    const now = Date.now();
    if (now < gestureCooldown) return;
    gestureCooldown = now + 500;
    const el = $("gestureStatus");
    if (el) el.textContent = `Gesture: ${name}`;
    lastGesture = name;
    if (calibrating) return;
    if (name === "palm" && mode === "control") {
      window.jarvisGestureRelease?.();
    }
  }

  function gestureTrackingActive() {
    return calibrating || mode !== "off";
  }

  function initGestureLoop() {
    const video = $("presenceVideo");
    const canvas = $("presenceCanvas");
    if (!video || !canvas) return;
    if (typeof window.Hands === "undefined") {
      if ($("presenceStatus")) {
        $("presenceStatus").textContent = "Gestures unavailable — MediaPipe failed to load (check CDN or try offline)";
      }
      return;
    }
    const ctx = canvas.getContext("2d");
    const hands = new Hands({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}` });
    hands.setOptions({ maxNumHands: 1, modelComplexity: 0, minDetectionConfidence: 0.6, minTrackingConfidence: 0.5 });
    hands.onResults((results) => {
      if (!ctx) return;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (!results.multiHandLandmarks?.length) {
        wasPinching = false;
        if (!calibrating) {
          window.jarvisFloatingPanels?.gestureFrame({
            indexX: 0.5,
            indexY: 0.5,
            wristX: 0.5,
            wristY: 0.5,
            isFist: false,
            mode,
          });
        }
        return;
      }
      const lm = results.multiHandLandmarks[0];
      ctx.fillStyle = "#4ade80";
      lm.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x * canvas.width, p.y * canvas.height, 4, 0, Math.PI * 2);
        ctx.fill();
      });
      const g = detectGestures(lm);
      if (calibrating) {
        recordCalibSample(g);
      }
      const controlMode = calibrating ? "preview" : mode;
      if (g.isPinch && !wasPinching) {
        onGestureName("pinch");
        if (!calibrating) window.jarvisFloatingPanels?.gesturePinchClick(g.index.x, g.index.y, controlMode);
      }
      wasPinching = g.isPinch;
      if (g.isFist) onGestureName("fist");
      if (g.isPalm) onGestureName("palm");
      if (!calibrating) {
        window.jarvisFloatingPanels?.gestureFrame({
          indexX: g.index.x,
          indexY: g.index.y,
          wristX: g.wrist.x,
          wristY: g.wrist.y,
          isFist: g.isFist,
          mode: controlMode,
        });
      }
    });
    let tickCount = 0;
    async function tick() {
      tickCount += 1;
      if (video.readyState >= 2 && gestureTrackingActive() && (!cpuThrottle || tickCount % (frameSkip + 1) === 0)) {
        await hands.send({ image: video });
      }
      requestAnimationFrame(tick);
    }
    tick();
  }

  function initPresence() {
    if (initialized) {
      loadSettings();
      return;
    }
    initialized = true;
    loadSettings();
    $("presenceStartBtn")?.addEventListener("click", startCamera);
    $("presenceStopBtn")?.addEventListener("click", stopCamera);
    $("gestureModeSelect")?.addEventListener("change", saveSettings);
    $("gestureCalibBtn")?.addEventListener("click", async () => {
      calibrating = !calibrating;
      if (calibrating) {
        calibSamples = { pinch: [], fist: [], palm: [] };
        updateCalibSteps(true);
        if (!$("presenceVideo")?.srcObject) {
          await startCamera();
        }
        return;
      }
      const calibration = buildCalibrationPayload();
      applyCalibration(calibration);
      savedCalibration = calibration;
      const captured = Object.values(calibration.captured).filter(Boolean).length;
      const steps = $("gestureCalibSteps");
      if (steps) {
        steps.textContent = captured
          ? `Calibration saved (${Object.entries(calibration.captured)
              .filter(([, v]) => v)
              .map(([k]) => k)
              .join(", ")})`
          : "Calibration saved — no gestures captured; using defaults";
      }
      await fetch("/api/security/gestures/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, calibration }),
      });
    });
    setInterval(refreshGpuMode, 20000);
    $("faceEnrollBtn")?.addEventListener("click", async () => {
      const video = $("presenceVideo");
      if (!video?.videoWidth) {
        if ($("presenceStatus")) $("presenceStatus").textContent = "Start camera first — enroll needs a live frame";
        return;
      }
      const c = document.createElement("canvas");
      c.width = video.videoWidth;
      c.height = video.videoHeight;
      c.getContext("2d").drawImage(video, 0, 0);
      const image = c.toDataURL("image/jpeg", 0.85);
      const r = await fetch("/api/security/face/enroll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image }),
      });
      const d = await r.json();
      if ($("presenceStatus")) {
        $("presenceStatus").textContent = d.ok ? "Face enrolled" : d.error || "Enroll failed";
      }
    });
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js";
    s.onload = initGestureLoop;
    s.onerror = () => {
      if ($("presenceStatus")) {
        $("presenceStatus").textContent = "Gestures unavailable — MediaPipe failed to load (check CDN or try offline)";
      }
    };
    document.head.appendChild(s);
  }

  window.initPresence = initPresence;
  document.addEventListener("DOMContentLoaded", initPresence);
})();
