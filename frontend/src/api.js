/**
 * API client for Med Guardian backend
 */

import axios from 'axios';

// Use environment variable if set, otherwise relative URL for production, absolute for development
const API_BASE_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : import.meta.env.DEV 
    ? 'http://localhost:8000/api' 
    : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Get latest trends for a city
 */
export const getLatestTrends = async (city, disease = 'Unknown') => {
  try {
    const response = await api.get('/trends/latest', {
      params: { city, disease },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching latest trends:', error);
    throw error;
  }
};

/**
 * Get prediction forecast for a city
 */
export const getPrediction = async (city, disease = 'Unknown') => {
  try {
    const response = await api.get('/predict', {
      params: { city, disease },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching prediction:', error);
    throw error;
  }
};

/**
 * Get health advisory
 */
export const getAdvisory = async (city, disease, aqi, temp) => {
  try {
    const response = await api.get('/advisory', {
      params: { city, disease, aqi, temp },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching advisory:', error);
    throw error;
  }
};

/**
 * Get directions between two cities
 */
export const getDirections = async (originCity, destinationCity) => {
  try {
    const response = await api.get('/directions', {
      params: {
        origin_city: originCity,
        destination_city: destinationCity,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching directions:', error);
    throw error;
  }
};

/**
 * Get list of all cities
 */
export const getCities = async () => {
  try {
    const response = await api.get('/cities');
    return response.data.cities;
  } catch (error) {
    console.error('Error fetching cities:', error);
    throw error;
  }
};

/**
 * Create EventSource connection for SSE stream
 * @param {string} city - City name
 * @param {string} disease - Disease name
 * @param {Function} onUpdate - Callback for update events
 * @param {Function} onError - Callback for error events
 * @returns {EventSource} EventSource instance
 */
export const createStreamConnection = (city, disease = 'Unknown', onUpdate, onError) => {
  const streamUrl = `${API_BASE_URL}/stream?city=${encodeURIComponent(city)}&disease=${encodeURIComponent(disease)}`;
  
  const eventSource = new EventSource(streamUrl);
  
  eventSource.addEventListener('update', (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('📊 Stream update received:', data);
      onUpdate(data);
    } catch (err) {
      console.error('Error parsing stream data:', err);
    }
  });
  
  eventSource.addEventListener('error', (event) => {
    console.error('❌ Stream error:', event);
    if (onError) {
      onError(event);
    }
  });
  
  eventSource.onopen = () => {
    console.log('✅ Stream connected:', { city, disease });
  };
  
  eventSource.onerror = (error) => {
    console.error('❌ Stream connection error:', error);
    if (onError) {
      onError(error);
    }
  };
  
  return eventSource;
};

export default api;

