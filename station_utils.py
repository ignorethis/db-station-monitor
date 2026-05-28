"""Hilfsfunktionen für Stationsnamen und Geo-Vergleiche."""

import re


def normalize_station_name(name):
    """Normalisiert Stationsnamen für Vergleiche."""
    normalized = name.lower()
    normalized = normalized.replace("(main)", "").replace("(m)", "")
    normalized = normalized.replace("hauptbahnhof", "hbf")
    return re.sub(r"[^a-z0-9äöüß]", "", normalized)


def destination_city_key(name):
    """Stadt-Kern aus Stationsnamen (z. B. „Berlin“ aus „Berlin Hbf“)."""
    normalized = normalize_station_name(name)
    for suffix in ("hbf", "bahnhof", "ostbahnhof", "sudbahnhof"):
        normalized = normalized.replace(suffix, "")
    return normalized


def station_names_match(search_name, candidate_name):
    """Prüft, ob zwei Stationsnamen dieselbe Station meinen."""
    search = normalize_station_name(search_name)
    candidate = normalize_station_name(candidate_name)
    if not search or not candidate:
        return False
    return search in candidate or candidate in search


def approx_distance_km(lat1, lon1, lat2, lon2):
    """Grober Abstand in km."""
    return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5 * 111


def is_wrong_nearby_stop(search_name, candidate_name):
    """Filtert nahe, aber falsche Halte (z.B. Messe bei Hbf-Suche)."""
    search = search_name.lower()
    candidate = candidate_name.lower()
    if "messe" in search:
        return False
    if ("hbf" in search or "hauptbahnhof" in search) and "messe" in candidate:
        if "hbf" not in candidate and "hauptbahnhof" not in candidate:
            return True
    return False


def destination_matches(target_text, direction, trip_to_name=""):
    """Prüft, ob eine Abfahrt in Richtung der gewünschten Zielstation fährt."""
    if not target_text or not str(target_text).strip():
        return True

    direction = direction or ""
    trip_to_name = trip_to_name or ""

    for part in target_text.split(","):
        part = part.strip()
        if not part:
            continue
        if station_names_match(part, direction) or station_names_match(part, trip_to_name):
            return True
        part_lower = part.lower()
        if part_lower in direction.lower() or part_lower in trip_to_name.lower():
            return True
        city = destination_city_key(part)
        if city and len(city) >= 4:
            haystack = normalize_station_name(f"{direction} {trip_to_name}")
            if city in haystack:
                return True
    return False


def stop_name_relevance(search_name, candidate_name):
    """Höherer Score = besser passender Stationsname."""
    if station_names_match(search_name, candidate_name):
        return 100

    search = normalize_station_name(search_name)
    candidate = normalize_station_name(candidate_name)
    score = 0
    if "hbf" in search and "hbf" in candidate:
        score += 40
    if "hauptbahnhof" in search_name.lower() and "hauptbahnhof" in candidate_name.lower():
        score += 40
    if search in candidate or candidate in search:
        score += 20
    if "messe" in candidate_name.lower() and "hbf" in search:
        score -= 50
    return score
