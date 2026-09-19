// Blackbox Extension Popup Controller

let currentMode = "FOCUSED";
let activeRunId = null;
let pollTimer = null;
let backendUrl = "http://localhost:8000";
let apiKey = "";

const targetUrlInput = document.getElementById("targetUrlInput");
const goalInput = document.getElementById("goalInput");
const goalField = document.getElementById("goalField");
const modeFocused = document.getElementById("modeFocused");
const modeFullSite = document.getElementById("modeFullSite");
const modelSelect = document.getElementById("modelSelect");
const launchForm = document.getElementById("launchForm");
const submitBtn = document.getElementById("submitBtn");
const errorBox = document.getElementById("errorBox");

const toggleSettingsBtn = document.getElementById("toggleSettingsBtn");
const settingsPanel = document.getElementById("settingsPanel");
const backendUrlInput = document.getElementById("backendUrlInput");
const apiKeyInput = document.getElementById("apiKeyInput");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");

const statusCard = document.getElementById("statusCard");
const runStatusPill = document.getElementById("runStatusPill");
const statMode = document.getElementById("statMode");
const statSteps = document.getElementById("statSteps");
const statScore = document.getElementById("statScore");
const viewReportLink = document.getElementById("viewReportLink");
const stopRunBtn = document.getElementById("stopRunBtn");
const recentList = document.getElementById("recentList");

// 1. Initialize State & Tab URL
document.addEventListener("DOMContentLoaded", async () => {
  chrome.storage.local.get(["backendUrl", "apiKey", "activeRunId"], async (res) => {
    if (res.backendUrl) {
      backendUrl = res.backendUrl;
      backendUrlInput.value = backendUrl;
    }
    if (res.apiKey) {
      apiKey = res.apiKey;
      apiKeyInput.value = apiKey;
    } else {
      // Auto-fetch API key from local backend on first run
      try {
        const infoRes = await fetch(`${backendUrl}/api/key-info`);
        if (infoRes.ok) {
          const infoData = await infoRes.json();
          if (infoData.api_key) {
            apiKey = infoData.api_key;
            apiKeyInput.value = apiKey;
            chrome.storage.local.set({ apiKey });
          }
        }
      } catch (e) {
        console.warn("Could not auto-fetch API key:", e);
      }
    }
    if (res.activeRunId) {
      activeRunId = res.activeRunId;
      showStatusCard();
      startPolling(activeRunId);
    }
    loadRecentRuns();
    loadModels();
  });

  // Query current active browser tab
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs && tabs[0] && tabs[0].url && !tabs[0].url.startsWith("chrome://")) {
      targetUrlInput.value = tabs[0].url;
    }
  } catch (e) {
    console.warn("Unable to get active tab URL:", e);
  }
});

// 2. Settings Toggle & Save
toggleSettingsBtn.addEventListener("click", () => {
  settingsPanel.classList.toggle("active");
});

saveSettingsBtn.addEventListener("click", () => {
  backendUrl = backendUrlInput.value.trim() || "http://localhost:8000";
  apiKey = apiKeyInput.value.trim();
  chrome.storage.local.set({ backendUrl, apiKey }, () => {
    settingsPanel.classList.remove("active");
    loadRecentRuns();
    loadModels();
  });
});

// 3. Mode Toggle
modeFocused.addEventListener("click", () => {
  currentMode = "FOCUSED";
  modeFocused.classList.add("active");
  modeFullSite.classList.remove("active");
  goalField.style.display = "block";
});

modeFullSite.addEventListener("click", () => {
  currentMode = "FULL_SITE";
  modeFullSite.classList.add("active");
  modeFocused.classList.remove("active");
  goalField.style.display = "none";
});

// 4. Form Submission
launchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorBox.style.display = "none";
  errorBox.textContent = "";

  const target_url = targetUrlInput.value.trim();
  const goal = currentMode === "FOCUSED" ? goalInput.value.trim() : "";
  const model = modelSelect ? modelSelect.value : "qwen3.6:35b";

  submitBtn.disabled = true;
  submitBtn.textContent = "Launching Agent...";

  try {
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;

    const res = await fetch(`${backendUrl}/api/runs`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        target_url,
        goal,
        mode: currentMode,
        model
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }

    const data = await res.json();
    activeRunId = data.run_id;
    chrome.storage.local.set({ activeRunId });

    // Tell background service worker to monitor
    chrome.runtime.sendMessage({
      type: "START_POLL",
      runId: activeRunId,
      backendUrl,
      apiKey
    });

    showStatusCard();
    startPolling(activeRunId);
    loadRecentRuns();

  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Start Autonomous Audit";
  }
});

// 5. Polling & Status Updates
function showStatusCard() {
  statusCard.classList.add("active");
  statMode.textContent = currentMode;
  viewReportLink.href = `http://localhost:3002/report/${activeRunId}`;
}

function startPolling(runId) {
  if (pollTimer) clearInterval(pollTimer);

  const fetchStatus = async () => {
    try {
      const headers = { "Content-Type": "application/json" };
      if (apiKey) headers["X-API-Key"] = apiKey;

      const res = await fetch(`${backendUrl}/api/runs/${runId}`, { headers });
      if (!res.ok) return;

      const run = await res.json();
      statMode.textContent = run.mode || "FOCUSED";
      statSteps.textContent = run.steps_count || 0;
      statScore.textContent = run.friction_score !== undefined ? run.friction_score.toFixed(1) : "100.0";

      runStatusPill.textContent = run.status;
      runStatusPill.className = "status-pill";
      if (run.status === "RUNNING") {
        runStatusPill.classList.add("pill-running");
        stopRunBtn.style.display = "block";
      } else if (run.status === "COMPLETED") {
        runStatusPill.classList.add("pill-completed");
        stopRunBtn.style.display = "none";
        clearInterval(pollTimer);
        pollTimer = null;
        chrome.storage.local.remove("activeRunId");
      } else {
        runStatusPill.classList.add("pill-stopped");
        stopRunBtn.style.display = "none";
        clearInterval(pollTimer);
        pollTimer = null;
        chrome.storage.local.remove("activeRunId");
      }
    } catch (e) {
      console.warn("Status poll failed:", e);
    }
  };

  fetchStatus();
  pollTimer = setInterval(fetchStatus, 2500);
}

// 6. Stop Run Button
stopRunBtn.addEventListener("click", async () => {
  if (!activeRunId) return;
  try {
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;

    await fetch(`${backendUrl}/api/runs/${activeRunId}/stop`, {
      method: "POST",
      headers
    });
    runStatusPill.textContent = "STOPPED";
    runStatusPill.className = "status-pill pill-stopped";
    stopRunBtn.style.display = "none";
    clearInterval(pollTimer);
    chrome.storage.local.remove("activeRunId");
  } catch (e) {
    console.error("Stop failed:", e);
  }
});

// 7. Recent Runs List
async function loadRecentRuns() {
  try {
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;

    const res = await fetch(`${backendUrl}/api/runs`, { headers });
    if (!res.ok) {
      recentList.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 8px;">No recent runs found or auth required.</div>`;
      return;
    }

    const runs = await res.json();
    if (!runs || runs.length === 0) {
      recentList.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 8px;">No audit runs yet.</div>`;
      return;
    }

    recentList.innerHTML = runs.slice(0, 4).map(r => `
      <a class="recent-item" href="http://localhost:3002/report/${r.id}" target="_blank">
        <div>
          <div class="recent-url">${r.target_url}</div>
          <div class="recent-meta">${r.mode || 'FOCUSED'} &bull; ${r.status} &bull; Score ${r.friction_score ? r.friction_score.toFixed(0) : 100}</div>
        </div>
        <span style="font-size: 12px; color: var(--text-muted);">&rarr;</span>
      </a>
    `).join("");
  } catch (e) {
    recentList.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 8px;">Connect to backend to view runs.</div>`;
  }
}

// 8. Load Models
async function loadModels() {
  if (!modelSelect) return;
  try {
    const res = await fetch(`${backendUrl}/api/models`);
    if (res.ok) {
      const data = await res.json();
      if (data?.models?.length > 0) {
        modelSelect.innerHTML = data.models.map(m => `
          <option value="${m.id}" ${m.id === (data.default || 'qwen3.6:35b') ? 'selected' : ''}>
            ${m.name || m.id}
          </option>
        `).join("");
      }
    }
  } catch (e) {
    console.warn("Could not load models:", e);
  }
}

