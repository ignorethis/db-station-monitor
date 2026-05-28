"""Persistenz für Stations-Historie."""

import logging
import os

from constants import (
    DESTINATION_HISTORY_FILE,
    HISTORY_FILE,
    LAST_DESTINATION_FILE,
    LAST_STATION_FILE,
)
from settings import Settings

logger = logging.getLogger(__name__)


class StationHistory:
    """Verwaltet zuletzt genutzte Stationen."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def load_combo_values(self):
        configured = list(self.settings.station_ids.keys())
        history = self._read_lines(HISTORY_FILE)
        values = list(dict.fromkeys(configured + history))
        return values if values else ["Frankfurt (Main) Hbf"]

    def load_last(self):
        return self._read_single_line(LAST_STATION_FILE)

    def save_last(self, station_name):
        self._write_single_line(LAST_STATION_FILE, station_name)

    def add(self, station_name):
        try:
            history = set(self._read_lines(HISTORY_FILE))
            history.add(station_name)
            with open(HISTORY_FILE, "w", encoding="utf-8") as handle:
                for entry in sorted(history):
                    handle.write(entry + "\n")
        except OSError as error:
            logger.error("Fehler beim Speichern in History: %s", error)

    def load_destination_values(self):
        history = self._read_lines(DESTINATION_HISTORY_FILE)
        return history if history else []

    def load_last_destination(self):
        return self._read_single_line(LAST_DESTINATION_FILE)

    def save_last_destination(self, destination_name):
        self._write_single_line(LAST_DESTINATION_FILE, destination_name)

    def add_destination(self, destination_name):
        if not destination_name.strip():
            return
        try:
            history = set(self._read_lines(DESTINATION_HISTORY_FILE))
            history.add(destination_name.strip())
            with open(DESTINATION_HISTORY_FILE, "w", encoding="utf-8") as handle:
                for entry in sorted(history):
                    handle.write(entry + "\n")
        except OSError as error:
            logger.error("Fehler beim Speichern der Ziel-Historie: %s", error)

    @staticmethod
    def _read_lines(path):
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return [line.strip() for line in handle if line.strip()]
        except OSError as error:
            logger.warning("Fehler beim Lesen der Historie: %s", error)
            return []

    @staticmethod
    def _read_single_line(path):
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                value = handle.read().strip()
                return value or None
        except OSError as error:
            logger.warning("Fehler beim Lesen von %s: %s", path, error)
        return None

    @staticmethod
    def _write_single_line(path, value):
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(value)
        except OSError as error:
            logger.error("Fehler beim Speichern von %s: %s", path, error)
