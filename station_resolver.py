"""Station-Auflösung über MOTIS mit Registry-Cache."""

import logging
import re
from constants import COMPLEMENTARY_STOP_MAX_KM
from input_sanitizer import sanitize_station_name, SanitizationError
from motis_client import MotisClient
from settings import Settings
from station_utils import approx_distance_km, is_wrong_nearby_stop, stop_name_relevance

logger = logging.getLogger(__name__)

class StationResolver:
    def __init__(self, settings: Settings, motis: MotisClient):
        self.settings = settings
        self.motis = motis

    def resolve(self, station_name):
        try:
            sanitize_station_name(station_name)
        except SanitizationError as error:
            logger.warning("Ungültige Station-Name: %s", error)
            return []
        cached = self.settings.get_registry_stops(station_name)
        if cached:
            logger.info("Registry-Treffer: %s (%s Quellen)", station_name, len(cached))
            return cached
        return self.discover(station_name)

    def discover(self, station_name):
        logger.info("Station-Discovery via MOTIS: %s", station_name)
        candidates = self._collect_geocode_candidates(station_name)
        legacy_id = self.settings.station_ids.get(station_name)
        if legacy_id:
            candidates.append({"id": legacy_id, "name": station_name})
        verified = []
        seen_ids = set()
        for location in candidates:
            stop_id = location.get("id")
            if not stop_id or stop_id in seen_ids:
                continue
            seen_ids.add(stop_id)
            result = self.motis.verify_stop(stop_id, station_name)
            if result:
                verified.append(result)
        if not verified:
            return []
        verified.sort(key=lambda item: (-item["departure_count"], item["name"]))
        primary = verified[0]
        selected = [primary]
        selected_ids = {primary["id"]}
        for complement in self._find_complementary_stops(primary, verified, station_name):
            if complement["id"] not in selected_ids:
                selected.append(complement)
                selected_ids.add(complement["id"])
        stop_entries = [self._build_stop_entry(stop) for stop in selected]
        self.settings.set_registry_stops(station_name, stop_entries)
        logger.info("Station verifiziert und gespeichert: %s -> %s", station_name, [entry["id"] for entry in stop_entries])
        return stop_entries

    def _collect_geocode_candidates(self, station_name):
        queries = [station_name, station_name.replace(" (Main)", "").replace("(Main)", ""), station_name.replace("Frankfurt (Main)", "Frankfurt (M)"), re.sub(r"\s*\([^)]*\)", "", station_name).strip()]
        lower = station_name.lower()
        if "hbf" in lower or "hauptbahnhof" in lower:
            queries.extend([station_name.replace("Hbf", "Hauptbahnhof"), station_name.replace("(Main) Hbf", "Hauptbahnhof"), f"{station_name} tief", f"{station_name} Regionalbahnhof"])
        min_chars = self.settings.min_search_chars
        queries = list(dict.fromkeys(query for query in queries if len(query) >= min_chars))
        candidates = {}
        for query in queries:
            for location in self.motis.geocode(query):
                stop_id = location.get("id")
                if stop_id and stop_id not in candidates:
                    candidates[stop_id] = location
        return list(candidates.values())

    def _find_complementary_stops(self, primary, verified_stops, station_name):
        if not primary or not primary.get("lat") or not primary.get("lon"):
            return []
        primary_feed = primary["id"].split("-")[0]
        candidates = []
        for stop in verified_stops:
            if stop["id"] == primary["id"]:
                continue
            if stop["id"].split("-")[0] == primary_feed:
                continue
            if is_wrong_nearby_stop(station_name, stop.get("name", "")):
                logger.info("Überspringe falschen Nah-Stop: %s (%s)", stop.get("name"), stop["id"])
                continue
            distance = approx_distance_km(primary["lat"], primary["lon"], stop.get("lat"), stop.get("lon"))
            if distance <= COMPLEMENTARY_STOP_MAX_KM:
                stop["_distance_km"] = distance
                stop["_relevance"] = stop_name_relevance(station_name, stop.get("name", ""))
                candidates.append(stop)
        candidates.sort(key=lambda item: (-item["_relevance"], item["_distance_km"]))
        return candidates

    @staticmethod
    def _build_stop_entry(stop):
        if stop["source"] == "openov":
            label = "Fernverkehr (OpenOV)"
        elif stop["source"] == "delfi":
            short_name = stop.get("name", "DELFI")
            if "tief" in short_name.lower():
                label = "Nahverkehr S-Bahn (Hauptbahnhof tief)"
            else:
                label = f"Nahverkehr ({short_name})"
        else:
            label = stop.get("name", stop["source"])
        return {"id": stop["id"], "source": stop["source"], "label": label}
