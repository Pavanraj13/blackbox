import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { FileText, CheckCircle2, AlertTriangle, ShieldAlert, ArrowLeft, ExternalLink, Camera } from 'lucide-react';
import { getRun, getRunSteps, getRunIssues } from '../services/api';

export default function ReportPage() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [steps, setSteps] = useState([]);
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedScreenshot, setSelectedScreenshot] = useState(null);

  useEffect(() => {
    fetchReportData();
  }, [id]);

  const fetchReportData = async () => {
    try {
      const runData = await getRun(id);
      setRun(runData);

      const stepsData = await getRunSteps(id);
      setSteps(stepsData);

      const issuesData = await getRunIssues(id);
      setIssues(issuesData);
    } catch (err) {
      console.error("Error fetching report data:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500">Loading audit report data...</div>;
  }

  if (!run) {
    return <div className="p-12 text-center text-slate-500">Audit report not found for run ID: {id}</div>;
  }

  const uxIssues = issues.filter(i => i.type === 'FRICTION');
  const a11yIssues = issues.filter(i => i.type === 'ACCESSIBILITY');

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="space-y-1">
          <Link to="/runs" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-cyan-400">
            <ArrowLeft size={14} /> Back to Runs
          </Link>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <FileText className="text-cyan-400" /> Autonomous UI/UX & Accessibility Audit Report
          </h1>
          <p className="text-xs text-slate-400 font-mono">Run ID: {run.id}</p>
        </div>

        <a
          href={`http://localhost:8000/api/runs/${run.id}/report`}
          target="_blank"
          rel="noreferrer"
          className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 transition shadow-lg shadow-cyan-500/20"
        >
          <ExternalLink size={14} /> Open Standalone HTML Report
        </a>
      </div>

      {/* Goal Banner */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Test Goal</span>
        <h3 className="text-lg font-bold text-white">{run.goal}</h3>
        <p className="text-xs text-slate-400 font-mono">Target App: {run.target_url}</p>
      </div>

      {/* KPI Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs text-slate-400 font-semibold uppercase">Total Steps</span>
          <div className="text-3xl font-extrabold text-white mt-2">{run.steps_count}</div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs text-slate-400 font-semibold uppercase">Screens Visited</span>
          <div className="text-3xl font-extrabold text-cyan-400 mt-2">{run.screens_count}</div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs text-slate-400 font-semibold uppercase">Paths Discovered</span>
          <div className="text-3xl font-extrabold text-indigo-400 mt-2">{run.paths_count}</div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs text-slate-400 font-semibold uppercase">Friction Score</span>
          <div className={`text-3xl font-extrabold mt-2 ${
            run.friction_score >= 80 ? 'text-emerald-400' : run.friction_score >= 50 ? 'text-amber-400' : 'text-rose-400'
          }`}>
            {run.friction_score} / 100
          </div>
        </div>
      </div>

      {/* Findings Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* UX Friction Findings */}
        <div className="bg-[#0f172a] border border-slate-800 p-6 rounded-2xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <AlertTriangle className="text-amber-400" size={18} /> UX Friction Findings ({uxIssues.length})
          </h3>

          {uxIssues.length === 0 ? (
            <p className="text-xs text-slate-500">No UX friction issues detected.</p>
          ) : (
            <div className="space-y-3">
              {uxIssues.map((issue) => (
                <div key={issue.id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-amber-400">{issue.title}</span>
                    <span className="text-[10px] uppercase font-bold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px]">{issue.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Accessibility Findings */}
        <div className="bg-[#0f172a] border border-slate-800 p-6 rounded-2xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <ShieldAlert className="text-rose-400" size={18} /> Accessibility Findings ({a11yIssues.length})
          </h3>

          {a11yIssues.length === 0 ? (
            <p className="text-xs text-slate-500">No accessibility issues detected.</p>
          ) : (
            <div className="space-y-3">
              {a11yIssues.map((issue) => (
                <div key={issue.id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-rose-400">{issue.title}</span>
                    <span className="text-[10px] uppercase font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px]">{issue.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Trajectory Screenshots Trace */}
      <div className="bg-[#0f172a] border border-slate-800 p-6 rounded-2xl space-y-6">
        <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
          <Camera className="text-cyan-400" size={18} /> Execution Trajectory & Screenshots
        </h3>

        <div className="space-y-4">
          {steps.map((step) => {
            const shotFilename = step.screenshot_path ? step.screenshot_path.split(/[\\/]/).pop() : null;
            const shotUrl = shotFilename ? `http://localhost:8000/screenshots/run_${run.id}/${shotFilename}` : null;

            return (
              <div key={step.id} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-6 items-start">
                {shotUrl && (
                  <img
                    src={shotUrl}
                    alt={`Step ${step.step_number}`}
                    className="w-full md:w-64 rounded-lg border border-slate-800 cursor-pointer hover:opacity-90 transition"
                    onClick={() => setSelectedScreenshot(shotUrl)}
                  />
                )}
                <div className="flex-1 space-y-2 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-cyan-400 font-extrabold text-sm">STEP #{step.step_number}</span>
                    <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase bg-cyan-500/20 text-cyan-400">
                      {step.action}
                    </span>
                  </div>

                  {step.target && (
                    <div className="text-white font-semibold text-sm">Target: {step.target}</div>
                  )}

                  <p className="text-slate-300 leading-relaxed">{step.reason}</p>

                  <div className="text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800/80">
                    Confidence: {(step.confidence * 100).toFixed(0)}% | URL: {step.url}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Screenshot Lightbox Modal */}
      {selectedScreenshot && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur z-50 flex items-center justify-center p-4" onClick={() => setSelectedScreenshot(null)}>
          <div className="max-w-4xl bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-2">
            <img src={selectedScreenshot} alt="Full screenshot view" className="w-full h-auto max-h-[80vh] rounded-lg" />
            <p className="text-center text-xs text-slate-400">Click anywhere to close preview</p>
          </div>
        </div>
      )}
    </div>
  );
}
