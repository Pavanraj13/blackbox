import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Play,
  Activity,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  Globe,
  Compass,
  Cpu,
  History
} from 'lucide-react';
import { getRuns, startRun, getHealth, getModels } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [targetUrl, setTargetUrl] = useState("http://localhost:3001");
  const [mode, setMode] = useState("FOCUSED"); // FOCUSED or FULL_SITE
  const [goal, setGoal] = useState("Search for blue running shoes under $100 and complete guest checkout.");
  const [selectedModel, setSelectedModel] = useState("qwen3.6:35b");
  const [availableModels, setAvailableModels] = useState([
    { id: "qwen3.6:35b", name: "qwen3.6:35b (21.1GB) - Recommended Default" },
    { id: "qwen2.5:7b", name: "qwen2.5:7b (4.4GB) - High Speed" },
    { id: "moondream:latest", name: "moondream:latest (1.6GB)" }
  ]);
  const [starting, setStarting] = useState(false);
  const [engineInfo, setEngineInfo] = useState("qwen3.6:35b");
  const navigate = useNavigate();

  useEffect(() => {
    fetchRuns();
    fetchHealth();
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const data = await getModels();
      if (data?.models?.length > 0) {
        setAvailableModels(data.models);
        if (data.default) setSelectedModel(data.default);
      }
    } catch (e) {}
  };

  const fetchHealth = async () => {
    try {
      const data = await getHealth();
      if (data?.model) {
        setEngineInfo(`${data.provider ? data.provider.toUpperCase() : 'OLLAMA'} (${data.model})`);
      }
    } catch (e) {}
  };

  const fetchRuns = async () => {
    try {
      const data = await getRuns();
      setRuns(data);
    } catch (err) {
      console.error("Failed to fetch runs", err);
    } finally {
      setLoading(false);
    }
  };

  const distinctPreviousRuns = React.useMemo(() => {
    const seen = new Set();
    const list = [];
    for (const r of runs) {
      const key = `${r.target_url}___${r.goal || ''}___${r.mode || 'FOCUSED'}`;
      if (!seen.has(key)) {
        seen.add(key);
        list.push(r);
      }
    }
    return list;
  }, [runs]);

  const handleSelectPreviousRun = (runId) => {
    if (!runId) return;
    const found = runs.find(r => r.id === runId);
    if (found) {
      setTargetUrl(found.target_url || '');
      setMode(found.mode || 'FOCUSED');
      if (found.goal) setGoal(found.goal);
      if (found.model) setSelectedModel(found.model);
    }
  };

  const handleStartTest = async (e) => {
    e.preventDefault();
    if (!targetUrl.trim()) return;
    setStarting(true);
    try {
      const res = await startRun(goal, targetUrl, mode, selectedModel);
      navigate(`/agent?run_id=${res.run_id}`);
    } catch (err) {
      alert("Failed to start run: " + (err.response?.data?.detail || err.message));
    } finally {
      setStarting(false);
    }
  };

  const totalRuns = runs.length;
  const completedRuns = runs.filter(r => r.status === 'COMPLETED').length;
  const totalIssues = runs.reduce((acc, r) => acc + (r.issues ? r.issues.length : 0), 0);
  const avgHealth = totalRuns > 0 ? (runs.reduce((acc, r) => acc + (r.friction_score || 100), 0) / totalRuns).toFixed(1) : '100.0';

  const applyPreset = (presetUrl, presetMode, presetGoal) => {
    setTargetUrl(presetUrl);
    setMode(presetMode);
    setGoal(presetGoal);
  };

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[var(--surface)] border border-[var(--border)] p-4 rounded-lg">
          <span className="text-[11px] text-[var(--text-muted)] font-semibold uppercase tracking-wider block mb-1">
            Total Audits
          </span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-[var(--text)] font-mono">{totalRuns}</span>
            <Activity className="w-5 h-5 text-[var(--text-muted)]" />
          </div>
        </div>

        <div className="bg-[var(--surface)] border border-[var(--border)] p-4 rounded-lg">
          <span className="text-[11px] text-[var(--text-muted)] font-semibold uppercase tracking-wider block mb-1">
            Completed Sessions
          </span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">{completedRuns}</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          </div>
        </div>

        <div className="bg-[var(--surface)] border border-[var(--border)] p-4 rounded-lg">
          <span className="text-[11px] text-[var(--text-muted)] font-semibold uppercase tracking-wider block mb-1">
            Defects Flagged
          </span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-amber-600 dark:text-amber-400 font-mono">{totalIssues}</span>
            <AlertTriangle className="w-5 h-5 text-amber-500" />
          </div>
        </div>

        <div className="bg-[var(--surface)] border border-[var(--border)] p-4 rounded-lg">
          <span className="text-[11px] text-[var(--text-muted)] font-semibold uppercase tracking-wider block mb-1">
            Avg Health Score
          </span>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-[var(--accent)] font-mono">{avgHealth}</span>
            <span className="text-xs text-[var(--text-muted)] font-mono">/ 100</span>
          </div>
        </div>
      </div>

      {/* Main Launch Console */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-semibold tracking-tight text-[var(--text)]">
                  Launch Autonomous Audit
                </h2>
                <p className="text-xs text-[var(--text-secondary)]">
                  Configure target application URL and audit scope.
                </p>
              </div>
              <span className="text-[11px] font-mono px-2 py-1 rounded bg-[var(--surface-elevated)] border border-[var(--border)] text-[var(--text-secondary)]">
                {engineInfo}
              </span>
            </div>

            <form onSubmit={handleStartTest} className="space-y-4">
              {/* Previous Test Run Dropdown */}
              {distinctPreviousRuns.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                      <History className="w-3.5 h-3.5 text-[var(--accent)]" />
                      <span>Re-run Previous Test Run</span>
                    </label>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">Autofill config</span>
                  </div>
                  <select
                    onChange={(e) => handleSelectPreviousRun(e.target.value)}
                    defaultValue=""
                    className="w-full px-3 py-2 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
                  >
                    <option value="" disabled>Select a previous test to re-run...</option>
                    {distinctPreviousRuns.slice(0, 20).map((r) => (
                      <option key={r.id} value={r.id}>
                        [{r.mode || 'FOCUSED'}] {r.target_url} &mdash; {r.goal ? (r.goal.slice(0, 50) + (r.goal.length > 50 ? '...' : '')) : 'Audit'}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Target URL */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
                  Target Web URL
                </label>
                <div className="relative">
                  <Globe className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                  <input
                    type="url"
                    value={targetUrl}
                    onChange={(e) => setTargetUrl(e.target.value)}
                    required
                    placeholder="https://your-app.com"
                    className="w-full pl-9 pr-4 py-2 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Model Selection Dropdown */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                    Model Engine
                  </label>
                  <span className="text-[10px] text-[var(--accent)] font-medium">Active: {selectedModel}</span>
                </div>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors font-mono"
                >
                  {availableModels.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name || m.id}
                    </option>
                  ))}
                </select>
              </div>

              {/* Mode Selection */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
                  Audit Scope
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setMode("FOCUSED")}
                    className={`p-3 rounded-md border text-left transition-all ${
                      mode === "FOCUSED"
                        ? 'border-[var(--accent)] bg-[var(--accent-soft)]'
                        : 'border-[var(--border)] bg-[var(--surface-elevated)] hover:border-[var(--border-hover)]'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Compass className={`w-4 h-4 ${mode === "FOCUSED" ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]'}`} />
                      <span className={`text-xs font-semibold ${mode === "FOCUSED" ? 'text-[var(--accent)]' : 'text-[var(--text)]'}`}>
                        Focused Flow
                      </span>
                    </div>
                    <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                      Follows a specific natural language objective or user journey.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setMode("FULL_SITE")}
                    className={`p-3 rounded-md border text-left transition-all ${
                      mode === "FULL_SITE"
                        ? 'border-[var(--accent)] bg-[var(--accent-soft)]'
                        : 'border-[var(--border)] bg-[var(--surface-elevated)] hover:border-[var(--border-hover)]'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Cpu className={`w-4 h-4 ${mode === "FULL_SITE" ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]'}`} />
                      <span className={`text-xs font-semibold ${mode === "FULL_SITE" ? 'text-[var(--accent)]' : 'text-[var(--text)]'}`}>
                        Full Site Crawl
                      </span>
                    </div>
                    <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                      BFS crawler + 2–3 parallel agents testing forms, a11y, and broken links.
                    </p>
                  </button>
                </div>
              </div>

              {/* Goal Input (if focused) */}
              {mode === "FOCUSED" && (
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
                    Testing Objective
                  </label>
                  <textarea
                    rows={2}
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="Describe the end-to-end task the agent should complete and audit..."
                    className="w-full p-3 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors leading-relaxed"
                  />
                </div>
              )}

              {/* Presets */}
              <div className="pt-1">
                <span className="text-[11px] font-medium text-[var(--text-muted)] block mb-1.5">
                  Quick Presets:
                </span>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => applyPreset("http://localhost:3001", "FOCUSED", "Search for blue running shoes under $100 and complete guest checkout.")}
                    className="px-2.5 py-1 text-[11px] rounded bg-[var(--surface-elevated)] border border-[var(--border)] hover:border-[var(--border-hover)] text-[var(--text-secondary)] transition-colors"
                  >
                    Target Demo Store (Checkout)
                  </button>
                  <button
                    type="button"
                    onClick={() => applyPreset("http://localhost:3001", "FULL_SITE", "")}
                    className="px-2.5 py-1 text-[11px] rounded bg-[var(--surface-elevated)] border border-[var(--border)] hover:border-[var(--border-hover)] text-[var(--text-secondary)] transition-colors"
                  >
                    Full Site Multi-Agent Crawl
                  </button>
                  <button
                    type="button"
                    onClick={() => applyPreset("https://kmec.in", "FOCUSED", "Navigate to Admissions guidelines and verify links.")}
                    className="px-2.5 py-1 text-[11px] rounded bg-[var(--surface-elevated)] border border-[var(--border)] hover:border-[var(--border-hover)] text-[var(--text-secondary)] transition-colors"
                  >
                    KMEC Admissions Audit
                  </button>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={starting}
                  className="w-full py-2.5 px-4 bg-[var(--accent)] hover:bg-blue-600 disabled:opacity-50 text-white rounded-md text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{starting ? "Spawning Agent..." : "Start Autonomous Audit"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Recent Audits Sidebar */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Recent Audits
            </h3>
            <Link to="/runs" className="text-xs text-[var(--accent)] hover:underline font-medium">
              View all
            </Link>
          </div>

          <div className="space-y-2.5">
            {loading ? (
              <div className="text-xs text-[var(--text-muted)] text-center py-8">Loading sessions...</div>
            ) : runs.length === 0 ? (
              <div className="text-xs text-[var(--text-muted)] text-center py-8 bg-[var(--surface)] border border-[var(--border)] rounded-lg">
                No audits executed yet.
              </div>
            ) : (
              runs.slice(0, 5).map((run) => (
                <Link
                  key={run.id}
                  to={`/report/${run.id}`}
                  className="block bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-hover)] rounded-lg p-3.5 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <StatusBadge status={run.status} mode={run.mode} />
                    <span className="text-xs font-mono font-semibold text-[var(--text)]">
                      {run.friction_score !== undefined ? `${run.friction_score.toFixed(0)}/100` : '—'}
                    </span>
                  </div>
                  <div className="text-xs font-medium text-[var(--text)] truncate mb-1" title={run.target_url}>
                    {run.target_url}
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] truncate" title={run.goal}>
                    {run.goal}
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
