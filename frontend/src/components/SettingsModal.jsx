import React, { useEffect, useState } from 'react';

export default function SettingsModal({ open, onClose }) {
  const [regions, setRegions] = useState('');
  const [pushNotifications, setPushNotifications] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(true);

  useEffect(() => {
    try {
      const cfg = JSON.parse(localStorage.getItem('mg-settings') || '{}');
      setRegions(cfg.regions || 'Southeast Asia, West Africa');
      setPushNotifications(cfg.push ?? true);
      setEmailAlerts(cfg.email ?? true);
    } catch {
      // ignore
    }
  }, [open]);

  const save = () => {
    const cfg = { regions, push: pushNotifications, email: emailAlerts };
    try { localStorage.setItem('mg-settings', JSON.stringify(cfg)); } catch {}
    onClose && onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-6">
      <div className="absolute inset-0 bg-black/50" onClick={onClose}></div>
      <div className="relative w-full max-w-3xl rounded-2xl bg-[var(--panel)] border border-[rgba(255,255,255,0.04)] shadow-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold">Notifications</h3>
          <button onClick={onClose} className="text-slate-300">Close</button>
        </div>

        <label className="block text-sm text-slate-300 mb-2">Subscribed Regions</label>
        <input value={regions} onChange={(e) => setRegions(e.target.value)} className="w-full p-3 rounded-md bg-slate-800 border border-slate-700 text-slate-100 mb-4" />

        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.03)]">
            <div>
              <div className="text-sm font-semibold">Push Notifications</div>
              <div className="text-xs text-slate-400">Receive real-time alerts on your device.</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked={pushNotifications} onChange={() => setPushNotifications(!pushNotifications)} className="sr-only" />
              <span className={`w-11 h-6 inline-block rounded-full transition-colors ${pushNotifications ? 'bg-indigo-500' : 'bg-slate-600'}`}></span>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.03)]">
            <div>
              <div className="text-sm font-semibold">Email Alerts</div>
              <div className="text-xs text-slate-400">Get daily or weekly summaries via email.</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked={emailAlerts} onChange={() => setEmailAlerts(!emailAlerts)} className="sr-only" />
              <span className={`w-11 h-6 inline-block rounded-full transition-colors ${emailAlerts ? 'bg-indigo-500' : 'bg-slate-600'}`}></span>
            </label>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button onClick={save} className="btn-primary">Update settings</button>
        </div>
      </div>
    </div>
  );
}
