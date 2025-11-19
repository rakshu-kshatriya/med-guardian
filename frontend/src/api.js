/**
 * API client for Med Guardian backend
 */

import axios from "axios";

/**
 * API base URL logic:
 * - If VITE_API_URL is set (Railway), use it
 * - If running locally (import.meta.env.DEV), use localhost
 * - Otherwise use relative path (when FastAPI serves frontend)
 */
const RAW_BASE_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL
  : import.meta.env.DEV
    ? "http://localhost:8000"
    : "";

// Append /api to all endpoints
const API_BASE_URL = `${RAW_BASE_URL}/api`;

console.log("📡 Using API base URL:", API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Get latest trends for a city
 */
export const getLatestTrends = async (city, disease = "Unknown") => {
  const response = await api.get("/trends/latest", {
    params: { city, disease },
  });
  return response.data;
};

/**
 * Get prediction forecast
 */
export const getPrediction = async (city, disease = "Unknown") => {
  const response = await api.get("/predictor", {
    params: { city, disease },
  });
  return response.data;
};

/**
 * Get health advisory
 */
export const getAdvisory = async (city, disease, aqi, temp) => {
  const response = await api.get("/advisory_service", {
    params: { city, disease, aqi, temp },
  });
  return response.data;
};

/**
 * Get list of cities
 */
export const getCities = async () => {
  const response = await api.get("/city_data");
  return response.data.cities;
};

/**
 * Get news/social trends
 */
export const getNewsTrends = async (
  city,
  disease = "Unknown",
  limit = 10
) => {
  const response = await api.get("/news_trends", {
    params: { city, disease, limit },
  });
  return response.data;
};

/**
 * SSE: News stream
 */
export const createNewsStreamConnection = (
  city,
  disease = "Unknown",
  onNews,
  onError
) => {
  const streamUrl = `${API_BASE_URL}/stream_news?city=${encodeURIComponent(
    city
  )}&disease=${encodeURIComponent(disease)}`;

  const eventSource = new EventSource(streamUrl);

  eventSource.addEventListener("news", (event) => {
    try {
      const data = JSON.parse(event.data);
      onNews(data);
    } catch (err) {
      console.error("Error parsing news stream:", err);
    }
  });

  eventSource.onerror = (err) => {
    console.error("❌ News stream error", err);
    if (onError) onError(err);
  };

  return eventSource;
};

/**
 * SSE: Prediction / trend stream
 */
export const createStreamConnection = (
  city,
  disease = "Unknown",
  onUpdate,
  onError
) => {
  const streamUrl = `${API_BASE_URL}/stream?city=${encodeURIComponent(
    city
  )}&disease=${encodeURIComponent(disease)}`;

  const eventSource = new EventSource(streamUrl);

  eventSource.addEventListener("update", (event) => {
    try {
      const data = JSON.parse(event.data);
      onUpdate(data);
    } catch (err) {
      console.error("Stream parse error:", err);
    }
  });

  eventSource.onerror = (err) => {
    console.error("❌ Stream error", err);
    if (onError) onError(err);
  };

  return eventSource;
};

export default api;
