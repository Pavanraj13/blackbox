import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Play,
  Square,
  Activity,
  FileText,
  Clock,
  Compass,
  Cpu,
  Layers,
  History,
  Maximize2,
  X
} from 'lucide-react';
import { startRun, stopRun, getRun, getRunSteps, getModels, getRuns } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function AgentPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const runIdParam = searchParams.get('run_id');

  const [targetUrl, setTargetUrl] = useState("http://localhost:3001");
  const [mode, setMode] = useState("FOCUSED");
  const [goal, setGoal] = useState("Search for blue running shoes under $100 and complete guest checkout.");
  const [selectedModel, setSelectedModel] = useState("qwen3.6:35b");
  const [availableModels, setAvailableModels] = useState([
    { id: "qwen3.6:35b", name: "qwen3.6:35b (21.1GB) - Recommended Default" },
    { id: "qwen2.5:7b", name: "qwen2.5:7b (4.4GB) - High Speed" }
  ]);
  const [allRuns, setAllRuns] = useState([]);
  const [currentRunId, setCurrentRunId] = useState(runIdParam || null);
  const [runDetails, setRunDetails] = useState(null);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [zoomScreenshot, setZoomScreenshot] = useState(null);

  useEffect(() => {
    if (runIdParam) {
      setCurrentRunId(runIdParam);
    }
  }, [runIdParam]);

  useEffect(() => {
    fetchModels();
    fetchRuns();
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

  const fetchRuns = async () => {
    try {
      const data = await getRuns();
      if (data) setAllRuns(data);
    } catch (e) {}
  };

  const distinctPreviousRuns = useMemo(() => {
    const seen = new Set();
    const list = [];
    for (const r of allRuns) {
      const key = `${r.target_url}___${r.goal || ''}___${r.mode || 'FOCUSED'}`;
      if (!seen.has(key)) {
        seen.add(key);
        list.push(r);
      }
    }
    return list;
  }, [allRuns]);

  const handleSelectPreviousRun = (runId) => {
    if (!runId) return;
    const found = allRuns.find(r => r.id === runId);
    if (found) {
      setTargetUrl(found.target_url || '');
      setMode(found.mode || 'FOCUSED');
      if (found.goal) setGoal(found.goal);
      if (found.model) setSelectedModel(found.model);
    }
  };

  useEffect(() => {
    if (!currentRunId) return;

    const poll = async () => {
      try {
        const runData = await getRun(currentRunId);
        setRunDetails(runData);

        const stepsData = await getRunSteps(currentRunId);
        setSteps(stepsData || []);
      } catch (err) {
        console.error("Polling error:", err);
      }
    };

    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [currentRunId]);

  const handleStart = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!targetUrl.trim()) return;
    setLoading(true);
    setRunDetails(null);
    setSteps([]);

    try {
      const res = await startRun(goal, targetUrl, mode, selectedModel);
      setCurrentRunId(res.run_id);
      setSearchParams({ run_id: res.run_id });
      fetchRuns();
    } catch (err) {
      alert("Failed to start agent: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!currentRunId || stopping) return;
    setStopping(true);
    try {
      await stopRun(currentRunId);
      const data = await getRun(currentRunId);
      setRunDetails(data);
    } catch (err) {
      console.error("Failed to stop run:", err);
    } finally {
      setStopping(false);
    }
  };

  const latestStep = steps.length > 0 ? steps[steps.length - 1] : null;
  const isRunning = runDetails?.status === 'RUNNING';
  const isCompleted = runDetails?.status === 'COMPLETED';

  let latestScreenshotUrl = null;
  if (latestStep?.screenshot_path) {
    const parts = latestStep.screenshot_path.replace(/\\/g, '/').split('/');
    const folder = parts[parts.length - 2];
    const file = parts[parts.length - 1];
    latestScreenshotUrl = `http://localhost:8000/screenshots/${folder}/${file}`;
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      {/* Top Launch/Status Header */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-5">
        <form onSubmit={handleStart} className="space-y-4">
          {/* Previous Run Dropdown */}
          {distinctPreviousRuns.length > 0 && !isRunning && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                  <History className="w-3.5 h-3.5 text-[var(--accent)]" />
                  <span>Re-run Previous Test</span>
                </label>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">Autofill config</span>
              </div>
              <select
                onChange={(e) => handleSelectPreviousRun(e.target.value)}
                defaultValue=""
                disabled={isRunning}
                className="w-full px-3 py-1.5 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
              >
                <option value="" disabled>Select a previous test configuration...</option>
                {distinctPreviousRuns.slice(0, 15).map((r) => (
                  <option key={r.id} value={r.id}>
                    [{r.mode || 'FOCUSED'}] {r.target_url} &mdash; {r.goal ? (r.goal.slice(0, 45) + (r.goal.length > 45 ? '...' : '')) : 'Audit'}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
            <div className="sm:col-span-6">
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                Target Web URL
              </label>
              <input
                type="url"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                disabled={isRunning}
                placeholder="https://..."
                className="w-full px-3 py-1.5 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
              />
            </div>

            <div className="sm:col-span-3">
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                Scope Mode
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                disabled={isRunning}
                className="w-full px-3 py-1.5 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
              >
                <option value="FOCUSED">Focused Flow</option>
                <option value="FULL_SITE">Full Site Crawl</option>
              </select>
            </div>

            <div className="sm:col-span-3">
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                Model Engine
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isRunning}
                className="w-full px-3 py-1.5 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors font-mono"
              >
                {availableModels.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name || m.id}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {mode === 'FOCUSED' && (
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                Testing Goal
              </label>
              <input
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                disabled={isRunning}
                placeholder="Goal description..."
                className="w-full px-3 py-1.5 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
              />
            </div>
          )}

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2">
              {currentRunId && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-[var(--text-muted)]">
                    Session: <strong className="text-[var(--text)]">{currentRunId.slice(0, 8)}</strong>
                  </span>
                  {runDetails && (
                    <StatusBadge status={runDetails.status} mode={runDetails.mode} />
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              {isRunning ? (
                <button
                  type="button"
                  onClick={handleStop}
                  disabled={stopping}
                  className="px-3.5 py-1.5 rounded-md bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Square className="w-3 h-3 fill-current" />
                  <span>{stopping ? 'Stopping...' : 'Terminate Test'}</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-1.5 rounded-md bg-[var(--accent)] hover:bg-blue-600 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <Play className="w-3 h-3 fill-current" />
                  <span>{loading ? 'Launching...' : 'Run Audit'}</span>
                </button>
              )}

              {currentRunId && (
                <Link
                  to={`/report/${currentRunId}`}
                  className="px-3 py-1.5 rounded-md border border-[var(--border)] hover:border-[var(--border-hover)] bg-[var(--surface-elevated)] text-xs font-medium text-[var(--text)] flex items-center gap-1.5 transition-colors"
                >
                  <FileText className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>Full Report</span>
                </Link>
              )}
            </div>
          </div>
        </form>
      </div>

      {/* Live Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Live Browser Viewport */}
        <div className="lg:col-span-7 bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4 flex flex-col justify-between min-h-[440px]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border)] mb-3">
              <span className="text-xs font-semibold tracking-tight text-[var(--text)] flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Rendered Browser Viewport</span>
              </span>
              {isRunning && (
                <span className="flex items-center gap-1 text-[11px] text-blue-600 dark:text-blue-400 font-mono">
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
                  Live Sync
                </span>
              )}
            </div>

            {latestScreenshotUrl ? (
              <div
                className="relative rounded overflow-hidden border border-[var(--border)] bg-black/20 group cursor-pointer"
                onClick={() => setZoomScreenshot(latestScreenshotUrl)}
                title="Click to view full resolution"
              >
                <img
                  src={latestScreenshotUrl}
                  alt="Live agent browser state"
                  className="w-full h-auto object-contain max-h-[380px]"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                  <span className="px-2.5 py-1 rounded bg-black/80 text-white text-[11px] font-mono flex items-center gap-1.5 shadow">
                    <Maximize2 className="w-3.5 h-3.5" />
                    Expand Viewport
                  </span>
                </div>
              </div>
            ) : (
              <div className="h-[340px] flex flex-col items-center justify-center text-xs text-[var(--text-muted)] font-mono border border-dashed border-[var(--border)] rounded">
                <span>Waiting for initial browser frame...</span>
              </div>
            )}
          </div>

          {latestStep && (
            <div className="mt-3 pt-3 border-t border-[var(--border)] flex items-center justify-between text-xs text-[var(--text-muted)] font-mono">
              <span className="truncate max-w-sm">{latestStep.url}</span>
              {latestStep.duration_ms > 0 && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{(latestStep.duration_ms / 1000).toFixed(2)}s</span>
                </span>
              )}
            </div>
          )}
        </div>

        {/* Step-by-Step Action Timeline */}
        <div className="lg:col-span-5 bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4 flex flex-col h-[520px]">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border)] mb-3">
            <span className="text-xs font-semibold tracking-tight text-[var(--text)]">
              Action Timeline ({steps.length} Steps)
            </span>
            <span className="text-[11px] font-mono text-[var(--text-muted)]">
              Score: {runDetails?.friction_score !== undefined ? `${runDetails.friction_score.toFixed(0)}/100` : '100/100'}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {steps.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-[var(--text-muted)] font-mono">
                No actions taken yet.
              </div>
            ) : (
              steps.map((step) => (
                <div
                  key={step.id}
                  className="p-3 rounded-md bg-[var(--surface-elevated)] border border-[var(--border)] space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-semibold text-[var(--text-muted)]">
                      STEP #{step.step_number}
                    </span>
                    <span className="text-[11px] font-semibold text-[var(--text)]">
                      {step.action}
                    </span>
                  </div>

                  {step.target && (
                    <div className="text-xs font-medium text-[var(--accent)] truncate">
                      {step.target}
                    </div>
                  )}

                  <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                    {step.reason}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Full-resolution Viewport Zoom Modal */}
      {zoomScreenshot && (
        <div
          className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4 backdrop-blur-sm"
          onClick={() => setZoomScreenshot(null)}
        >
          <div
            className="relative max-w-6xl w-full max-h-[92vh] bg-[var(--surface)] border border-[var(--border)] rounded-lg overflow-hidden flex flex-col shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)] bg-[var(--surface-elevated)]">
              <span className="text-xs font-mono font-medium text-[var(--text)]">
                Rendered Browser Viewport &bull; Live Frame
              </span>
              <button
                onClick={() => setZoomScreenshot(null)}
                className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)] transition-colors"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="overflow-auto max-h-[84vh] bg-black/30 flex items-center justify-center p-3">
              <img
                src={zoomScreenshot}
                alt="Full resolution browser frame"
                className="max-w-full h-auto rounded object-contain shadow-lg"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
