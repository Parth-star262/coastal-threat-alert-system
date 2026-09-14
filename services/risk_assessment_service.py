import json
import logging
import math

import psycopg2

from config import COASTAL_LOCATIONS, DB_CONFIG

logger = logging.getLogger(__name__)


class RiskAssessmentService:
    def assess_all(self):
        weather = self._latest_weather()
        coastal = self._latest_coastal()
        storms = self._storm_events()
        assessments = []

        for city, (latitude, longitude) in COASTAL_LOCATIONS.items():
            factors = {}
            score = 0
            weather_row = weather.get(city)
            coastal_row = coastal.get(city)

            if weather_row:
                if weather_row["wind_speed"] >= 20:
                    score += 3
                    factors["high_wind"] = weather_row["wind_speed"]
                elif weather_row["wind_speed"] >= 15:
                    score += 2
                    factors["elevated_wind"] = weather_row["wind_speed"]
                if weather_row["pressure"] is not None and weather_row["pressure"] < 1000:
                    score += 1
                    factors["low_pressure"] = weather_row["pressure"]

            if coastal_row:
                if coastal_row["wave_height_m"] is not None:
                    if coastal_row["wave_height_m"] >= 4:
                        score += 3
                        factors["very_high_waves_m"] = coastal_row["wave_height_m"]
                    elif coastal_row["wave_height_m"] >= 2:
                        score += 2
                        factors["high_waves_m"] = coastal_row["wave_height_m"]
                if coastal_row["sea_level_height_m"] is not None and abs(coastal_row["sea_level_height_m"]) >= 1:
                    score += 2
                    factors["sea_level_height_m"] = coastal_row["sea_level_height_m"]

            nearby_storms = [
                storm for storm in storms
                if storm["latitude"] is not None
                and storm["longitude"] is not None
                and self._distance_km(latitude, longitude, storm["latitude"], storm["longitude"]) <= 500
            ]
            if nearby_storms:
                score += 3
                factors["nearby_cyclone_events"] = len(nearby_storms)

            risk_level = self._risk_level(score)
            geometry = self._point_buffer_geojson(longitude, latitude, 0.25)
            assessment = {
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "risk_score": score,
                "risk_level": risk_level,
                "factors": factors,
                "geometry": geometry,
            }
            self._store(assessment)
            assessments.append(assessment)

        logger.info("risk_assessments_updated count=%s", len(assessments))
        return assessments

    @staticmethod
    def _risk_level(score):
        if score >= 6:
            return "CRITICAL"
        if score >= 4:
            return "HIGH"
        if score >= 2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _distance_km(latitude1, longitude1, latitude2, longitude2):
        radius = 6371
        lat1, lat2 = math.radians(latitude1), math.radians(latitude2)
        delta_lat = math.radians(latitude2 - latitude1)
        delta_lon = math.radians(longitude2 - longitude1)
        value = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        )
        return 2 * radius * math.asin(math.sqrt(value))

    @staticmethod
    def _point_buffer_geojson(longitude, latitude, radius_degrees):
        return {
            "type": "Polygon",
            "coordinates": [[
                [longitude - radius_degrees, latitude - radius_degrees],
                [longitude + radius_degrees, latitude - radius_degrees],
                [longitude + radius_degrees, latitude + radius_degrees],
                [longitude - radius_degrees, latitude + radius_degrees],
                [longitude - radius_degrees, latitude - radius_degrees],
            ]],
        }

    @staticmethod
    def _latest_weather():
        rows = RiskAssessmentService._query("""
            SELECT DISTINCT ON (city) city, wind_speed, pressure
            FROM weather_data
            ORDER BY city, timestamp DESC
        """)
        return {
            row[0]: {"wind_speed": row[1], "pressure": row[2]}
            for row in rows
        }

    @staticmethod
    def _latest_coastal():
        rows = RiskAssessmentService._query("""
            SELECT DISTINCT ON (city) city, wave_height_m, sea_level_height_m
            FROM coastal_observations
            ORDER BY city, observed_at DESC
        """)
        return {
            row[0]: {"wave_height_m": row[1], "sea_level_height_m": row[2]}
            for row in rows
        }

    @staticmethod
    def _storm_events():
        rows = RiskAssessmentService._query("""
            SELECT latitude, longitude
            FROM storm_events
            WHERE event_type = 'TROPICAL_CYCLONE'
              AND event_time >= NOW() - INTERVAL '14 days'
        """)
        return [{"latitude": row[0], "longitude": row[1]} for row in rows]

    @staticmethod
    def _query(query):
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()

    @staticmethod
    def _store(assessment):
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO risk_assessments
                        (city, latitude, longitude, risk_score, risk_level, factors, assessed_at)
                    VALUES (%(city)s, %(latitude)s, %(longitude)s, %(risk_score)s,
                            %(risk_level)s, %(factors)s::jsonb, NOW())
                    ON CONFLICT (city) DO UPDATE SET
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        risk_score = EXCLUDED.risk_score,
                        risk_level = EXCLUDED.risk_level,
                        factors = EXCLUDED.factors,
                        assessed_at = NOW()
                    """,
                    {**assessment, "factors": json.dumps(assessment["factors"])},
                )
