import React from 'react';
import { Terminal, Shield } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { Link } from 'react-router-dom';

export default function Header({ title, subtitle }) {
  return (
    <header className="h-14 bg-[var(--surface)]/80 backdrop-blur border-b border-[var(--border)] px-6 flex items-center justify-between sticky top-0 z-40">
      <div>
        <h2 className="text-sm font-semibold tracking-tight text-[var(--text)]">
          {title}
        </h2>
        {subtitle && (
          <p className="text-[11px] text-[var(--text-secondary)] font-medium">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono border border-[var(--border)] bg-[var(--surface-elevated)] text-[var(--text-secondary)]">
          <Terminal className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span>Autonomous Engine v2.0</span>
        </span>

        <ThemeToggle />
      </div>
    </header>
  );
}
