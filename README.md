# 🚂 DB Station Monitor - OpenOV Edition

***DISCLAIMER: Initial Version was written by hand and then juiced by AI***

**Real-time train departure monitoring for German railways with multi-source data integration, intelligent filtering, and instant notifications.**

A feature-rich GUI application for monitoring train departures from German railway stations in real-time. Combines data from multiple transportation APIs (OpenOV, DELFI, Transitous) to provide comprehensive coverage and automatically detects the most reliable data source for any station.

---

## 🌟 Features

### Core Functionality
- **Multi-Source Integration**: Automatically combines data from OpenOV (long-distance trains) and DELFI (regional transport) with intelligent source detection
- **Real-Time Monitoring**: Live departure board with automatic updates, delay tracking, and cancellation alerts
- **Smart Station Resolver**: Registry-based caching with intelligent fallback mechanisms to minimize API calls
- **Flexible Filtering**: Filter departures by transport type (long-distance, regional, all), destination, and time windows

### Alarm System
- **Time-Based Alarms**: Define active hours for notifications (e.g., only 7 AM - 10 PM)
- **Destination Monitoring**: Automatic alerts when trains to specific destinations appear
- **Delay Tracking**: Get notified about delays exceeding configurable thresholds
- **Push Notifications**: Integration with ntfy.sh for cross-device notifications

### User Experience
- **Dark Mode UI**: Modern customtkinter-based interface with responsive design
- **Search Suggestions**: Real-time geocoding with autocomplete suggestions
- **Station History**: Remembers recent searches and destinations for quick access
- **Status Indicators**: Visual indicators for on-time, delayed, and cancelled trains
- **Responsive Layout**: Automatically scales to different screen sizes

### Data Integrity & Security
- **Input Sanitization**: Comprehensive validation for all user inputs (station names, destinations, time formats)
- **XSS & Injection Prevention**: Protection against malicious input patterns
- **Configuration Validation**: JSON schema validation for config files
- **Robust Error Handling**: Graceful fallbacks for API failures and invalid data

---

## 🚀 Quick Start

### Requirements
- Python 3.8+
- Windows, macOS, or Linux

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ignorethis/db-station-monitor.git
cd db-station-monitor
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python station.py
```

---

## ⚙️ Configuration

### config.json Structure

Create a `config.json` file in the project directory:

```json
{
  "ntfy_topic": "your_unique_topic_id",
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
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ntfy_topic` | string | - | Unique identifier for ntfy.sh notifications |
| `motis_api` | string | `https://api.transitous.org` | MOTIS/Transitous API endpoint |
| `update_interval` | integer | `60000` | Milliseconds between refresh attempts |
| `min_search_chars` | integer | `3` | Minimum characters before autocomplete |
| `api_timeout` | integer | `10` | API request timeout in seconds |
| `rate_limit_delay` | integer | `1000` | Milliseconds between API calls |
| `debug` | boolean | `false` | Enable verbose logging |
| `station_ids` | object | `{}` | Cached station IDs for faster lookup |

### Station Configuration (Advanced)

For stations with multiple stops (long-distance vs. regional), use `station_variants`:

```json
{
  "station_variants": {
    "Frankfurt (Main) Hbf": {
      "primary": "nl-OpenOV_stoparea:17791",
      "additional": "de-DELFI_de:06412:7010",
      "note": "Combines long-distance (OpenOV) + regional (DELFI)"
    }
  }
}
```

---

## 🔧 Usage

### Basic Workflow

1. **Select Station**: Type a station name in the "Bahnhof" field
   - Auto-suggestions appear after 3 characters
   - Recently searched stations appear first
   - Click "Update" or press Enter to load departures

2. **Filter Results**: 
   - **Fernverkehr Only**: Shows only long-distance trains
   - **Nahverkehr Only**: Shows only regional trains
   - **Ziel**: Filter to show only trains going to a specific destination

3. **Set Alarms**:
   - Check "Aktivieren" to enable the alarm window
   - Set start and end times (format: HH:MM)
   - Alarms only trigger during this window

4. **Monitor Departures**:
   - Green ✅ = On-time
   - Orange ⚠️ = Delayed (< 15 min)
   - Red ⚠️ = Delayed (≥ 15 min)
   - Red ⛔ = Cancelled

### API Response

The application works with the Transitous/MOTIS API structure:

**Example Departure Data:**
```json
{
  "routeShortName": "ICE 100",
  "headsign": "München Hbf",
  "scheduledDeparture": "2024-05-26T12:30:00+02:00",
  "realtimeDeparture": "2024-05-26T12:45:00+02:00",
  "cancelled": false
}
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest test_input_sanitization.py -v

# With coverage report
pytest test_input_sanitization.py --cov=input_sanitizer --cov-report=html

# Quick test run
pytest test_input_sanitization.py -q
```

### Test Coverage

- ✅ 40+ unit tests for input sanitization
- ✅ XSS and SQL injection prevention tests
- ✅ Configuration validation tests
- ✅ Edge cases and Unicode handling
- ✅ Type conversion and error handling

---

## 🔐 Security Features

### Input Validation
- **Station Names**: Max 200 characters, alphanumeric + basic punctuation
- **Stop IDs**: Format validation (alphanumeric + `:-._`)
- **Time Fields**: HH:MM format with hour (00-23) and minute (00-59) validation
- **URL Parameters**: Malicious character filtering before API calls

### Injection Prevention
- HTML escaping for display fields
- Whitelist validation for transport modes
- JSON schema validation for configuration
- URL encoding for API parameters

### Configuration Security
- Type validation for all config fields
- Required field checking
- Graceful fallback to defaults on validation failure
- Secrets not stored in version control (.gitignore rules)

---

## 📁 Project Structure

```
db-station-monitor/
├── bahn_gui.py                # Main GUI application
├── station.py                 # Entry point
├── motis_client.py           # MOTIS/Transitous API client
├── station_resolver.py       # Station lookup & verification
├── departures.py             # Departure parsing & filtering
├── input_sanitizer.py        # Input validation module
├── json_utils.py             # JSON handling utilities
├── settings.py               # Configuration management
├── station_history.py        # Search history persistence
├── station_utils.py          # Station utility functions
├── datetime_utils.py         # Time/date utilities
├── constants.py              # Application constants
├── test_input_sanitization.py # Unit tests
├── config.json              # User configuration (create this)
├── stations_registry.json   # Cached station data
├── requirements.txt         # Python dependencies
├── .gitignore              # Git exclusion rules
└── README.md               # This file
```

---

## 🐛 Troubleshooting

### Station Not Found
- Check spelling carefully
- Try alternative station names (e.g., "Frankfurt a.M." vs "Frankfurt (Main)")
- Ensure API is reachable: `curl https://api.transitous.org/api/v1/geocode?text=Berlin`

### No Departures Shown
- Station may have no departures in the next hour
- Check if time window falls within available data
- Try a different transport type filter

### Notifications Not Working
- Verify `ntfy_topic` is correctly set in config.json
- Test manually: `curl -d "test" ntfy.sh/your_topic_id`
- Check if push notifications are enabled on your device

### API Timeout Errors
- Increase `api_timeout` in config.json (default: 10 seconds)
- Check internet connection
- Verify API endpoint is reachable

### High CPU Usage
- Reduce `update_interval` in config.json (currently 60 seconds)
- Check for stuck API requests in logs

---

## 📝 Logging

Application logs are written to `bahn_monitor.log`. Enable debug mode in config.json for verbose output:

```json
{
  "debug": true
}
```

Common log locations:
- **Windows**: `%APPDATA%/db-station-monitor/logs/`
- **macOS**: `~/Library/Logs/db-station-monitor/`
- **Linux**: `~/.local/share/db-station-monitor/logs/`

---

### Development Setup

```bash
# Clone and setup
git clone <your-fork>
cd db-station-monitor
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run tests before committing
pytest test_input_sanitization.py -v

# Format code (optional but recommended)
python -m black *.py
```

---

## 📜 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- **Transitous/MOTIS**: Open public transport routing API
- **OpenOV**: European open travel data
- **DELFI**: German public transport data
- **customtkinter**: Modern Python GUI framework
- **ntfy.sh**: Simple push notifications

---

## 🗺️ Roadmap

- [ ] Web interface (Flask/FastAPI)
- [ ] Mobile app (Kivy)
- [ ] Multiple alarm profiles
- [ ] Journey planning integration
- [ ] Database backend for history
- [ ] Multi-language support
- [ ] Dark/Light theme toggle
- [ ] Custom sound notifications

---

**Made with ❤️ for German railway enthusiasts and commuters**
