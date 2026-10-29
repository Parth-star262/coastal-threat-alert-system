import React from "react";
import WeatherCharts from "./weatherCharts";
import WeatherTable from "./weatherTable";
import MapView from "./MapView";
import "./App.css";

const configuredApiBaseUrl = process.env.REACT_APP_API_BASE_URL;
const API_BASE_URL = (configuredApiBaseUrl || (process.env.NODE_ENV === "production" ? "" : "http://127.0.0.1:5000")).replace(/\/+$/, "");

if (!/^https?:\/\//i.test(API_BASE_URL)) {
  throw new Error("REACT_APP_API_BASE_URL must include an http:// or https:// scheme.");
}

const REQUEST_TIMEOUT_MS = 10000;
const INITIAL_LOAD_TIMEOUT_MS = 12000;

async function fetchJson(url) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

function Metric({ label, value, detail, tone = "" }) {
  return (
    <div className={`metric-card ${tone}`}>
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <span className="metric-detail">{detail}</span>
    </div>
  );
}

function SectionHeader({ eyebrow, title, action }) {
  return (
    <div className="section-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  );
}

function App() {
  const [data, setData] = React.useState([]);
  const [coastalData, setCoastalData] = React.useState([]);
  const [riskZones, setRiskZones] = React.useState({ type: "FeatureCollection", features: [] });
  const [prediction, setPrediction] = React.useState(null);
  const [alerts, setAlerts] = React.useState([]);
  const [coastalAnomalies, setCoastalAnomalies] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [lastUpdated, setLastUpdated] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [failedSections, setFailedSections] = React.useState([]);
  const [selectedCity, setSelectedCity] = React.useState("Mumbai");
  const hasDataRef = React.useRef(false);
  hasDataRef.current = data.length > 0;

  const cities = [...new Set(data.map((item) => item.city))];
  const cityData = data.filter((item) => item.city === selectedCity);
  const cityLatestData = cityData[0] || null;
  const cityCoastalData = coastalData.find((item) => item.city === selectedCity);
  const cityRiskZone = riskZones.features.find((feature) => feature.properties.city === selectedCity);
  const cityAnomaly = coastalAnomalies.find((item) => item.city === selectedCity);
  const cityAlerts = alerts.filter((alert) => alert.city === selectedCity);
  const weatherIsStale = cityLatestData?.timestamp
    ? Date.now() - new Date(cityLatestData.timestamp).getTime() > 30 * 60 * 1000
    : false;

  const fetchDashboardData = React.useCallback(async () => {
    const requests = [
      ["weather history", fetchJson(`${API_BASE_URL}/history`)],
      ["coastal observations", fetchJson(`${API_BASE_URL}/coastal/latest`)],
      ["risk zones", fetchJson(`${API_BASE_URL}/risk-zones`)],
      ["active alerts", fetchJson(`${API_BASE_URL}/alerts?status=active`)],
      ["coastal anomalies", fetchJson(`${API_BASE_URL}/coastal/anomalies`)],
    ];
    const results = await Promise.allSettled(requests.map(([, request]) => request));
    const failures = [];

    results.forEach((result, index) => {
      const section = requests[index][0];
      if (result.status === "rejected") {
        failures.push(section);
        console.error(`${section} request failed`, result.reason);
        return;
      }

      switch (index) {
        case 0:
          setData(result.value);
          break;
        case 1:
          setCoastalData(result.value);
          break;
        case 2:
          setRiskZones(result.value);
          break;
        case 3:
          setAlerts(result.value);
          break;
        case 4:
          setCoastalAnomalies(result.value);
          break;
        default:
          break;
      }
    });

    setFailedSections(failures);
    if (failures.length) {
      setError(`Some data could not be refreshed: ${failures.join(", ")}.`);
    } else {
      setError(null);
    }
    setLastUpdated(new Date());
    return failures;
  }, []);

  React.useEffect(() => {
    let active = true;
    const loadData = async () => {
      setRefreshing(true);
      const timeout = new Promise((_, reject) => {
        setTimeout(() => reject(new Error("Initial dashboard load timed out")), INITIAL_LOAD_TIMEOUT_MS);
      });

      try {
        await Promise.race([fetchDashboardData(), timeout]);
      } catch (err) {
        if (!hasDataRef.current) {
          setError("The dashboard could not load within 12 seconds. Check your connection and retry.");
        }
        console.error("Initial dashboard load failed", err);
      } finally {
        if (active) {
          setRefreshing(false);
          setLoading(false);
        }
      }
    };
    loadData();
    const interval = setInterval(loadData, 300000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [fetchDashboardData]);

  React.useEffect(() => {
    if (!selectedCity) return;
    fetchJson(`${API_BASE_URL}/predict/${encodeURIComponent(selectedCity)}`)
      .then(setPrediction)
      .catch((err) => {
        setPrediction(null);
        setFailedSections((sections) => sections.includes("alert prediction") ? sections : [...sections, "alert prediction"]);
        setError((currentError) => currentError || "The alert prediction could not be refreshed.");
        console.error("alert prediction request failed", err);
      });
  }, [selectedCity]);

  const handleCitySelect = (cityName) => setSelectedCity(cityName);
  const retryLoad = () => {
    setLoading(true);
    setError(null);
    fetchDashboardData()
      .catch((err) => {
        setError("The dashboard could not be refreshed. Check your connection and retry.");
        console.error("Dashboard retry failed", err);
      })
      .finally(() => setLoading(false));
  };

  if (loading && !data.length) {
    return <div className="boot-screen"><div className="boot-mark">◒</div><strong>Coastal intelligence</strong><span>Connecting to live observations…</span></div>;
  }

  if (error && !data.length) {
    return <div className="boot-screen"><strong>Unable to load live data</strong><span>{error}</span><button className="button button-primary" onClick={retryLoad}>Retry connection</button></div>;
  }

  const riskLevel = cityRiskZone?.properties?.risk_level || "—";
  const riskScore = cityRiskZone?.properties?.risk_score ?? "—";
  const predictionLabel = prediction?.alert_level || "—";

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">◒</span><span>COASTAL<br /><b>INTELLIGENCE</b></span></div>
        <div className="sidebar-rule" />
        <nav className="side-nav" aria-label="Dashboard navigation">
          <a className="active" href="#overview"><span>⌂</span> Overview</a>
          <a href="#map"><span>⌖</span> Risk map</a>
          <a href="#trends"><span>◌</span> Trends</a>
          <a href="#alerts"><span>!</span> Alerts <em>{alerts.length}</em></a>
        </nav>
        <div className="sidebar-footer">
          <span className="status-dot" /> LIVE INGESTION
          <small>OpenWeather · Open-Meteo<br />GDACS · PostgreSQL</small>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div><span className="topbar-label">OPERATIONS / COASTAL RISK MONITOR</span><h1>Situation overview</h1></div>
          <div className="topbar-actions">
            <span className="sync-status"><i className={refreshing ? "pulse" : ""} /> {refreshing ? "Syncing" : "System nominal"}</span>
            <span className="updated-time">{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Awaiting sync"}</span>
          </div>
        </header>

        {(error || weatherIsStale) && <div className="notice warning" role="status"><span>{error || "The selected weather observation is older than 30 minutes."}{failedSections.length ? ` Failed sections: ${failedSections.join(", ")}.` : ""}</span><button className="button button-primary" onClick={retryLoad}>Retry</button></div>}

        <section id="overview" className="overview-grid">
          <div className="hero-panel">
            <div className="hero-grid-lines" />
            <span className="eyebrow accent">SELECTED MONITORING ZONE</span>
            <div className="city-select-wrap">
              <select value={selectedCity} onChange={(event) => setSelectedCity(event.target.value)} aria-label="Select monitoring city">
                {cities.map((city) => <option key={city} value={city}>{city}</option>)}
              </select>
              <span className="select-chevron">⌄</span>
            </div>
            <p className="hero-copy">Environmental signals and coastal risk indicators for the selected zone.</p>
            <div className="hero-meta"><span><i className="status-dot" /> Monitoring active</span><span>7 coastal locations</span></div>
          </div>
          <div className={`risk-panel risk-${riskLevel.toLowerCase()}`}>
            <div className="risk-ring"><strong>{riskScore}</strong><span>RISK<br />SCORE</span></div>
            <div><span className="eyebrow">COMPOSITE ASSESSMENT</span><h2>{riskLevel} risk</h2><p>Weather, marine and event signals combined</p></div>
          </div>
        </section>

        <section className="metric-grid" aria-label="Current measurements">
          <Metric label="Air temperature" value={cityLatestData ? `${cityLatestData.temperature}°` : "—"} detail="degrees Celsius" tone="blue" />
          <Metric label="Relative humidity" value={cityLatestData ? `${cityLatestData.humidity}%` : "—"} detail="at observation point" tone="cyan" />
          <Metric label="Wind velocity" value={cityLatestData ? `${cityLatestData.wind_speed}` : "—"} detail="metres per second" tone="orange" />
          <Metric label="Wave height" value={cityCoastalData?.wave_height_m != null ? `${cityCoastalData.wave_height_m}m` : "—"} detail="Open-Meteo marine" tone="violet" />
          <Metric label="Sea level" value={cityCoastalData?.sea_level_height_m != null ? `${cityCoastalData.sea_level_height_m}m` : "—"} detail={cityAnomaly?.is_abnormal ? "anomaly detected" : "within baseline"} tone={cityAnomaly?.is_abnormal ? "red" : "green"} />
        </section>

        <section id="map" className="content-grid">
          <div className="card map-card">
            <SectionHeader eyebrow="01 / GEOSPATIAL SIGNALS" title="Coastal risk map" action={<span className="card-caption">GEOJSON ZONES · LEAFLET</span>} />
            <MapView data={data} selectedCity={selectedCity} onCitySelect={handleCitySelect} riskZones={riskZones} />
          </div>
          <div id="alerts" className="card alerts-card">
            <SectionHeader eyebrow="02 / RESPONSE QUEUE" title="Active alerts" action={<span className="alert-count">{cityAlerts.length}</span>} />
            {cityAlerts.length ? cityAlerts.slice(0, 5).map((alert) => (
              <div className="alert-item" key={alert.id}><span className={`severity severity-${alert.severity?.toLowerCase()}`}>{alert.severity}</span><div><strong>{alert.message}</strong><small>{alert.recommended_action || "Monitor official guidance"} · {alert.status}</small></div></div>
            )) : <div className="empty-state"><span>✓</span><strong>No active alerts</strong><p>The selected zone is within configured thresholds.</p></div>}
            <div className="alert-footer">Notification channels · Email / SMS</div>
          </div>
        </section>

        <section id="trends" className="card trend-card">
          <SectionHeader eyebrow="03 / TELEMETRY" title={`${selectedCity} environmental trends`} action={<span className="card-caption">LAST {cityData.length} OBSERVATIONS</span>} />
          <WeatherCharts data={cityData} cityName={selectedCity} />
        </section>

        <section className="detail-grid">
          <div className="card table-card"><SectionHeader eyebrow="04 / OBSERVATIONS" title="Recent weather records" /><WeatherTable data={cityData} cityName={selectedCity} /></div>
          <div className="card signal-card"><SectionHeader eyebrow="05 / MODEL OUTPUT" title="Alert classifier" /><div className="model-output"><span className={`model-badge model-${predictionLabel.toLowerCase()}`}>{predictionLabel}</span><div><strong>{prediction?.confidence ? `${Math.round(prediction.confidence * 100)}%` : "—"}</strong><small>model confidence</small></div></div><p>Weather-only classifier using temperature, humidity, wind, pressure, hour and month.</p><div className="model-foot"><span>PyTorch / scikit-learn</span><span>{weatherIsStale ? "Stale observation" : "Fresh observation"}</span></div></div>
        </section>

        <footer className="dashboard-footer"><span>COASTAL INTELLIGENCE SYSTEM</span><span>Prototype monitoring interface · Data is advisory, not an evacuation boundary</span></footer>
      </main>
    </div>
  );
}

export default App;
