import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Square,
  Download,
  ExternalLink,
  ShieldCheck,
  FileCode,
  Layers,
  Clock,
  Globe,
  Trash2,
  History,
  ChevronLeft,
  ChevronRight,
  X
} from 'lucide-react';
import { getRun, getRunSteps, getRunIssues, getRuns, stopRun, deleteRun } from '../services/api';
import ScoreRing from '../components/ScoreRing';
import StatusBadge from '../components/StatusBadge';
import IssueCard from '../components/IssueCard';

export default function ReportPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [steps, setSteps] = useState([]);
  const [issues, setIssues] = useState([]);
  const [allRuns, setAllRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stopping, setStopping] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [stepFilter, setStepFilter] = useState('ALL');
  const [selectedScreenshot, setSelectedScreenshot] = useState(null);

  useEffect(() => {
    fetchReportData();
    const interval = setInterval(() => {
      fetchReportData();
    }, 2500);
    return () => clearInterval(interval);
  }, [id]);

  const fetchReportData = async () => {
    try {
      const [runData, stepsData, issuesData, runsData] = await Promise.all([
        getRun(id),
        getRunSteps(id),
        getRunIssues(id),
        getRuns().catch(() => [])
      ]);
      setRun(runData);
      setSteps(stepsData || []);
      setIssues(issuesData || []);
      if (runsData) setAllRuns(runsData);
    } catch (err) {
      console.error("Error fetching report data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStopRun = async () => {
    if (!id || stopping) return;
    setStopping(true);
    try {
      await stopRun(id);
      await fetchReportData();
    } catch (err) {
      alert("Failed to stop test: " + (err.response?.data?.detail || err.message));
    } finally {
      setStopping(false);
    }
  };

  const handleDeleteRun = async () => {
    if (!window.confirm("Are you sure you want to delete this test run and all its screenshots and logs?")) {
      return;
    }
    try {
      setDeleting(true);
      await deleteRun(id);
      navigate('/runs');
    } catch (err) {
      alert("Failed to delete run: " + (err.response?.data?.detail || err.message));
    } finally {
      setDeleting(false);
    }
  };

  if (loading && !run) {
    return (
      <div className="p-16 text-center text-xs text-[var(--text-muted)] font-mono">
        Loading audit report data...
      </div>
    );
  }

  if (!run) {
    return (
      <div className="p-16 text-center text-xs text-rose-500 font-mono">
        Audit report not found for run ID: {id}
      </div>
    );
  }

  const isRunning = run.status === 'RUNNING';
  const categoryScores = run.category_scores || {
    accessibility: 100,
    friction: 100,
    security: 100,
    performance: 100,
    broken_links: 100
  };

  const filteredIssues = issues.filter(i => {
    if (categoryFilter === 'ALL') return true;
    const cat = (i.category || i.type || '').toUpperCase();
    return cat === categoryFilter;
  });

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Navigation & Header */}
      <div className="border-b border-[var(--border)] pb-6 space-y-4">
        <Link
          to="/runs"
          className="inline-flex items-center gap-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Runs</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5 flex-wrap">
              <h1 className="text-xl font-semibold tracking-tight text-[var(--text)]">
                Audit Report &mdash; {run.id.slice(0, 8)}
              </h1>
              <StatusBadge status={run.status} mode={run.mode} />
              <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[var(--surface-elevated)] border border-[var(--border)] text-[var(--text-secondary)]">
                {run.model || 'qwen3.6:35b'}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--text-secondary)] font-mono">
              <span className="flex items-center gap-1">
                <Globe className="w-3.5 h-3.5" />
                <span>{run.target_url}</span>
              </span>
              <span>&bull;</span>
              <span>Steps: {run.steps_count}</span>
              <span>&bull;</span>
              <span>Screens: {run.screens_count}</span>
            </div>

            {/* Test Run History Dropdown */}
            {allRuns.length > 1 && (
              <div className="flex items-center gap-2 mt-3 pt-2 border-t border-[var(--border)]">
                <History className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                  Switch Run:
                </span>
                <select
                  value={id}
                  onChange={(e) => navigate(`/report/${e.target.value}`)}
                  className="px-2.5 py-1 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] rounded text-[var(--text)] outline-none max-w-sm"
                >
                  {allRuns.map((r) => {
                    const isSameUrl = r.target_url === run.target_url;
                    return (
                      <option key={r.id} value={r.id}>
                        {isSameUrl ? '★ ' : ''}[{r.mode || 'FOCUSED'}] {r.id.slice(0, 8)} &mdash; {r.target_url.replace(/https?:\/\//, '').slice(0, 20)} ({r.status})
                      </option>
                    );
                  })}
                </select>
              </div>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {isRunning && (
              <button
                onClick={handleStopRun}
                disabled={stopping}
                className="px-3 py-1.5 rounded-md bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>{stopping ? 'Stopping...' : 'Terminate Test'}</span>
              </button>
            )}

            <a
              href={`http://localhost:8000/api/runs/${run.id}/report`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-md border border-[var(--border)] hover:border-[var(--border-hover)] bg-[var(--surface)] text-xs font-medium text-[var(--text)] flex items-center gap-1.5 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              <span>Standalone HTML</span>
            </a>

            <a
              href={`http://localhost:8000/api/runs/${run.id}/summary`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-md border border-[var(--border)] hover:border-[var(--border-hover)] bg-[var(--surface)] text-xs font-medium text-[var(--text)] flex items-center gap-1.5 transition-colors"
            >
              <FileCode className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              <span>JSON Payload</span>
            </a>

            <button
              onClick={handleDeleteRun}
              disabled={deleting}
              className="px-3 py-1.5 rounded-md border border-rose-500/30 hover:bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs font-medium flex items-center gap-1.5 transition-colors"
              title="Delete this test run and all its logs"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{deleting ? 'Deleting...' : 'Delete Run'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Executive Summary Panel */}
      {run.llm_summary && (
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--accent)] mb-2">
            AI Executive Summary
          </div>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
            {run.llm_summary}
          </p>
        </div>
      )}

      {/* Health Scores Card & Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6 flex flex-col items-center justify-center">
          <ScoreRing score={run.friction_score} label="Overall Health" size={130} />
          <div className="mt-3 text-center">
            <span className="text-xs text-[var(--text-muted)] font-medium">
              Dynamic Composite Score
            </span>
          </div>
        </div>

        <div className="lg:col-span-3 bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
          <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-4">
            Category Health Breakdown
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            <div className="p-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md">
              <span className="block text-[10px] uppercase font-semibold text-[var(--text-muted)] mb-1">
                Accessibility
              </span>
              <span className="text-lg font-bold font-mono text-[var(--text)]">
                {categoryScores.accessibility !== undefined ? `${categoryScores.accessibility.toFixed(0)}%` : '100%'}
              </span>
            </div>

            <div className="p-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md">
              <span className="block text-[10px] uppercase font-semibold text-[var(--text-muted)] mb-1">
                UX Friction
              </span>
              <span className="text-lg font-bold font-mono text-[var(--text)]">
                {categoryScores.friction !== undefined ? `${categoryScores.friction.toFixed(0)}%` : '100%'}
              </span>
            </div>

            <div className="p-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md">
              <span className="block text-[10px] uppercase font-semibold text-[var(--text-muted)] mb-1">
                Security
              </span>
              <span className="text-lg font-bold font-mono text-[var(--text)]">
                {categoryScores.security !== undefined ? `${categoryScores.security.toFixed(0)}%` : '100%'}
              </span>
            </div>

            <div className="p-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md">
              <span className="block text-[10px] uppercase font-semibold text-[var(--text-muted)] mb-1">
                Broken Links
              </span>
              <span className="text-lg font-bold font-mono text-[var(--text)]">
                {categoryScores.broken_links !== undefined ? `${categoryScores.broken_links.toFixed(0)}%` : '100%'}
              </span>
            </div>

            <div className="p-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md">
              <span className="block text-[10px] uppercase font-semibold text-[var(--text-muted)] mb-1">
                Performance
              </span>
              <span className="text-lg font-bold font-mono text-[var(--text)]">
                {categoryScores.performance !== undefined ? `${categoryScores.performance.toFixed(0)}%` : '100%'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Agent Sub-Runs Summary (if FULL_SITE) */}
      {run.mode === 'FULL_SITE' && run.sub_runs && run.sub_runs.length > 0 && (
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-4 h-4 text-[var(--accent)]" />
            <h3 className="text-sm font-semibold tracking-tight text-[var(--text)]">
              Multi-Agent Parallel Tracks ({run.sub_runs.length} Workers)
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {run.sub_runs.map((sub, idx) => (
              <div key={idx} className="p-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md">
                <div className="text-xs font-semibold text-[var(--text)] mb-1">
                  Worker #{sub.worker || idx + 1}: {sub.role || 'Agent Worker'}
                </div>
                <div className="text-[11px] text-[var(--text-secondary)] font-mono">
                  Pages Checked: {sub.pages_checked || 0} &bull; Issues: {sub.issues_found || 0}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues Section with Category Filter */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
          <h2 className="text-sm font-semibold tracking-tight text-[var(--text)]">
            Detected Issues &amp; Remediations ({filteredIssues.length})
          </h2>

          <div className="flex flex-wrap gap-1.5">
            {['ALL', 'ACCESSIBILITY', 'FRICTION', 'SECURITY', 'BROKEN_LINK', 'PERFORMANCE'].map(cat => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                  categoryFilter === cat
                    ? 'bg-[var(--accent)] text-white'
                    : 'bg-[var(--surface)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text)]'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {filteredIssues.length === 0 ? (
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-8 text-center text-xs text-[var(--text-muted)] font-mono">
            No issues found under category "{categoryFilter}".
          </div>
        ) : (
          <div className="space-y-3">
            {filteredIssues.map((issue, idx) => (
              <IssueCard key={issue.id || idx} issue={issue} />
            ))}
          </div>
        )}
      </div>

      {/* Execution Timeline & Screenshots */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
          <h2 className="text-sm font-semibold tracking-tight text-[var(--text)]">
            Step Execution Timeline ({steps.length})
          </h2>

          {steps.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-[var(--text-muted)] font-medium">Filter Step:</span>
              <select
                value={stepFilter}
                onChange={(e) => setStepFilter(e.target.value)}
                className="px-2.5 py-1 text-xs bg-[var(--surface-elevated)] border border-[var(--border)] rounded text-[var(--text)] outline-none"
              >
                <option value="ALL">All Steps ({steps.length})</option>
                {steps.map((s) => (
                  <option key={s.id} value={s.step_number}>
                    Step {s.step_number}: {s.action} &mdash; {s.target ? s.target.slice(0, 30) : 'Action'}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="space-y-3">
          {steps
            .filter((s) => stepFilter === 'ALL' || s.step_number === parseInt(stepFilter, 10))
            .map((step, idx) => {
              let screenshotUrl = null;
              if (step.screenshot_path) {
                const parts = step.screenshot_path.replace(/\\/g, '/').split('/');
                const folder = parts[parts.length - 2];
                const file = parts[parts.length - 1];
                screenshotUrl = `http://localhost:8000/screenshots/${folder}/${file}`;
              }

              return (
                <div
                  key={step.id}
                  className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-[var(--surface-elevated)] border border-[var(--border)] text-[var(--text-muted)]">
                        STEP {step.step_number}
                      </span>
                      <span className="text-xs font-semibold text-[var(--text)]">
                        {step.action} &mdash; {step.target || 'Browser Action'}
                      </span>
                    </div>

                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                      {step.reason}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] font-mono text-[var(--text-muted)]">
                      <span className="truncate max-w-sm">{step.url}</span>
                      {step.duration_ms > 0 && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{(step.duration_ms / 1000).toFixed(2)}s</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {screenshotUrl && (
                    <div className="flex-shrink-0">
                      <div
                        onClick={() => setSelectedScreenshot({
                          index: steps.findIndex(s => s.id === step.id),
                          step_number: step.step_number,
                          action: step.action,
                          target: step.target,
                          reason: step.reason,
                          url: step.url,
                          screenshotUrl
                        })}
                        className="w-48 aspect-video rounded border border-[var(--border)] bg-black/5 dark:bg-black/20 hover:border-[var(--accent)] cursor-pointer overflow-hidden relative group transition-all"
                        title="Click to view full uncropped screenshot"
                      >
                        <img
                          src={screenshotUrl}
                          alt={`Step ${step.step_number}`}
                          className="w-full h-full object-contain"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-[11px] font-medium transition-opacity">
                          Click to Expand
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      </div>

      {/* Interactive Screenshot Slideshow Modal */}
      {selectedScreenshot && (
        <div
          className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4 backdrop-blur-sm"
          onClick={() => setSelectedScreenshot(null)}
        >
          <div
            className="w-full max-w-5xl max-h-[95vh] rounded-lg border border-[var(--border)] bg-[var(--surface)] flex flex-col overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-3.5 border-b border-[var(--border)] flex items-center justify-between bg-[var(--surface-elevated)]">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-[var(--surface)] border border-[var(--border)] text-[var(--text)]">
                  STEP {selectedScreenshot.step_number} of {steps.length}
                </span>
                <span className="text-xs font-semibold text-[var(--text)]">
                  {selectedScreenshot.action} &mdash; {selectedScreenshot.target || 'Action'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={selectedScreenshot.index <= 0}
                  onClick={() => {
                    const prevStep = steps[selectedScreenshot.index - 1];
                    if (prevStep) {
                      const parts = prevStep.screenshot_path.replace(/\\/g, '/').split('/');
                      const folder = parts[parts.length - 2];
                      const file = parts[parts.length - 1];
                      setSelectedScreenshot({
                        index: selectedScreenshot.index - 1,
                        step_number: prevStep.step_number,
                        action: prevStep.action,
                        target: prevStep.target,
                        reason: prevStep.reason,
                        url: prevStep.url,
                        screenshotUrl: `http://localhost:8000/screenshots/${folder}/${file}`
                      });
                    }
                  }}
                  className="p-1 rounded border border-[var(--border)] hover:bg-[var(--surface)] disabled:opacity-30 text-[var(--text)] transition-colors"
                  title="Previous Step"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>

                <button
                  disabled={selectedScreenshot.index >= steps.length - 1}
                  onClick={() => {
                    const nextStep = steps[selectedScreenshot.index + 1];
                    if (nextStep) {
                      const parts = nextStep.screenshot_path.replace(/\\/g, '/').split('/');
                      const folder = parts[parts.length - 2];
                      const file = parts[parts.length - 1];
                      setSelectedScreenshot({
                        index: selectedScreenshot.index + 1,
                        step_number: nextStep.step_number,
                        action: nextStep.action,
                        target: nextStep.target,
                        reason: nextStep.reason,
                        url: nextStep.url,
                        screenshotUrl: `http://localhost:8000/screenshots/${folder}/${file}`
                      });
                    }
                  }}
                  className="p-1 rounded border border-[var(--border)] hover:bg-[var(--surface)] disabled:opacity-30 text-[var(--text)] transition-colors"
                  title="Next Step"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>

                <button
                  onClick={() => setSelectedScreenshot(null)}
                  className="p-1 rounded border border-[var(--border)] hover:bg-[var(--surface)] text-[var(--text)] transition-colors ml-2"
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Modal Image Display */}
            <div className="p-4 bg-black/40 flex items-center justify-center flex-1 overflow-auto max-h-[75vh]">
              <img
                src={selectedScreenshot.screenshotUrl}
                alt={`Step ${selectedScreenshot.step_number}`}
                className="w-auto h-auto max-h-[72vh] max-w-full object-contain rounded border border-white/10"
              />
            </div>

            {/* Modal Footer Info */}
            <div className="p-3 border-t border-[var(--border)] bg-[var(--surface)] text-xs text-[var(--text-secondary)] flex items-center justify-between">
              <span className="truncate max-w-lg font-mono text-[11px]">{selectedScreenshot.url}</span>
              <span className="text-[11px] text-[var(--text-muted)] italic max-w-md truncate">{selectedScreenshot.reason}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
