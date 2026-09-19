import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Play, Square, Activity, CheckCircle, AlertTriangle, FileText, Camera, ArrowRight } from 'lucide-react';
import { startRun, stopRun, getRun, getRunSteps } from '../services/api';

export default function AgentPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const runIdParam = searchParams.get('run_id');

  const [goal, setGoal] = useState("Search for blue running shoes under $100 and complete guest checkout.");
  const [targetUrl, setTargetUrl] = useState("http://localhost:3001");
  const [currentRunId, setCurrentRunId] = useState(runIdParam || null);
  const [runDetails, setRunDetails] = useState(null);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (runIdParam) {
      setCurrentRunId(runIdParam);
    }
  }, [runIdParam]);

  // Polling loop for active run status & steps
  useEffect(() => {
    if (!currentRunId) return;

    const poll = async () => {
      try {
        const runData = await getRun(currentRunId);
        setRunDetails(runData);

        const stepsData = await getRunSteps(currentRunId);
        setSteps(stepsData);
      } catch (err) {
        console.error("Polling error:", err);
      }
    };

    poll();
    const interval = setInterval(poll, 1500);
    return () => clearInterval(interval);
  }, [currentRunId]);

  const handleStart = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!goal.trim()) return;
    setLoading(true);
    setRunDetails(null);
    setSteps([]);
    try {
      const res = await startRun(goal, targetUrl);
      setCurrentRunId(res.run_id);
      setSearchParams({ run_id: res.run_id });
    } catch (err) {
      alert("Failed to start test run: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!currentRunId) return;
    try {
      await stopRun(currentRunId);
    } catch (err) {
      console.error("Failed to stop run:", err);
    }
  };

  const latestStep = steps.length > 0 ? steps[steps.length - 1] : null;
  const isRunning = runDetails?.status === 'RUNNING';
  const isCompleted = runDetails?.status === 'COMPLETED';

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Controls Bar */}
      <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl space-y-4">
        <form onSubmit={handleStart} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div className="md:col-span-1">
            <label className="block text-xs font-semibold text-slate-400 mb-1">Target URL</label>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              disabled={isRunning}
            />
          </div>

          <div className="md:col-span-3">
            <label className="block text-xs font-semibold text-slate-400 mb-1">Testing Goal</label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              disabled={isRunning}
            />
          </div>

          <div className="md:col-span-1 flex gap-2">
            {!isRunning ? (
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs py-3 px-4 rounded-xl shadow-lg shadow-cyan-500/20 transition flex items-center justify-center gap-1.5"
              >
                <Play size={14} /> START TEST
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStop}
                className="w-full bg-rose-500 hover:bg-rose-600 text-white font-bold text-xs py-3 px-4 rounded-xl shadow-lg shadow-rose-500/20 transition flex items-center justify-center gap-1.5"
              >
                <Square size={14} /> STOP AGENT
              </button>
            )}
          </div>
        </form>

        {/* Live Status Bar */}
        {runDetails && (
          <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center gap-3">
              <span className="text-slate-400">STATUS:</span>
              <span className={`px-2.5 py-1 rounded-full font-bold uppercase ${
                runDetails.status === 'RUNNING' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 animate-pulse' :
                runDetails.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
                'bg-slate-800 text-slate-400'
              }`}>
                {runDetails.status}
              </span>
              <span className="text-slate-500">Run ID: {runDetails.id.slice(0, 8)}</span>
            </div>

            {latestStep && (
              <div className="flex items-center gap-4 text-slate-300">
                <span>Step: <strong className="text-white">{latestStep.step_number}</strong></span>
                <span>Action: <strong className="text-cyan-400">{latestStep.action}</strong></span>
                <span>Confidence: <strong className="text-emerald-400">{(latestStep.confidence * 100).toFixed(0)}%</strong></span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Agent Split Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Center: Live Screenshot Feed (7 Cols) */}
        <div className="lg:col-span-7 bg-[#0f172a] border border-slate-800 rounded-2xl p-5 flex flex-col justify-between min-h-[480px]">
          <div className="flex justify-between items-center pb-3 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Camera size={16} className="text-cyan-400" /> Live Browser Observation
            </h3>
            {latestStep && (
              <span className="text-xs text-slate-400 font-mono truncate max-w-xs">{latestStep.url}</span>
            )}
          </div>

          <div className="my-4 flex-1 flex items-center justify-center bg-slate-950 rounded-xl border border-slate-800 overflow-hidden relative min-h-[360px]">
            {latestStep && latestStep.screenshot_path ? (
              <img
                src={`http://localhost:8000/screenshots/run_${currentRunId}/${latestStep.screenshot_path.split(/[\\/]/).pop()}`}
                alt="Current step observation"
                className="w-full h-auto object-contain max-h-[460px] rounded"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            ) : (
              <div className="text-center p-8 text-slate-600 space-y-2">
                <Activity size={32} className="mx-auto text-slate-700 animate-bounce" />
                <p className="text-xs">Waiting for agent observation screenshot...</p>
              </div>
            )}
          </div>

          {latestStep && (
            <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-xs text-slate-300 flex items-center justify-between">
              <span className="truncate">Target: <strong className="text-cyan-400">{latestStep.target || 'Page Viewport'}</strong></span>
              <span className="font-mono text-slate-500">{new Date(latestStep.timestamp).toLocaleTimeString()}</span>
            </div>
          )}
        </div>

        {/* Right: Reasoning & Action Timeline (5 Cols) */}
        <div className="lg:col-span-5 bg-[#0f172a] border border-slate-800 rounded-2xl p-5 flex flex-col justify-between max-h-[560px]">
          <h3 className="text-sm font-bold text-white pb-3 border-b border-slate-800 flex items-center justify-between">
            <span>Agent Reasoning Timeline</span>
            <span className="text-xs font-mono text-cyan-400">{steps.length} Steps</span>
          </h3>

          <div className="my-3 overflow-y-auto space-y-3 pr-2 flex-1">
            {steps.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No steps executed yet. Start a run to watch real-time AI reasoning.
              </div>
            ) : (
              steps.map((step) => (
                <div key={step.id} className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-cyan-400 font-bold">STEP {step.step_number}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      step.action === 'CLICK' ? 'bg-cyan-500/20 text-cyan-400' :
                      step.action === 'TYPE' ? 'bg-indigo-500/20 text-indigo-400' :
                      step.action === 'FINISH' ? 'bg-emerald-500/20 text-emerald-400' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      {step.action}
                    </span>
                  </div>

                  {step.target && (
                    <div className="text-white font-medium truncate">Target: {step.target}</div>
                  )}

                  <p className="text-slate-400 text-[11px] leading-relaxed">{step.reason}</p>

                  {step.thinking && (
                    <details className="mt-1 text-[10px] text-cyan-300/90 bg-slate-950/70 p-2 rounded-lg border border-cyan-900/40">
                      <summary className="cursor-pointer font-mono font-semibold text-cyan-400 hover:text-cyan-300 select-none">
                        🧠 View AI Chain-of-Thought
                      </summary>
                      <div className="mt-1.5 font-mono whitespace-pre-wrap text-slate-300 max-h-40 overflow-y-auto leading-normal">
                        {step.thinking}
                      </div>
                    </details>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Completion banner */}
          {isCompleted && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle size={16} /> GOAL COMPLETED SUCCESSFULLY
              </div>
              <p className="text-slate-300 text-[11px]">The agent executed {steps.length} autonomous steps and verified guest checkout completion.</p>
              <Link
                to={`/report/${currentRunId}`}
                className="inline-flex items-center gap-1 bg-emerald-500 text-slate-950 px-3 py-1.5 rounded-lg font-bold text-xs hover:bg-emerald-400 transition"
              >
                VIEW FULL AUDIT REPORT <ArrowRight size={12} />
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Trajectory Flow */}
      {steps.length > 0 && (
        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl space-y-3">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Step Trajectory Trace</h4>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {steps.map((step) => (
              <div key={step.id} className="min-w-[140px] bg-slate-900 border border-slate-800 p-3 rounded-xl space-y-1 flex-shrink-0 text-xs">
                <span className="text-[10px] font-mono text-slate-500">Step {step.step_number}</span>
                <div className="font-bold text-cyan-400">{step.action}</div>
                <div className="text-slate-300 truncate text-[11px]">{step.target || 'Page'}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
