/** Chat request state bridge — extracted from app.js. */
(function () {
  let lastAssistantText = "";
  let useStreaming = true;
  let chatAbortController = null;
  let chatStopRequested = false;
  let activeStreamText = "";
  let activeChatRequestId = "";
  let chatRequestActive = false;

  window.jarvisChat = {
    get chatRequestActive() { return chatRequestActive; },
    set chatRequestActive(v) { chatRequestActive = v; },
    get chatAbortController() { return chatAbortController; },
    set chatAbortController(v) { chatAbortController = v; },
    get chatStopRequested() { return chatStopRequested; },
    set chatStopRequested(v) { chatStopRequested = v; },
    get activeStreamText() { return activeStreamText; },
    set activeStreamText(v) { activeStreamText = v; },
    get activeChatRequestId() { return activeChatRequestId; },
    set activeChatRequestId(v) { activeChatRequestId = v; },
    get useStreaming() { return useStreaming; },
    set useStreaming(v) { useStreaming = v; },
    get lastAssistantText() { return lastAssistantText; },
    set lastAssistantText(v) { lastAssistantText = v; },
  };

  function mediaWorkActive() {
    return chatRequestActive || (window.activeMediaJobs?.size || 0) > 0;
  }
  window.mediaWorkActive = mediaWorkActive;

  function syncMediaBusyClass() {
    if (!window.activeMediaJobs) window.activeMediaJobs = new Set();
    document.documentElement.classList.toggle("media-busy", window.activeMediaJobs.size > 0);
  }
  window.syncMediaBusyClass = syncMediaBusyClass;
})();
