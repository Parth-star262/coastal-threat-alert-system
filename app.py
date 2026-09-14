from flask import Flask, jsonify, request
import psycopg2
from flask_cors import CORS
from services.alert_service import AlertService
from services.coastal_anomaly_service import CoastalAnomalyService
from config import APP_DEBUG, APP_HOST, APP_PORT, CORS_ORIGINS

# ========== EMAIL ALERT FUNCTION ==========
def send_email_alert(city, temperature, humidity, wind_speed, description):
    return alert_service.send_email_alert(
        city, temperature, humidity, wind_speed, description
    )


# ========== FLASK APP ==========
app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


from config import DB_CONFIG, ML_CONFIG

alert_service = AlertService()
coastal_anomaly_service = CoastalAnomalyService()


@app.route("/health", methods=["GET"])
def health_check():
    try:
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return jsonify({"status": "ok", "database": "ok"})
    except psycopg2.Error:
        return jsonify({"status": "degraded", "database": "unavailable"}), 503


def validate_weather_payload(data):
    required = ["city", "temperature", "humidity", "wind_speed", "description"]
    missing = [field for field in required if field not in data]
    if missing:
        return f"Missing fields: {', '.join(missing)}"
    if not isinstance(data["city"], str) or not data["city"].strip():
        return "city must be a non-empty string"
    for field in ["temperature", "humidity", "wind_speed"]:
        if not isinstance(data[field], (int, float)):
            return f"{field} must be numeric"
    if not 0 <= data["humidity"] <= 100:
        return "humidity must be between 0 and 100"
    if data["wind_speed"] < 0:
        return "wind_speed cannot be negative"
    return None

# ========== HOME / API STATUS ROUTE ==========
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Coastal Threat Alert API",
        "status": "Online",
        "ml_model": "Active (PyTorch CUDA GPU - RTX 2050)" if ML_CONFIG.get("use_model") else "Disabled",
        "endpoints": {
            "root": "/",
            "predict": "/predict (POST/GET)",
            "latest_weather": "/latest",
            "latest_city_weather": "/latest/<city>",
            "weather_history": "/history",
            "add_record": "/add_record (POST)"
        }
    })

# ========== ML MODEL PREDICTION ENDPOINT ==========
@app.route("/predict", methods=["POST", "GET"])
def predict_threat():
    try:
        from ml_models.model_inference import ModelInference
        inference = ModelInference()
        
        if request.method == "POST":
            data = request.get_json() or {}
            required_features = ["temperature", "humidity", "wind_speed", "pressure", "hour", "month"]
            missing_features = [feature for feature in required_features if feature not in data]
            if missing_features:
                return jsonify({"error": f"Missing prediction features: {', '.join(missing_features)}"}), 400
            if any(not isinstance(data[feature], (int, float)) for feature in required_features):
                return jsonify({"error": "Prediction features must be numeric"}), 400
        else:
            data = {
                "temperature": float(request.args.get("temperature", 25)),
                "humidity": float(request.args.get("humidity", 60)),
                "wind_speed": float(request.args.get("wind_speed", 10)),
                "pressure": float(request.args.get("pressure", 1013)),
                "hour": int(request.args.get("hour", 12)),
                "month": int(request.args.get("month", 6))
            }
        
        result = inference.predict_with_fallback(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict/<city>", methods=["GET"])
def predict_city_threat(city):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT temperature, humidity, wind_speed, pressure, timestamp
            FROM weather_data
            WHERE LOWER(city) = LOWER(%s)
            ORDER BY timestamp DESC
            LIMIT 1;
        """, (city,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({"error": f"No weather data found for {city}"}), 404

        timestamp = row[4]
        data = {
            "temperature": row[0],
            "humidity": row[1],
            "wind_speed": row[2],
            "pressure": row[3],
            "hour": timestamp.hour,
            "month": timestamp.month,
        }
        from ml_models.model_inference import ModelInference
        result = ModelInference().predict_with_fallback(data)
        result["city"] = city
        result["observed_at"] = str(timestamp)
        return jsonify(result)
    except Exception as error:
        return jsonify({"error": str(error)}), 500
# ========== LATEST WEATHER (GENERAL) ==========
@app.route("/latest", methods=["GET"])
def get_latest_weather():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT city, temperature, humidity, wind_speed, pressure, rainfall_1h_mm, visibility_m, description, latitude, longitude, timestamp
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
                "rainfall_1h_mm": row[5],
                "visibility_m": row[6],
                "description": row[7],
                "latitude": row[8],
                "longitude": row[9],
                "timestamp": str(row[10])
            }

            # ✅ ALERT CONDITION
            if alert_service.should_send_alert(row[3], row[2]):
                created_alert = alert_service.create_weather_alert(
                    row[0], row[1], row[2], row[3], row[7], row[10]
                )
                if created_alert:
                    alert_service.notify_alert(
                        created_alert[0], row[0], row[1], row[2], row[3], row[7]
                    )

            return jsonify(data)
        else:
            return jsonify({"message": "No data found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ========== LATEST WEATHER PER CITY ==========
@app.route("/latest/<city>", methods=["GET"])
def get_latest_city_weather(city):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT city, temperature, humidity, wind_speed, pressure, rainfall_1h_mm, visibility_m, description, latitude, longitude, timestamp
            FROM weather_data
            WHERE LOWER(city) = LOWER(%s)
            ORDER BY timestamp DESC
            LIMIT 1;
        """, (city,))
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
                "rainfall_1h_mm": row[5],
                "visibility_m": row[6],
                "description": row[7],
                "latitude": row[8],
                "longitude": row[9],
                "timestamp": str(row[10])
            }

            # ✅ ALERT CONDITION (change thresholds as needed)
            if alert_service.should_send_alert(row[3], row[2]):
                created_alert = alert_service.create_weather_alert(
                    row[0], row[1], row[2], row[3], row[7], row[10]
                )
                if created_alert:
                    alert_service.notify_alert(
                        created_alert[0], row[0], row[1], row[2], row[3], row[7]
                    )

            return jsonify(data)
        else:
            return jsonify({"message": f"No data found for {city}"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== WEATHER HISTORY (MULTI-CITY) ==========
@app.route("/history", methods=["GET"])
def get_weather_history():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT city, temperature, humidity, wind_speed, pressure, rainfall_1h_mm, visibility_m, description, latitude, longitude, timestamp
            FROM weather_data
            ORDER BY timestamp DESC
            LIMIT 50;
        """)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "city": row[0],
                "temperature": row[1],
                "humidity": row[2],
                "wind_speed": row[3],
                "pressure": row[4],
                "rainfall_1h_mm": row[5],
                "visibility_m": row[6],
                "description": row[7],
                "latitude": row[8],
                "longitude": row[9],
                "timestamp": str(row[10])
            })

        return jsonify(history)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/coastal/latest", methods=["GET"])
def get_latest_coastal_observations():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ON (city)
                city, latitude, longitude, observed_at, wave_height_m,
                sea_level_height_m, sea_surface_temperature_c,
                ocean_current_velocity_kmh, source
            FROM coastal_observations
            ORDER BY city, observed_at DESC;
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify([
            {
                "city": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "observed_at": str(row[3]),
                "wave_height_m": row[4],
                "sea_level_height_m": row[5],
                "sea_surface_temperature_c": row[6],
                "ocean_current_velocity_kmh": row[7],
                "source": row[8],
            }
            for row in rows
        ])
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/coastal/history", methods=["GET"])
def get_coastal_history():
    try:
        city = request.args.get("city")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
            SELECT city, latitude, longitude, observed_at, wave_height_m,
                   sea_level_height_m, sea_surface_temperature_c,
                   ocean_current_velocity_kmh, source
            FROM coastal_observations
        """
        params = []
        if city:
            query += " WHERE LOWER(city) = LOWER(%s)"
            params.append(city)
        query += " ORDER BY observed_at DESC LIMIT 200"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify([
            {
                "city": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "observed_at": str(row[3]),
                "wave_height_m": row[4],
                "sea_level_height_m": row[5],
                "sea_surface_temperature_c": row[6],
                "ocean_current_velocity_kmh": row[7],
                "source": row[8],
            }
            for row in rows
        ])
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/coastal/anomalies", methods=["GET"])
def get_coastal_anomalies():
    try:
        return jsonify(coastal_anomaly_service.detect(request.args.get("city")))
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/risk-zones", methods=["GET"])
def get_risk_zones():
    try:
        city = request.args.get("city")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
            SELECT city, latitude, longitude, risk_score, risk_level,
                   factors, assessed_at
            FROM risk_assessments
        """
        params = []
        if city:
            query += " WHERE LOWER(city) = LOWER(%s)"
            params.append(city)
        query += " ORDER BY risk_score DESC, city"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        features = []
        for row in rows:
            latitude, longitude = row[1], row[2]
            radius = 0.25
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [longitude - radius, latitude - radius],
                        [longitude + radius, latitude - radius],
                        [longitude + radius, latitude + radius],
                        [longitude - radius, latitude + radius],
                        [longitude - radius, latitude - radius],
                    ]],
                },
                "properties": {
                    "city": row[0],
                    "risk_score": row[3],
                    "risk_level": row[4],
                    "factors": row[5],
                    "assessed_at": str(row[6]),
                },
            })
        return jsonify({"type": "FeatureCollection", "features": features})
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/alerts", methods=["GET"])
def get_alerts():
    try:
        city = request.args.get("city")
        status = request.args.get("status")
        query = """
            SELECT id, city, severity, confidence, trigger, message,
                   recommended_action, status, observed_at, created_at, resolved_at
            FROM alerts
        """
        filters = []
        params = []
        if city:
            filters.append("LOWER(city) = LOWER(%s)")
            params.append(city)
        if status:
            filters.append("status = %s")
            params.append(status)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY created_at DESC LIMIT 200"

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify([
            {
                "id": row[0], "city": row[1], "severity": row[2],
                "confidence": row[3], "trigger": row[4], "message": row[5],
                "recommended_action": row[6], "status": row[7],
                "observed_at": str(row[8]) if row[8] else None,
                "created_at": str(row[9]),
                "resolved_at": str(row[10]) if row[10] else None,
            }
            for row in rows
        ])
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/notifications", methods=["GET"])
def get_notifications():
    try:
        alert_id = request.args.get("alert_id")
        query = """
            SELECT id, alert_id, channel, recipient, status, error_message,
                   sent_at, created_at
            FROM notifications
        """
        params = []
        if alert_id:
            query += " WHERE alert_id = %s"
            params.append(alert_id)
        query += " ORDER BY created_at DESC LIMIT 200"
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify([
            {
                "id": row[0], "alert_id": row[1], "channel": row[2],
                "recipient": row[3], "status": row[4], "error_message": row[5],
                "sent_at": str(row[6]) if row[6] else None,
                "created_at": str(row[7]),
            }
            for row in rows
        ])
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/alerts/<int:alert_id>/status", methods=["PATCH"])
def update_alert_status(alert_id):
    try:
        payload = request.get_json(silent=True) or {}
        status = payload.get("status")
        allowed_statuses = {"active", "acknowledged", "resolved", "expired"}
        if status not in allowed_statuses:
            return jsonify({"error": "Invalid alert status"}), 400

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE alerts
            SET status = %s,
                resolved_at = CASE WHEN %s IN ('resolved', 'expired') THEN NOW() ELSE NULL END
            WHERE id = %s
            RETURNING id, status, resolved_at
            """,
            (status, status, alert_id),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        if not row:
            return jsonify({"error": "Alert not found"}), 404
        return jsonify({"id": row[0], "status": row[1], "resolved_at": str(row[2]) if row[2] else None})
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/storms", methods=["GET"])
def get_storm_events():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, event_type, alert_level, title, description,
                   latitude, longitude, event_time, published_at, link, source
            FROM storm_events
            ORDER BY event_time DESC NULLS LAST
            LIMIT 100;
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify([
            {
                "event_id": row[0],
                "event_type": row[1],
                "alert_level": row[2],
                "title": row[3],
                "description": row[4],
                "latitude": row[5],
                "longitude": row[6],
                "event_time": str(row[7]) if row[7] else None,
                "published_at": str(row[8]) if row[8] else None,
                "link": row[9],
                "source": row[10],
            }
            for row in rows
        ])
    except Exception as error:
        return jsonify({"error": str(error)}), 500


# ========== ADD RECORD API (for testing/demo) ==========
@app.route("/add_record", methods=["POST"])
def add_record():
    """Insert new weather record (multi-city)"""
    try:
        data = request.get_json()
        validation_error = validate_weather_payload(data or {})
        if validation_error:
            return jsonify({"error": validation_error}), 400
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO weather_data
                (city, temperature, humidity, wind_speed, pressure, rainfall_1h_mm,
                 visibility_m, description, latitude, longitude, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW());
        """, (
            data["city"],
            data["temperature"],
            data["humidity"],
            data["wind_speed"],
            data.get("pressure"),
            data.get("rainfall_1h_mm"),
            data.get("visibility_m"),
            data["description"],
            data.get("latitude"),
            data.get("longitude"),
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Record added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== MAIN ==========
if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)
