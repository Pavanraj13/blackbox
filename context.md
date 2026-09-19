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
