import React from 'react';
import { Sparkles, Terminal } from 'lucide-react';

export default function Header({ title, subtitle }) {
  return (
    <header className="h-16 bg-[#0b1120]/80 backdrop-blur border-b border-slate-800 px-8 flex items-center justify-between sticky top-0 z-40">
      <div>
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          {title}
        </h2>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        <span className="text-xs font-mono bg-slate-800 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-2">
          <Terminal size={14} className="text-cyan-400" />
          Black-Box Playwright Engine
        </span>
      </div>
    </header>
  );
}
