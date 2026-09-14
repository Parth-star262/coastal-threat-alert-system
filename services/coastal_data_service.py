import logging
from datetime import datetime, timezone

import psycopg2
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import COASTAL_LOCATIONS, DB_CONFIG

logger = logging.getLogger(__name__)
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"


class CoastalDataService:
    def __init__(self, session=None):
        self.session = session or self._create_session()

    @staticmethod
    def _create_session():
        retry_policy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry_policy))
        return session

    def collect_city(self, city):
        if city not in COASTAL_LOCATIONS:
            raise ValueError(f"Unknown coastal city: {city}")

        latitude, longitude = COASTAL_LOCATIONS[city]
        response = self.session.get(
            MARINE_API_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "wave_height,sea_level_height_msl,sea_surface_temperature,ocean_current_velocity",
                "cell_selection": "sea",
                "timezone": "UTC",
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current", {})
        observed_at = current.get("time")
        if not observed_at:
            raise ValueError("coastal observation timestamp is missing")
        observed_datetime = datetime.fromisoformat(observed_at).replace(tzinfo=timezone.utc)
        if abs((datetime.now(timezone.utc) - observed_datetime).total_seconds()) > 21600:
            raise ValueError("coastal observation is stale")

        wave_height = current.get("wave_height")
        sea_level = current.get("sea_level_height_msl")
        sea_temperature = current.get("sea_surface_temperature")
        current_velocity = current.get("ocean_current_velocity")
        if wave_height is not None and wave_height < 0:
            raise ValueError("wave height cannot be negative")
        if sea_temperature is not None and not -5 <= sea_temperature <= 45:
            raise ValueError("sea-surface temperature is outside expected range")
        if current_velocity is not None and current_velocity < 0:
            raise ValueError("ocean current velocity cannot be negative")

        observation = {
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
            "wave_height_m": wave_height,
            "sea_level_height_m": sea_level,
            "sea_surface_temperature_c": sea_temperature,
            "ocean_current_velocity_kmh": current_velocity,
            "source": "Open-Meteo Marine API",
        }
        self._store(observation)
        logger.info("coastal_observation_stored city=%s", city)
        return observation

    def collect_all(self):
        observations = []
        for city in COASTAL_LOCATIONS:
            try:
                observations.append(self.collect_city(city))
            except (requests.RequestException, ValueError, KeyError, psycopg2.Error) as error:
                logger.error("coastal_collection_failed city=%s error=%s", city, error)
        return observations

    @staticmethod
    def _store(observation):
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO coastal_observations
                        (city, latitude, longitude, observed_at, wave_height_m,
                         sea_level_height_m, sea_surface_temperature_c,
                         ocean_current_velocity_kmh, source)
                    VALUES (%(city)s, %(latitude)s, %(longitude)s, %(observed_at)s,
                            %(wave_height_m)s, %(sea_level_height_m)s,
                            %(sea_surface_temperature_c)s,
                            %(ocean_current_velocity_kmh)s, %(source)s)
                    """,
                    observation,
                )
