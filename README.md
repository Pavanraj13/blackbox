# Autonomous Black-Box UI/UX & Accessibility Testing Agent

An autonomous, black-box agentic framework for UI/UX testing, accessibility auditing, and friction detection.

Given a high-level natural-language goal (such as *"Search for blue running shoes under $100 and complete guest checkout"*), the agent autonomously perceives web application states through standard DOM accessibility metadata and visual observations, plans actions using LLMs (or a semantic fallback planner), controls a Playwright Chromium browser, detects UX friction and accessibility defects, and generates reproducible audit reports with visual trajectories.

---

## 🌟 Key Features

1. **Zero Source-Code Modifications**: Completely black-box. Requires no `data-testid` attributes, proprietary hooks, or pre-recorded test scripts.
2. **Autonomous Reason-Observe-Act Loop**: Observes interactive element roles, accessible names, text content, and bounding boxes; selects next actions (`CLICK`, `TYPE`, `SCROLL`, `BACK`, `FINISH`).
3. **Deterministic & LLM Dual Engine**: Supports OpenAI-compatible LLM endpoints (`OPENAI_API_KEY`) and features a semantic fallback planner so demonstrations run reliably out-of-the-box.
4. **Deterministic Accessibility Analyzer**: Inspects unlabeled icon buttons, form fields missing `<label>` tags or `aria-label` attributes, non-descriptive links, and touch target violations.
5. **Friction Scoring Engine**: Detects navigation loops, backtracking, excessive scrolling, and controls below the viewport fold to output a transparent 0–100 friction score.
6. **Visual Audit Reports**: Captures screenshots after every step and generates JSON & standalone HTML audit reports with step-by-step trajectory trace.
7. **Developer Dark Dashboard**: Real-time agent monitoring screen, live screenshot feed, reasoning timeline, issue tracker, and historical run analytics.

---

## 📂 Project Architecture

```
autonomous-ui-agent/
├── target-app/        # Demo E-Commerce Shopping App (React + Vite, Port 3001)
├── backend/           # FastAPI Python Server + Playwright + SQLite (Port 8000)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── routes/    # API Controllers (agent, runs, reports)
│   │   └── services/  # Core Services (browser, observer, planner, a11y, friction, reporter)
│   ├── screenshots/
│   ├── reports/
│   └── requirements.txt
├── frontend/          # React + Vite + Tailwind CSS Dark Dashboard (Port 3000)
├── README.md
└── .env.example
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Node.js** v18+ and **npm**
- **Python** 3.10+

---

### 2. Install & Start Demo Target Application (Port 3001)

```bash
cd autonomous-ui-agent/target-app
npm install
npm run dev
```
*The target application will run at `http://localhost:3001`.*

---

### 3. Install & Start FastAPI Backend Engine (Port 8000)

In a new terminal:

```bash
cd autonomous-ui-agent/backend

# Create virtual environment (optional)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
playwright install chromium

uvicorn app.main:app --reload --port 8000
```
*Backend API will run at `http://localhost:8000`.*

---

### 4. Install & Start React Dashboard (Port 3000)

In a third terminal:

```bash
cd autonomous-ui-agent/frontend
npm install
npm run dev
```
*Dashboard UI will open at `http://localhost:3000`.*

---

## 🧪 Acceptance Test & Hackathon Demonstration Flow

1. Open `http://localhost:3000` in your browser.
2. Navigate to **Test Agent** or use the **Launch New Autonomous Test** form on the Dashboard.
3. Keep Target URL as `http://localhost:3001`.
4. Set Natural Language Testing Goal:
   > **"Search for blue running shoes under $100 and complete guest checkout."**
5. Click **START AUTONOMOUS TEST**.
6. **Watch the Agent**:
   - Observe Chrome being navigated autonomously.
   - Watch live reasoning timeline & screenshot updates.
   - View detected accessibility bugs (e.g. unlabeled cart icon button, missing email input label).
   - See the agent reach **Order Confirmation**.
7. Click **VIEW FULL AUDIT REPORT** to inspect execution trajectory, friction score breakdown, discovered paths, and step screenshots.

---

## 🔒 Environment Variables (`.env`)

Optionally set your OpenAI key in `backend/.env` or root `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
BACKEND_URL=http://localhost:8000
TARGET_URL=http://localhost:3001
```
*Note: If `OPENAI_API_KEY` is not provided, the framework seamlessly utilizes the semantic fallback planner so all tests complete cleanly.*
