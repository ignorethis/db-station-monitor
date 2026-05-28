"""Anwendungskonstanten für DB Pi-Monitor Pro."""

CONFIG_FILE = "config.json"
STATIONS_REGISTRY_FILE = "stations_registry.json"
HISTORY_FILE = "station_history.txt"
LAST_STATION_FILE = "last_station.txt"
DESTINATION_HISTORY_FILE = "destination_history.txt"
LAST_DESTINATION_FILE = "last_destination.txt"

COMPLEMENTARY_STOP_MAX_KM = 1.5
DEPARTURE_GRACE_MINUTES = 2
STOPTIMES_DEFAULT = 50
STOPTIMES_WITH_DESTINATION = 150

WINDOW_WIDTH_RATIO = 0.85
WINDOW_MIN_WIDTH = 1024
WINDOW_MAX_WIDTH = 1600
WINDOW_ASPECT_RATIO = 16 / 9

# (Spalten-ID, Überschrift, Breite in px; 0 = Restbreite)
DEPARTURE_TABLE_COLUMNS = (
    ("zeit", "Zeit", 72),
    ("in_min", "In", 56),
    ("linie", "Linie", 108),
    ("typ", "Typ", 160),
    ("status", "Status", 200),
    ("ziel", "Ziel", 0),
)

MODE_NAMES = {
    "HIGHSPEED_RAIL": "ICE/Hochgeschwindigkeit",
    "LONG_DISTANCE": "Fernverkehr",
    "NIGHT_RAIL": "Nachtverkehr",
    "REGIONAL_RAIL": "Regionalverkehr",
    "REGIONAL_FAST_RAIL": "Regional-Express",
    "SUBURBAN": "S-Bahn",
    "SUBWAY": "U-Bahn",
    "TRAM": "Straßenbahn",
    "BUS": "Bus",
    "COACH": "Fernbus",
}

FERNVERKEHR_MODES = {"HIGHSPEED_RAIL", "LONG_DISTANCE", "NIGHT_RAIL"}
NAHVERKEHR_MODES = {"SUBURBAN", "REGIONAL_RAIL", "REGIONAL_FAST_RAIL", "TRAM", "SUBWAY", "BUS"}

DEFAULT_CONFIG = {
    "ntfy_topic": "mein_pi_bahn_alarm_123",
    "transitous_api": "https://api.transitous.org",
    "motis_api": "https://api.transitous.org",
    "update_interval": 60000,
    "min_search_chars": 3,
    "api_timeout": 10,
    "rate_limit_delay": 1000,
    "debug": False,
    "station_ids": {},
    "station_variants": {},
}

USER_AGENT = "Station-Monitor/1.0"
