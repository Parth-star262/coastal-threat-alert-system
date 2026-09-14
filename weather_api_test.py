import requests
import psycopg2
import time
import logging
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import API_CONFIG, COASTAL_LOCATIONS, DB_CONFIG

logger = logging.getLogger(__name__)

API_KEY = API_CONFIG["openweather_api_key"]

if not API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY is not configured")

# 🌊 Multiple Coastal Cities
CITIES = [
    "Mumbai",
    "Chennai", 
    "Kolkata",
    "Visakhapatnam",
    "Surat",
    "Kochi",
    "Mangalore"
]

API_URL = "https://api.openweathermap.org/data/2.5/weather"


def create_http_session():
    retry_policy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_policy)
    session = requests.Session()
    session.mount("https://", adapter)
    return session


def fetch_and_store(session=None):
    session = session or create_http_session()
    stored_count = 0
    from services.alert_service import AlertService
    alert_service = AlertService()

    for city in CITIES:
        try:
            response = session.get(
                API_URL,
                params={"q": city, "appid": API_KEY, "units": "metric"},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            pressure = data["main"]["pressure"]
            rainfall_1h = data.get("rain", {}).get("1h", 0)
            visibility = data.get("visibility")
            description = data["weather"][0]["description"]
            latitude, longitude = COASTAL_LOCATIONS[city]
            observed_at = datetime.fromtimestamp(data["dt"], tz=timezone.utc)

            if abs((datetime.now(timezone.utc) - observed_at).total_seconds()) > 7200:
                raise ValueError("weather observation is stale")
            if not 0 <= humidity <= 100 or wind_speed < 0 or pressure <= 0:
                raise ValueError("weather observation contains invalid measurements")

            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO weather_data
                            (city, temperature, humidity, wind_speed, pressure, rainfall_1h_mm,
                            visibility_m, description, latitude, longitude, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        (
                            city, temperature, humidity, wind_speed, pressure,
                            rainfall_1h, visibility, description, latitude, longitude, observed_at,
                        ),
                    )

            if alert_service.should_send_alert(wind_speed, humidity):
                created_alert = alert_service.create_weather_alert(
                    city, temperature, humidity, wind_speed, description, observed_at
                )
                if created_alert:
                    alert_service.notify_alert(
                        created_alert[0], city, temperature, humidity, wind_speed, description
                    )

            stored_count += 1
            logger.info(
                "weather_stored city=%s temperature=%s humidity=%s wind_speed=%s",
                city,
                temperature,
                humidity,
                wind_speed,
            )
        except requests.RequestException as error:
            logger.error("weather_api_failed city=%s error=%s", city, error)
        except (KeyError, TypeError, ValueError) as error:
            logger.error("weather_data_invalid city=%s error=%s", city, error)
        except psycopg2.Error as error:
            logger.error("weather_database_failed city=%s error=%s", city, error)

        time.sleep(2)

    logger.info("weather_collection_complete stored_count=%s", stored_count)
    return stored_count


def run_forever(interval_seconds=600):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    while True:
        fetch_and_store()
        from services.coastal_data_service import CoastalDataService
        from services.risk_assessment_service import RiskAssessmentService
        from services.storm_data_service import StormDataService

        CoastalDataService().collect_all()
        StormDataService().collect_current_cyclones()
        RiskAssessmentService().assess_all()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_forever()