# BlackBox UI Agent

## 1. Team Details

**Team Name / ID:** BlackBox

**Team Lead:** Upendra Pavan Raj

**Team Members:**

<!--
One line per person, including the team lead. Role is optional.
Pick one, combine two, write your own, or leave it blank:
  Agent Whisperer (agents, prompts, LLMs)
  Backend Developer
  Frontend Developer
  UI/UX Designer
  Integrations Engineer (APIs, tools, connecting services)
  Data Engineer (data, databases, retrieval)
  Product & Pitch Lead (idea, presentation, demo)
  Cool Team Member (a bit of everything)
-->

- Upendra Pavan Raj | Cool Team Member

**Repo Link (Optional):** https://github.com/Pavanraj13/blackbox.git

**Demo Link (Optional):** N/A: Runs locally on http://localhost:3000

---

## 2. Problem Statement

<!-- Paste the full problem statement exactly as it was given to you. Don't shorten, fix, or reword anything. No character limit here. -->

Autonomous Black-Box UI/UX & Accessibility Testing Agent: Build an autonomous, black-box agentic framework for UI/UX testing, accessibility auditing, and friction detection on modern web applications without requiring source-code modifications, proprietary test-ids, or pre-recorded test scripts.

---

## 3. TL;DR

<!-- One line each. A judge should get your idea in 10 seconds. -->

**Problem:** Manual UI/UX and accessibility testing is slow, and traditional automated test scripts are brittle and hard to maintain.

**Solution:** An autonomous agent that drives a browser, detects accessibility flaws, and scores user friction with zero code changes.

**Who benefits:** QA engineers and developers get instant accessibility audits, friction scores, and reproducible visual bug trajectories.

---

## 4. Scope of the Project

**What are you building?**

An autonomous black-box testing framework where an agent takes a natural language goal, inspects live DOM elements and ARIA accessibility trees in a Playwright Chromium browser, decides sequential actions, detects accessibility violations and UX friction (navigation loops, excessive scrolling), and outputs a full visual audit report with screenshots.

**How does it solve the problem statement?**

It eliminates brittle test scripts and test-id tags. By combining live DOM perception with LLM reasoning and a semantic fallback planner, it explores real interfaces like a human user, uncovering hidden accessibility bugs and user experience bottlenecks.

**Key features you're building for this hackathon:**

<!-- Up to 5 features. -->

- Autonomous Reason-Observe-Act loop driving Chromium via Playwright.
- Deterministic & LLM dual planner supporting OpenAI and offline fallback.
- Real-time accessibility auditor checking missing labels, roles, and targets.
- UX friction engine detecting loops, excessive scrolling, and backtracking.
- Dark developer dashboard with live screenshot feed and audit reports.

**What are you deliberately NOT doing? (Optional)**

Not testing native mobile apps or non-web desktop apps; not auto-generating fix PRs or source code modifications.

---

## 5. Why an Agentic Approach?

<!-- This is an Agentic AI hackathon, so this is one of the most important answers in the file. Be specific. "It uses an LLM" is not an answer. -->

**What does your agent decide or do on its own?**

<!-- e.g. plans its steps, picks which tool to call, handles unexpected input, retries when something fails, hands work to another agent. -->

At every step, it observes visible interactive elements and decides whether to CLICK, TYPE, SCROLL, GO BACK, or FINISH based on the goal. When elements move or pages dynamically update, it re-perceives the page state, adapts its path, recovers from misclicks, and autonomously flags accessibility defects and navigation friction it encounters along the way.

**Why wouldn't a fixed script, if-else rules, or a simple chatbot be enough?**

<!-- e.g. plans its steps, picks which tool to call, handles unexpected input, retries when something fails, hands work to another agent. -->

Fixed scripts break whenever a CSS selector, layout, or button text changes. If-else rules cannot handle non-linear navigation or multi-step checkout paths across arbitrary web pages. A chatbot cannot interact with the DOM or control a real browser. Only an agentic reason-observe-act loop can dynamically navigate unscripted interfaces like an actual user.

---

## 6. Who It's For & What Changes

**Who or what is this for?**

<!-- Doesn't have to be end users. It could be people, a team, a business, developers, or an internal system or process. -->

Frontend developers, QA automation teams, product managers, and accessibility compliance officers auditing modern web apps.

**The world today, without your solution:**

<!-- What happens right now? Who struggles, and what does it cost them in time, money, effort, errors, or missed opportunities? -->

QA teams manually click through complex user journeys or maintain brittle Selenium/Cypress test scripts that break on every minor redesign. Accessibility audits are done late via tedious manual checklists or static linters that miss dynamic interaction defects. UX friction like repetitive loops or buried checkout buttons goes unnoticed until users bounce.

**The world with your solution, fully built and scaled to production:**

<!-- Imagine your whole idea is built properly and used by everyone it's meant for. What's different? -->

Developers give high-level user stories in plain English, and a fleet of autonomous agents continuously tests every staging deployment in real browsers. Teams receive automated visual regression traces, WCAG accessibility violation logs, and UX friction scores before code hits production, with zero test maintenance overhead.

**What your hackathon build actually delivers today:**

<!-- Of everything you proposed, which part have you built, and which part of the problem does that piece solve right now? A small piece that truly works is a great answer. -->

A working end-to-end prototype: a FastAPI backend controlling Playwright, an accessibility and friction analysis engine, a React dashboard displaying real-time agent execution and screenshots, and an interactive demo e-commerce store where the agent autonomously searches, fills forms, and completes checkout.

**Before vs. After**

<!--
2 to 4 rows. Pick things that change: time, cost, effort, accuracy, scale, reach, manual work, risk.
Max 80 characters per cell. Replace the example row with your own.
-->

| What Changes | Today | With Our Current Build | At Production Scale |
| :---- | :---- | :---- | :---- |
| Test Script Setup | Days writing fragile selectors | 1 minute prompt-based run | Continuous CI/CD test generation |
| Accessibility Audit | Manual audits & static linters | Dynamic runtime WCAG checks per step | Automated continuous compliance across all flows |
| UX Friction Discovery | Discovered via user churn analytics | Detected instantly from step loops & scrolling | Real-time UX heatmaps and friction warnings |

---

## 7. Architecture & Agents

<!--
All the examples in this section describe ONE made-up project, a college helpdesk agent,
so you can see how the parts fit together. Aim for this level of detail, no more.
You don't need to list every library or every function.
-->

**How is your system put together?**

<!--
Example:
Students ask questions in a web chat. A Triage Agent sorts each message, an Answer Agent
replies using college policy documents, and anything needing a human becomes a helpdesk ticket.
-->

The React dashboard sends natural language testing goals to a FastAPI backend. An Autonomous Agent loop drives a headless Playwright Chromium browser. At each step, an Observer extracts DOM accessibility trees, an LLM/Fallback Planner decides the next browser action, while Accessibility and Friction Analyzers inspect the state, persisting logs and screenshots to SQLite.

### 7.1 Agents

<!--
One line per agent. For each one, say what its job is, which model it uses and why that model
fits the job, and what it talks to (other agents, APIs, databases, services).

 

Example:
- **Triage Agent:** Reads each message and decides if it's a policy question, a complaint, or needs a human. Uses Llama 3.1 8B locally, since sorting is simple and student data stays on our machine. Talks to the Answer Agent and Web Chat.
- **Answer Agent:** Answers policy questions from college documents and files a ticket when approval is needed. Uses Claude Sonnet because it handles long policy text and reasons well about exceptions. Talks to College Docs Store and Helpdesk Ticket API.
-->

- **UI Navigation & Planning Agent:** Decides next browser action from DOM observation. Uses OpenAI gpt-4o-mini for structured JSON reasoning, with deterministic fallback. Talks to Browser Service and SQLite.
- **Accessibility & Friction Analyzer:** Evaluates WCAG compliance (missing labels, touch targets) and UX friction (loops, backtracking, excessive scrolls) per step. Uses deterministic rules. Talks to Agent Service and DB.

### 7.2 Services, APIs, Databases & Memory

<!--
One line for everything that isn't an agent: databases, APIs, external services, tools,
and your interface (web app, bot, CLI). Say what it is, what it does, and who uses it.
Mention if it's mocked.

 

Example:
- **College Docs Store (Chroma vector database):** Holds fee, exam, and hostel policy PDFs. Used by the Answer Agent.
- **Helpdesk Ticket API (mocked):** Creates a ticket for the right college office. Used by the Answer Agent.
- **Web Chat (Streamlit):** Where students type questions and see answers. Talks to the Triage Agent.
-->

- **Playwright Browser Service (Python):** Controls Chromium browser, executes clicks/typing/scrolls, and captures step screenshots. Used by UI Agent.
- **FastAPI Backend (REST API):** Manages test runs, streams step telemetry, serves screenshots and audit reports. Talks to React Dashboard.
- **SQLite Database (Storage):** Stores runs, step logs, detected accessibility issues, and friction scores. Used by Backend services.
- **Developer Dashboard (React + Vite):** Dark UI to launch tests, monitor live screenshot feeds, and inspect audit reports. Used by developers.

**How does your system remember things (memory & state)?**

<!--
Example:
Each chat keeps its last 10 messages in session memory so follow-up questions make sense.
Tickets are saved in SQLite so students can check their status later.
-->

Maintains the last 5 executed actions in prompt context and tracks visited DOM state signatures in memory to detect repetitive navigation loops, backtracking, and prevent redundant clicks. Full step history is persisted in SQLite.

**Diagram Link (Optional):** N/A: See project architecture section in README.md

### 7.3 Example Walkthrough

<!--
Take ONE realistic input and show how it moves through your system: which agent picks it up,
what gets passed on, which tools or databases are used, and what comes out at the end.
Up to 8 steps. If the flow branches, use 3a / 3b.

 

Example:
**Example input:** A student types "Can I pay my semester fee late? I'm waiting on my scholarship."

 

1. [Web Chat] Sends the message and the student's ID to the Triage Agent.
2. [Triage Agent] Classifies it as a fee-policy question and passes it to the Answer Agent.
3. [Answer Agent] Finds the late-fee policy (uses: College Docs Store) and sees scholarship cases need approval.
4. [Answer Agent] Explains the policy and files an approval request (uses: Helpdesk Ticket API).
5. [Web Chat] Shows the student the answer and their ticket number.

 

**Final output:** A clear answer quoting the late-fee policy, plus a ticket raised with the accounts office.
-->

**Example input:** Search for blue running shoes under $100 and complete guest checkout.

1. Developer Dashboard sends test goal and target URL to FastAPI backend to initialize run (uses: REST API).
2. Browser Service launches Chromium and navigates to target store at http://localhost:3001 (uses: Playwright).
3. Observer Service extracts visible interactive elements, accessible names, and DOM state signature.
4. Accessibility Analyzer detects unlabeled cart icon button and logs accessibility warning (uses: SQLite).
5. Planning Agent selects search input, types "blue running shoes", and presses Enter (uses: gpt-4o-mini).
6. Browser Service navigates to product, clicks "Add to Cart", and proceeds to Checkout (uses: Playwright).
7. Planning Agent fills guest email and clicks Place Order button, confirming order page.
8. Reporter Service compiles step screenshots, friction score (100/100), and accessibility report.

**Final output:** Completed guest checkout order with a visual audit report detailing 2 accessibility defects and 0 friction loops.

**Anything special about how your workflow runs? (Optional)**

<!--
An algorithm you use, how agents decide what to do next, routing logic, loops, agents working
in parallel, scoring, self-checks. Anything you want us to notice.

 

Example:
The Triage Agent gives a confidence score with every decision. Below 0.7, the message skips the
Answer Agent and goes straight to a human, so students never get a confident wrong answer.
-->

A dual-engine planner: queries gpt-4o-mini for open-ended sites, but automatically falls back to an offline semantic planner if API keys are absent or rate-limited. It computes a dynamic friction score based on loop detection and fold distance, and takes visual snapshots at every step so engineers can replay exactly what happened.

---

## 8. Tech Stack

<!-- Write N/A for any row that doesn't apply. Models are already listed per agent in 7.1. Max 60 characters per cell. -->

| Layer | Technology |
| :---- | :---- |
| Frontend / Interface | React 18, Vite, Tailwind CSS, Lucide Icons |
| Backend | Python 3.10, FastAPI, Uvicorn |
| Agent Framework | Custom Reason-Observe-Act loop with Playwright |
| Database / Storage | SQLite (SQLAlchemy ORM), Local File Storage |
| Hosting | Local machine (localhost:3000, localhost:8000) |
| Other | Playwright Chromium, OpenAI API (gpt-4o-mini) |

---

## 9. What to Expect From Our Current Build

<!--
Be honest. Unfinished, faked, or hard-coded parts are completely normal at a hackathon.
Telling us means we judge what you actually built, and that works in your favour.
Max 120 characters per bullet.
-->

**Working:**

- End-to-end autonomous navigation and checkout flow on the demo e-commerce target app.
- Deterministic accessibility audit detecting missing labels, empty buttons, and touch targets.
- Friction scoring engine tracking navigation loops, backtracking, and excessive scrolling.
- Real-time dark mode dashboard with step timeline, live screenshots, and audit reports.

**Partly working, mocked, or hard-coded:**

- Semantic fallback planner handles e-commerce flows offline; general web navigation needs OpenAI API key.
- Target app runs locally on port 3001 with predefined catalog data rather than a live payment gateway.

**Not working or not built yet:**

- Multi-tab browser testing or iframe-nested authentication flows (e.g. Google OAuth popups).
- Automated GitHub PR generation with proposed code fixes for detected accessibility bugs.

**What we'd most like to be judged on:**

The completely black-box Reason-Observe-Act loop that requires zero test-ids or source-code alterations, combined with the automatic extraction of accessibility bugs and UX friction scores with full visual replay.

---

## 10. Future Scope

<!-- 2 or 3 things you're NOT building yet but plan to. If you clear the checkpoint, you may be asked to build one of them, so keep them concrete and doable. -->

### Idea 1

**Name:** Automated Fix Suggestion Engine

**What it is:** Generates exact JSX / HTML code patches or pull requests to fix flagged accessibility violations and missing ARIA attributes.

**Why it matters:** Turns diagnostic audit reports into immediate actionable code fixes for developers.

**How we'd build it:** Pass element DOM context and WCAG failure reason to an LLM code generator connected to GitHub Octokit API.

**Done when:** Clicking "Generate Fix" in dashboard displays a ready-to-merge git diff.

### Idea 2

**Name:** Multi-Persona Emulation Testing

**What it is:** Simulates diverse user personas like screen reader users, elderly users with tremors, or slow-network mobile users.

**Why it matters:** Ensures digital products work seamlessly for all user capabilities and assistive technologies.

**How we'd build it:** Configure Playwright keyboard-only navigation mode, color-blindness emulation, and network throttling.

**Done when:** The agent verifies an entire checkout flow using keyboard navigation only.

### Idea 3 (Optional)

**Name:** N/A: Two concrete ideas submitted above

**What it is:** N/A

**Why it matters:** N/A

**How we'd build it:** N/A

**Done when:** N/A

---

## 11. Additional Notes (Optional)

<!-- Anything else you'd like us to know. -->

The system was designed for zero barrier to entry: it runs completely locally with a demo target app and includes an offline fallback planner so evaluators can run live demonstrations even without configuring external API keys. All code, backend services, and dashboard components are pushed to the GitHub repository.
