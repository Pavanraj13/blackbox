import React, { useState } from 'react';
import { Copy, Check, ExternalLink } from 'lucide-react';

export default function IssueCard({ issue }) {
  const [copied, setCopied] = useState(false);

  const dynamicScore = issue.dynamic_score !== undefined ? Number(issue.dynamic_score) : 5.0;
  const severity = (issue.severity || 'MEDIUM').toUpperCase();
  const category = (issue.category || issue.type || 'ACCESSIBILITY').toUpperCase();

  const getScoreBadge = () => {
    if (dynamicScore >= 8.0 || severity === 'CRITICAL') {
      return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/25';
    }
    if (dynamicScore >= 6.0 || severity === 'HIGH') {
      return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25';
    }
    if (dynamicScore >= 4.0 || severity === 'MEDIUM') {
      return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/25';
    }
    return 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20';
  };

  const copyFix = () => {
    if (issue.fix_suggestion) {
      navigator.clipboard.writeText(issue.fix_suggestion);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-hover)] rounded-lg p-5 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-2.5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-[var(--surface-elevated)] border border-[var(--border)] text-[var(--text-muted)]">
              {category}
            </span>
            {issue.step_number && (
              <span className="text-[11px] font-mono text-[var(--text-muted)]">
                Step {issue.step_number}
              </span>
            )}
          </div>
          <h4 className="text-[15px] font-semibold tracking-tight text-[var(--text)]">
            {issue.title}
          </h4>
        </div>
        <div className={`px-2.5 py-1 rounded text-xs font-mono font-semibold border ${getScoreBadge()}`}>
          Score {dynamicScore.toFixed(1)} &bull; {severity}
        </div>
      </div>

      <p className="text-sm text-[var(--text-secondary)] mb-3 leading-relaxed">
        {issue.description}
      </p>

      {issue.url && (
        <div className="flex items-center gap-1 text-xs text-[var(--text-muted)] font-mono mb-3 truncate">
          <ExternalLink className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{issue.url}</span>
        </div>
      )}

      {issue.impact_summary && (
        <div className="bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md p-3 mb-2.5">
          <span className="block text-[10px] font-semibold tracking-wider uppercase text-[var(--accent)] mb-1">
            User / Accessibility Impact
          </span>
          <p className="text-xs text-[var(--text)] leading-relaxed">
            {issue.impact_summary}
          </p>
        </div>
      )}

      {issue.fix_suggestion && (
        <div className="bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold tracking-wider uppercase text-[var(--text-muted)]">
              Remediation Suggestion
            </span>
            <button
              onClick={copyFix}
              type="button"
              className="inline-flex items-center gap-1 text-[11px] text-[var(--text-secondary)] hover:text-[var(--text)] font-medium"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="text-xs font-mono text-blue-600 dark:text-blue-300 bg-black/5 dark:bg-black/40 p-2.5 rounded border border-[var(--border)] overflow-x-auto whitespace-pre-wrap">
            {issue.fix_suggestion}
          </pre>
        </div>
      )}
    </div>
  );
}
