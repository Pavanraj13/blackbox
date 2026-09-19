import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Square, ExternalLink, Search, Filter, Trash2, AlertCircle } from 'lucide-react';
import { getRuns, stopRun, deleteRun, deleteAllRuns } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function RunsPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stoppingId, setStoppingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [clearingAll, setClearingAll] = useState(false);
  const [search, setSearch] = useState('');
  const [modeFilter, setModeFilter] = useState('ALL');

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(() => {
      fetchRuns(true);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchRuns = async (silent = false) => {
    try {
      const data = await getRuns();
      setRuns(data);
    } catch (err) {
      if (!silent) console.error("Error fetching runs:", err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const handleStopRun = async (runId) => {
    try {
      setStoppingId(runId);
      await stopRun(runId);
      await fetchRuns(true);
    } catch (err) {
      console.error("Failed to stop run:", err);
    } finally {
      setStoppingId(null);
    }
  };

  const handleDeleteRun = async (runId) => {
    if (!window.confirm("Are you sure you want to delete this test run and all its screenshots and logs?")) {
      return;
    }
    try {
      setDeletingId(runId);
      await deleteRun(runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
    } catch (err) {
      alert("Failed to delete run: " + (err.response?.data?.detail || err.message));
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm("Are you sure you want to delete ALL test runs, screenshots, and logs? This cannot be undone.")) {
      return;
    }
    try {
      setClearingAll(true);
      await deleteAllRuns();
      setRuns([]);
    } catch (err) {
      alert("Failed to clear logs: " + (err.response?.data?.detail || err.message));
    } finally {
      setClearingAll(false);
    }
  };

  const filteredRuns = runs.filter((r) => {
    const matchesSearch =
      (r.target_url || '').toLowerCase().includes(search.toLowerCase()) ||
      (r.goal || '').toLowerCase().includes(search.toLowerCase()) ||
      r.id.toLowerCase().includes(search.toLowerCase());
    const matchesMode =
      modeFilter === 'ALL' || (r.mode || 'FOCUSED').toUpperCase() === modeFilter;
    return matchesSearch && matchesMode;
  });

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[var(--text)] mb-1">
            Audit Test Sessions
          </h1>
          <p className="text-xs text-[var(--text-secondary)]">
            Review previous autonomous test runs, dynamic health scores, and defect breakdowns.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {runs.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={clearingAll}
              className="px-3 py-2 rounded-md border border-rose-500/30 hover:bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs font-medium inline-flex items-center gap-1.5 transition-colors"
              title="Delete all test runs and screenshots"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{clearingAll ? 'Clearing...' : 'Clear All Logs'}</span>
            </button>
          )}
          <Link
            to="/"
            className="px-3.5 py-2 rounded-md bg-[var(--accent)] hover:bg-blue-600 text-white text-xs font-semibold inline-flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>New Audit</span>
          </Link>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by URL, goal, or ID..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-[var(--surface)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          <span className="text-[11px] text-[var(--text-muted)] font-medium mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Scope:
          </span>
          {['ALL', 'FOCUSED', 'FULL_SITE'].map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setModeFilter(m)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                modeFilter === m
                  ? 'bg-[var(--accent)] text-white'
                  : 'bg-[var(--surface)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text)]'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Runs Table */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-16 text-center text-xs text-[var(--text-muted)] font-mono">
            Loading run history...
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="p-16 text-center text-xs text-[var(--text-muted)] font-mono space-y-2">
            <p>No audit sessions match criteria.</p>
            <Link to="/" className="text-xs text-[var(--accent)] hover:underline">
              Launch a new test audit
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[var(--text-secondary)]">
              <thead className="bg-[var(--surface-elevated)] text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] border-b border-[var(--border)]">
                <tr>
                  <th className="p-3.5">Session ID</th>
                  <th className="p-3.5">Scope &amp; Status</th>
                  <th className="p-3.5">Model</th>
                  <th className="p-3.5">Target Application</th>
                  <th className="p-3.5">Steps</th>
                  <th className="p-3.5">Health Score</th>
                  <th className="p-3.5">Started</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {filteredRuns.map((r) => {
                  const isRunning = r.status === 'RUNNING';
                  const dateStr = r.started_at
                    ? new Date(r.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    : 'Recently';

                  return (
                    <tr
                      key={r.id}
                      className="hover:bg-[var(--surface-elevated)] transition-colors"
                    >
                      <td className="p-3.5 font-mono text-[11px] text-[var(--text)] font-semibold">
                        <Link to={`/report/${r.id}`} className="hover:text-[var(--accent)]">
                          {r.id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="p-3.5">
                        <StatusBadge status={r.status} mode={r.mode} />
                      </td>
                      <td className="p-3.5">
                        <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[var(--surface-elevated)] border border-[var(--border)] text-[var(--text-secondary)]">
                          {r.model || 'qwen3.6:35b'}
                        </span>
                      </td>
                      <td className="p-3.5 max-w-xs">
                        <div className="font-medium text-[var(--text)] truncate" title={r.target_url}>
                          {r.target_url}
                        </div>
                        <div className="text-[11px] text-[var(--text-muted)] truncate" title={r.goal}>
                          {r.goal}
                        </div>
                      </td>
                      <td className="p-3.5 font-mono text-[var(--text)] font-medium">
                        {r.steps_count}
                      </td>
                      <td className="p-3.5">
                        <span className="font-mono font-bold text-xs text-[var(--text)]">
                          {r.friction_score !== undefined ? `${r.friction_score.toFixed(0)}/100` : '—'}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-[11px] text-[var(--text-muted)]">
                        {dateStr}
                      </td>
                      <td className="p-3.5 text-right space-x-1.5 whitespace-nowrap">
                        {isRunning && (
                          <button
                            onClick={() => handleStopRun(r.id)}
                            disabled={stoppingId === r.id}
                            className="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30 text-[11px] font-semibold transition-colors"
                          >
                            {stoppingId === r.id ? 'Stopping...' : 'Stop'}
                          </button>
                        )}
                        <Link
                          to={`/report/${r.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[var(--surface-elevated)] border border-[var(--border)] hover:border-[var(--border-hover)] text-[11px] font-medium text-[var(--text)] transition-colors"
                        >
                          <span>Report</span>
                          <ExternalLink className="w-3 h-3 text-[var(--text-muted)]" />
                        </Link>
                        <button
                          onClick={() => handleDeleteRun(r.id)}
                          disabled={deletingId === r.id}
                          className="inline-flex items-center p-1.5 rounded hover:bg-rose-500/10 text-[var(--text-muted)] hover:text-rose-500 border border-transparent hover:border-rose-500/20 transition-colors align-middle"
                          title="Delete run & logs"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
