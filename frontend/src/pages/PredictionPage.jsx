import React, { useState } from 'react';
import CitySelector from '../components/CitySelector';
import PredictionChart from '../components/PredictionChart';
import AIAdvisory from '../components/AIAdvisory';

export default function PredictionPage() {
  const [selectedCity, setSelectedCity] = useState('Chennai');
  const [selectedDisease, setSelectedDisease] = useState('flu');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl md:text-3xl font-extrabold">30-day Disease Forecast</h2>
          <p className="text-sm text-gray-400">Accurate near-term forecasting to help planning and response.</p>
        </div>
      </div>

      <CitySelector
        selectedCity={selectedCity}
        onCityChange={setSelectedCity}
        selectedDisease={selectedDisease}
        onDiseaseChange={setSelectedDisease}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PredictionChart city={selectedCity} disease={selectedDisease} />
        <AIAdvisory city={selectedCity} disease={selectedDisease} />
      </div>
    </div>
  );
}
