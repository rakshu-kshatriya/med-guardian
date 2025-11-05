import React, { useState, useEffect, useCallback } from 'react';
import { GoogleMap, LoadScript, Polyline, Marker } from '@react-google-maps/api';
import { getDirections, getCities } from '../api';
import clsx from 'clsx';

const mapContainerStyle = {
  width: '100%',
  height: '500px',
};

const defaultCenter = {
  lat: 20.5937,
  lng: 78.9629,
};

export default function CityMap() {
  const [cities, setCities] = useState([]);
  const [originCity, setOriginCity] = useState('');
  const [destinationCity, setDestinationCity] = useState('');
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [steps, setSteps] = useState([]);
  const [showSteps, setShowSteps] = useState(false);
  const [animationPosition, setAnimationPosition] = useState(null);

  useEffect(() => {
    const fetchCities = async () => {
      try {
        const cityList = await getCities();
        setCities(cityList);
      } catch (err) {
        console.error('Failed to fetch cities:', err);
      }
    };
    fetchCities();
  }, []);

  const decodePolyline = (encoded) => {
    // Simple polyline decoder (handles | separated lat,lng pairs)
    if (!encoded) return [];
    
    const points = encoded.split('|');
    return points.map((point) => {
      const [lat, lng] = point.split(',');
      return { lat: parseFloat(lat), lng: parseFloat(lng) };
    });
  };

  const handleGetRoute = async () => {
    if (!originCity || !destinationCity) {
      setError('Please select both origin and destination cities');
      return;
    }

    if (originCity === destinationCity) {
      setError('Origin and destination must be different');
      return;
    }

    setLoading(true);
    setError(null);
    setRoute(null);
    setSteps([]);
    setAnimationPosition(null);

    try {
      const directions = await getDirections(originCity, destinationCity);
      
      if (directions.routes && directions.routes.length > 0) {
        const leg = directions.routes[0].legs[0];
        const routeSteps = leg.steps || [];
        
        // Decode polyline
        const polylinePoints = routeSteps.length > 0 && routeSteps[0].polyline
          ? decodePolyline(routeSteps[0].polyline.points)
          : [];
        
        setRoute({
          path: polylinePoints,
          bounds: directions.routes[0].bounds,
          summary: {
            distance: leg.distance?.text || 'N/A',
            duration: leg.duration?.text || 'N/A',
          },
        });
        
        setSteps(routeSteps);
        
        // Start animation
        if (polylinePoints.length > 0) {
          animateMarker(polylinePoints);
        }
      }
    } catch (err) {
      console.error('Error fetching directions:', err);
      setError('Failed to load route. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const animateMarker = (path) => {
    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex < path.length) {
        setAnimationPosition(path[currentIndex]);
        currentIndex++;
      } else {
        clearInterval(interval);
        // Reset after completion
        setTimeout(() => {
          setAnimationPosition(null);
        }, 1000);
      }
    }, 100); // Update every 100ms for smooth animation
  };

  const getMapCenter = () => {
    if (route && route.bounds) {
      const ne = route.bounds.northeast;
      const sw = route.bounds.southwest;
      return {
        lat: (ne.lat + sw.lat) / 2,
        lng: (ne.lng + sw.lng) / 2,
      };
    }
    return defaultCenter;
  };

  const getMapBounds = () => {
    if (route && route.bounds) {
      return {
        north: route.bounds.northeast.lat,
        south: route.bounds.southwest.lat,
        east: route.bounds.northeast.lng,
        west: route.bounds.southwest.lng,
      };
    }
    return null;
  };

  return (
    <div className="card-gradient rounded-2xl p-6 card-hover animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </div>
        <h3 className="text-2xl font-bold gradient-text">🗺️ City Route Planner</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Origin City
          </label>
          <select
            value={originCity}
            onChange={(e) => setOriginCity(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-smooth bg-white shadow-sm hover:shadow-md font-medium"
          >
            <option value="">Select origin...</option>
            {cities.map((city) => (
              <option key={`origin-${city.city_name}`} value={city.city_name}>
                {city.city_name}, {city.state}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Destination City
          </label>
          <select
            value={destinationCity}
            onChange={(e) => setDestinationCity(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-smooth bg-white shadow-sm hover:shadow-md font-medium"
          >
            <option value="">Select destination...</option>
            {cities.map((city) => (
              <option key={`dest-${city.city_name}`} value={city.city_name}>
                {city.city_name}, {city.state}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button
        onClick={handleGetRoute}
        disabled={loading}
        className={clsx(
          "w-full md:w-auto px-8 py-3 rounded-xl font-bold transition-all duration-300 mb-4 shadow-lg",
          loading
            ? "bg-gray-400 cursor-not-allowed text-white"
            : "btn-primary"
        )}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 8 0 12 5.373 12 0 12 4 12 4 12z"></path>
            </svg>
            Loading Route...
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
            Get Route
          </span>
        )}
      </button>

      {error && (
        <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4 flex items-center gap-2 shadow-md">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-medium">{error}</span>
        </div>
      )}

      {route && (
        <div className="mb-4 animate-fade-in">
          <div className="relative bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-6 text-white shadow-xl overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
            <div className="relative">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    </svg>
                    <p className="text-sm text-blue-100 font-medium">Distance</p>
                  </div>
                  <p className="text-3xl font-bold text-shadow">{route.summary.distance}</p>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-blue-100 font-medium">Estimated Time</p>
                  </div>
                  <p className="text-3xl font-bold text-shadow">{route.summary.duration}</p>
                </div>
              </div>
            </div>
          </div>

          {steps.length > 0 && (
            <button
              onClick={() => setShowSteps(!showSteps)}
              className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              {showSteps ? 'Hide' : 'Show'} Step-by-Step Directions
            </button>
          )}

          {showSteps && steps.length > 0 && (
            <div className="mt-4 bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
              <ol className="list-decimal list-inside space-y-2">
                {steps.map((step, index) => (
                  <li key={index} className="text-sm text-gray-700">
                    {step.html_instructions || `Step ${index + 1}`} - {step.distance?.text || ''}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      <div className="rounded-xl overflow-hidden border-2 border-gray-200 shadow-xl">
        {import.meta.env.VITE_GOOGLE_MAPS_API_KEY ? (
          <LoadScript googleMapsApiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
            <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={getMapCenter()}
            zoom={route ? 6 : 5}
            options={{
              disableDefaultUI: false,
              zoomControl: true,
              streetViewControl: false,
              mapTypeControl: true,
              styles: [
                {
                  featureType: "poi",
                  elementType: "labels",
                  stylers: [{ visibility: "off" }]
                }
              ]
            }}
          >
            {route && route.path.length > 0 && (
              <>
                <Polyline
                  path={route.path}
                  options={{
                    strokeColor: '#3b82f6',
                    strokeWeight: 4,
                    strokeOpacity: 0.8,
                  }}
                />
                {route.path[0] && (
                  <Marker
                    position={route.path[0]}
                    label="Start"
                    icon={{
                      url: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
                    }}
                  />
                )}
                {route.path[route.path.length - 1] && (
                  <Marker
                    position={route.path[route.path.length - 1]}
                    label="End"
                    icon={{
                      url: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
                    }}
                  />
                )}
                {animationPosition && (
                  <Marker
                    position={animationPosition}
                    icon={{
                      url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                      scaledSize: { width: 20, height: 20 },
                    }}
                  />
                )}
              </>
            )}
            </GoogleMap>
          </LoadScript>
        ) : (
          <div className="h-96 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center rounded-xl">
            <div className="text-center p-8 bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
              <p className="text-gray-700 font-semibold mb-2">Google Maps API Key Not Configured</p>
              <p className="text-sm text-gray-500">Set VITE_GOOGLE_MAPS_API_KEY in environment variables</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

