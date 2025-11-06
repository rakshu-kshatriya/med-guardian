import React, { useEffect, useState, useRef } from 'react';
import { getNewsTrends, createNewsStreamConnection } from '../api';

export default function TrendsFeed({ city, disease }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const eventRef = useRef(null);

  useEffect(() => {
    if (!city) return;
    setLoading(true);
    getNewsTrends(city, disease, 8)
      .then((res) => {
        setItems(res.items || []);
      })
      .catch((err) => console.error('Failed to load news trends', err))
      .finally(() => setLoading(false));
  }, [city, disease]);

  useEffect(() => {
    if (!city) return;

    // Close previous
    if (eventRef.current) {
      eventRef.current.close();
      eventRef.current = null;
    }

    const handleNews = (news) => {
      setItems((prev) => [news, ...prev].slice(0, 20));
    };

    const handleError = () => {
      // ignore for now
    };

    try {
      const ev = createNewsStreamConnection(city, disease, handleNews, handleError);
      eventRef.current = ev;
    } catch (err) {
      console.error('Failed to open news stream', err);
    }

    return () => {
      if (eventRef.current) {
        eventRef.current.close();
        eventRef.current = null;
      }
    };
  }, [city, disease]);

  if (!city) return null;

  return (
    <div className="card-gradient rounded-2xl p-6 card-hover animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold gradient-text">Live News & Social Trends</h3>
        <div className="text-sm text-muted">Real-time updates</div>
      </div>

      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="h-4 bg-slate-700 rounded w-3/4"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        </div>
      )}

      {!loading && items.length === 0 && (
        <div className="text-sm text-muted">No recent trends available.</div>
      )}

      <ul className="space-y-3 mt-3">
        {items.map((it) => (
          <li key={it.id || it.timestamp} className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.03)] list-item-hover transition-smooth">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm text-muted mb-1">{it.source} • <span className="text-xs text-muted">{new Date(it.timestamp).toLocaleString()}</span></div>
                <div className="text-sm text-gray-100">{it.title}</div>
              </div>
              <div className="text-xs font-medium capitalize text-slate-300">{it.sentiment}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
