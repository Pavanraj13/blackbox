import React from 'react';

export default function StatusBadge({ status, mode, className = '' }) {
  const s = (status || 'UNKNOWN').toUpperCase();

  const getStyle = () => {
    switch (s) {
      case 'RUNNING':
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
      case 'COMPLETED':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
      case 'STOPPED':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
      case 'FAILED':
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
      default:
        return 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20';
    }
  };

  return (
    <div className={`inline-flex items-center gap-1.5 ${className}`}>
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold tracking-wider uppercase border ${getStyle()}`}>
        {s === 'RUNNING' && (
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse mr-1" />
        )}
        {s}
      </span>
      {mode && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium tracking-wide uppercase border border-[var(--border)] text-[var(--text-muted)] bg-[var(--surface-elevated)]">
          {mode}
        </span>
      )}
    </div>
  );
}
