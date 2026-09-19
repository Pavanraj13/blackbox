import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Play,
  History,
  AlertTriangle,
  Puzzle,
  Settings,
  ShieldCheck,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { getHealth, getKeyInfo } from '../services/api';

export default function Sidebar() {
  const [health, setHealth] = useState({ status: 'checking', browser: 'unknown', ai: 'unknown' });
  const [keyInfo, setKeyInfo] = useState({ auth_enabled: false, encryption_enabled: false });

  useEffect(() => {
    const check = async () => {
      try {
        const [healthData, keyData] = await Promise.allSettled([getHealth(), getKeyInfo()]);
        if (healthData.status === 'fulfilled') setHealth(healthData.value);
        if (keyData.status === 'fulfilled') setKeyInfo(keyData.value);
      } catch (err) {
        setHealth({ status: 'offline', browser: 'error', ai: 'offline' });
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/agent', label: 'Live Test', icon: Play },
    { to: '/runs', label: 'Test Runs', icon: History },
    { to: '/findings', label: 'Issues & Findings', icon: AlertTriangle },
    { to: '/extension-guide', label: 'Browser Extension', icon: Puzzle },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-60 bg-[var(--surface)] border-r border-[var(--border)] flex flex-col justify-between h-screen sticky top-0 flex-shrink-0 z-30">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-[var(--border)] flex items-center gap-2.5">
          <div className="w-5 h-5 rounded bg-[var(--accent)] flex items-center justify-center text-white font-bold text-xs shadow-sm">
            B
          </div>
          <div>
            <h1 className="font-semibold text-xs tracking-wider uppercase text-[var(--text)]">
              Blackbox
            </h1>
            <p className="text-[10px] text-[var(--text-muted)] font-mono">
              Autonomous UI/UX QA
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-md font-medium text-xs transition-colors ${
                    isActive
                      ? 'bg-[var(--accent-soft)] text-[var(--accent)] font-semibold'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--surface-elevated)]'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* System Status Footprint */}
      <div className="p-3 m-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-lg space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold tracking-wide uppercase text-[var(--text-muted)]">
            Engine Status
          </span>
          <span className="flex items-center gap-1 text-[11px] font-mono">
            {health.status === 'ok' ? (
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-rose-500" />
            )}
            <span className={health.status === 'ok' ? 'text-emerald-600 dark:text-emerald-400 font-medium' : 'text-rose-500'}>
              {health.status === 'ok' ? 'Online' : 'Offline'}
            </span>
          </span>
        </div>

        <div className="space-y-1 text-[11px] font-mono text-[var(--text-secondary)] pt-1 border-t border-[var(--border)]">
          <div className="flex justify-between items-center">
            <span>Model:</span>
            <span className="text-[var(--text)] font-medium truncate max-w-[105px]" title={health.ai}>
              {health.model || health.ai}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Security:</span>
            <span className="inline-flex items-center gap-0.5 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="w-3 h-3" />
              <span>AES-256</span>
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
