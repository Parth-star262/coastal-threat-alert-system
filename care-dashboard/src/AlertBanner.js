import React from "react";

function AlertBanner({ data }) {
  if (data.length === 0) return null;

  // latest record check karo
  const latest = data[data.length - 1];
  const { city, wind_speed, description } = latest;

  let alertMessage = "";
  let bgColor = "";

  if (wind_speed > 20) {
    alertMessage = `⚠️ High Wind Alert in ${city}: ${wind_speed} m/s 🌪️`;
    bgColor = "bg-red-500";
  } else if (description.includes("rain")) {
    alertMessage = `🌧️ Rain Alert in ${city}: ${description}`;
    bgColor = "bg-yellow-500";
  }

  if (!alertMessage) return null;

  return (
    <div className={`${bgColor} text-white p-3 mb-4 rounded-lg shadow-lg`}>
      <strong>{alertMessage}</strong>
    </div>
  );
}

export default AlertBanner;
