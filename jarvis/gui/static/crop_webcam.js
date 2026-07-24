/** Crop modal + webcam capture — extracted from app.js. */
(function () {
  function attach() {
    return window.jarvisAttach || {};
  }

  async function openCropModal() {
    const a = attach();
    const pendingFile = a.pendingFile;
    if (!pendingFile || typeof a.isVisionAttachment !== "function" || !a.isVisionAttachment(pendingFile)) {
      return;
    }
    const modal = document.getElementById("cropModal");
    const canvas = document.getElementById("cropCanvas");
    if (!modal || !canvas) return;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.onload = () => {
      const maxW = 640;
      const scale = Math.min(1, maxW / img.width);
      canvas.width = Math.round(img.width * scale);
      canvas.height = Math.round(img.height * scale);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      modal.classList.remove("hidden");
      let start = null;
      let rect = null;
      const redraw = () => {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        if (rect) {
          ctx.strokeStyle = "#d4a054";
          ctx.lineWidth = 2;
          ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);
        }
      };
      canvas.onmousedown = (ev) => {
        start = { x: ev.offsetX, y: ev.offsetY };
        rect = null;
      };
      canvas.onmousemove = (ev) => {
        if (!start) return;
        rect = {
          x: Math.min(start.x, ev.offsetX),
          y: Math.min(start.y, ev.offsetY),
          w: Math.abs(ev.offsetX - start.x),
          h: Math.abs(ev.offsetY - start.y),
        };
        redraw();
      };
      canvas.onmouseup = () => {
        start = null;
      };
      document.getElementById("cropApplyBtn").onclick = () => {
        if (rect && rect.w > 4 && rect.h > 4) {
          a.pendingCrop = {
            x: rect.x / canvas.width,
            y: rect.y / canvas.height,
            w: rect.w / canvas.width,
            h: rect.h / canvas.height,
          };
        }
        modal.classList.add("hidden");
        a.updateAttachmentPreview?.();
        window.showAriaToast?.("Crop region set", "ok", 2000);
      };
      document.getElementById("cropCancelBtn").onclick = () => modal.classList.add("hidden");
    };
    img.onerror = () => {
      window.showAriaToast?.("Could not load image for crop", "err", 4000);
    };
    img.src = URL.createObjectURL(pendingFile);
  }

  async function captureWebcamAttachment() {
    const a = attach();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      const video = document.createElement("video");
      video.srcObject = stream;
      await video.play();
      await new Promise((r) => setTimeout(r, 400));
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      canvas.getContext("2d").drawImage(video, 0, 0);
      stream.getTracks().forEach((t) => t.stop());
      canvas.toBlob((blob) => {
        if (!blob) {
          window.showAriaToast?.("Webcam capture failed", "err", 4000);
          return;
        }
        a.assignAttachment?.(new File([blob], `webcam-${Date.now()}.jpg`, { type: "image/jpeg" }));
        window.showAriaToast?.("Webcam photo attached", "ok", 2500);
      }, "image/jpeg", 0.92);
    } catch (e) {
      const hint = window.jarvisCameraErrorHint?.(e) || e.message || String(e);
      window.showError?.(`Webcam unavailable: ${hint}`);
      window.showAriaToast?.(`Webcam unavailable: ${hint}`, "err", 5000);
    }
  }

  window.openCropModal = openCropModal;
  window.captureWebcamAttachment = captureWebcamAttachment;

  function bindWebcam() {
    document.getElementById("webcamBtn")?.addEventListener("click", () => {
      captureWebcamAttachment();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindWebcam);
  } else {
    bindWebcam();
  }
})();
