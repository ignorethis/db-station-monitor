"""GUI für DB Pi-Monitor Pro."""

import logging
from datetime import datetime, time

import customtkinter as ctk
import requests
from tkinter import ttk

from constants import (
    DEPARTURE_TABLE_COLUMNS,
    STOPTIMES_DEFAULT,
    STOPTIMES_WITH_DESTINATION,
    WINDOW_ASPECT_RATIO,
    WINDOW_MAX_WIDTH,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH_RATIO,
)
from datetime_utils import minutes_until_departure
from departures import (
    DepartureService,
    build_departure_filter,
    get_status_text,
    trip_notification_key,
)
from input_sanitizer import (
    sanitize_station_name,
    sanitize_destination_name,
    sanitize_time_string,
    SanitizationError,
)
from motis_client import MotisClient
from settings import Settings, settings
from station_history import StationHistory
from station_resolver import StationResolver

logger = logging.getLogger(__name__)


class BahnGui(ctk.CTk):
    """Haupt-GUI für DB Pi-Monitor Pro."""

    def __init__(self, app_settings: Settings | None = None):
        super().__init__()
        self.app_settings = app_settings or settings
        self.motis = MotisClient(self.app_settings)
        self.resolver = StationResolver(self.app_settings, self.motis)
        self.departures = DepartureService(self.motis)
        self.history = StationHistory(self.app_settings)

        self.current_station_id = None
        self.last_request_time = 0
        self.autocomplete_timer = None
        self.destination_autocomplete_timer = None
        self.last_notified_trip = None
        self._current_next_trip_key = None

        self.title("🚂 DB Pi-Monitor Pro - OpenOV Edition")
        self._setup_window()
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_controls()
        self._build_departure_board()
        self._build_status_bar()

    def _setup_window(self):
        screen_width = self.winfo_screenwidth()
        target_width = min(
            max(int(screen_width * WINDOW_WIDTH_RATIO), WINDOW_MIN_WIDTH),
            WINDOW_MAX_WIDTH,
        )
        target_height = int(target_width * WINDOW_ASPECT_RATIO)
        self.geometry(f"{target_width}x{target_height}")

        self.font_small = max(9, int(target_width / 120))
        self.font_normal = max(10, int(target_width / 100))
        self.font_large = max(12, int(target_width / 85))
        self.font_title = max(14, int(target_width / 70))

    def _build_controls(self):
        self._build_station_selector()
        self._build_alarm_settings()
        self._build_filter_settings()

    def _build_station_selector(self):
        frame = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        frame.grid(row=0, column=0, pady=10, padx=12, sticky="ew")
        frame.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(frame, text="🚂 Bahnhof:", font=("Arial", self.font_large, "bold")).grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")
        self.station_combo = ctk.CTkComboBox(frame, values=self.history.load_combo_values(), font=("Arial", self.font_normal), height=35)
        self.station_combo.grid(row=0, column=2, padx=10, pady=(8, 4), sticky="ew")
        last_station = self.history.load_last()
        if last_station:
            self.station_combo.set(last_station)
        self.station_combo._entry.bind("<KeyRelease>", self.on_station_input)
        ctk.CTkButton(frame, text="🔄 Update", command=self.update_list, font=("Arial", self.font_normal), width=100, height=35).grid(row=0, column=3, padx=10, pady=(8, 4))
        ctk.CTkLabel(frame, text="🎯 Ziel:", font=("Arial", self.font_large, "bold")).grid(row=1, column=0, padx=10, pady=(4, 8), sticky="w")
        self.destination_combo = ctk.CTkComboBox(frame, values=self.history.load_destination_values(), font=("Arial", self.font_normal), height=35)
        self.destination_combo.grid(row=1, column=2, padx=10, pady=(4, 8), sticky="ew")
        self.destination_combo.set("")
        last_destination = self.history.load_last_destination()
        if last_destination:
            self.destination_combo.set(last_destination)
        self.destination_combo._entry.bind("<KeyRelease>", self.on_destination_input)
        ctk.CTkLabel(frame, text="leer = alle Richtungen", font=("Arial", self.font_small), text_color="gray").grid(row=1, column=3, padx=10, pady=(4, 8), sticky="w")

    def _build_alarm_settings(self):
        frame = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        frame.grid(row=1, column=0, pady=8, padx=12, sticky="ew")
        frame.grid_columnconfigure(5, weight=1)
        ctk.CTkLabel(frame, text="⏰ Alarm-Fenster:", font=("Arial", self.font_large, "bold")).grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.alarm_active = ctk.CTkCheckBox(frame, text="Aktivieren", font=("Arial", self.font_normal))
        self.alarm_active.grid(row=0, column=1, padx=10, pady=6)
        self.start_time = ctk.CTkEntry(frame, placeholder_text="07:00", width=70, height=32)
        self.start_time.grid(row=0, column=2, padx=5, pady=6)
        self.start_time.insert(0, "07:00")
        ctk.CTkLabel(frame, text="bis", font=("Arial", self.font_normal)).grid(row=0, column=3, padx=5)
        self.end_time = ctk.CTkEntry(frame, placeholder_text="09:00", width=70, height=32)
        self.end_time.grid(row=0, column=4, padx=5, pady=6)
        self.end_time.insert(0, "09:00")
        self.workdays_only = ctk.CTkCheckBox(frame, text="Nur Mo-Fr", font=("Arial", self.font_normal))
        self.workdays_only.grid(row=0, column=5, padx=10, pady=6, sticky="e")
        self.workdays_only.select()

    def _build_filter_settings(self):
        frame = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        frame.grid(row=2, column=0, pady=8, padx=12, sticky="ew")
        frame.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(frame, text="🔍 Filter:", font=("Arial", self.font_large, "bold")).grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.filter_lines = ctk.CTkEntry(frame, placeholder_text="z.B. ICE,IC,RE (leer=alle)", height=32)
        self.filter_lines.grid(row=0, column=2, padx=10, pady=6, sticky="ew")
        self.fernverkehr_only = ctk.CTkCheckBox(frame, text="Fernverkehr", command=self.on_fernverkehr_changed)
        self.fernverkehr_only.grid(row=0, column=3, padx=10, pady=6)
        self.nahverkehr_only = ctk.CTkCheckBox(frame, text="Nahverkehr", command=self.on_nahverkehr_changed)
        self.nahverkehr_only.grid(row=0, column=4, padx=10, pady=6)

    def _build_departure_board(self):
        container = ctk.CTkFrame(self)
        container.grid(row=3, column=0, pady=10, padx=12, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        self.next_train_banner = ctk.CTkFrame(container, fg_color=("gray85", "gray20"), corner_radius=5, height=50)
        self.next_train_banner.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.next_train_banner.grid_propagate(False)
        self.next_train_banner.grid_columnconfigure(0, weight=1)
        self.next_train_label = ctk.CTkLabel(self.next_train_banner, text="🚂 Deine nächste Bahn wird nach dem Update angezeigt", font=("Arial", self.font_large, "bold"), text_color=("gray30", "gray70"), anchor="w")
        self.next_train_label.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        table_frame = ctk.CTkFrame(container, fg_color=("white", "gray10"), corner_radius=5)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        self._configure_departures_tree_style()
        column_ids = [col_id for col_id, _, _ in DEPARTURE_TABLE_COLUMNS]
        self.departures_tree = ttk.Treeview(table_frame, columns=column_ids, show="headings", selectmode="none", style="Departures.Treeview")
        self._configure_departures_tree_tags()
        for col_id, heading, width in DEPARTURE_TABLE_COLUMNS:
            self.departures_tree.heading(col_id, text=heading, anchor="w")
            if width > 0:
                self.departures_tree.column(col_id, width=width, minwidth=width, stretch=False, anchor="w")
            else:
                self.departures_tree.column(col_id, width=240, minwidth=120, stretch=True, anchor="w")
        scrollbar = ctk.CTkScrollbar(table_frame, command=self.departures_tree.yview)
        self.departures_tree.configure(yscrollcommand=scrollbar.set)
        self.departures_tree.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=4)

    def _configure_departures_tree_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        row_height = max(28, self.font_normal + 18)
        style.configure("Departures.Treeview", background="#1a1a1a", foreground="#e0e0e0", fieldbackground="#1a1a1a", borderwidth=0, relief="flat", rowheight=row_height, font=("Arial", self.font_normal))
        style.configure("Departures.Treeview.Heading", background="#333333", foreground="#ffffff", relief="flat", font=("Arial", self.font_normal, "bold"))
        style.map("Departures.Treeview", background=[("selected", "#1a1a1a")], foreground=[("selected", "#e0e0e0")])

    def _configure_departures_tree_tags(self):
        self.departures_tree.tag_configure("next", background="#1a3a52")
        self.departures_tree.tag_configure("ok", foreground="#00DD00")
        self.departures_tree.tag_configure("delay", foreground="#FFAA00")
        self.departures_tree.tag_configure("late", foreground="#FF4444")
        self.departures_tree.tag_configure("cancelled", foreground="#FF0000")

    def _build_status_bar(self):
        frame = ctk.CTkFrame(self, fg_color=("gray90", "gray15"), height=40)
        frame.grid(row=4, column=0, sticky="ew", padx=12, pady=8)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_propagate(False)
        self.status_label = ctk.CTkLabel(frame, text="⏸️ Bereit", font=("Arial", self.font_normal), text_color="gray")
        self.status_label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

    def on_station_input(self, event=None):
        if self.autocomplete_timer:
            self.after_cancel(self.autocomplete_timer)
        self.autocomplete_timer = self.after(500, self._fetch_geocode_suggestions)

    def on_destination_input(self, event=None):
        if self.destination_autocomplete_timer:
            self.after_cancel(self.destination_autocomplete_timer)
        self.destination_autocomplete_timer = self.after(500, self._fetch_destination_suggestions)

    def _fetch_geocode_suggestions(self):
        text = self.station_combo.get().strip()
        if not self._can_query_geocode(text):
            return
        try:
            sanitize_station_name(text)
            suggestions = self.motis.geocode(text)
            if not suggestions:
                return
            station_names = [item.get("name", "") for item in suggestions]
            configured = [name for name in self.app_settings.station_ids if text.lower() in name.lower()]
            self.station_combo.configure(values=list(dict.fromkeys(configured + station_names)))
        except SanitizationError as error:
            logger.warning("Ungültige Station-Eingabe: %s", error)
        except Exception as error:
            logger.error("API-Fehler bei Stationssuche: %s", error)

    def _fetch_destination_suggestions(self):
        text = self.destination_combo.get().strip()
        if not self._can_query_geocode(text):
            return
        try:
            sanitize_destination_name(text)
            suggestions = self.motis.geocode(text)
            if not suggestions:
                return
            names = [item.get("name", "") for item in suggestions if item.get("name")]
            history_matches = [name for name in self.history.load_destination_values() if text.lower() in name.lower()]
            self.destination_combo.configure(values=list(dict.fromkeys(history_matches + names)))
        except SanitizationError as error:
            logger.warning("Ungültige Ziel-Eingabe: %s", error)
        except Exception as error:
            logger.error("API-Fehler bei Zielsuche: %s", error)

    def _can_query_geocode(self, text):
        now = datetime.now().timestamp()
        if now - self.last_request_time < self.app_settings.rate_limit_delay / 1000:
            return False
        self.last_request_time = now
        return len(text) >= self.app_settings.min_search_chars

    def on_fernverkehr_changed(self):
        if self.fernverkehr_only.get():
            self.nahverkehr_only.deselect()

    def on_nahverkehr_changed(self):
        if self.nahverkehr_only.get():
            self.fernverkehr_only.deselect()

    def _resolve_destination_plan(self, stop_entries, destination_name):
        if not destination_name:
            return set(), []
        to_stop_id = self.motis.resolve_stop_id(destination_name)
        if not to_stop_id:
            logger.warning("Zielstation nicht gefunden: %s", destination_name)
            return set(), []
        from_stop_ids = [entry["id"] for entry in stop_entries]
        return self.motis.resolve_destination_plan(from_stop_ids, to_stop_id)

    def update_list(self):
        station_name = self.station_combo.get().strip()
        if not station_name:
            self._show_error("❌ Bitte Bahnhof eingeben")
            self.status_label.configure(text="❌ Bitte Bahnhof eingeben", text_color="red")
            return
        destination_name = self.destination_combo.get().strip()
        try:
            sanitize_station_name(station_name)
            if destination_name:
                sanitize_destination_name(destination_name)
        except SanitizationError as error:
            self._show_error(f"❌ Ungültige Eingabe: {error}")
            self.status_label.configure(text="❌ Ungültige Eingabe", text_color="red")
            return
        self.history.save_last(station_name)
        self.history.add(station_name)
        if destination_name:
            self.history.save_last_destination(destination_name)
            self.history.add_destination(destination_name)
        self.status_label.configure(text="⏳ Lade Daten...", text_color="orange")
        self.update_idletasks()
        try:
            stop_entries = self.resolver.resolve(station_name)
            if not stop_entries:
                self._show_error(f"❌ Keine verifizierte Station gefunden für '{station_name}'")
                self.status_label.configure(text="❌ Station nicht verifiziert", text_color="red")
                return
            self.current_station_id = stop_entries[0]["id"]
            logger.info("Verwende %s Stop-ID(s): %s", len(stop_entries), ", ".join(entry["id"] for entry in stop_entries))
            destination_trip_ids = set()
            if destination_name:
                destination_trip_ids, extra_stops = self._resolve_destination_plan(stop_entries, destination_name)
                stop_entries = stop_entries + extra_stops
            stoptimes_count = STOPTIMES_WITH_DESTINATION if destination_name else STOPTIMES_DEFAULT
            raw_departures = self.departures.fetch_merged(stop_entries, per_stop_count=stoptimes_count)
            if not raw_departures:
                self._show_info("ℹ️ Keine Abfahrten verfügbar", "orange")
                self.status_label.configure(text="⚠️ Keine Abfahrten", text_color="orange")
                return
            departure_filter = build_departure_filter(self.fernverkehr_only.get(), self.nahverkehr_only.get(), self.filter_lines.get().strip(), destination_name, destination_trip_ids)
            filtered = self.departures.parse_stop_times(raw_departures, departure_filter)
            if not filtered and destination_name:
                self._show_info(f"ℹ️ Keine Abfahrten Richtung {destination_name} im aktuellen Fenster", "orange")
                self.status_label.configure(text=f"⚠️ Keine Treffer Richtung {destination_name}", text_color="orange")
                return
            self._display_departures(filtered, destination_name)
        except requests.exceptions.Timeout:
            self._show_error("❌ Fehler: API antwortet nicht (Timeout)")
            self.status_label.configure(text="❌ Timeout", text_color="red")
            logger.error("Timeout bei API-Anfrage")
        except requests.exceptions.ConnectionError:
            self._show_error("❌ Fehler: Keine Internetverbindung")
            self.status_label.configure(text="❌ Keine Verbindung", text_color="red")
            logger.error("Fehler: Keine Verbindung zur API")
        except Exception as error:
            self._show_error(f"❌ Fehler: {error}")
            self.status_label.configure(text="❌ Fehler", text_color="red")
            logger.error("Fehler: %s", error)

    def start_auto_update(self):
        self.update_list()
        self.after(self.app_settings.update_interval, self.start_auto_update)

    def _display_departures(self, valid_departures, destination_name=""):
        next_departure = valid_departures[0] if valid_departures else None
        next_trip_key = trip_notification_key(next_departure) if next_departure else None
        if next_trip_key != self._current_next_trip_key:
            self.last_notified_trip = None
            self._current_next_trip_key = next_trip_key
        self._update_next_train_banner(next_departure, destination_name)
        self._clear_departures_tree()
        if not valid_departures:
            empty_msg = f"ℹ️ Keine Abfahrten Richtung {destination_name}" if destination_name else "ℹ️ Keine weiteren Abfahrten im aktuellen Fenster"
            self._show_info(empty_msg, "orange")
            self.status_label.configure(text="⚠️ Keine weiteren Abfahrten", text_color="orange")
            return
        for item in valid_departures:
            is_next = item is next_departure
            status_text, color = get_status_text(item["cancelled"], item["diff"])
            if is_next and item["diff"] > 0.5:
                self._check_alarm(item)
            self._insert_departure_row(item, status_text, is_next=is_next)
        self.status_label.configure(text=self._build_status_text(next_departure, valid_departures, destination_name), text_color="green")

    def _build_status_text(self, next_departure, valid_departures, destination_name=""):
        dest_hint = f" → {destination_name}" if destination_name else ""
        if not next_departure:
            return f"✅ {len(valid_departures)} Abfahrten{dest_hint} angezeigt"
        next_status, _ = get_status_text(next_departure["cancelled"], next_departure["diff"])
        minutes_in = minutes_until_departure(next_departure["actual_time"])
        countdown = "jetzt" if minutes_in <= 0 else f"in {minutes_in} Min"
        return f"Nächste{dest_hint}: {next_departure['linie']} {next_departure['zeit']} ({countdown}) · {next_status} · {len(valid_departures)} Abfahrten gesamt"

    def _update_next_train_banner(self, next_item, destination_name=""):
        if not next_item:
            empty_text = f"ℹ️ Keine Abfahrten Richtung {destination_name}" if destination_name else "ℹ️ Keine weiteren Abfahrten im aktuellen Fenster"
            self.next_train_label.configure(text=empty_text, text_color="orange")
            return
        minutes_in = minutes_until_departure(next_item["actual_time"])
        status_text, color = get_status_text(next_item["cancelled"], next_item["diff"])
        countdown = "jetzt" if minutes_in <= 0 else f"in {minutes_in} Min"
        dest_label = destination_name or next_item["direction"]
        self.next_train_label.configure(text=f"🚂 Deine nächste Bahn: {next_item['linie']} → {dest_label} · {next_item['zeit']} · {countdown} · {status_text}", text_color=color)

    def _departure_row_tags(self, item, is_next):
        tags = []
        if is_next:
            tags.append("next")
        if item["cancelled"]:
            tags.append("cancelled")
        elif item["diff"] > 15:
            tags.append("late")
        elif item["diff"] > 0.5:
            tags.append("delay")
        else:
            tags.append("ok")
        return tags

    def _insert_departure_row(self, item, status, is_next=False):
        status_text = f"▶ Nächste · {status}" if is_next else status
        self.departures_tree.insert("", "end", values=(item["zeit"], item["minutes_in"], item["linie"], item["typ_text"], status_text, item["direction"]), tags=self._departure_row_tags(item, is_next))

    def _clear_departures_tree(self):
        self.departures_tree.delete(*self.departures_tree.get_children())

    def _show_error(self, message):
        self.next_train_label.configure(text=message, text_color="red")
        self._clear_departures(message, "red")

    def _show_info(self, message, color="orange"):
        self.next_train_label.configure(text=message, text_color=color)
        self._clear_departures(message, color)

    def _clear_departures(self, message, color):
        self._clear_departures_tree()

    def _check_alarm(self, departure):
        trip_key = trip_notification_key(departure)
        if not self.alarm_active.get() or departure["diff"] < 10:
            return
        if self.last_notified_trip == trip_key:
            return
        now = datetime.now()
        if self.workdays_only.get() and now.weekday() > 4:
            return
        if not self._is_in_alarm_window(now.time()):
            return
        self._send_notification(departure["linie"], departure["diff"], departure["direction"])
        self.last_notified_trip = trip_key

    def _is_in_alarm_window(self, current_time: time):
        start = self._parse_time(self.start_time.get())
        end = self._parse_time(self.end_time.get())
        return bool(start and end and start <= current_time <= end)

    @staticmethod
    def _parse_time(value):
        try:
            return datetime.strptime(value, "%H:%M").time()
        except ValueError:
            return None

    def _send_notification(self, train, delay, destination):
        message = f"🚨 Achtung! {train} nach {destination} hat +{int(delay)} Min Verspätung!"
        try:
            response = requests.post(f"https://ntfy.sh/{self.app_settings.ntfy_topic}", data=message.encode("utf-8"), headers={"Title": "Bahn-Alarm Pi", "Priority": "high"}, verify=True, timeout=5)
            if response.status_code == 200:
                logger.info("Benachrichtigung erfolgreich gesendet")
            else:
                logger.warning("Benachrichtigung fehlgeschlagen: %s", response.status_code)
        except requests.exceptions.RequestException as error:
            logger.error("Konnte Nachricht nicht senden: %s", error)
