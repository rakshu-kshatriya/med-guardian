import React, { useState, useEffect } from 'react';
import { getAdvisory, getLatestTrends } from '../api';

export default function AIAdvisory({ city, disease }) {
  const [advisory, setAdvisory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchAdvisory = async () => {
      if (!city || !disease) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Get latest trends to extract current AQI and temp
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
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-4/5"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  if (!advisory) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-gray-500">Select a city and disease to view advisory</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-800">
          AI Advisory — {city} — {disease}
        </h3>
        <button
          onClick={copyToClipboard}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-smooth text-sm font-medium flex items-center gap-2"
        >
          {copied ? (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy
            </>
          )}
        </button>
      </div>

      <div className="prose prose-sm max-w-none">
        <div className="bg-blue-50 rounded-lg p-4 mb-6 border-l-4 border-blue-500">
          <h4 className="text-sm font-semibold text-blue-800 mb-2">Reasoning</h4>
          <p className="text-gray-700 leading-relaxed">{advisory.reasoning}</p>
        </div>

        <div className="bg-green-50 rounded-lg p-4 border-l-4 border-green-500">
          <h4 className="text-sm font-semibold text-green-800 mb-3">Precautions</h4>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
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

