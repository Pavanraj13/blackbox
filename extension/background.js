// Blackbox Chrome Extension Background Service Worker (MV3)

chrome.runtime.onInstalled.addListener(() => {
  console.log("[Blackbox] Extension installed successfully.");
  chrome.storage.local.get(["backendUrl", "apiKey"], (res) => {
    if (!res.backendUrl) {
      chrome.storage.local.set({ backendUrl: "http://localhost:8000" });
    }
  });
});

// Update extension icon badge
function updateBadge(text, color) {
  chrome.action.setBadgeText({ text: text || "" });
  if (color) {
    chrome.action.setBadgeBackgroundColor({ color: color });
  }
}

// Background polling for active runs
let activePollInterval = null;

function startPollingRun(runId, backendUrl, apiKey) {
  if (activePollInterval) {
    clearInterval(activePollInterval);
  }

  updateBadge("RUN", "#3b82f6");

  activePollInterval = setInterval(async () => {
    try {
      const headers = { "Content-Type": "application/json" };
      if (apiKey) headers["X-API-Key"] = apiKey;

      const res = await fetch(`${backendUrl}/api/runs/${runId}`, { headers });
      if (!res.ok) return;

      const data = await res.json();
      if (data.status === "COMPLETED") {
        updateBadge("DONE", "#10b981");
        clearInterval(activePollInterval);
        activePollInterval = null;
        chrome.storage.local.set({ lastFinishedRun: data });
      } else if (data.status === "FAILED" || data.status === "STOPPED") {
        updateBadge("STOP", "#ef4444");
        clearInterval(activePollInterval);
        activePollInterval = null;
      }
    } catch (err) {
      console.warn("[Blackbox] Poll failed:", err);
    }
  }, 3000);
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "START_POLL") {
    startPollingRun(msg.runId, msg.backendUrl, msg.apiKey);
    sendResponse({ ok: true });
  } else if (msg.type === "CLEAR_BADGE") {
    if (activePollInterval) {
      clearInterval(activePollInterval);
      activePollInterval = null;
    }
    updateBadge("", "#000000");
    sendResponse({ ok: true });
  }
  return true;
});
