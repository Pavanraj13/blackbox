import React, { useEffect, useState } from 'react';
import { AlertTriangle, ShieldAlert, Filter, ExternalLink } from 'lucide-react';
import { getRuns } from '../services/api';

export default function FindingsPage() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [sevFilter, setSevFilter] = useState('ALL');

  useEffect(() => {
    fetchFindings();
  }, []);

  const fetchFindings = async () => {
    try {
      const runs = await getRuns();
      let allIssues = [];
      runs.forEach(r => {
        if (r.issues && r.issues.length > 0) {
          r.issues.forEach(i => {
            allIssues.push({ ...i, run_goal: r.goal, run_id: r.id });
          });
        }
      });
      setIssues(allIssues);
    } catch (err) {
      console.error("Error fetching findings:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredIssues = issues.filter(i => {
    const matchType = typeFilter === 'ALL' || i.type === typeFilter;
    const matchSev = sevFilter === 'ALL' || i.severity === sevFilter;
    return matchType && matchSev;
  });

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <AlertTriangle className="text-amber-400" /> Discovered Findings & Defects
          </h2>
          <p className="text-xs text-slate-400">Automated accessibility violations and UX friction points detected by black-box observation.</p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none"
          >
            <option value="ALL">All Finding Types</option>
            <option value="ACCESSIBILITY">Accessibility Only</option>
            <option value="FRICTION">UX Friction Only</option>
          </select>

          <select
            value={sevFilter}
            onChange={(e) => setSevFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="HIGH">High Severity</option>
            <option value="MEDIUM">Medium Severity</option>
            <option value="LOW">Low Severity</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500">Loading findings database...</div>
      ) : filteredIssues.length === 0 ? (
        <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-12 text-center text-slate-500 space-y-2">
          <ShieldAlert size={36} className="mx-auto text-slate-600" />
          <p>No matching findings recorded.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredIssues.map((issue, idx) => (
            <div
              key={`${issue.id}-${idx}`}
              className={`bg-[#0f172a] border border-slate-800 p-5 rounded-2xl border-l-4 space-y-3 ${
                issue.severity === 'HIGH' ? 'border-l-rose-500' :
                issue.severity === 'MEDIUM' ? 'border-l-amber-500' :
                'border-l-cyan-500'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    issue.type === 'ACCESSIBILITY' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {issue.type}
                  </span>
                  <h4 className="font-bold text-base text-white">{issue.title}</h4>
                </div>

                <span className={`px-2.5 py-0.5 rounded text-xs font-extrabold uppercase ${
                  issue.severity === 'HIGH' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                  issue.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                  'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                }`}>
                  {issue.severity}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{issue.description}</p>

              {issue.element_summary && (
                <div className="bg-slate-950 p-2.5 rounded-lg text-xs font-mono text-cyan-300/80 border border-slate-800 truncate">
                  {issue.element_summary}
                </div>
              )}

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800/60">
                <span>Step #{issue.step_number} | URL: <span className="text-slate-400">{issue.url}</span></span>
                <span>Run ID: <strong className="text-cyan-400">{issue.run_id.slice(0, 8)}</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
