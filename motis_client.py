"""MOTIS/Transitous API-Client."""

import logging
from urllib.parse import quote

import requests

from constants import USER_AGENT
from input_sanitizer import sanitize_url_parameter, SanitizationError
from settings import Settings
from station_utils import station_names_match

MAX_PLAN_ITINERARIES = 20
PLAN_TIMEOUT = 60
PLAN_EXCLUDED_MODES = frozenset({"WALK", "COACH", "CAR", "BIKE", "CAR_PARKING"})

logger = logging.getLogger(__name__)

class MotisClient:
    """HTTP-Zugriff auf MOTIS-Endpunkte (Geocoding, Stoptimes, Plan)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.motis_api.rstrip("/")
        self.timeout = settings.api_timeout
        self.headers = {"User-Agent": USER_AGENT}

    def geocode(self, text):
        try:
            sanitize_url_parameter(text)
        except SanitizationError as error:
            logger.warning("Ungültiger Geocode-Parameter: %s", error)
            return []
        
        url = f"{self.base_url}/api/v1/geocode?text={quote(text)}&type=STOP"
        response = requests.get(url, timeout=self.timeout, headers=self.headers, verify=True)
        response.raise_for_status()
        locations = response.json()
        return locations if isinstance(locations, list) else []

    def fetch_stoptimes(self, stop_id, count=50):
        try:
            sanitize_url_parameter(stop_id)
        except SanitizationError as error:
            logger.warning("Ungültige Stop-ID: %s", error)
            return [], {}
        
        url = f"{self.base_url}/api/v5/stoptimes?stopId={quote(stop_id)}&n={count}"
        response = requests.get(url, timeout=self.timeout, headers=self.headers, verify=True)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return [], {}
        return data.get("stopTimes", []) or [], data.get("place", {}) or {}

    def verify_stop(self, stop_id, station_name, sample_size=5):
        try:
            stop_times, place = self.fetch_stoptimes(stop_id, count=sample_size)
            if not stop_times:
                return None
            place_name = place.get("name", "")
            if not station_names_match(station_name, place_name):
                return None
            if "OpenOV" in stop_id:
                source = "openov"
            elif "DELFI" in stop_id:
                source = "delfi"
            else:
                source = "other"
            return {"id": stop_id, "name": place_name, "lat": place.get("lat"), "lon": place.get("lon"), "source": source, "modes": {item.get("mode") for item in stop_times if item.get("mode")}, "departure_count": len(stop_times)}
        except Exception as error:
            logger.debug("Verifizierung fehlgeschlagen für %s: %s", stop_id, error)
            return None

    def resolve_stop_id(self, station_name):
        candidates = self.geocode(station_name)
        if not candidates:
            return None
        for location in candidates:
            if station_names_match(station_name, location.get("name", "")):
                return location.get("id")
        return candidates[0].get("id")

    def _fetch_plan_itineraries(self, from_stop_id, to_stop_id):
        url = f"{self.base_url}/api/v5/plan?fromPlace={quote(from_stop_id)}&toPlace={quote(to_stop_id)}&maxTransfers=4"
        response = requests.get(url, timeout=PLAN_TIMEOUT, headers=self.headers, verify=True)
        response.raise_for_status()
        data = response.json()
        return data.get("itineraries") or []

    def resolve_destination_plan(self, from_stop_ids, to_stop_id):
        if not to_stop_id:
            return set(), []
        if isinstance(from_stop_ids, str):
            from_stop_ids = [from_stop_ids]
        known_ids = set(from_stop_ids)
        trip_ids = set()
        extra_stops = []
        for from_id in from_stop_ids:
            try:
                itineraries = self._fetch_plan_itineraries(from_id, to_stop_id)
            except Exception as error:
                logger.warning("Routenplanung fehlgeschlagen (%s): %s", from_id, error)
                continue
            if not itineraries:
                continue
            for itinerary in itineraries[:MAX_PLAN_ITINERARIES]:
                transit_legs = [leg for leg in itinerary.get("legs") or [] if leg.get("mode") not in PLAN_EXCLUDED_MODES]
                boarding_index = None
                for index, leg in enumerate(transit_legs):
                    boarding_id = (leg.get("from") or {}).get("stopId")
                    if boarding_id and boarding_id in known_ids:
                        boarding_index = index
                        break
                if boarding_index is None:
                    continue
                for leg in transit_legs[boarding_index:]:
                    if leg.get("mode") in PLAN_EXCLUDED_MODES:
                        break
                    trip_id = leg.get("tripId")
                    if trip_id:
                        trip_ids.add(trip_id)
                    boarding_stop = leg.get("from") or {}
                    boarding_id = boarding_stop.get("stopId")
                    if boarding_id and boarding_id not in known_ids:
                        known_ids.add(boarding_id)
                        extra_stops.append({"id": boarding_id, "source": "delfi" if "DELFI" in boarding_id else "plan", "label": f"Routenplanung ({boarding_stop.get('name', boarding_id)})"})
            if trip_ids or extra_stops:
                logger.info("Routenplanung: %s tripIds, %s Zusatz-Stops von %s nach %s", len(trip_ids), len(extra_stops), from_id, to_stop_id)
                return trip_ids, extra_stops
        return trip_ids, extra_stops

    def fetch_trip_ids_to_destination(self, from_stop_ids, to_stop_id):
        trip_ids, _extra = self.resolve_destination_plan(from_stop_ids, to_stop_id)
        return trip_ids
