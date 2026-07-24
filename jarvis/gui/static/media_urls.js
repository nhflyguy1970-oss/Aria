/** Media URL helpers — extracted from app.js. Load after lan_access.js, before app.js. */
(function () {
  function getStoredApiKey() {
    return typeof window.getStoredApiKey === "function"
      ? window.getStoredApiKey()
      : (sessionStorage.getItem("jarvis_api_key") || "");
  }

  function apiAuthUrl(url) {
    if (!url) return "";
    const key = getStoredApiKey();
    if (!key) return url;
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}api_key=${encodeURIComponent(key)}`;
  }

  function isSameMachineHost() {
    if (typeof window.isSameMachineHost === "function") return window.isSameMachineHost();
    const host = location.hostname;
    return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
  }

  function mediaNeedsApiKey() {
    if (typeof window.mediaNeedsApiKey === "function") return window.mediaNeedsApiKey();
    return false;
  }

  async function fetchMediaBlobUrl(url) {
    const res = await fetch(url);
    if (!res.ok) return { ok: false, status: res.status };
    const blob = await res.blob();
    const type = (blob.type || "").toLowerCase();
    if (type.includes("json") || type.includes("text")) {
      return { ok: false, status: res.status || 415 };
    }
    const videoBlob = type.startsWith("video/") ? blob : new Blob([blob], { type: "video/mp4" });
    return { ok: true, url: URL.createObjectURL(videoBlob) };
  }

  function resolveVideoUrl(pathOrName, { playback = true } = {}) {
    const raw = (pathOrName || "").split(/[/\\]/).pop();
    if (!raw) return "";
    let file = raw;
    if (playback && !/\.webm$/i.test(file)) {
      file = file.replace(/\.(mp4|mov|m4v|mkv|avi)$/i, ".webm");
    }
    const url = `/api/video-gallery/${encodeURIComponent(file)}`;
    if (!mediaNeedsApiKey() || isSameMachineHost()) return url;
    return apiAuthUrl(url);
  }

  async function resolveVideoPlaybackUrl(pathOrName) {
    const url = resolveVideoUrl(pathOrName, { playback: true });
    if (!url) return { ok: false, url: "", needsKey: false };
    if (mediaNeedsApiKey() && !isSameMachineHost() && !getStoredApiKey()) {
      return { ok: false, url, needsKey: true };
    }
    return { ok: true, url, direct: true, needsKey: false };
  }

  const MEDIA_LOAD_ERROR_HINT =
    "Could not play this clip in the app — try Video gallery or open the file from data/generated_videos/";

  function attachMediaLoadError(el, kind = "media") {
    if (!el || el.dataset.mediaErrorBound) return;
    el.dataset.mediaErrorBound = "1";
    el.addEventListener("error", () => {
      const parent = el.closest("figure") || el.parentElement;
      if (!parent || parent.querySelector(".media-load-warn")) return;
      const warn = document.createElement("p");
      warn.className = "media-load-warn warn small";
      warn.textContent = kind === "video"
        ? `Video failed to load — ${MEDIA_LOAD_ERROR_HINT}`
        : `Image failed to load — ${MEDIA_LOAD_ERROR_HINT}`;
      parent.appendChild(warn);
    });
  }

  Object.assign(window, {
    apiAuthUrl,
    fetchMediaBlobUrl,
    resolveVideoUrl,
    resolveVideoPlaybackUrl,
    attachMediaLoadError,
  });
})();
