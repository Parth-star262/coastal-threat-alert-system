import React from "react";
import { GeoJSON, MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Default custom icon (red location pin)
const locationIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png", // red pin icon
  iconSize: [32, 32], // size of the icon
  iconAnchor: [16, 32], // point of the icon which will correspond to marker's location
  popupAnchor: [0, -32], // point from which the popup should open relative to the iconAnchor
});


function riskZoneStyle(feature) {
    const colors = {
        LOW: "#22c55e",
        MEDIUM: "#eab308",
        HIGH: "#f97316",
        CRITICAL: "#dc2626",
    };
    const color = colors[feature.properties.risk_level] || "#64748b";
    return { color, fillColor: color, fillOpacity: 0.22, weight: 2 };
}

function MapView({ data, selectedCity, onCitySelect, riskZones }) {
    // Get unique cities with their latest data
    const citiesData = [];
    const cities = [...new Set(data.map(item => item.city))];

    cities.forEach(city => {
        const cityData = data.filter(item => item.city === city);
        if (cityData.length > 0) {
            citiesData.push({
                city: city,
                data: cityData[0] // Latest data for this city
            });
        }
    });

    // Get data for selected city
    const selectedCityData = data.filter(item => item.city === selectedCity);

    // City coordinates (you can add more cities)
    const cityCoordinates = {
        "Mumbai": [19.0760, 72.8777],
        "Chennai": [13.0827, 80.2707],
        "Kolkata": [22.5726, 88.3639],
        "Surat": [21.1702, 72.8311],
        "Visakhapatnam": [17.6868, 83.2185],
        "Kochi": [9.9312, 76.2673],
        "Mangalore": [12.9716, 74.8609]
    };

    return (
        <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">🗺️ Multi-City Location View</h3>

            {/* City Selection Buttons Above Map */}
            <div className="mb-4 bg-white p-4 rounded-lg shadow-md">
                <h4 className="font-semibold mb-3 text-gray-700">📍 Select City:</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                    {citiesData.map((cityInfo) => (
                        <button
                            key={cityInfo.city}
                            onClick={() => onCitySelect(cityInfo.city)}
                            className={`relative group p-4 rounded-xl border-2 shadow-md transition-all duration-300 flex flex-col items-center justify-center ${cityInfo.city === selectedCity
                                    ? 'bg-gradient-to-r from-red-500 to-pink-500 text-white border-red-600 scale-105'
                                    : 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white border-blue-600 hover:scale-105 hover:shadow-lg'
                                }`}
                        >
                            {/* Location Icon */}
                            <span className="text-2xl mb-2">📍</span>

                            {/* City Name */}
                            <span className="font-semibold">{cityInfo.city}</span>

                            {/* Selected Badge */}
                            {cityInfo.city === selectedCity && (
                                <span className="absolute -top-2 right-2 bg-white text-red-600 text-xs px-2 py-0.5 rounded-full shadow">
                                    ✅ Selected
                                </span>
                            )}
                        </button>
                    ))}
                </div>
            </div>



            {/* Map View */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                <MapContainer
                    center={[23.5937, 78.9629]} // Center of India
                    zoom={5}
                    style={{ height: "500px", width: "100%" }}
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />

                    {riskZones.features.length > 0 && (
                        <GeoJSON
                            data={riskZones}
                            style={riskZoneStyle}
                            onEachFeature={(feature, layer) => {
                                layer.bindPopup(
                                    `<strong>${feature.properties.city}</strong><br/>Risk: ${feature.properties.risk_level}<br/>Score: ${feature.properties.risk_score}`
                                );
                            }}
                        />
                    )}

                    {citiesData.map((cityInfo) => {
                        const coords = cityCoordinates[cityInfo.city];
                        if (!coords) return null;

                        return (

                            <Marker
                                key={cityInfo.city}
                                position={coords}
                                icon={locationIcon}
                                eventHandlers={{
                                    click: () => onCitySelect(cityInfo.city)
                                }}
                            >


                                <Popup>
                                    <div className="text-center p-3">
                                        <h4 className="font-bold text-lg text-blue-600 mb-2">{cityInfo.city}</h4>
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <span className="font-semibold">🌡️ Temperature:</span>
                                                <span className="text-blue-600">{cityInfo.data.temperature}°C</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="font-semibold">💧 Humidity:</span>
                                                <span className="text-green-600">{cityInfo.data.humidity}%</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="font-semibold">💨 Wind:</span>
                                                <span className="text-orange-600">{cityInfo.data.wind_speed} m/s</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="font-semibold">☁️ Condition:</span>
                                                <span className="text-purple-600 capitalize">{cityInfo.data.description}</span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => onCitySelect(cityInfo.city)}
                                            className="mt-3 w-full px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg text-sm hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-md"
                                        >
                                            🎯 Select This City
                                        </button>
                                    </div>
                                </Popup>
                            </Marker>
                        );
                    })}
                </MapContainer>
            </div>

            {/* Current City Info */}
            {selectedCityData.length > 0 && (
                <div className="mt-4 bg-white p-4 rounded-lg shadow-md">
                    <h4 className="font-semibold mb-2 text-gray-700">
                        �� Currently Viewing: {selectedCity}
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                        <div className="bg-blue-50 p-3 rounded-lg">
                            <div className="text-lg font-bold text-blue-600">
                                {selectedCityData[0].temperature}°C
                            </div>
                            <div className="text-sm text-gray-600">Temperature</div>
                        </div>
                        <div className="bg-green-50 p-3 rounded-lg">
                            <div className="text-lg font-bold text-green-600">
                                {selectedCityData[0].humidity}%
                            </div>
                            <div className="text-sm text-gray-600">Humidity</div>
                        </div>
                        <div className="bg-orange-50 p-3 rounded-lg">
                            <div className="text-lg font-bold text-orange-600">
                                {selectedCityData[0].wind_speed} m/s
                            </div>
                            <div className="text-sm text-gray-600">Wind Speed</div>
                        </div>
                        <div className="bg-purple-50 p-3 rounded-lg">
                            <div className="text-lg font-bold text-purple-600 capitalize">
                                {selectedCityData[0].description}
                            </div>
                            <div className="text-sm text-gray-600">Condition</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default MapView;