import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

function WeatherCharts({ data, cityName }) {
  if (!data.length) return <div className="component-empty">No weather data available for {cityName}</div>;

  const chartData = data.map((item) => ({
    time: new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    temperature: item.temperature,
    humidity: item.humidity,
    windSpeed: item.wind_speed,
  }));

  return (
    <div className="chart-frame">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="#e6eef1" strokeDasharray="2 5" vertical={false} />
          <XAxis dataKey="time" tick={{ fill: "#80919a", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#80919a", fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ border: "1px solid #dce7ed", borderRadius: 7, fontSize: 11, boxShadow: "0 8px 24px #18374618" }} />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
          <Line type="monotone" dataKey="humidity" stroke="#04a7a0" strokeWidth={2} dot={false} name="Humidity (%)" />
          <Line type="monotone" dataKey="temperature" stroke="#ec8b3d" strokeWidth={2} dot={false} name="Temperature (°C)" />
          <Line type="monotone" dataKey="windSpeed" stroke="#1664d8" strokeWidth={2} dot={false} name="Wind (m/s)" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default WeatherCharts;
