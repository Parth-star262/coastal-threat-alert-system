import React from "react";
import WeatherCharts from "./weatherCharts";
import WeatherTable from "./weatherTable";
import AlertBanner from "./AlertBanner";
import MapView from "./MapView";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

function App() {
  const [data, setData] = React.useState([]);
  const [coastalData, setCoastalData] = React.useState([]);
  const [riskZones, setRiskZones] = React.useState({ type: "FeatureCollection", features: [] });
  const [prediction, setPrediction] = React.useState(null);
  const [alerts, setAlerts] = React.useState([]);
  const [coastalAnomalies, setCoastalAnomalies] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [selectedCity, setSelectedCity] = React.useState("Mumbai");

  // Get unique cities from data
  const cities = [...new Set(data.map(item => item.city))];

  // Filter data for selected city
  const cityData = data.filter(item => item.city === selectedCity);
  
  // Get latest data for selected city only
  const cityLatestData = cityData.length > 0 ? cityData[0] : null;
  const cityCoastalData = coastalData.find(item => item.city === selectedCity);
  const cityRiskZone = riskZones.features.find(feature => feature.properties.city === selectedCity);
  const cityAnomaly = coastalAnomalies.find(item => item.city === selectedCity);
  const cityAlerts = alerts.filter(alert => alert.city === selectedCity);
  const weatherIsStale = cityLatestData?.timestamp
    ? Date.now() - new Date(cityLatestData.timestamp).getTime() > 30 * 60 * 1000
    : false;

  const fetchDashboardData = async () => {
    try {
      const [historyResponse, coastalResponse, riskResponse, alertsResponse, anomalyResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/history`),
        fetch(`${API_BASE_URL}/coastal/latest`),
        fetch(`${API_BASE_URL}/risk-zones`),
        fetch(`${API_BASE_URL}/alerts?status=active`),
        fetch(`${API_BASE_URL}/coastal/anomalies`),
      ]);
      if (!historyResponse.ok || !coastalResponse.ok || !riskResponse.ok || !alertsResponse.ok || !anomalyResponse.ok) {
        throw new Error("Dashboard API request failed");
      }
      setData(await historyResponse.json());
      setCoastalData(await coastalResponse.json());
      setRiskZones(await riskResponse.json());
      setAlerts(await alertsResponse.json());
      setCoastalAnomalies(await anomalyResponse.json());
      setError(null);
    } catch (err) {
      setError("Failed to fetch dashboard data");
      console.error(err);
    }
  };

  React.useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchDashboardData();
      setLoading(false);
    };
    
    loadData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  React.useEffect(() => {
    if (!selectedCity) return;
    fetch(`${API_BASE_URL}/predict/${encodeURIComponent(selectedCity)}`)
      .then(response => response.ok ? response.json() : null)
      .then(setPrediction)
      .catch(() => setPrediction(null));
  }, [selectedCity]);

  // Function to handle city selection from map
  const handleCitySelect = (cityName) => {
    setSelectedCity(cityName);
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="text-xl">🔄 Loading weather data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="text-red-500 text-xl">❌ {error}</div>
        <button 
          onClick={() => window.location.reload()} 
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">🌊 Coastal Threat Alert Dashboard</h1>
      
      {/* City Selector */}
      <div className="mb-4 text-center">
        <label className="text-lg font-semibold mr-3">Select City:</label>
        <select 
          value={selectedCity} 
          onChange={(e) => setSelectedCity(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>

      {/* Selected City Current Weather - Only show if city has data */}
      {cityLatestData && (
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <h2 className="text-lg font-semibold mb-2">🌤️ Current Weather in {selectedCity}</h2>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{cityLatestData.temperature}°C</div>
              <div className="text-sm text-gray-600">Temperature</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{cityLatestData.humidity}%</div>
              <div className="text-sm text-gray-600">Humidity</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">{cityLatestData.wind_speed} m/s</div>
              <div className="text-sm text-gray-600">Wind Speed</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">{cityLatestData.description}</div>
              <div className="text-sm text-gray-600">Condition</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-cyan-600">{cityLatestData.rainfall_1h_mm ?? 0} mm</div>
              <div className="text-sm text-gray-600">Rainfall (1h)</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-indigo-600">{cityLatestData.visibility_m ?? "—"} m</div>
              <div className="text-sm text-gray-600">Visibility</div>
            </div>
          </div>
          {cityCoastalData && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-center">
              <div>
                <div className="text-xl font-bold text-cyan-600">{cityCoastalData.wave_height_m ?? "—"} m</div>
                <div className="text-sm text-gray-600">Wave Height</div>
              </div>
              <div>
                <div className="text-xl font-bold text-indigo-600">{cityCoastalData.sea_level_height_m ?? "—"} m</div>
                <div className="text-sm text-gray-600">Sea Level</div>
              </div>
              <div>
                <div className="text-xl font-bold text-teal-600">{cityCoastalData.sea_surface_temperature_c ?? "—"}°C</div>
                <div className="text-sm text-gray-600">Sea Temperature</div>
              </div>
              <div>
                <div className="text-xl font-bold text-red-600">{cityRiskZone?.properties.risk_level ?? "—"}</div>
                <div className="text-sm text-gray-600">Risk Level</div>
              </div>
              <div>
                <div className="text-xl font-bold text-amber-600">{cityAnomaly ? (cityAnomaly.is_abnormal ? "ABNORMAL" : "Normal") : "—"}</div>
                <div className="text-sm text-gray-600">Tide Baseline</div>
              </div>
              <div>
                <div className="text-xl font-bold text-rose-600">{prediction?.alert_level ?? "—"}</div>
                <div className="text-sm text-gray-600">
                  ML Alert {prediction?.confidence != null ? `(${Math.round(prediction.confidence * 100)}%)` : ""}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Show message if no data for selected city */}
      {!cityLatestData && (
        <div className="bg-yellow-50 p-4 rounded-lg mb-4 text-center">
          <p className="text-yellow-700">No weather data available for {selectedCity}</p>
        </div>
      )}
      {weatherIsStale && (
        <div className="bg-orange-50 border border-orange-200 p-3 rounded-lg mb-4 text-orange-800">
          Latest weather data for {selectedCity} is older than 30 minutes.
        </div>
      )}
      
      <AlertBanner data={cityData} /> 
      {cityAlerts.length > 0 && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-4">
          <h2 className="font-semibold text-red-700">Active Alerts ({cityAlerts.length})</h2>
          {cityAlerts.slice(0, 5).map(alert => (
            <div key={alert.id} className="mt-2 text-sm text-red-800">
              <strong>{alert.city} · {alert.severity}</strong>: {alert.message}
            </div>
          ))}
        </div>
      )}
      <WeatherCharts data={cityData} cityName={selectedCity} />
      <WeatherTable data={cityData} cityName={selectedCity} />
      
      {/* Pass city selection handler to MapView */}
      <MapView
        data={data}
        selectedCity={selectedCity}
        onCitySelect={handleCitySelect}
        riskZones={riskZones}
      />
    </div>
  );
}

export default App;