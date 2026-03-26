"""Modal map window to pick GPS coordinates by clicking on OpenStreetMap."""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

try:
    from tkintermapview import TkinterMapView
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False


class MapPickerDialog(tk.Toplevel):
    """
    A modal dialog showing an interactive OpenStreetMap.
    The user clicks on the map to pick GPS coordinates.
    The selected lat/lon is returned via the `on_confirm` callback.
    """

    DEFAULT_LAT = 48.401   # Stockerau, Lower Austria
    DEFAULT_LON = 16.168
    DEFAULT_ZOOM = 10

    def __init__(self, parent, on_confirm: Callable[[float, float], None],
                 initial_lat: Optional[float] = None,
                 initial_lon: Optional[float] = None):
        super().__init__(parent)
        self.title("Ort auf Karte auswählen")
        self.geometry("800x600")
        self.resizable(True, True)
        self.grab_set()  # Modal

        self.on_confirm = on_confirm
        self._lat = initial_lat or self.DEFAULT_LAT
        self._lon = initial_lon or self.DEFAULT_LON
        self._marker = None

        self._build_ui()
        self._init_map()

    def _build_ui(self):
        """Build toolbar and map widget."""
        # --- Toolbar ---
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(toolbar, text="Adresse / Ort suchen:").pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        self._search_entry = ttk.Entry(toolbar, textvariable=self._search_var, width=35)
        self._search_entry.pack(side=tk.LEFT, padx=4)
        self._search_entry.bind("<Return>", lambda e: self._search_address())
        ttk.Button(toolbar, text="Suchen", command=self._search_address).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Separator(toolbar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Label(toolbar, text="Lat:").pack(side=tk.LEFT)
        self._lat_var = tk.StringVar(value=f"{self._lat:.6f}")
        lat_entry = ttk.Entry(toolbar, textvariable=self._lat_var, width=12)
        lat_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(toolbar, text="Lon:").pack(side=tk.LEFT, padx=(6, 0))
        self._lon_var = tk.StringVar(value=f"{self._lon:.6f}")
        lon_entry = ttk.Entry(toolbar, textvariable=self._lon_var, width=12)
        lon_entry.pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="Koordinaten anwenden", command=self._jump_to_coords).pack(side=tk.LEFT, padx=6)

        # --- Status bar ---
        self._status_var = tk.StringVar(value="Auf die Karte klicken um einen Standort zu wählen.")
        status_bar = ttk.Label(self, textvariable=self._status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)

        # --- Button row ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)
        ttk.Button(btn_frame, text="✔ Koordinaten übernehmen", command=self._confirm).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="Abbrechen", command=self.destroy).pack(side=tk.LEFT)

        # Reverse geocode button
        ttk.Button(btn_frame, text="📍 Adresse anzeigen", command=self._reverse_geocode).pack(side=tk.RIGHT)

        # --- Map ---
        self._map_widget = TkinterMapView(self, corner_radius=0)
        self._map_widget.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

    def _init_map(self):
        """Set initial map position and register click handler."""
        self._map_widget.set_position(self._lat, self._lon)
        self._map_widget.set_zoom(self.DEFAULT_ZOOM)
        self._map_widget.add_left_click_map_command(self._on_map_click)
        # Show marker for initial coords if provided
        self._place_marker(self._lat, self._lon)

    def _on_map_click(self, coords: tuple):
        """Called when user clicks the map."""
        lat, lon = coords
        self._lat = lat
        self._lon = lon
        self._lat_var.set(f"{lat:.6f}")
        self._lon_var.set(f"{lon:.6f}")
        self._place_marker(lat, lon)
        self._status_var.set(f"Ausgewählt: {lat:.6f}, {lon:.6f}")

    def _place_marker(self, lat: float, lon: float):
        """Remove old marker and place a new one."""
        if self._marker:
            self._marker.delete()
        self._marker = self._map_widget.set_marker(
            lat, lon,
            text=f"{lat:.5f}, {lon:.5f}"
        )

    def _search_address(self):
        """Jump map to searched address using OSM Nominatim."""
        query = self._search_var.get().strip()
        if not query:
            return
        self._status_var.set(f"Suche nach '{query}'...")
        self.update_idletasks()
        try:
            self._map_widget.set_address(query, marker=False)
            # After set_address, center coords are updated — get new position
            pos = self._map_widget.get_position()
            if pos:
                lat, lon = pos
                self._lat = lat
                self._lon = lon
                self._lat_var.set(f"{lat:.6f}")
                self._lon_var.set(f"{lon:.6f}")
                self._place_marker(lat, lon)
                self._status_var.set(f"Gefunden: {lat:.6f}, {lon:.6f}")
        except Exception as e:
            self._status_var.set(f"Fehler bei der Suche: {e}")

    def _jump_to_coords(self):
        """Pan map to manually entered coordinates."""
        try:
            lat = float(self._lat_var.get())
            lon = float(self._lon_var.get())
            self._lat = lat
            self._lon = lon
            self._map_widget.set_position(lat, lon)
            self._map_widget.set_zoom(12)
            self._place_marker(lat, lon)
            self._status_var.set(f"Springe zu: {lat:.6f}, {lon:.6f}")
        except ValueError:
            self._status_var.set("⚠ Ungültige Koordinaten. Bitte Dezimalzahlen eingeben (z.B. 48.401, 16.168)")

    def _reverse_geocode(self):
        """Show human-readable address for current marker position."""
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="ExifToolGUI/1.0")
            location = geolocator.reverse(f"{self._lat}, {self._lon}", language="de")
            if location:
                self._status_var.set(f"📍 {location.address}")
            else:
                self._status_var.set("Keine Adresse gefunden.")
        except Exception as e:
            self._status_var.set(f"Geocoding-Fehler: {e}")

    def _confirm(self):
        """Return selected coordinates and close dialog."""
        self.on_confirm(self._lat, self._lon)
        self.destroy()
