from flask import Flask, jsonify
import psycopg2
from weather_api_test import fetch_and_store   # Weather fetch function
from alerts import send_email_alert            # 👈 Email/SMS alert function
from config import DB_CONFIG

app = Flask(__name__)

@app.route("/latest", methods=["GET"])
def get_latest_weather():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT city, temperature, humidity, wind_speed, pressure, description, latitude, longitude, timestamp
            FROM weather_data
            ORDER BY timestamp DESC
            LIMIT 1;
        """)
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if row:
            data = {
                "city": row[0],
                "temperature": row[1],
                "humidity": row[2],
                "wind_speed": row[3],
                "pressure": row[4],
                "description": row[5],
                "latitude": row[6],
                "longitude": row[7],
                "timestamp": str(row[8])
            }

            # ✅ ALERT CONDITION
            if row[3] > 15 or row[2] > 85:   # Example: wind >15 m/s OR humidity >85%
                send_email_alert(row[0], row[1], row[2], row[3], row[4])

            return jsonify(data)
        else:
            return jsonify({"message": "No data found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
