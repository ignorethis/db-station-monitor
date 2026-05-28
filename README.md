# DB Station Monitor - OpenOV Edition

**Live-Bahnhofanzeige für deutsche Bahnhöfe mit intelligentem Multi-Source-Fallback.**

Dieses Projekt bietet eine lokale GUI-Anwendung zur Anzeige von Abfahrten in Echtzeit. Es kombiniert mehrere Datenquellen und wählt automatisch die zuverlässigsten Quellen für jeden Bahnhof aus, um eine umfassende Übersicht über Fern- und Nahverkehr zu liefern.

## Was das Projekt macht

- Lädt aktuelle Abfahrtsdaten für deutsche Bahnhöfe
- Nutzt verknüpfte Datenquellen wie OpenOV und Transitous/MOTIS
- Zeigt Verspätungen, Ausfälle und Zeitänderungen an
- Ermöglicht Filter nach Fernverkehr, Nahverkehr und Ziel
- Speichert Suchhistorie für schnellen Zugriff
- Unterstützt Alarmfenster und Push-Benachrichtigungen via ntfy

## Installation

### Voraussetzungen
- Python 3.8 oder neuer
- Windows, macOS oder Linux

### Schritte

1. Repository klonen oder Projektordner öffnen
2. Virtuelle Umgebung erstellen:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
3. Abhängigkeiten installieren:
   pip install -r requirements.txt

## Anwendung starten

Im Projektordner ausführen:
   python station.py

Die Anwendung startet das GUI-Fenster und lädt nach dem Start automatisch die Abfahrtsdaten.

## Konfiguration

Die Anwendung liest Einstellungen aus config.json. Eine Beispielstruktur sieht so aus:

{
  "ntfy_topic": "your_topic",
  "motis_api": "https://api.transitous.org",
  "update_interval": 60000,
  "min_search_chars": 3,
  "api_timeout": 10,
  "rate_limit_delay": 1000,
  "debug": false,
  "station_ids": {
    "Frankfurt (Main) Hbf": "nl-OpenOV_stoparea:17791"
  }
}

- ntfy_topic: Topic für Push-Benachrichtigungen
- motis_api: Endpunkt für Transitous/MOTIS
- update_interval: Aktualisierungsintervall in Millisekunden
- min_search_chars: Minimale Zeichenanzahl für Autovervollständigung
- api_timeout: Timeout in Sekunden für API-Anfragen
- rate_limit_delay: Verzögerung zwischen API-Aufrufen in Millisekunden
- debug: Debug-Modus ein-/ausschalten
- station_ids: Optionaler Cache für Station-IDs

## Wichtigste Projektdateien

- station.py – Hauptstartdatei
- bahn_gui.py – Benutzeroberfläche
- motis_client.py – API-Client
- station_resolver.py – Bahnhofssuche und ID-Auflösung
- departures.py – Verarbeitung von Abfahrtsdaten
- input_sanitizer.py – Eingabevalidierung
- settings.py – Konfigurationsverwaltung
- station_history.py – Suchhistorie
- json_utils.py, datetime_utils.py, station_utils.py, constants.py

## Testen

Die Tests lassen sich mit pytest starten:
   pytest

## Abhängigkeiten

Aktive externe Laufzeitpakete:
- customtkinter
- requests

Test-/Entwicklungsabhängigkeiten:
- pytest
- pytest-cov
- tzdata

## Lizenz-Check der Abhängigkeiten

Die direkt im Projekt genutzten externen Pakete sind frei verwendbar und haben keine restriktive Lizenz:
- customtkinter (MIT)
- requests (Apache 2.0)
- pytest (MIT)
- pytest-cov (MIT)
- tzdata (PSF-kompatibel / permissiv)
