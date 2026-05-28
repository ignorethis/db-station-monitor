"""Input-Validierung und Sanitization für sicheren Datenzugang."""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Grenzen für Eingaben
MAX_STATION_NAME_LENGTH = 200
MAX_STOP_ID_LENGTH = 100
MAX_DESTINATION_LENGTH = 200
MIN_SEARCH_CHARS = 1

# Erlaubte Stop-ID Patterns
STOP_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_:\-\.]+$")
TIME_PATTERN = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")


class SanitizationError(ValueError):
    """Fehler bei Sanitization."""
    pass


def sanitize_station_name(value: Any) -> str:
    """
    Sanitiert Stationsnamen.
    
    - Konvertiert zu String
    - Striped Whitespace
    - Prüft Längenlimit
    - Prüft auf ungültige Zeichen
    
    Args:
        value: Eingabewert (any type)
    
    Returns:
        Sanitierter Stationsname
    
    Raises:
        SanitizationError: Bei ungültiger Eingabe
    """
    if not value:
        raise SanitizationError("Stationsname darf nicht leer sein")
    
    try:
        text = str(value).strip()
    except Exception as error:
        raise SanitizationError(f"Stationsname konnte nicht konvertiert werden: {error}")
    
    if not text:
        raise SanitizationError("Stationsname darf nicht leer sein")
    
    if len(text) > MAX_STATION_NAME_LENGTH:
        raise SanitizationError(
            f"Stationsname zu lang (max {MAX_STATION_NAME_LENGTH} Zeichen)"
        )
    
    if len(text) < MIN_SEARCH_CHARS:
        raise SanitizationError(
            f"Stationsname zu kurz (min {MIN_SEARCH_CHARS} Zeichen)"
        )
    
    if re.search(r'[<>"\'{};\\]', text):
        raise SanitizationError("Stationsname enthält ungültige Zeichen")
    
    return text


def sanitize_destination_name(value: Any) -> str:
    """
    Sanitiert Destinationsnamen.
    
    - Ähnlich wie sanitize_station_name aber erlaubt leer
    - Wird verwendet für optionales Filterfeld
    
    Args:
        value: Eingabewert (any type)
    
    Returns:
        Sanitierter Destinationsname (kann leer sein)
    
    Raises:
        SanitizationError: Bei ungültiger Eingabe
    """
    if not value:
        return ""
    
    try:
        text = str(value).strip()
    except Exception as error:
        raise SanitizationError(f"Destination konnte nicht konvertiert werden: {error}")
    
    if not text:
        return ""
    
    if len(text) > MAX_DESTINATION_LENGTH:
        raise SanitizationError(
            f"Destination zu lang (max {MAX_DESTINATION_LENGTH} Zeichen)"
        )
    
    if re.search(r'[<>"\'{};\\]', text):
        raise SanitizationError("Destination enthält ungültige Zeichen")
    
    return text


def sanitize_stop_id(value: Any) -> str:
    """
    Sanitiert Stop-IDs (z.B. 'nl-OpenOV_stoparea:17791').
    
    - Konvertiert zu String
    - Prüft Format (alphanumerisch + Sonderzeichen)
    - Prüft Längenlimit
    
    Args:
        value: Eingabewert (any type)
    
    Returns:
        Sanitierte Stop-ID
    
    Raises:
        SanitizationError: Bei ungültiger Eingabe
    """
    if not value:
        raise SanitizationError("Stop-ID darf nicht leer sein")
    
    try:
        stop_id = str(value).strip()
    except Exception as error:
        raise SanitizationError(f"Stop-ID konnte nicht konvertiert werden: {error}")
    
    if not stop_id:
        raise SanitizationError("Stop-ID darf nicht leer sein")
    
    if len(stop_id) > MAX_STOP_ID_LENGTH:
        raise SanitizationError(f"Stop-ID zu lang (max {MAX_STOP_ID_LENGTH} Zeichen)")
    
    if not STOP_ID_PATTERN.match(stop_id):
        raise SanitizationError("Stop-ID hat ungültiges Format")
    
    return stop_id


def sanitize_time_string(value: Any) -> str:
    """
    Sanitiert Zeit-Strings im Format HH:MM.
    
    - Konvertiert zu String
    - Validiert Format (HH:MM)
    - Prüft auf gültige Stunden und Minuten
    
    Args:
        value: Eingabewert (any type)
    
    Returns:
        Sanitierte Zeit-String
    
    Raises:
        SanitizationError: Bei ungültiger Eingabe
    """
    if not value:
        raise SanitizationError("Zeit darf nicht leer sein")
    
    try:
        time_str = str(value).strip()
    except Exception as error:
        raise SanitizationError(f"Zeit konnte nicht konvertiert werden: {error}")
    
    if not TIME_PATTERN.match(time_str):
        raise SanitizationError("Zeit muss im Format HH:MM sein (z.B. 07:00)")
    
    return time_str


def sanitize_integer(value: Any, min_value: int = 1, max_value: int = 1000) -> int:
    """
    Sanitiert Integer-Eingaben mit Bereichsprüfung.
    
    Args:
        value: Eingabewert (any type)
        min_value: Minimaler Wert (inklusive)
        max_value: Maximaler Wert (inklusive)
    
    Returns:
        Sanitierte Integer
    
    Raises:
        SanitizationError: Bei ungültiger Eingabe
    """
    if isinstance(value, float):
        raise SanitizationError("Floats sind nicht erlaubt, nur Integer")
    
    try:
        num = int(value)
    except (ValueError, TypeError) as error:
        raise SanitizationError(f"Wert ist keine ganze Zahl: {error}")
    
    if num < min_value or num > max_value:
        raise SanitizationError(
            f"Wert muss zwischen {min_value} und {max_value} liegen"
        )
    
    return num


def sanitize_url_parameter(value: Any) -> str:
    """
    Sanitiert URL-Parameter.
    
    - Konvertiert zu String
    - Entfernt gefährliche Zeichen
    - Prüft Längenlimit
    
    Args:
        value: Eingabewert (any type)
    
    Returns:
        Sanitierter URL-Parameter
    
    Raises:
        SanitizationError: Bei ungültiger Eingabe
    """
    if not value:
        raise SanitizationError("URL-Parameter darf nicht leer sein")
    
    try:
        param = str(value).strip()
    except Exception as error:
        raise SanitizationError(f"Parameter konnte nicht konvertiert werden: {error}")
    
    if not param:
        raise SanitizationError("URL-Parameter darf nicht leer sein")
    
    if len(param) > MAX_STOP_ID_LENGTH:
        raise SanitizationError("Parameter zu lang")
    
    if re.search(r'[<>"\'{};\\`\n\r]', param):
        raise SanitizationError("Parameter enthält ungültige Zeichen")
    
    return param


def validate_config_structure(config: Any) -> bool:
    """
    Validiert config.json Struktur.
    
    Prüft auf erforderliche Felder und Datentypen.
    
    Args:
        config: Zu validierende Konfiguration
    
    Returns:
        True wenn valide
    
    Raises:
        SanitizationError: Bei ungültiger Struktur
    """
    if not isinstance(config, dict):
        raise SanitizationError("Config muss ein Dict sein")
    
    required_fields = ["ntfy_topic", "motis_api", "update_interval", "api_timeout"]
    
    for field in required_fields:
        if field not in config:
            raise SanitizationError(f"Erforderliches Feld fehlend: {field}")
    
    if not isinstance(config.get("ntfy_topic"), str):
        raise SanitizationError("ntfy_topic muss ein String sein")
    
    if not isinstance(config.get("motis_api"), str):
        raise SanitizationError("motis_api muss ein String sein")
    
    if not isinstance(config.get("update_interval"), int):
        raise SanitizationError("update_interval muss eine Integer sein")
    
    if not isinstance(config.get("api_timeout"), int):
        raise SanitizationError("api_timeout muss eine Integer sein")
    
    return True


def validate_stop_entry(entry: Any) -> bool:
    """
    Validiert einen Stop-Eintrag aus stations_registry.
    
    Args:
        entry: Stop-Eintrag
    
    Returns:
        True wenn valide
    
    Raises:
        SanitizationError: Bei ungültiger Struktur
    """
    if not isinstance(entry, dict):
        raise SanitizationError("Stop-Eintrag muss ein Dict sein")
    
    required_fields = ["id", "source"]
    for field in required_fields:
        if field not in entry:
            raise SanitizationError(f"Stop-Eintrag fehlend: {field}")
    
    try:
        sanitize_stop_id(entry["id"])
    except SanitizationError as error:
        raise SanitizationError(f"Ungültige Stop-ID: {error}")
    
    source = entry.get("source", "")
    if source and source not in ["openov", "delfi", "unknown", "other"]:
        raise SanitizationError(f"Ungültige Stop-Quelle: {source}")
    
    return True
