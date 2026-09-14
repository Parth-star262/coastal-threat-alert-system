import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

function WeatherCharts({ data, cityName }) {
  if (data.length === 0) {
    return (
      <div className="mt-6 text-center text-gray-500">
        No weather data available for {cityName}
      </div>
    );
  }

  // Prepare chart data from the API history window.
  const chartData = data.map((item, index) => ({
    time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    temperature: item.temperature,
    humidity: item.humidity,
    windSpeed: item.wind_speed,
  }));

  return (
    <div className="mt-8">
      <h3 className="text-xl font-semibold mb-4 text-center text-gray-700">
        �� Weather Trends for {cityName} (Last 10 Records)
      </h3>
      <div className="bg-white p-4 rounded-lg shadow-lg">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="humidity" stroke="#10B981" strokeWidth={3} name="Humidity (%)" />
            <Line type="monotone" dataKey="temperature" stroke="#F59E0B" strokeWidth={3} name="Temperature (°C)" />
            <Line type="monotone" dataKey="windSpeed" stroke="#3B82F6" strokeWidth={3} name="Wind Speed (m/s)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default WeatherCharts;