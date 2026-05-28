"""Zentralisierte JSON-Verwaltung mit Fehlerbehandlung."""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def load_json_file(path: str, default: Any = None) -> Any:
    """
    Lädt eine JSON-Datei mit robuster Fehlerbehandlung.
    
    Args:
        path: Dateipfad
        default: Standardwert bei Fehler (default: None)
    
    Returns:
        Geladene Daten oder default
    """
    if default is None:
        default = {}
    
    if not os.path.exists(path):
        logger.debug("JSON-Datei nicht vorhanden: %s", path)
        return default
    
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            logger.debug("JSON erfolgreich geladen: %s (%d Zeichen)", path, len(handle.read()))
            return data
    except json.JSONDecodeError as error:
        logger.error("Ungültiges JSON in %s: %s", path, error)
        return default
    except OSError as error:
        logger.error("Fehler beim Lesen von %s: %s", path, error)
        return default
    except Exception as error:
        logger.error("Unerwarteter Fehler beim Laden von %s: %s", path, error)
        return default


def save_json_file(path: str, data: Any, create_dirs: bool = True) -> bool:
    """
    Speichert Daten als JSON mit robuster Fehlerbehandlung.
    
    Args:
        path: Dateipfad
        data: Zu speichernde Daten
        create_dirs: Verzeichnisse ggf. erstellen
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        dir_path = os.path.dirname(path)
        if create_dirs and dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        logger.info("JSON erfolgreich gespeichert: %s", path)
        return True
    except OSError as error:
        logger.error("Fehler beim Speichern von %s: %s", path, error)
        return False
    except Exception as error:
        logger.error("Unerwarteter Fehler beim Speichern von %s: %s", path, error)
        return False


def merge_json_dicts(base: dict, override: dict, keep_unknown: bool = True) -> dict:
    """
    Merged zwei JSON-Dicts intelligent.
    
    Args:
        base: Basis-Dict (Defaults)
        override: Override-Dict
        keep_unknown: Unbekannte Keys aus override behalten
    
    Returns:
        Gemergtes Dict
    """
    result = dict(base)
    
    if not isinstance(override, dict):
        return result
    
    if keep_unknown:
        result.update(override)
    else:
        result.update({key: override[key] for key in base if key in override})
    
    return result
