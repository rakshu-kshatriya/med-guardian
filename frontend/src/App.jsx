import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header, { attachHeaderThemeToggle } from './components/Header';
import HomePage from './pages/HomePage';
import PredictionPage from './pages/PredictionPage';
import TrendsPage from './pages/TrendsPage';
import DataSourcesPage from './pages/DataSourcesPage';
import CitySelector from './components/CitySelector';
import PredictionChart from './components/PredictionChart';
import AIAdvisory from './components/AIAdvisory';
import CityMap from './components/CityMap';
import TrendsFeed from './components/TrendsFeed';

function App() {
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedDisease, setSelectedDisease] = useState('Unknown');
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('mg-theme') || 'dark';
    } catch {
      return 'dark';
    }
  });

  useEffect(() => {
    // Apply theme to document root
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.style.setProperty('--bg', '#071025');
      root.style.setProperty('--panel', '#0b1220');
      root.style.setProperty('--muted', '#94a3b8');
      root.style.setProperty('--text', '#e6eef8');
    } else {
      root.classList.remove('dark');
      root.style.setProperty('--bg', 'linear-gradient(180deg,#f8fafc,#eef2ff)');
      root.style.setProperty('--panel', '#ffffff');
      root.style.setProperty('--muted', '#6b7280');
      root.style.setProperty('--text', '#0f172a');
    }

    try { localStorage.setItem('mg-theme', theme); } catch {}
  }, [theme]);

  useEffect(() => {
    // Attach header button handlers (theme toggle)
    attachHeaderThemeToggle();
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
        <Header />

        <main className="container mx-auto px-4 py-8 max-w-7xl">
          <div className="animate-fade-in">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/prediction" element={<PredictionPage />} />
              <Route path="/trends" element={<TrendsPage />} />
              <Route path="/data-sources" element={<DataSourcesPage />} />
              {/* legacy single-page fallback */}
              <Route path="/legacy" element={(
                <>
                  <CitySelector
                    selectedCity={selectedCity}
                    onCityChange={setSelectedCity}
                    selectedDisease={selectedDisease}
                    onDiseaseChange={setSelectedDisease}
                  />

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 mt-6">
                    <PredictionChart city={selectedCity} disease={selectedDisease} />
                    <AIAdvisory city={selectedCity} disease={selectedDisease} />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                      <CityMap />
                    </div>
                    <div className="lg:col-span-1">
                      <TrendsFeed city={selectedCity} disease={selectedDisease} />
                    </div>
                  </div>
                </>
              )} />
            </Routes>
          </div>
        </main>

        <footer className="relative mt-16 py-8 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white">
          <div className="absolute inset-0 pointer-events-none opacity-20 bg-[radial-gradient(circle_at_25%_25%,rgba(255,255,255,0.08),transparent_35%),radial-gradient(circle_at_75%_75%,rgba(255,255,255,0.08),transparent_35%)]"></div>
          <div className="relative container mx-auto px-4 text-center">
            <p className="text-sm font-medium text-gray-300">
              Med Guardian - Disease Prediction & Health Advisory System
            </p>
            <p className="text-xs text-gray-500">
              Powered by AI • Real-time Monitoring • India Health Insights
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
