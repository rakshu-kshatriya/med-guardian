import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';
import { getPrediction, getLatestTrends, createStreamConnection } from '../api';

export default function PredictionChart({ city, disease }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [streamConnected, setStreamConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const eventSourceRef = useRef(null);
  const [kpis, setKpis] = useState({
    currentCases: 0,
    sevenDayAvg: 0,
    trend: 'stable',
  });

  // Fetch initial data and setup SSE stream
  useEffect(() => {
    const fetchData = async () => {
      if (!city) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const prediction = await getPrediction(city, disease);
        const trends = await getLatestTrends(city, disease);
        
        // Combine data
        const chartData = prediction.data.map((item) => ({
          date: item.ds,
          actual: item.y,
          predicted: item.yhat,
          lower: item.yhat_lower,
          upper: item.yhat_upper,
        }));
        
        setData(chartData);
        
        // Calculate KPIs
        const history = trends.history || [];
        if (history.length > 0) {
          const current = history[history.length - 1].y;
          const last7 = history.slice(-7).map((h) => h.y);
          const avg7 = last7.reduce((a, b) => a + b, 0) / last7.length;
          const prev7 = history.slice(-14, -7).map((h) => h.y);
          const prevAvg = prev7.length > 0 
            ? prev7.reduce((a, b) => a + b, 0) / prev7.length 
            : avg7;
          
          const trend = avg7 > prevAvg * 1.05 ? 'up' : avg7 < prevAvg * 0.95 ? 'down' : 'stable';
          
          setKpis({
            currentCases: current,
            sevenDayAvg: Math.round(avg7),
            trend,
          });
        }
      } catch (err) {
        console.error('Error fetching prediction data:', err);
        setError('Failed to load prediction data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [city, disease]);

  // Setup SSE stream for real-time updates
  useEffect(() => {
    if (!city) return;

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    console.log('🔌 Setting up SSE stream for:', { city, disease });

    const handleUpdate = (streamData) => {
      console.log('📈 Updating chart with stream data:', streamData);
      setLastUpdate(new Date());

      // Update the chart data with the latest stream update
      setData((prevData) => {
        const newData = [...prevData];
        
        // Find today's date in the data
        const today = new Date().toISOString().split('T')[0];
        const todayIndex = newData.findIndex((d) => d.date === today || d.date.startsWith(today));
        
        if (todayIndex >= 0) {
          // Update existing today's data point
          newData[todayIndex] = {
            ...newData[todayIndex],
            actual: streamData.cases,
            // Keep predicted values if they exist
            predicted: newData[todayIndex].predicted,
            lower: newData[todayIndex].lower,
            upper: newData[todayIndex].upper,
          };
        } else {
          // Add new data point for today
          newData.push({
            date: today,
            actual: streamData.cases,
            predicted: null,
            lower: null,
            upper: null,
          });
        }

        // Update KPIs with latest data
        const historyData = newData.filter((d) => d.actual !== null);
        if (historyData.length > 0) {
          const current = streamData.cases;
          const last7 = historyData.slice(-7).map((h) => h.actual).filter(v => v !== null);
          const avg7 = last7.length > 0 
            ? last7.reduce((a, b) => a + b, 0) / last7.length 
            : current;
          
          // Calculate trend from last 2 values
          const recent = historyData.slice(-2).map((h) => h.actual).filter(v => v !== null);
          let trend = 'stable';
          if (recent.length === 2) {
            trend = recent[1] > recent[0] * 1.02 ? 'up' : recent[1] < recent[0] * 0.98 ? 'down' : 'stable';
          }
          
          setKpis({
            currentCases: current,
            sevenDayAvg: Math.round(avg7),
            trend,
          });
        }

        return newData;
      });
    };

    const handleError = (error) => {
      console.error('Stream error:', error);
      setStreamConnected(false);
    };

    try {
      const eventSource = createStreamConnection(city, disease, handleUpdate, handleError);
      eventSourceRef.current = eventSource;
      setStreamConnected(true);

      // Cleanup on unmount or when city/disease changes
      return () => {
        console.log('🔌 Closing SSE stream');
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
        setStreamConnected(false);
      };
    } catch (err) {
      console.error('Failed to setup stream:', err);
      setStreamConnected(false);
    }
  }, [city, disease]);

  const formatDate = (dateStr) => {
    try {
      return format(new Date(dateStr), 'dd MMM');
    } catch {
      return dateStr;
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800 mb-2">
            {formatDate(payload[0].payload.date)}
          </p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value !== null && entry.value !== undefined 
                ? Math.round(entry.value) 
                : 'N/A'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="card-gradient rounded-2xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gradient-to-r from-gray-200 to-gray-300 rounded w-1/4"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-24 bg-gradient-to-r from-blue-200 to-blue-300 rounded-xl"></div>
            <div className="h-24 bg-gradient-to-r from-green-200 to-green-300 rounded-xl"></div>
            <div className="h-24 bg-gradient-to-r from-purple-200 to-purple-300 rounded-xl"></div>
          </div>
          <div className="h-96 bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card-gradient rounded-2xl p-6">
        <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200 text-red-700 px-6 py-4 rounded-xl flex items-center gap-3">
          <svg className="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-semibold">{error}</span>
        </div>
      </div>
    );
  }

  // Separate history and forecast
  const historyData = data.filter((d) => d.actual !== null);
  const forecastData = data.filter((d) => d.predicted !== null);

  return (
    <div className="card-gradient rounded-2xl p-6 card-hover animate-fade-in">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="relative bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg transform hover:scale-105 transition-all duration-300 overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
          <div className="relative">
            <p className="text-blue-100 text-sm font-medium mb-2">Current Cases</p>
            <div className="flex items-center justify-between">
              <p className="text-4xl font-bold text-shadow">{kpis.currentCases.toLocaleString()}</p>
              {streamConnected && (
                <div className="flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-3 py-1">
                  <div className="w-2 h-2 bg-green-300 rounded-full pulse-glow"></div>
                  <span className="text-xs font-semibold">Live</span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="relative bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl p-6 text-white shadow-lg transform hover:scale-105 transition-all duration-300 overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
          <div className="relative">
            <p className="text-emerald-100 text-sm font-medium mb-2">7-Day Average</p>
            <p className="text-4xl font-bold text-shadow">{kpis.sevenDayAvg.toLocaleString()}</p>
          </div>
        </div>
        
        <div className="relative bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-6 text-white shadow-lg transform hover:scale-105 transition-all duration-300 overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
          <div className="relative">
            <p className="text-purple-100 text-sm font-medium mb-2">Trend</p>
            <div className="flex items-center gap-3">
              <p className="text-4xl font-bold text-shadow capitalize">{kpis.trend}</p>
              {kpis.trend === 'up' && (
                <div className="bg-red-400/30 backdrop-blur-sm rounded-full p-2">
                  <svg className="w-6 h-6 text-red-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </div>
              )}
              {kpis.trend === 'down' && (
                <div className="bg-green-400/30 backdrop-blur-sm rounded-full p-2">
                  <svg className="w-6 h-6 text-green-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 17l5-5m0 0l-5-5m5 5H6" />
                  </svg>
                </div>
              )}
              {kpis.trend === 'stable' && (
                <div className="bg-blue-400/30 backdrop-blur-sm rounded-full p-2">
                  <svg className="w-6 h-6 text-blue-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h14" />
                  </svg>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stream Status Indicator */}
      {streamConnected && (
        <div className="mb-6 flex items-center justify-between bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-200/50">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-3 h-3 bg-green-500 rounded-full pulse-glow"></div>
              <div className="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping opacity-75"></div>
            </div>
            <span className="text-green-700 font-semibold">Real-time updates active</span>
          </div>
          {lastUpdate && (
            <span className="text-green-600 text-sm font-medium bg-white/60 px-3 py-1 rounded-full">
              Last update: {format(lastUpdate, 'HH:mm:ss')}
            </span>
          )}
        </div>
      )}

      {/* Chart */}
      <div className="chart-container">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold gradient-text">
            📊 Disease Trend Analysis
          </h3>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-gray-600 font-medium">Historical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
              <span className="text-gray-600 font-medium">Forecast</span>
            </div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={500}>
          <LineChart 
            data={data} 
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            style={{ filter: 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))' }}
          >
            <defs>
              <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fb923c" stopOpacity={0.4} />
                <stop offset="50%" stopColor="#fb923c" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#fb923c" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorHistory" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity={1} />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity={1} />
              </linearGradient>
              <linearGradient id="colorPrediction" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#fb923c" stopOpacity={1} />
                <stop offset="100%" stopColor="#f97316" stopOpacity={1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Confidence interval area (only for forecast data) */}
            {forecastData.length > 0 && (
              <>
                <Area
                  type="monotone"
                  dataKey="upper"
                  stroke="none"
                  fill="url(#colorConfidence)"
                  fillOpacity={0.3}
                  connectNulls={false}
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  stroke="none"
                  fill="white"
                  connectNulls={false}
                />
              </>
            )}
            
            {/* Historical data (solid line with gradient) */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke="url(#colorHistory)"
              strokeWidth={3}
              dot={{ fill: "#3b82f6", r: 4, strokeWidth: 2, stroke: "#fff" }}
              activeDot={{ r: 6, strokeWidth: 2, stroke: "#3b82f6" }}
              name="Historical Cases"
              connectNulls={false}
              animationDuration={1000}
            />
            
            {/* Predicted data (dashed line with gradient) */}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="url(#colorPrediction)"
              strokeWidth={3}
              strokeDasharray="8 4"
              dot={{ fill: "#fb923c", r: 4, strokeWidth: 2, stroke: "#fff" }}
              activeDot={{ r: 6, strokeWidth: 2, stroke: "#fb923c" }}
              name="Predicted Cases"
              connectNulls={false}
              animationDuration={1000}
            />
            
            {/* Confidence bounds (optional - can be hidden via legend) */}
            <Line
              type="monotone"
              dataKey="upper"
              stroke="#fb923c"
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
              name="Upper Bound"
              connectNulls={false}
              hide={true}
            />
            <Line
              type="monotone"
              dataKey="lower"
              stroke="#fb923c"
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
              name="Lower Bound"
              connectNulls={false}
              hide={true}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

