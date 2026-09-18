import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Play, Activity, AlertTriangle, Eye, ShieldAlert, CheckCircle2, ArrowRight } from 'lucide-react';
import { getRuns, startRun } from '../services/api';

export default function Dashboard() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [goal, setGoal] = useState("Search for blue running shoes under $100 and complete guest checkout.");
  const [targetUrl, setTargetUrl] = useState("http://localhost:3001");
  const [starting, setStarting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRuns();
  }, []);

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

  const handleStartTest = async (e) => {
    e.preventDefault();
    if (!goal.trim()) return;
    setStarting(true);
    try {
      const res = await startRun(goal, targetUrl);
      navigate(`/agent?run_id=${res.run_id}`);
    } catch (err) {
      alert("Failed to start run: " + (err.response?.data?.detail || err.message));
    } finally {
      setStarting(false);
    }
  };

  const totalRuns = runs.length;
  const completedRuns = runs.filter(r => r.status === 'COMPLETED').length;
  const totalUXIssues = runs.reduce((acc, r) => acc + (r.issues ? r.issues.filter(i => i.type === 'FRICTION').length : 0), 0);
  const totalA11yIssues = runs.reduce((acc, r) => acc + (r.issues ? r.issues.filter(i => i.type === 'ACCESSIBILITY').length : 0), 0);
  const avgFriction = totalRuns > 0 ? (runs.reduce((acc, r) => acc + (r.friction_score || 100), 0) / totalRuns).toFixed(1) : '100.0';

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl space-y-2">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Total Runs</span>
          <div className="flex items-center justify-between">
            <span className="text-3xl font-extrabold text-white">{totalRuns}</span>
            <Activity className="text-cyan-400" size={24} />
          </div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl space-y-2">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Successful Runs</span>
          <div className="flex items-center justify-between">
            <span className="text-3xl font-extrabold text-emerald-400">{completedRuns}</span>
            <CheckCircle2 className="text-emerald-400" size={24} />
          </div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl space-y-2">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">UX Friction Issues</span>
          <div className="flex items-center justify-between">
            <span className="text-3xl font-extrabold text-amber-400">{totalUXIssues}</span>
            <AlertTriangle className="text-amber-400" size={24} />
          </div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl space-y-2">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">A11y Violations</span>
          <div className="flex items-center justify-between">
            <span className="text-3xl font-extrabold text-rose-400">{totalA11yIssues}</span>
            <ShieldAlert className="text-rose-400" size={24} />
          </div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 p-5 rounded-2xl space-y-2">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Avg Friction Score</span>
          <div className="flex items-center justify-between">
            <span className="text-3xl font-extrabold text-cyan-400">{avgFriction}</span>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
        </div>
      </div>

      {/* Quick Launch Panel */}
      <div className="bg-gradient-to-r from-slate-900 via-[#0f172a] to-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Play className="text-cyan-400" size={20} /> Launch New Autonomous Test
            </h3>
            <p className="text-xs text-slate-400">Specify a natural language goal. The black-box agent will explore Chrome autonomously.</p>
          </div>
        </div>

        <form onSubmit={handleStartTest} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-1">
            <label className="block text-xs font-semibold text-slate-400 mb-1">Target Application URL</label>
            <input
              type="url"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-400 mb-1">Natural Language Testing Goal</label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Find blue running shoes under $100 and complete guest checkout."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div className="md:col-span-1 flex items-end">
            <button
              type="submit"
              disabled={starting}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold py-3 px-6 rounded-xl transition duration-200 shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2"
            >
              {starting ? 'Initializing...' : 'START AUTONOMOUS TEST'}
            </button>
          </div>
        </form>
      </div>

      {/* Recent Test Runs Table */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <h3 className="text-base font-bold text-white">Recent Audit Runs</h3>
          <Link to="/runs" className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
            View All Runs <ArrowRight size={14} />
          </Link>
        </div>

        {runs.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <p>No audit runs recorded yet.</p>
            <p className="text-xs text-slate-600">Enter a goal above and click Start Autonomous Test!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-4">Run ID</th>
                  <th className="p-4">Goal</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Steps</th>
                  <th className="p-4">Friction Score</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {runs.slice(0, 5).map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40 transition">
                    <td className="p-4 font-mono text-xs text-cyan-400 font-semibold">{r.id.slice(0, 8)}</td>
                    <td className="p-4 max-w-xs truncate text-slate-200">{r.goal}</td>
                    <td className="p-4">
                      <span className={`inline-block px-2.5 py-1 text-xs font-bold rounded-full ${
                        r.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        r.status === 'RUNNING' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="p-4 font-mono">{r.steps_count}</td>
                    <td className="p-4">
                      <span className={`font-bold ${r.friction_score >= 80 ? 'text-emerald-400' : r.friction_score >= 50 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {r.friction_score}/100
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <Link
                        to={`/report/${r.id}`}
                        className="inline-flex items-center gap-1 text-xs font-bold text-cyan-400 hover:underline"
                      >
                        <Eye size={14} /> Report
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
