import React, { useState } from 'react';
import CityMap from '../components/CityMap';
import TrendsFeed from '../components/TrendsFeed';
import CitySelector from '../components/CitySelector';

export default function TrendsPage() {
  const [city, setCity] = useState('Chennai');
  const [disease, setDisease] = useState('flu');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl md:text-3xl font-extrabold">Trends & Maps</h2>
          <p className="text-sm text-gray-400">Explore recent trends and routing with live maps.</p>
        </div>
      </div>

      <CitySelector selectedCity={city} onCityChange={setCity} selectedDisease={disease} onDiseaseChange={setDisease} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <CityMap />
        </div>
        <div className="lg:col-span-1">
          <TrendsFeed city={city} disease={disease} />
        </div>
      </div>
    </div>
  );
}
