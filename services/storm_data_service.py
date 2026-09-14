import logging
import xml.etree.ElementTree as ET
from datetime import datetime

import psycopg2
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import DB_CONFIG

logger = logging.getLogger(__name__)
GDACS_RSS_URL = "https://www.gdacs.org/xml/rss.xml"


class StormDataService:
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

    def collect_current_cyclones(self):
        response = self.session.get(GDACS_RSS_URL, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        events = []

        for item in root.findall("./channel/item"):
            subject = self._text(item, "subject")
            if not subject.startswith("TC"):
                continue

            point = self._text(item, "point").split()
            if len(point) != 2:
                logger.warning("storm_event_missing_point guid=%s", self._text(item, "guid"))
                continue

            event = {
                "event_id": self._text(item, "guid"),
                "event_type": "TROPICAL_CYCLONE",
                "alert_level": subject,
                "title": self._text(item, "title"),
                "description": self._text(item, "description"),
                "latitude": float(point[0]),
                "longitude": float(point[1]),
                "event_time": self._parse_date(self._text(item, "fromdate")),
                "published_at": self._parse_date(self._text(item, "pubDate")),
                "link": self._text(item, "link"),
                "source": "GDACS RSS",
            }
            self._store(event)
            events.append(event)

        logger.info("storm_events_collected count=%s", len(events))
        return events

    @staticmethod
    def _text(item, name):
        element = item.find(name)
        return (element.text or "").strip() if element is not None else ""

    @staticmethod
    def _parse_date(value):
        return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z") if value else None

    @staticmethod
    def _store(event):
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO storm_events
                        (event_id, event_type, alert_level, title, description,
                         latitude, longitude, event_time, published_at, link, source, updated_at)
                    VALUES (%(event_id)s, %(event_type)s, %(alert_level)s, %(title)s,
                            %(description)s, %(latitude)s, %(longitude)s,
                            %(event_time)s, %(published_at)s, %(link)s, %(source)s, NOW())
                    ON CONFLICT (event_id) DO UPDATE SET
                        alert_level = EXCLUDED.alert_level,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        event_time = EXCLUDED.event_time,
                        published_at = EXCLUDED.published_at,
                        link = EXCLUDED.link,
                        updated_at = NOW()
                    """,
                    event,
                )
