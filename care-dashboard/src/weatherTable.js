import React from "react";

function WeatherTable({ data, cityName }) {
  if (!data.length) return <div className="component-empty">No weather records available for {cityName}</div>;
  const recentData = data.slice(-8).reverse();

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead><tr><th>Time</th><th>Temp</th><th>Humidity</th><th>Wind</th><th>Condition</th></tr></thead>
        <tbody>{recentData.map((item, index) => (
          <tr key={`${item.timestamp}-${index}`}>
            <td>{new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
            <td><b>{item.temperature}°</b></td>
            <td>{item.humidity}%</td>
            <td>{item.wind_speed} m/s</td>
            <td className="condition">{item.description || "—"}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

export default WeatherTable;
