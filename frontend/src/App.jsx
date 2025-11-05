import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import CitySelector from './components/CitySelector';
import PredictionChart from './components/PredictionChart';
import AIAdvisory from './components/AIAdvisory';
import CityMap from './components/CityMap';

function App() {
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedDisease, setSelectedDisease] = useState('Unknown');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="animate-fade-in">
          <CitySelector
            selectedCity={selectedCity}
            onCityChange={setSelectedCity}
            selectedDisease={selectedDisease}
            onDiseaseChange={setSelectedDisease}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="animate-slide-in">
            <PredictionChart city={selectedCity} disease={selectedDisease} />
          </div>
          <div className="animate-slide-in" style={{ animationDelay: '0.1s' }}>
            <AIAdvisory city={selectedCity} disease={selectedDisease} />
          </div>
        </div>

        <div className="mt-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <CityMap />
        </div>
      </main>
      

      <footer className="relative mt-16 py-8 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white">
        <div className="absolute inset-0 pointer-events-none opacity-20 bg-[radial-gradient(circle_at_25%_25%,rgba(255,255,255,0.08),transparent_35%),radial-gradient(circle_at_75%_75%,rgba(255,255,255,0.08),transparent_35%)]"></div>
        <div className="relative container mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <p className="text-sm font-medium text-gray-300">
              Med Guardian - Disease Prediction & Health Advisory System
            </p>
          </div>
          <p className="text-xs text-gray-500">
            Powered by AI • Real-time Monitoring • India Health Insights
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;

