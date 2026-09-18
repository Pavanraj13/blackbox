import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Play, History, AlertTriangle, FileText, Activity } from 'lucide-react';
import { getHealth } from '../services/api';

export default function Sidebar() {
  const [health, setHealth] = useState({ status: 'checking', browser: 'unknown', ai: 'unknown' });

  useEffect(() => {
    const check = async () => {
      try {
        const data = await getHealth();
        setHealth(data);
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
    { to: '/agent', label: 'Test Agent', icon: Play },
    { to: '/runs', label: 'Test Runs', icon: History },
    { to: '/findings', label: 'Findings', icon: AlertTriangle },
  ];

  return (
    <aside className="w-64 bg-[#0b1120] border-r border-slate-800 flex flex-col justify-between h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="bg-gradient-to-tr from-cyan-500 to-indigo-600 p-2 rounded-xl text-white shadow-lg shadow-cyan-500/20">
            <Activity size={22} />
          </div>
          <div>
            <h1 className="font-extrabold text-sm tracking-wide text-white uppercase">Black-Box Agent</h1>
            <p className="text-[10px] text-slate-400 font-mono">UI/UX & A11y Tester</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl font-medium text-sm transition duration-200 ${
                    isActive
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`
                }
              >
                <Icon size={18} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* System Health Widget */}
      <div className="p-4 m-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-400">System Status</span>
          <span className={`w-2 h-2 rounded-full ${health.status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`} />
        </div>

        <div className="space-y-1 text-[11px] font-mono">
          <div className="flex justify-between text-slate-400">
            <span>Playwright:</span>
            <span className="text-emerald-400 font-bold">{health.browser}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>AI Planner:</span>
            <span className="text-cyan-400 font-bold">{health.ai}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
