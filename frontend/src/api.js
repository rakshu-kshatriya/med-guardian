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
    const response = await api.get('/predictor', {
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
    const response = await api.get('/advisory_service', {
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
    // Backend exposes city list at /api/city_data
    const response = await api.get('/city_data');
    return response.data.cities;
  } catch (error) {
    console.error('Error fetching cities:', error);
    throw error;
  }
};

/**
 * Get latest news/social trends for a city and disease
 */
export const getNewsTrends = async (city, disease = 'Unknown', limit = 10) => {
  try {
    const response = await api.get('/news_trends', {
      params: { city, disease, limit }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching news trends:', error);
    throw error;
  }
};

/**
 * Create EventSource for news SSE stream
 */
export const createNewsStreamConnection = (city, disease = 'Unknown', onNews, onError) => {
  const streamUrl = `${API_BASE_URL}/stream_news?city=${encodeURIComponent(city)}&disease=${encodeURIComponent(disease)}`;
  const eventSource = new EventSource(streamUrl);

  eventSource.addEventListener('news', (event) => {
    try {
      const data = JSON.parse(event.data);
      onNews(data);
    } catch (err) {
      console.error('Error parsing news stream data:', err);
    }
  });

  eventSource.addEventListener('error', (ev) => {
    console.error('News stream error:', ev);
    if (onError) onError(ev);
  });

  eventSource.onopen = () => console.log('News stream connected');
  eventSource.onerror = (err) => { if (onError) onError(err); };

  return eventSource;
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

