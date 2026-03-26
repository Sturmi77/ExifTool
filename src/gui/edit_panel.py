"""Edit panel for date and GPS location."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

try:
    from .map_picker import MapPickerDialog, MAP_AVAILABLE
except ImportError:
    MAP_AVAILABLE = False


class EditPanel(ttk.LabelFrame):
    def __init__(self, parent, exiftool, file_listbox):
        super().__init__(parent, text="Metadaten bearbeiten")
        self.exiftool = exiftool
        self.file_listbox = file_listbox
        self._build()

    def _build(self):
        # --- Date/Time row ---
        date_frame = ttk.Frame(self)
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(date_frame, text="Datum & Zeit:").pack(side=tk.LEFT)
        self._date_var = tk.StringVar(value=datetime.now().strftime("%Y:%m:%d %H:%M:%S"))
        ttk.Entry(date_frame, textvariable=self._date_var, width=22).pack(side=tk.LEFT, padx=5)
        ttk.Label(date_frame, text="(Format: YYYY:MM:DD HH:MM:SS)", foreground="gray").pack(side=tk.LEFT)

        # --- GPS row ---
        gps_frame = ttk.Frame(self)
        gps_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(gps_frame, text="Breitengrad (Lat):").pack(side=tk.LEFT)
        self._lat_var = tk.StringVar()
        ttk.Entry(gps_frame, textvariable=self._lat_var, width=14).pack(side=tk.LEFT, padx=5)

        ttk.Label(gps_frame, text="Längengrad (Lon):").pack(side=tk.LEFT)
        self._lon_var = tk.StringVar()
        ttk.Entry(gps_frame, textvariable=self._lon_var, width=14).pack(side=tk.LEFT, padx=5)

        # Map picker button
        if MAP_AVAILABLE:
            ttk.Button(
                gps_frame,
                text="🗺 Karte öffnen",
                command=self._open_map_picker
            ).pack(side=tk.LEFT, padx=(4, 0))
        else:
            ttk.Label(
                gps_frame,
                text="(pip install tkintermapview für Kartenauswahl)",
                foreground="gray"
            ).pack(side=tk.LEFT, padx=5)

        ttk.Label(gps_frame, text="(z.B. 48.4010, 16.1680)", foreground="gray").pack(side=tk.LEFT, padx=8)

        # --- Buttons ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=(5, 8))

        ttk.Button(btn_frame, text="Auf Auswahl anwenden", command=self._apply_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Auf alle Dateien anwenden", command=self._apply_all).pack(side=tk.LEFT)
        ttk.Label(
            btn_frame,
            text="  ⚠ Originale werden automatisch gesichert (_original)",
            foreground="gray"
        ).pack(side=tk.LEFT, padx=10)

    def _open_map_picker(self):
        """Open the map picker dialog and receive selected coordinates."""
        initial_lat = None
        initial_lon = None
        try:
            if self._lat_var.get():
                initial_lat = float(self._lat_var.get())
            if self._lon_var.get():
                initial_lon = float(self._lon_var.get())
        except ValueError:
            pass

        MapPickerDialog(
            self,
            on_confirm=self._on_coords_selected,
            initial_lat=initial_lat,
            initial_lon=initial_lon
        )

    def _on_coords_selected(self, lat: float, lon: float):
        """Callback: receives confirmed coordinates from MapPickerDialog."""
        self._lat_var.set(f"{lat:.6f}")
        self._lon_var.set(f"{lon:.6f}")

    def _get_selected_files(self) -> list[str]:
        indices = self.file_listbox.curselection()
        return [self.file_listbox.get(i) for i in indices]

    def _get_all_files(self) -> list[str]:
        return list(self.file_listbox.get(0, tk.END))

    def _apply(self, files: list[str]):
        if not files:
            messagebox.showwarning("Keine Dateien", "Bitte Dateien auswählen.")
            return
        date = self._date_var.get().strip() or None
        lat = self._lat_var.get().strip() or None
        lon = self._lon_var.get().strip() or None
        if not date and not lat and not lon:
            messagebox.showwarning("Keine Änderungen", "Bitte Datum oder GPS-Koordinaten eingeben.")
            return
        try:
            self.exiftool.write_metadata(files, date=date, lat=lat, lon=lon)
            messagebox.showinfo("Erfolg", f"{len(files)} Datei(en) erfolgreich aktualisiert.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def _apply_selected(self):
        self._apply(self._get_selected_files())

    def _apply_all(self):
        self._apply(self._get_all_files())
