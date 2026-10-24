import React from "react";
import { GeoJSON, MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";

const locationIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
  iconSize: [26, 26],
  iconAnchor: [13, 26],
  popupAnchor: [0, -26],
});

const cityCoordinates = {
  Mumbai: [19.076, 72.8777],
  Chennai: [13.0827, 80.2707],
  Kolkata: [22.5726, 88.3639],
  Surat: [21.1702, 72.8311],
  Visakhapatnam: [17.6868, 83.2185],
  Kochi: [9.9312, 76.2673],
  Mangalore: [12.9716, 74.8609],
};

function riskZoneStyle(feature) {
  const colors = { LOW: "#22a875", MEDIUM: "#d49a20", HIGH: "#e47a38", CRITICAL: "#d94d4d" };
  const color = colors[feature.properties.risk_level] || "#64748b";
  return { color, fillColor: color, fillOpacity: 0.2, weight: 2 };
}

function MapView({ data, selectedCity, onCitySelect, riskZones }) {
  const citiesData = [...new Set(data.map((item) => item.city))]
    .map((city) => ({ city, data: data.find((item) => item.city === city) }))
    .filter((item) => item.data);

  return (
    <div className="map-view">
      <div className="map-toolbar">
        <span className="map-toolbar-label">MONITORED LOCATIONS</span>
        <div className="city-picker">
          {citiesData.map(({ city }) => (
            <button key={city} type="button" className={city === selectedCity ? "selected" : ""} onClick={() => onCitySelect(city)}>
              <i />{city}
            </button>
          ))}
        </div>
      </div>
      <div className="map-frame">
        <MapContainer center={[20.6, 78.9]} zoom={5} scrollWheelZoom={false} style={{ height: "390px", width: "100%" }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors" />
          {riskZones.features.length > 0 && <GeoJSON data={riskZones} style={riskZoneStyle} />}
          {citiesData.map(({ city, data: cityData }) => {
            const coords = cityCoordinates[city];
            if (!coords) return null;
            return (
              <Marker key={city} position={coords} icon={locationIcon} eventHandlers={{ click: () => onCitySelect(city) }}>
                <Popup>
                  <strong>{city}</strong><br />
                  {cityData.temperature}°C · {cityData.humidity}% humidity<br />
                  {cityData.wind_speed} m/s wind
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
        <div className="map-legend"><span><i className="legend-low" /> Low</span><span><i className="legend-medium" /> Medium</span><span><i className="legend-high" /> High</span><span><i className="legend-critical" /> Critical</span></div>
      </div>
    </div>
  );
}

export default MapView;
