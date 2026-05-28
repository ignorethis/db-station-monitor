"""Zeit-Parsing und Countdown-Hilfen für MOTIS-Abfahrten."""

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from constants import DEPARTURE_GRACE_MINUTES

logger = logging.getLogger(__name__)


def now_utc():
    return datetime.now(timezone.utc)


def parse_api_datetime(value, tz_name=None, source_stop_id=None):
    """Parst ISO-Zeitstempel.

    OpenOV liefert lokale Wandzeiten mit Z-Suffix (nicht UTC).
    DELFI und die meisten anderen Feeds liefern echtes UTC mit Z.
    """
    if tz_name and source_stop_id and "OpenOV" in source_stop_id:
        try:
            naive = datetime.fromisoformat(value.replace("Z", ""))
            return naive.replace(tzinfo=ZoneInfo(tz_name))
        except Exception:
            logger.debug("TZ-Parsing fehlgeschlagen für %s (%s), fallback UTC", value, tz_name)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_local_time(dt):
    return dt.astimezone().strftime("%H:%M")


def minutes_until_departure(departure_time):
    dep_utc = departure_time.astimezone(timezone.utc)
    return max(0, round((dep_utc - now_utc()).total_seconds() / 60))


def format_countdown(minutes):
    return "jetzt" if minutes <= 0 else f"{minutes}m"


def is_departure_past(departure_time):
    cutoff = now_utc() - timedelta(minutes=DEPARTURE_GRACE_MINUTES)
    return departure_time.astimezone(timezone.utc) < cutoff
