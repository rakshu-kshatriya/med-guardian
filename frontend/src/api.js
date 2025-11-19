// frontend/src/api.js

const API_BASE = import.meta.env.VITE_API_URL || "https://med-guardian-production-1e13.up.railway.app";

// GET cities list
export async function getCities() {
  const res = await fetch(`${API_BASE}/api/city_data`);
  return res.json();
}

// GET directions between 2 cities
export async function getDirections(origin, destination) {
  const url = `${API_BASE}/api/directions?origin_city=${origin}&destination_city=${destination}`;
  const res = await fetch(url);
  return res.json();
}

// GET trends (latest 30 days)
export async function getLatestTrends(city, disease) {
  const res = await fetch(`${API_BASE}/api/trends/latest?city=${city}&disease=${disease}`);
  return res.json();
}

// GET disease forecast
export async function getForecast(city, disease) {
  const res = await fetch(`${API_BASE}/api/predictor?city=${city}&disease=${disease}`);
  return res.json();
}

// GET health advisory
export async function getAdvisory(city, disease, aqi, temp) {
  const url = `${API_BASE}/api/advisory_service?city=${city}&disease=${disease}&aqi=${aqi}&temp=${temp}`;
  const res = await fetch(url);
  return res.json();
}

// GET news + social trends
export async function getNews(city, disease, limit = 10) {
  const url = `${API_BASE}/api/news_trends?city=${city}&disease=${disease}&limit=${limit}`;
  const res = await fetch(url);
  return res.json();
}
