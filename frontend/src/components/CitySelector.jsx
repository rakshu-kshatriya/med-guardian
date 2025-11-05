import React, { useState, useEffect } from 'react';
import { getCities } from '../api';

export default function CitySelector({ selectedCity, onCityChange, selectedDisease, onDiseaseChange }) {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);

  const commonDiseases = [
    'Unknown',
    'Dengue',
    'Malaria',
    'Chikungunya',
    'COVID-19',
    'Influenza',
    'Typhoid',
    'Cholera',
  ];

  useEffect(() => {
    const fetchCities = async () => {
      try {
        const cityList = await getCities();
        setCities(cityList);
        if (!selectedCity && cityList.length > 0) {
          onCityChange(cityList[0].city_name);
        }
      } catch (error) {
        console.error('Failed to fetch cities:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCities();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="h-10 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="card-gradient rounded-2xl p-6 mb-6 card-hover animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="city-select" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Select City
          </label>
          <select
            id="city-select"
            value={selectedCity || ''}
            onChange={(e) => onCityChange(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-smooth bg-white shadow-sm hover:shadow-md font-medium"
          >
            {cities.map((city) => (
              <option key={city.city_name} value={city.city_name}>
                {city.city_name}, {city.state}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="disease-select" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
            <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Disease Type
          </label>
          <select
            id="disease-select"
            value={selectedDisease || 'Unknown'}
            onChange={(e) => onDiseaseChange(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-smooth bg-white shadow-sm hover:shadow-md font-medium"
          >
            {commonDiseases.map((disease) => (
              <option key={disease} value={disease}>
                {disease}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

