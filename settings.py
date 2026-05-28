"""Konfiguration und Stations-Registry."""

import logging
import os

from constants import CONFIG_FILE, DEFAULT_CONFIG, STATIONS_REGISTRY_FILE
from input_sanitizer import validate_config_structure, SanitizationError
from json_utils import load_json_file, save_json_file, merge_json_dicts

logger = logging.getLogger(__name__)


def migrate_variants_to_registry(registry, variants, station_ids):
    """Übernimmt station_variants aus config.json in die Registry."""
    for station_name, variant in variants.items():
        if station_name in registry:
            continue

        stop_ids = []
        primary = variant.get("primary")
        additional = variant.get("additional")
        if primary:
            stop_ids.append({"id": primary, "source": "openov", "label": "Fernverkehr (OpenOV)"})
        if additional:
            stop_ids.append({"id": additional, "source": "delfi", "label": "Nahverkehr (DELFI)"})
        if not stop_ids and station_name in station_ids:
            stop_ids.append({"id": station_ids[station_name], "source": "unknown", "label": "Legacy"})

        if stop_ids:
            registry[station_name] = {
                "verified": True,
                "display_name": station_name,
                "stop_ids": stop_ids,
            }
    return registry


class Settings:
    """Zentrale Anwendungseinstellungen und persistierte Station-Daten."""

    def __init__(self):
        self.config = self._load_config()
        self._stations_registry = load_json_file(STATIONS_REGISTRY_FILE, {})
        if not isinstance(self._stations_registry, dict):
            self._stations_registry = {}

        migrated = migrate_variants_to_registry(
            dict(self._stations_registry),
            self.config.get("station_variants", {}),
            self.config.get("station_ids", {}),
        )
        if migrated != self._stations_registry:
            self._stations_registry = migrated
            self.save_registry()

    def _load_config(self):
        config = dict(DEFAULT_CONFIG)
        if not os.path.exists(CONFIG_FILE):
            logger.warning("Konfigurationsdatei %s nicht gefunden. Verwende Standardwerte.", CONFIG_FILE)
            return config

        loaded = load_json_file(CONFIG_FILE, {})
        if not isinstance(loaded, dict):
            return config

        config.update({key: loaded[key] for key in DEFAULT_CONFIG if key in loaded})
        config.update({key: loaded[key] for key in loaded if key not in config})
        
        try:
            validate_config_structure(config)
            logger.info("Konfiguration erfolgreich geladen und validiert.")
        except SanitizationError as error:
            logger.warning("Konfiguration validierung fehlgeschlagen: %s. Verwende Defaults.", error)
            config = dict(DEFAULT_CONFIG)
        
        return config

    @property
    def ntfy_topic(self):
        return self.config["ntfy_topic"]

    @property
    def motis_api(self):
        return self.config.get("motis_api", self.config["transitous_api"])

    @property
    def update_interval(self):
        return self.config["update_interval"]

    @property
    def min_search_chars(self):
        return self.config["min_search_chars"]

    @property
    def api_timeout(self):
        return self.config["api_timeout"]

    @property
    def rate_limit_delay(self):
        return self.config["rate_limit_delay"]

    @property
    def station_ids(self):
        return self.config.setdefault("station_ids", {})

    @property
    def stations_registry(self):
        return self._stations_registry

    @stations_registry.setter
    def stations_registry(self, value):
        self._stations_registry = value if isinstance(value, dict) else {}

    def save_config(self):
        if save_json_file(CONFIG_FILE, self.config):
            logger.info("Konfiguration erfolgreich gespeichert.")

    def save_registry(self):
        if save_json_file(STATIONS_REGISTRY_FILE, self.stations_registry):
            logger.info("Stations-Registry gespeichert.")

    def get_registry_stops(self, station_name):
        entry = self.stations_registry.get(station_name, {})
        if entry.get("verified"):
            return entry.get("stop_ids", [])
        return []

    def set_registry_stops(self, station_name, stop_entries):
        self.stations_registry[station_name] = {
            "verified": True,
            "display_name": station_name,
            "stop_ids": stop_entries,
        }
        self.save_registry()

        primary_id = stop_entries[0]["id"] if stop_entries else None
        if primary_id and self.station_ids.get(station_name) != primary_id:
            self.station_ids[station_name] = primary_id
            self.save_config()


settings = Settings()
