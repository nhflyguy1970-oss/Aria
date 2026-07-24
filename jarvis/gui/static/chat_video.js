/** Chat video figure helpers — extracted from app.js. */
(function () {
  async function appendAuthenticatedVideo(container, videoPath, videoName) {
    if (!container || !videoPath) return;
    const label = videoName || videoPath.split(/[/\\]/).pop();
    const fig = document.createElement("figure");
    fig.className = "gen-video";
    const video = document.createElement("video");
    video.controls = true;
    video.preload = "metadata";
    video.className = "chat-video-player";
    window.attachMediaLoadError?.(video, "video");
    const cap = document.createElement("figcaption");
    cap.textContent = label;
    fig.appendChild(video);
    fig.appendChild(cap);
    container.appendChild(fig);

    const playback = await window.resolveVideoPlaybackUrl?.(videoPath);
    if (!playback) return;
    if (!playback.ok && playback.needsKey) {
      const warn = document.createElement("p");
      warn.className = "media-load-warn warn small";
      warn.innerHTML = 'Video needs your API key — <button type="button" class="ghost-btn small media-key-btn">Enter API key</button>';
      warn.querySelector(".media-key-btn")?.addEventListener("click", () => window.showApiKeyModal?.(""));
      fig.appendChild(warn);
      return;
    }
    if (playback.url) video.src = playback.url;
    window.bindClickableVideos?.(fig);
  }

  function appendGeneratedVideo(container, videoPath, videoName) {
    void appendAuthenticatedVideo(container, videoPath, videoName);
  }

  function buildVideoMessageHtml(data, text) {
    let intro = (text || data.message || "").trim();
    const prompt = (data.enhanced_prompt || "").trim();
    intro = intro.replace(/\n\n\*\*Keyframe prompt:\*\*\n[\s\S]*$/, "").trim();
    if (!intro) intro = "Here's your video.";
    const format = window.formatMessage || ((t) => t);
    const esc = window.escapeHtml || ((t) => t);
    let html = format(intro);
    if (prompt) {
      html += `<details class="prompt-details" open><summary>Keyframe prompt</summary><pre class="prompt-text">${esc(prompt)}</pre></details>`;
    }
    return html;
  }

  Object.assign(window, {
    appendAuthenticatedVideo,
    appendGeneratedVideo,
    buildVideoMessageHtml,
  });
})();
