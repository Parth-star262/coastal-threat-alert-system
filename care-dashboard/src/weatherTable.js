import React from "react";

function WeatherTable({ data, cityName }) {
  if (data.length === 0) {
    return (
      <div className="mt-6 text-center text-gray-500">
        No weather records available for {cityName}
      </div>
    );
  }

  const recentData = data.slice(-10); // last 10 records

  return (
    <div className="mt-8">
      <h3 className="text-xl font-semibold mb-4 text-center text-gray-700">
        📋 Recent Weather Records for {cityName}
      </h3>
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
              <th className="px-6 py-3 text-left text-sm font-medium">Time</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Temp (°C)</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Humidity (%)</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Wind (m/s)</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Condition</th>
            </tr>
          </thead>
          <tbody>
            {recentData.map((item, index) => (
              <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">{item.temperature}</td>
                <td className="px-6 py-4 text-sm text-gray-900">{item.humidity}</td>
                <td className="px-6 py-4 text-sm text-gray-900">{item.wind_speed}</td>
                <td className="px-6 py-4 text-sm text-gray-900 capitalize">{item.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default WeatherTable;