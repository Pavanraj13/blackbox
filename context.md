# Project Context: Autonomous Black-Box UI/UX & Accessibility Testing Agent

## Project Overview
The project is an autonomous black-box agentic framework for UI/UX testing, accessibility auditing, and friction detection. It drives a Playwright Chromium browser to accomplish natural language testing goals on target web applications without modifying their source code.

## Architecture Components

1. **Target App (`target-app/`)**
   - **Tech Stack:** React + Vite + Tailwind CSS
   - **Port:** 3001 (`http://localhost:3001`)
   - **Role:** Demo e-commerce store with deliberate accessibility defects (unlabeled icon buttons, missing form labels, touch target violations) and checkout flow for agent testing.

2. **Backend Engine (`backend/`)**
   - **Tech Stack:** Python 3.10+, FastAPI, Playwright (Chromium), SQLAlchemy, SQLite, Uvicorn
   - **Port:** 8000 (`http://localhost:8000`)
   - **Role:** Coordinates the Reason-Observe-Act loop.
     - Playwright browser driver
     - DOM / ARIA accessibility observer
     - Dual-engine planner (LLM via OpenAI API / Semantic Fallback Planner)
     - Deterministic accessibility analyzer & friction scoring engine
     - SQLite database for test runs and visual audit report generation.

3. **Frontend Dashboard (`frontend/`)**
   - **Tech Stack:** React + Vite + Tailwind CSS + Lucide Icons + React Router
   - **Port:** 3000 (`http://localhost:3000`)
   - **Role:** Real-time developer dark dashboard to launch test runs, observe live screenshot feeds, inspect reasoning timelines, view detected accessibility issues, and read visual audit reports.

## Conceptual Architecture & Execution Loop (In Simple Terms)

```
[ User Prompt: Goal + URL ]
          │
          ▼
   ┌──────────────┐
   │ 1. OBSERVE   │ ──> Playwright scans the rendered web page (The "Eyes")
   └──────┬───────┘     Extracts buttons, links, inputs, and their visual position.
          │
          ▼
   ┌──────────────┐
   │ 2. REASON    │ ──> Local Ollama LLM / Fallback Planner (The "Brain")
   └──────┬───────┘     Decides the single next action: CLICK #5 ("Buy Now"), TYPE, SCROLL.
          │
          ▼
   ┌──────────────┐
   │ 3. ACT       │ ──> Playwright drives Chrome (The "Hands")
   └──────┬───────┘     Clicks, types, scrolls, and takes a full screenshot.
          │
          ▼
   ┌──────────────┐
   │ 4. AUDIT     │ ──> Accessibility & Friction Engine (The "Inspector")
   └──────┬───────┘     Checks WCAG contrast, missing labels, touch targets & friction.
          │
     (Repeat loop until Goal Finished or Max Steps reached)
          │
          ▼
[ Comprehensive Visual Audit Report + Friction Score ]
```

## How to Run the Application

### 1. Prerequisites
- Node.js (v18+) & npm
- Python (v3.10+)

### 2. Services Execution Commands

#### Terminal 1: Target App (Port 3001)
```powershell
cd target-app
npm install
npm run dev
```

#### Terminal 2: Backend API (Port 8000)
```powershell
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Install dependencies & Playwright browser:
pip install -r requirements.txt
playwright install chromium
# Start server:
uvicorn app.main:app --reload --port 8000
```

#### Terminal 3: Frontend Dashboard (Port 3000)
```powershell
cd frontend
npm install
npm run dev
```

## Configuration & Environment Variables
- Optional OpenAI API Key for LLM-based planning (defaults to semantic fallback if not provided):
  Create `.env` in `backend/` or root:
  ```env
  OPENAI_API_KEY=your_key_here
  OPENAI_MODEL=gpt-4o-mini
  BACKEND_URL=http://localhost:8000
  TARGET_URL=http://localhost:3001
  ```

## Current Status & Next Actions
- All 3 services are active and running:
  1. **Demo Target Store**: `http://localhost:3001`
  2. **FastAPI Backend Engine**: `http://localhost:8000` (verified active with `ollama:qwen3.6:35b`)
  3. **Frontend Dashboard**: `http://localhost:3002` (running via Vite)
- **Root Cause of `FAILED` runs**:
  - In Windows, Uvicorn's reload runner configures `WindowsSelectorEventLoopPolicy`.
  - Calling Playwright Chromium (`async_playwright().start()`) inside a selector loop fails with `NotImplementedError` because `asyncio.create_subprocess_exec` is only supported under `WindowsProactorEventLoopPolicy`.
- **Permanent Architecture Fix**:
  - Updated `backend/app/routes/agent.py` to spawn the autonomous agent execution in a dedicated background worker thread with its own `WindowsProactorEventLoopPolicy` event loop (`_execute_run_thread`).
  - Added `asyncio.WindowsProactorEventLoopPolicy` at the top of `backend/app/main.py`.
- **Full Verification on `https://kmec.in/`**:
  - Triggered run `9f1274a1-1468-4f4a-ab54-4634c1117afb` via `POST /api/runs`.
  - **Status: COMPLETED**.
  - **Steps Executed (4)**:
    1. `CLICK 'About KMEC'`
    2. `CLICK 'Admissions'`
    3. `SCROLL` (viewing admission guidelines)
    4. `FINISH` (goal accomplished)
  - **Issues Detected**: 9 accessibility defects (unlabeled controls, small touch targets, non-descriptive link labels).
  - **Screenshots**: `step_001.png`, `step_002.png`, `step_003.png`.
  - **Report**: Full HTML audit report generated at `backend/reports/run_9f1274a1-1468-4f4a-ab54-4634c1117afb.html`.

## Deep E-Commerce Perception & Planning Upgrades (Amazon Root Cause Resolution)

### 1. Root Causes for Missing "Buy Now" and Repeating Search:
1. **DOM Hard Truncation (`[:50]` elements)**:
   - Amazon pages have 300+ interactive elements. The original observer truncated elements to the first 50 strictly in document tree order.
   - The first 50 elements were exclusively top navbar links (Mobiles, Best Sellers, Customer Service, Search bar).
   - The Buy Box (`#buy-now-button`, `#add-to-cart-button`, `#submit.buy-now`) was sliced off before being presented to the planner. The model's own internal reasoning explicitly noted: *"I don't see a clear 'Add to Cart' or 'Buy Now' button in the list of 50 elements provided... let me scroll down"*.
2. **AUI (Amazon UI) Transparent Input Overlays & CSS**:
   - Amazon's `<input id="buy-now-button" class="a-button-input">` has `opacity: 0.01`, overlaying `<span id="submit.buy-now" class="a-button">` with text "Buy Now".
   - The original observer discarded elements with low opacity or spans with children, and the `<input>` element had `value: ""` and `innerText: ""` resulting in an empty accessible name.
3. **Ollama `qwen3.6:35b` Thinking Exhaustion**:
   - `qwen3.6:35b` is a reasoning model that produces `<think>` traces. When fed ~12,000 character prompts with 85 elements, its internal thinking exceeded `num_predict: 1024` tokens before generating the final JSON response, yielding empty content and falling back into generic search loops.
4. **Tab Detachment on `target="_blank"`**:
   - Amazon product cards open in new tabs (`target="_blank"`), leaving the browser page object detached on the search results tab.

### 2. Implemented Architecture Fixes:
1. **Observer Overhaul (`backend/app/services/observer.py`)**:
   - Added specific selectors for `.a-button`, `[id*="buy-now"]`, `[id*="add-to-cart"]`.
   - Permitted styled overlay buttons with low/zero opacity.
   - Synthesized accessible labels from parent `.a-button` wrappers, `title`, and `aria-labelledby`.
   - Filtered primary actions strictly to high-intent purchasing actions (`Buy Now`, `Add to Cart`, `Proceed to Checkout`, `Place Order`)—excluding generic `search` and `submit`.
   - Prioritized primary actions to the top of the element observation list, followed by visual reading order of elements within the active viewport.
2. **Planner Optimization (`backend/app/services/planner.py`)**:
   - Filtered nameless junk elements to deliver a clean, compact ~45-element observation payload (~4,500 chars).
   - Configured `"think": False` in Ollama chat payload, dropping evaluation latency from 90s timeout down to ~15s with direct, structured JSON action generation.
   - Enhanced fallback planner and system prompt with strict e-commerce rules: if on a product page or if `[PRIMARY ACTION]` is visible, immediately click 'Buy Now' or 'Add to Cart'.
3. **Browser Resilience (`backend/app/services/browser.py`)**:
   - Integrated `_strip_target_blank()` to keep navigation within a single tab.
   - Auto-synchronized `self.page = self.context.pages[-1]`.
   - Added `force=True` fallback in Playwright click execution to handle overlay spans and transparent button inputs.
4. **Test Run Termination UI (`frontend/`)**:
   - **Report Page (`ReportPage.jsx`)**: Added red `TERMINATE TEST` button with real-time polling to immediately stop running tests.
   - **Runs Page (`RunsPage.jsx`)**: Added `Stop` button in the actions column for any active run with status `RUNNING`, along with 3-second auto-refresh polling.

## Local LLM Architecture Evaluation & Recommendations
- **Current Installed Models in Ollama**:
  - `qwen3.6:35b` (22 GB) - High intelligence/reasoning, but ~14-18s latency per action step and high VRAM usage.
  - `moondream:latest` (1.7 GB) - Lightweight vision model.
- **Evaluation for Multi-Agent & Per-Issue Dynamic Scoring Overhaul**:
  - Running 2-3 parallel agents with 15-20 steps each + per-issue scoring on a single 35B model will saturate GPU VRAM and cause severe queuing (10-15+ minute runs).
  - **Recommended Architecture: Two-Tier (Dual-Model) Setup**:
    1. **Action Planner Agent**: `qwen2.5:7b` or `llama3.1:8b` (~2-3s response time, low VRAM, runs parallel instances reliably for rapid browser navigation).
    2. **Auditor / Scorer / Reporter**: `qwen2.5:14b` or `qwen3.6:35b` (handles deep UX analysis, dynamic severity scoring 0-10, and executive audit summaries).
    3. **Vision / OCR Enhancement**: `moondream` or `qwen2.5-vl` / OCR integration for visually recognizing elements without accessible DOM labels.

## Blackbox v2.0 Complete Overhaul (Implemented & Verified)

### 1. Two-Tier Local LLM Architecture
- **Action Planner Engine (`qwen2.5:7b`)**: Downloaded and verified via Ollama. Replaces 35B for action step planning, dropping step latency from ~15-20s down to ~0.8s-2.0s with strict JSON compliance.
- **Auditor & Scoring Engine (`qwen3.6:35b`)**: Utilized for dynamic per-issue severity scoring (1-10), impact explanations, and generating comprehensive executive summaries.

### 2. Chrome Extension (Manifest V3)
- Located at `extension/`.
- `manifest.json`: Manifest V3 with `activeTab`, `storage`, and `tabs` permissions.
- `popup.html` & `popup.js`: Sleek Linear-style popup automatically capturing active tab URL, supporting Focused Flow and Full Site Crawl modes, real-time status polling, and direct links to dashboard reports.
- `background.js`: Service worker providing toolbar icon status badges (`RUN`, `DONE`, `STOP`).

### 3. Security, Encryption & Redaction
- **API Key Auth (`backend/app/security.py`)**: `APIKeyMiddleware` validates `X-API-Key` on all protected endpoints. Public endpoints include `/api/key-info`, `/docs`, `/static`.
- **AES-256-GCM Encryption at Rest**: `AESCipher` automatically encrypts report paths and sensitive session attributes before storing in SQLite.
- **Sensitive Data Redaction (`redact_sensitive`)**: Scans and masks emails, credit cards, SSNs, phone numbers, and credentials before payloads are sent to LLM providers.

### 4. Dynamic Issue Scoring & Categorized Auditing
- Each discovered defect is dynamically evaluated by LLM via `PlannerService.score_issue()`:
  - `dynamic_score`: 1.0 (minor) to 10.0 (blocker/WCAG violation)
  - `severity`: LOW, MEDIUM, HIGH, CRITICAL
  - `impact_summary`: 1-2 sentence real-world user or business impact
  - `fix_suggestion`: Actionable HTML/CSS/JS code remediation snippet
- **Category Breakdown (`FrictionAnalyzer`)**: Computes scores for Accessibility, Friction, Security, Broken Links, and Performance.

### 5. Multi-Agent Full Website Audit
- **`SiteCrawler` (`backend/app/services/crawler.py`)**: Fast BFS link discovery across internal routes (up to 15 pages).
- **`MultiAgentOrchestrator` (`backend/app/services/multi_agent.py`)**: Partitions discovered routes into 2-3 parallel specialized agent contexts (Form & Security Inspector, Navigation Auditor, Accessibility Auditor) executing concurrently in dedicated Playwright contexts.

### 6. Rich Reporting
- `backend/app/services/reporter.py`:
  - Produces structured JSON (`run_{id}.json`) and sleek modern HTML (`run_{id}.html`).
  - Endpoints: `GET /api/runs/{id}/report`, `GET /api/runs/{id}/summary`, `GET /api/runs/{id}/export`.

### 7. Frontend UI Overhaul
- **Design System**: Strict Linear/Vercel aesthetic, Inter font, neutral monochrome surfaces, single blue accent (`#3b82f6`), zero emojis.
- **Light/Dark Mode**: `ThemeProvider` context defaulting to Light mode with seamless Dark mode toggle.
- **Components**: `ScoreRing.jsx`, `IssueCard.jsx`, `ThemeToggle.jsx`, `StatusBadge.jsx`, `Header.jsx`, `Sidebar.jsx`.
- **Pages**:
  - `Dashboard.jsx`: Launch console with Mode switch (Focused vs Full Site) and quick presets.
  - `AgentPage.jsx`: Live test console with synchronized viewport preview and action timeline.
  - `ReportPage.jsx`: Visual audit report with executive summary, category scores, filterable issue cards with code fix copy buttons, and screenshot modal.
  - `RunsPage.jsx`: Filterable session table with mode tags and status badges.
  - `FindingsPage.jsx`: Centralized defect catalog with multi-category filters.
  - `SettingsPage.jsx`: API key management, connection testing, and encryption status.
  - `ExtensionGuidePage.jsx`: Unpacked Chrome extension loading guide.

### 8. End-to-End Live Verification (Run `eec0f387`)
- **Target Application**: `http://localhost:3001` (Demo e-commerce store).
- **Goal**: "Search for shoes and complete checkout".
- **Planner Model**: `qwen2.5:7b` (~0.8s inference latency).
- **Execution Trace (7 Steps, Status: COMPLETED)**:
  1. `[TYPE] Search products` (typed search query "shoes")
  2. `[CLICK] Load Additional Clearance Shoes Below`
  3. `[CLICK] View Details`
  4. `[CLICK] Add to Cart`
  5. `[CLICK] Proceed to Guest Checkout`
  6. `[CLICK] Place Order & Complete Guest Checkout`
  7. `[FINISH]` (order confirmation detected)
- **Security & Encryption**:
  - Verified `report_path` stored in SQLite starts with `enc:...` (AES-256-GCM authenticated ciphertext).
  - Decrypted transparently via `app.security.cipher`.
- **Dynamic Scoring & Report Output**:
  - 17 WCAG and UX friction issues detected and dynamically scored.
  - Composite health score calculated: 67.8 / 100.
  - AI Executive Summary generated with 3 prioritized engineering recommendations.
  - Standalone HTML and structured JSON reports saved in `backend/reports/`.

### 9. API Authentication & Auto-Bootstrap Resolution
- **Issue Reported**: `Unauthorized: Missing or invalid API key. Provide header 'X-API-Key' or parameter 'api_key'.`
- **Root Causes**:
  1. On initial load, the frontend (`localStorage.getItem('blackbox_api_key')`) and extension storage were empty, sending requests without `X-API-Key`.
  2. Standalone HTML/JSON report and summary routes (`/api/runs/{id}/report`, `/api/runs/{id}/summary`, `/api/runs/{id}/export`) and `/api/health` were not exempted in `APIKeyMiddleware`, causing 401s when opened directly in browser tabs or invoked by monitoring utilities.
  3. `GET /api/key-info` only returned a masked `key_preview`, preventing local clients from auto-negotiating the key.
- **Architectural Fixes Implemented**:
  1. **`backend/app/security.py`**:
     - Added `/api/health` to `EXEMPT_PREFIXES`.
     - Added `EXEMPT_SUFFIXES = ("/report", "/summary", "/export")` to allow unrestricted viewing and downloading of generated audit reports in browser tabs.
     - Added Bearer token parsing (`Authorization: Bearer <key>`) alongside `X-API-Key` and `?api_key=`.
     - Added loopback exemption: requests originating from local loopback (`127.0.0.1`, `::1`, `localhost`, `testclient`) without an explicit key are permitted, eliminating friction during local development and testing. Invalid explicit keys continue to be rejected with 401.
  2. **`backend/app/main.py`**:
     - Updated `GET /api/key-info` to return `api_key` for local loopback clients.
  3. **`frontend/src/services/api.js`**:
     - Implemented `ensureApiKey()` which automatically queries `/api/key-info` on startup if `localStorage` is empty, caching and attaching `X-API-Key` on subsequent requests.
  4. **`frontend/src/pages/SettingsPage.jsx`**:
     - Updated `loadInfo()` to automatically populate the input field with the active key.
  5. **`extension/popup/popup.js`**:
     - Added auto-fetch in `DOMContentLoaded` so that upon installing/opening the extension, it queries `${backendUrl}/api/key-info` and saves the API key to `chrome.storage.local` automatically.
- **Verification**:
  - `GET /api/health` -> `200 OK`
  - `GET /api/key-info` -> `200 OK` (returns `api_key`)
  - `GET /api/runs/{id}/report` -> `200 OK` (direct HTML view)
  - `GET /api/runs` without header on loopback -> `200 OK`
  - `GET /api/runs` with invalid header -> `401 Unauthorized` (proper rejection)
  - `GET /api/runs` with valid `X-API-Key` -> `200 OK` (runs count: 34)
  - Frontend production build (`npm run build`) -> `1543 modules`, built in 1.89s, 0 errors.

## 10. Model Selection, Screenshot Clarity, Log Deletion & Run History Switcher

### 1. Default Model & Dynamic Model Selection
- **Default Engine**: Updated default planner model in `backend/app/config.py` from `qwen2.5:7b` to `qwen3.6:35b`.
- **Installed Model Auto-Discovery**: Added `GET /api/models` endpoint which dynamically inspects local Ollama instance (`/api/tags`), listing installed models (`qwen3.6:35b` [21.1GB], `qwen2.5:7b` [4.4GB], etc.) with sizes and friendly labels.
- **Model Choice UI Dropdowns**:
  - **Dashboard Launch Console (`Dashboard.jsx`)**: Added "Model Engine" dropdown for instant switching between `qwen3.6:35b` and `qwen2.5:7b`.
  - **Live Agent View (`AgentPage.jsx`)**: Model selector integrated into the agent launch console.
  - **Chrome Extension (`popup.html` & `popup.js`)**: Dynamic model selection populated from `/api/models`.
  - **Report & Sessions View**: Model used for each test session is stored in SQLite (`runs.model`) and rendered as a font-mono badge in session tables, audit reports, and cards.

### 2. Screenshot Clarity & Target Highlighting
- **Resolution & Viewport**: Raised Playwright browser viewport to 1440x900 with `device_scale_factor=1.25`.
- **Target Element Highlighting (`browser.py`)**:
  - Before taking a screenshot for an action step (`CLICK` or `TYPE`), the browser injects a high-contrast outline (`outline: 3px solid #2563eb`) and floating action badge (`STEP N: CLICK / TYPE`) over the target element.
  - Added multi-tier targeting: CSS selector -> `elementFromPoint(x, y)` -> coordinate bounding box fallback.
  - The badge and outline are captured directly in the screenshot, providing clear visual evidence of what the agent decided to interact with.
  - Highlighting is automatically cleared before executing the action.
- **Uncropped Views & Slideshow Modal**:
  - Replaced thumbnail cropping (`object-cover`) in `ReportPage.jsx` with full uncropped `aspect-video` frames.
  - Clicking any screenshot opens an interactive high-resolution slideshow modal with Next Step / Previous Step keyboard and mouse navigation.
  - Added full-resolution viewport zoom modal in `AgentPage.jsx`.

### 3. Log & Session Deletion
- **Individual Session Deletion**:
  - Backend: `DELETE /api/runs/{run_id}` cleanly deletes all associated database records (`issues`, `steps`, `paths`, `runs`) and wipes the filesystem directory `backend/screenshots/run_{run_id}` and report files `backend/reports/run_{run_id}.*`.
  - Frontend: Added red trash icon button in the Actions column of `RunsPage.jsx` and "Delete Run" button in `ReportPage.jsx` header.
- **Bulk Log Deletion**:
  - Backend: `DELETE /api/runs` wipes all test runs, orphan screenshot folders, and report artifacts.
  - Frontend: Added "Clear All Logs" button with confirmation modal on `RunsPage.jsx`.

### 4. Same Test Run Dropdown (Re-run & History Switcher)
- **Re-run Previous Test Dropdown**:
  - Added "Re-run Previous Test" dropdown to `Dashboard.jsx` and `AgentPage.jsx`.
  - Selecting any previous test run instantly autofills the Target URL, Scope Mode (Focused vs Full Site), Testing Goal, and Model Engine.
- **Audit Report Run Switcher**:
  - Added "Switch Run" dropdown in `ReportPage.jsx` header, allowing instant navigation across historical test runs without returning to the runs table.
- **Execution Timeline Step Filter**:
  - Added "Jump to Step" filter dropdown in `ReportPage.jsx` to filter or jump directly to any specific action step.

## 11. Subresource 404 Filtering, Out-of-Bounds Recovery, Anti-Loop Blacklisting & Issue Deduplication

### 1. Root Causes for Agent Freezing & Repeating 404s
1. **Subresource Asset 404s Flagged as High-Severity Broken Links**:
   - The Playwright `response` listener captured all HTTP >= 400 responses across the entire page, including background missing retina images (`/assets/.../DSC_0226@2x.webp`, `/assets/img/log@2x.webp`), fonts, and stylesheets.
   - These are background static assets, not broken HTML document links that a user would navigate to.
   - Each subresource 404 was flagged as a `BROKEN_LINK` (Score 7.5 HIGH) and invoked an expensive 15-second local LLM severity scoring query sequentially, freezing the agent for 1–2 minutes per step and repeating on every step.
2. **Issue Inflation & Step-by-Step Duplication**:
   - `AccessibilityAnalyzer` was checking `x["step_number"] == step_number`, causing the exact same 11 accessibility issues on the page to be re-added on every single step (generating 160+ duplicate issues per run).
3. **Out-of-Bounds & Network Failure Trapping**:
   - When navigation was attempted on broken routes, Chromium navigated to `chrome-error://chromewebdata/` (or external domains like social media).
   - Although the boundary guard returned inside scope, the failed element remained on the page and was re-selected by the planner in an infinite loop.

### 2. Architecture Fixes Implemented
1. **Subresource Filtering & Deduplication (`agent.py` & `multi_agent.py`)**:
   - In `handle_response`, inspect `response.request.resource_type`. Subresources (`image`, `media`, `font`, `stylesheet`, `other`, `ping`) and static file extensions (`.webp`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.ico`, `.css`, `.js`, `.map`, `.woff`, `.woff2`, `.ttf`, `.eot`, `.mp4`, `.mp3`) are ignored.
   - Only true document navigation failures (`resource_type == "document"`) are recorded.
   - Added `seen_error_urls = set()`: any genuine error URL is recorded at most once per test run.
   - Replaced expensive LLM queries for routine HTTP status codes with instant, deterministic scoring templates (9.0 CRITICAL for 5xx, 7.0 HIGH for document 404).
2. **Observer Media Link Sanitization (`observer.py`)**:
   - Filtered out `<a>` tags with `href` pointing directly to raw static media assets (`.webp`, `.jpg`, `.png`, `.pdf`, etc.), `mailto:`, `tel:`, and `javascript:`.
   - External social media and third-party origins are tagged as `is_external: true` and sorted to the very bottom of candidate lists.
3. **Failed Target Blacklisting & Loop Breaker (`planner.py` & `agent.py`)**:
   - Added `failed_targets: set = set()` to track any element whose click causes a navigation failure, `chrome-error://`, or out-of-bounds redirection.
   - Tagged `el["is_failed"] = True` on observation elements.
   - `_validate_decision` and `_generalized_fallback_planner` reject blacklisted/failed targets, forcing the agent to pick untried candidates, scroll down, or conclude with `FINISH`.
   - Disallow back-to-back duplicate clicks on the same element when state signature is unchanged.
4. **Issue Deduplication Across Session**:
   - Deduplicated accessibility and friction issues across `all_issues` using `(title, element_summary)` identity, eliminating hundreds of duplicate issues per test session.

### 3. Verification Results on `https://kmec.in/` (Run `0d8a7605-a32c-47e8-8a34-866af3c2dabc`)
- **Target URL**: `https://kmec.in/`
- **Goal**: "explore the website and view admissions guidelines"
- **Model Engine**: `qwen3.6:35b`
- **Results**:
  - **Subresource 404s**: 0 false broken links recorded (all background `.webp` and `.png` asset 404s cleanly ignored).
  - **Deduplication**: 18 genuine unique issues recorded across the entire session instead of 174 duplicates.
  - **Out-of-Bounds & Loops**: 0 loops or `chrome-error://chromewebdata/` trapping. The agent cleanly navigated `CLICK 'Admissions'` -> `CLICK 'Admission Procedure'` -> continuous reading scrolls across the guidelines page.
  - **Full Executive Report**: HTML and JSON reports generated successfully with dynamic scoring.
