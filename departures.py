"""Abfahrtsdaten laden, parsen und filtern."""

import logging
from constants import (FERNVERKEHR_MODES, MODE_NAMES, NAHVERKEHR_MODES, STOPTIMES_DEFAULT)
from datetime_utils import (format_countdown, format_local_time, is_departure_past, minutes_until_departure, parse_api_datetime)
from motis_client import MotisClient
from station_utils import destination_matches

logger = logging.getLogger(__name__)

def departure_dedup_key(stop_time):
    place = stop_time.get("place", {})
    trip_id = stop_time.get("tripId")
    if trip_id:
        return ("trip", trip_id, place.get("scheduledDeparture", ""))
    return (stop_time.get("displayName", stop_time.get("routeShortName", "")), place.get("scheduledDeparture", ""), stop_time.get("headsign", stop_time.get("tripTo", {}).get("name", "")))

def get_status_text(cancelled, delay_minutes):
    if cancelled:
        return "⚫ GESTRICHEN", "#FF0000"
    if delay_minutes > 0.5:
        mins = int(round(delay_minutes))
        color = "#FF4444" if delay_minutes > 15 else "#FFAA00"
        return f"⚠️ +{mins}min", color
    return "✅ Pünktlich", "#00DD00"

def trip_notification_key(departure):
    return (departure["linie"], departure["direction"], departure["planned_time"].isoformat())

class DepartureService:
    def __init__(self, motis: MotisClient):
        self.motis = motis

    def fetch_merged(self, stop_entries, per_stop_count=STOPTIMES_DEFAULT):
        merged = []
        seen_keys = set()
        sources_loaded = []
        for entry in stop_entries:
            stop_id = entry["id"]
            label = entry.get("label", entry.get("source", stop_id))
            try:
                stop_times, _place = self.motis.fetch_stoptimes(stop_id, count=per_stop_count)
                added = 0
                for stop_time in stop_times:
                    stop_time["_source_stop_id"] = stop_id
                    key = departure_dedup_key(stop_time)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    merged.append(stop_time)
                    added += 1
                if added:
                    sources_loaded.append(f"{label} ({added})")
                    logger.info("%s Abfahrten von %s (%s)", added, stop_id, label)
            except Exception as error:
                logger.warning("Abfahrten für %s nicht geladen: %s", stop_id, error)
        if sources_loaded:
            logger.info("Quellen geladen: %s", ", ".join(sources_loaded))
        return merged

    @staticmethod
    def parse_stop_times(stop_times, departure_filter):
        departures = []
        for stop_time in stop_times:
            try:
                departure = DepartureService._parse_stop_time(stop_time)
                if departure and departure_filter(departure):
                    departures.append(departure)
            except Exception as error:
                logger.error("Fehler beim Parsen eines Eintrags: %s", error)
        departures.sort(key=lambda item: item["planned_time"])
        return [item for item in departures if not is_departure_past(item["actual_time"])]

    @staticmethod
    def _parse_stop_time(stop_time):
        place = stop_time.get("place", {})
        planned_str = place.get("scheduledDeparture", "")
        if not planned_str:
            return None
        actual_str = place.get("departure", planned_str)
        tz_name = place.get("tz")
        source_stop_id = stop_time.get("_source_stop_id")
        planned_time = parse_api_datetime(planned_str, tz_name, source_stop_id)
        actual_time = parse_api_datetime(actual_str, tz_name, source_stop_id) if actual_str else planned_time
        trip_to = stop_time.get("tripTo") or {}
        direction = stop_time.get("headsign", trip_to.get("name", "unbekannt"))
        return {"zeit": format_local_time(planned_time), "linie": stop_time.get("displayName", stop_time.get("routeShortName", "N/A")), "mode": stop_time.get("mode", "BUS"), "diff": (actual_time - planned_time).total_seconds() / 60, "direction": direction, "trip_to": trip_to.get("name", ""), "trip_id": stop_time.get("tripId", ""), "cancelled": place.get("cancelled", False), "planned_time": planned_time, "actual_time": actual_time, "typ_text": MODE_NAMES.get(stop_time.get("mode", "BUS"), stop_time.get("mode", "BUS")), "minutes_in": format_countdown(minutes_until_departure(actual_time))}

def build_departure_filter(fernverkehr_only, nahverkehr_only, filter_text, destination_text="", destination_trip_ids=None):
    allowed_lines = [line.strip().upper() for line in filter_text.split(",") if line.strip()]
    destination_text = destination_text.strip()
    destination_trip_ids = destination_trip_ids or set()
    def matches_destination(departure):
        if not destination_text and not destination_trip_ids:
            return True
        if destination_trip_ids:
            trip_id = departure.get("trip_id")
            return bool(trip_id and trip_id in destination_trip_ids)
        return destination_matches(destination_text, departure["direction"], departure["trip_to"])
    def departure_filter(departure):
        modes = [departure["mode"]]
        line_name = departure["linie"]
        if fernverkehr_only and not any(mode in FERNVERKEHR_MODES for mode in modes):
            return False
        if nahverkehr_only and not any(mode in NAHVERKEHR_MODES for mode in modes):
            return False
        if allowed_lines:
            line_upper = line_name.upper()
            if not any(line_upper.startswith(allowed) for allowed in allowed_lines):
                return False
        if not matches_destination(departure):
            return False
        return True
    return departure_filter
