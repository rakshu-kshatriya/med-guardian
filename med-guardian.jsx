import React, { useEffect, useState } from 'react';
import QuickOverview from './QuickOverview';
import SettingsModal from './SettingsModal';

export default function Header() {
  const [openSettings, setOpenSettings] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-50" style={{ background: 'var(--panel)', borderBottom: '1px solid rgba(255,255,255,0.04)', backdropFilter: 'blur(6px)' }}>
        <div className="container mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-blue-600 rounded-lg flex items-center justify-center shadow-md float-up" aria-hidden>
              <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <div>
              <div className="text-lg font-bold">MedGuardian</div>
              <div className="text-xs text-slate-400">India Health Monitor</div>
            </div>
          </div>

          <div className="flex-1 px-6 hidden lg:block">
            <div className="relative">
              <input placeholder="Search diseases or regions..." className="w-full bg-transparent text-white placeholder-slate-400 rounded-md px-4 py-2 border border-transparent focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">⌘K</div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-3 mr-2">
              <span className="w-3 h-3 rounded-full bg-emerald-400 pulse-glow" aria-hidden="true"></span>
              <QuickOverview city={null} disease={null} />
            </div>
            <button onClick={() => setOpenSettings(true)} className="px-3 py-2 rounded-md border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 transition-smooth">Settings</button>
            <button id="theme-toggle" aria-label="Toggle theme" className="p-2 rounded-md bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 transition-smooth">🌙</button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-500 to-rose-500 shadow-sm flex items-center justify-center text-white">R</div>
          </div>
        </div>
      </header>
      <SettingsModal open={openSettings} onClose={() => setOpenSettings(false)} />
    </>
  );
}

// Attach theme toggle behavior to the button. This keeps Header simple
// and avoids global state management for now.
export function attachHeaderThemeToggle() {
  try {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.onclick = () => {
      const root = document.documentElement;
      const isDark = root.classList.contains('dark');
      if (isDark) {
        root.classList.remove('dark');
        root.style.setProperty('--bg', 'linear-gradient(180deg,#f8fafc,#eef2ff)');
        root.style.setProperty('--panel', '#ffffff');
        root.style.setProperty('--muted', '#6b7280');
        root.style.setProperty('--text', '#0f172a');
        try { localStorage.setItem('mg-theme', 'light'); } catch {}
      } else {
        root.classList.add('dark');
        root.style.setProperty('--bg', '#071025');
        root.style.setProperty('--panel', '#0b1220');
        root.style.setProperty('--muted', '#94a3b8');
        root.style.setProperty('--text', '#e6eef8');
        try { localStorage.setItem('mg-theme', 'dark'); } catch {}
      }
    };
  } catch (err) {
    // ignore
  }
}

