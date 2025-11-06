import React, { useEffect, useState } from 'react';
import { getLatestTrends } from '../api';

function Sparkline({ data = [] }) {
  if (!data || data.length === 0) return null;
  const w = 120; const h = 32;
  const values = data.map(d => d.y || 0);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = Math.max(1, max - min);
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <polyline fill="none" stroke="#60a5fa" strokeWidth="2" points={points} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function QuickOverview({ city, disease }) {
  const [data, setData] = useState([]);
  useEffect(() => {
    if (!city) return;
    getLatestTrends(city, disease).then(res => {
      setData(res.history ? res.history.slice(-14) : []);
    }).catch(() => setData([]));
  }, [city, disease]);

  if (!city) return null;

  const latest = data.length ? data[data.length-1].y : 0;

  return (
    <div className="flex items-center gap-4">
      <div>
        <div className="text-xs text-slate-400">Current Cases</div>
        <div className="text-lg font-bold text-white">{latest.toLocaleString()}</div>
      </div>
      <Sparkline data={data} />
    </div>
  );
}
