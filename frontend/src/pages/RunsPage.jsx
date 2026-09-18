import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { History, Eye, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { getRuns } from '../services/api';

export default function RunsPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRuns();
  }, []);

  const fetchRuns = async () => {
    try {
      const data = await getRuns();
      setRuns(data);
    } catch (err) {
      console.error("Error fetching runs:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <History className="text-cyan-400" /> Historical Test Runs
          </h2>
          <p className="text-xs text-slate-400">Review past autonomous black-box audit runs and metrics.</p>
        </div>

        <Link
          to="/agent"
          className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-4 py-2 rounded-xl font-bold text-xs flex items-center gap-1.5 transition"
        >
          <Play size={14} /> NEW TEST RUN
        </Link>
      </div>

      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading run history...</div>
        ) : runs.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <p>No test runs found.</p>
            <Link to="/agent" className="text-xs text-cyan-400 underline">Start your first autonomous test run</Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-4">Run ID</th>
                  <th className="p-4">Testing Goal</th>
                  <th className="p-4">Target URL</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Steps</th>
                  <th className="p-4">Friction Score</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4 text-right">Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {runs.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40 transition">
                    <td className="p-4 font-mono text-xs text-cyan-400 font-bold">{r.id.slice(0, 8)}</td>
                    <td className="p-4 max-w-sm truncate text-slate-200">{r.goal}</td>
                    <td className="p-4 font-mono text-xs text-slate-400">{r.target_url}</td>
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
                    <td className="p-4 font-bold">
                      <span className={r.friction_score >= 80 ? 'text-emerald-400' : r.friction_score >= 50 ? 'text-amber-400' : 'text-rose-400'}>
                        {r.friction_score}/100
                      </span>
                    </td>
                    <td className="p-4 font-mono text-xs text-slate-500">
                      {new Date(r.started_at).toLocaleString()}
                    </td>
                    <td className="p-4 text-right">
                      <Link
                        to={`/report/${r.id}`}
                        className="inline-flex items-center gap-1 text-xs font-bold text-cyan-400 hover:underline bg-cyan-500/10 px-3 py-1.5 rounded-lg border border-cyan-500/20"
                      >
                        <Eye size={14} /> Audit Report
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
