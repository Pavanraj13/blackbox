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
