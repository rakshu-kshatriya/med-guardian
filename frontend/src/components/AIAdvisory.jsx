import React, { useState, useEffect } from 'react';
import { getAdvisory, getLatestTrends } from '../api';

export default function AIAdvisory({ city, disease }) {
  const [advisory, setAdvisory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    const fetchAdvisory = async () => {
      if (!city || !disease) return;
      setLoading(true);
      setError(null);
      try {
        const trends = await getLatestTrends(city, disease);
        const latest = trends.history && trends.history.length > 0
          ? trends.history[trends.history.length - 1]
          : { avg_temp: 25.0, real_time_aqi: 80.0 };
        const aqi = latest.real_time_aqi || 80.0;
        const temp = latest.avg_temp || 25.0;
        const advisoryData = await getAdvisory(city, disease, aqi, temp);
        setAdvisory(advisoryData);
      } catch (err) {
        console.error('Error fetching advisory:', err);
        setError('Failed to load health advisory');
      } finally {
        setLoading(false);
      }
    };
    fetchAdvisory();
  }, [city, disease]);

  const copyToClipboard = () => {
    if (!advisory) return;
    const text = `AI Health Advisory - ${city} - ${disease}\n\n` +
      `Reasoning:\n${advisory.reasoning}\n\n` +
      `Precautions:\n${advisory.precautions.map((p, i) => `${i + 1}. ${p}`).join('\n')}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (loading) {
    return (
      <div className="rounded-2xl p-6 card-gradient">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-700 rounded w-1/3"></div>
          <div className="h-4 bg-slate-700 rounded w-full"></div>
          <div className="h-4 bg-slate-700 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl p-6 card-gradient">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  if (!advisory) {
    return (
      <div className="rounded-2xl p-6 card-gradient">
        <p className="text-slate-400">Select a city and disease to view advisory</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl p-6 card-gradient">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-xl font-bold">AI Advisory — {city} — {disease}</h3>
          <div className="text-xs px-2 py-1 rounded bg-indigo-100 text-indigo-800 font-semibold">AI-powered</div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              if (!city || !disease) return;
              setRegenerating(true);
              try {
                const trends = await getLatestTrends(city, disease);
                const latest = trends.history && trends.history.length > 0 ? trends.history[trends.history.length - 1] : { avg_temp: 25.0, real_time_aqi: 80.0 };
                const aqi = latest.real_time_aqi || 80.0;
                const temp = latest.avg_temp || 25.0;
                const advisoryData = await getAdvisory(city, disease, aqi, temp);
                setAdvisory(advisoryData);
              } catch (err) {
                console.error('Error regenerating advisory:', err);
              } finally {
                setRegenerating(false);
              }
            }}
            className="px-3 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm font-medium"
          >
            {regenerating ? 'Regenerating...' : 'Regenerate'}
          </button>
          <button onClick={copyToClipboard} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="prose prose-sm max-w-none">
        <div className="bg-[rgba(255,255,255,0.02)] rounded-lg p-4 mb-6 border-l-4 border-indigo-600">
          <h4 className="text-sm font-semibold text-slate-200 mb-2">Reasoning</h4>
          <p className="text-slate-200 leading-relaxed">{advisory.reasoning}</p>
        </div>

        <div className="bg-[rgba(255,255,255,0.02)] rounded-lg p-4 border-l-4 border-emerald-500">
          <h4 className="text-sm font-semibold text-slate-200 mb-3">Precautions</h4>
          <ol className="list-decimal list-inside space-y-2 text-slate-200">
            {advisory.precautions.map((precaution, index) => (
              <li key={index} className="leading-relaxed">
                {precaution}
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}

