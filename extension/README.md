# Blackbox Browser Extension (Chrome MV3)

A lightweight toolbar controller for the Blackbox Autonomous Web Testing & Accessibility Auditing Agent.

## Features
- **One-Click Launch**: Auto-fills the URL of your active browser tab.
- **Mode Toggle**: Choose between **Focused Flow** (directed goal navigation) or **Full Site Crawl** (multi-agent BFS site audit).
- **Encrypted Local Storage**: Backend API key and URL securely saved in `chrome.storage.local`.
- **Live Status & Badges**: Extension icon badge displays active status (`RUN`, `DONE`, `STOP`).
- **Direct Report Access**: One click to jump directly into the full interactive visual audit report in the Blackbox Dashboard.

## Installation in Chrome / Edge / Brave

1. Open your browser and navigate to:
   - Chrome: `chrome://extensions`
   - Edge: `edge://extensions`
   - Brave: `brave://extensions`
2. Enable **Developer mode** toggle in the top-right corner.
3. Click **Load unpacked**.
4. Select the `extension/` folder located at:
   ```
   c:\Users\SRIRAM\Documents\GitHub\blackbox\blackbox\extension
   ```
5. Click on the Blackbox icon in your browser toolbar.
6. If API Key authentication is enabled on your backend, click **Config** in the popup and paste your API key (found in `backend/.env` or on the Dashboard **Settings** page).
