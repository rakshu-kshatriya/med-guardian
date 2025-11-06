import React, { useState, useEffect } from 'react';
import api from '../api';

function downloadCSV(filename, rows) {
  const csvContent = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.setAttribute('download', filename);
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export default function DataSourcesPage() {
  const [city] = useState('Chennai');
  const [disease] = useState('flu');
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Try to fetch 1000 recent synthetic rows by hitting backend trends multiple times
    const buildDataset = async () => {
      setLoading(true);
      try {
        // Backend supports synthetic generator; request 1000 days by calling a dedicated endpoint if available
        const resp = await api.get('/data_sources', { params: { city, disease } }).catch(() => null);
        if (resp && resp.data && resp.data.rows && resp.data.rows.length >= 1) {
          setRows(resp.data.rows);
          setLoading(false);
          return;
        }

        // Fallback: call trends/latest repeatedly to compose 1000 rows client-side
        const collected = [];
        let attempts = 0;
        while (collected.length < 1000 && attempts < 20) {
          const r = await api.get('/trends/latest', { params: { city, disease } });
          const history = r.data.history || [];
          history.forEach(h => collected.push([h.ds, h.y, h.avg_temp, h.real_time_aqi]));
          attempts++;
        }
        setRows(collected.slice(0, 1000));
      } catch (err) {
        console.error('Failed to build dataset:', err);
      } finally {
        setLoading(false);
      }
    };

    buildDataset();
  }, [city, disease]);

  const handleDownload = () => {
    const header = ['date', 'cases', 'avg_temp', 'real_time_aqi'];
    downloadCSV('medguardian_data_1000.csv', [header, ...rows]);
  };

  return (
    <div className="space-y-6">
      <div className="card-gradient rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-extrabold">Data Sources</h2>
            <p className="text-sm text-gray-400">Where data comes from and recent exported dataset (1000 rows).</p>
          </div>
          <div>
            <button onClick={handleDownload} disabled={rows.length === 0} className="btn-primary">Download CSV (1000 rows)</button>
          </div>
        </div>
      </div>

      <div className="card-gradient rounded-2xl p-4 overflow-auto">
        {loading ? (
          <p className="text-gray-400">Building dataset…</p>
        ) : (
          <table className="min-w-full text-left">
            <thead>
              <tr className="text-sm text-gray-300">
                <th className="px-4 py-2">Date</th>
                <th className="px-4 py-2">Cases</th>
                <th className="px-4 py-2">Avg Temp</th>
                <th className="px-4 py-2">AQI</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 1000).map((r, idx) => (
                <tr key={idx} className={idx % 2 === 0 ? 'bg-white/3' : ''}>
                  <td className="px-4 py-2 text-sm">{r[0]}</td>
                  <td className="px-4 py-2 text-sm">{r[1]}</td>
                  <td className="px-4 py-2 text-sm">{r[2]}</td>
                  <td className="px-4 py-2 text-sm">{r[3]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
