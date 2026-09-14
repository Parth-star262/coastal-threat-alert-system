import logging

import psycopg2

from config import DB_CONFIG

logger = logging.getLogger(__name__)


class CoastalAnomalyService:
    def detect(self, city=None):
        query = """
            WITH city_stats AS (
                SELECT city,
                       AVG(sea_level_height_m) AS mean_level,
                       STDDEV_POP(sea_level_height_m) AS stddev_level
                FROM coastal_observations
                WHERE sea_level_height_m IS NOT NULL
                GROUP BY city
            ), latest AS (
                SELECT DISTINCT ON (city)
                       city, observed_at, sea_level_height_m
                FROM coastal_observations
                WHERE sea_level_height_m IS NOT NULL
                ORDER BY city, observed_at DESC
            )
            SELECT latest.city, latest.observed_at, latest.sea_level_height_m,
                   city_stats.mean_level, city_stats.stddev_level
            FROM latest
            JOIN city_stats ON city_stats.city = latest.city
        """
        params = []
        if city:
            query += " WHERE LOWER(latest.city) = LOWER(%s)"
            params.append(city)

        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        results = []
        for row in rows:
            mean_level = row[3]
            stddev_level = row[4] or 0
            deviation = abs(row[2] - mean_level)
            threshold = max(2 * stddev_level, 0.25)
            results.append({
                "city": row[0],
                "observed_at": str(row[1]),
                "sea_level_height_m": row[2],
                "baseline_mean_m": mean_level,
                "baseline_stddev_m": stddev_level,
                "deviation_m": deviation,
                "is_abnormal": deviation > threshold,
                "method": "two-standard-deviation baseline with 0.25m minimum deviation",
            })
        logger.info("coastal_anomalies_detected count=%s", len(results))
        return results
