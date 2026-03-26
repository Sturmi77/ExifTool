"""Edit panel for date and GPS location — including copy-from-file feature."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

try:
    from .map_picker import MapPickerDialog, MAP_AVAILABLE
except ImportError:
    MAP_AVAILABLE = False

try:
    from .date_picker import DateTimePickerDialog
except ImportError:
    pass

IMAGE_EXTENSIONS = (
    "*.jpg", "*.jpeg", "*.png", "*.tiff", "*.tif",
    "*.heic", "*.raw", "*.cr2", "*.nef", "*.arw", "*.dng"
)


class EditPanel(ttk.LabelFrame):
    def __init__(self, parent, exiftool, file_listbox):
        super().__init__(parent, text="Metadaten bearbeiten")
        self.exiftool = exiftool
        self.file_listbox = file_listbox
        self._build()

    def _build(self):
        # ── Row 1: Copy from reference file ───────────────────────────
        copy_frame = ttk.LabelFrame(self, text="Metadaten von Referenzdatei übernehmen")
        copy_frame.pack(fill=tk.X, padx=5, pady=(6, 2))

        inner_copy = ttk.Frame(copy_frame)
        inner_copy.pack(fill=tk.X, padx=5, pady=6)

        self._ref_file_var = tk.StringVar(value="— keine Referenzdatei ausgewählt —")
        ttk.Label(inner_copy, textvariable=self._ref_file_var,
                  foreground="gray", anchor=tk.W, width=50).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(inner_copy, text="📎 Referenzdatei wählen",
                   command=self._pick_reference_file).pack(side=tk.LEFT, padx=(0, 6))

        self._copy_date_var = tk.BooleanVar(value=True)
        self._copy_gps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(inner_copy, text="Datum",
                        variable=self._copy_date_var).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(inner_copy, text="GPS",
                        variable=self._copy_gps_var).pack(side=tk.LEFT, padx=2)

        self._copy_btn = ttk.Button(
            inner_copy, text="→ In Felder übernehmen",
            command=self._copy_from_reference, state=tk.DISABLED
        )
        self._copy_btn.pack(side=tk.LEFT, padx=(8, 0))

        self._ref_info_var = tk.StringVar(value="")
        ttk.Label(copy_frame, textvariable=self._ref_info_var,
                  foreground="#0055aa", font=("Segoe UI", 8)
                  ).pack(anchor=tk.W, padx=8, pady=(0, 4))

        # ── Row 2: Date/Time ───────────────────────────────────────
        date_frame = ttk.Frame(self)
        date_frame.pack(fill=tk.X, padx=5, pady=4)

        ttk.Label(date_frame, text="Datum & Zeit:").pack(side=tk.LEFT)
        self._date_var = tk.StringVar(value=datetime.now().strftime("%Y:%m:%d %H:%M:%S"))
        ttk.Entry(date_frame, textvariable=self._date_var, width=22).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="📅 Kalender",
                   command=self._open_date_picker).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(date_frame, text="(YYYY:MM:DD HH:MM:SS)",
                  foreground="gray").pack(side=tk.LEFT)

        # ── Row 3: GPS ────────────────────────────────────────────
        gps_frame = ttk.Frame(self)
        gps_frame.pack(fill=tk.X, padx=5, pady=4)

        ttk.Label(gps_frame, text="Breitengrad (Lat):").pack(side=tk.LEFT)
        self._lat_var = tk.StringVar()
        ttk.Entry(gps_frame, textvariable=self._lat_var, width=14).pack(side=tk.LEFT, padx=5)
        ttk.Label(gps_frame, text="Längengrad (Lon):").pack(side=tk.LEFT)
        self._lon_var = tk.StringVar()
        ttk.Entry(gps_frame, textvariable=self._lon_var, width=14).pack(side=tk.LEFT, padx=5)

        if MAP_AVAILABLE:
            ttk.Button(gps_frame, text="🗺 Karte öffnen",
                       command=self._open_map_picker).pack(side=tk.LEFT, padx=(4, 0))
        else:
            ttk.Label(gps_frame, text="(pip install tkintermapview)",
                      foreground="gray").pack(side=tk.LEFT, padx=5)
        ttk.Label(gps_frame, text="(z.B. 48.4010, 16.1680)",
                  foreground="gray").pack(side=tk.LEFT, padx=8)

        # ── Row 4: Apply buttons ───────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=(4, 8))
        ttk.Button(btn_frame, text="Auf Auswahl anwenden",
                   command=self._apply_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Auf alle Dateien anwenden",
                   command=self._apply_all).pack(side=tk.LEFT)
        ttk.Label(btn_frame, text="  ⚠ Originale werden als _original gesichert",
                  foreground="gray").pack(side=tk.LEFT, padx=10)

    # ------------------------------------------------------------------ #
    # Copy-from-reference                                                  #
    # ------------------------------------------------------------------ #

    def _pick_reference_file(self):
        path = filedialog.askopenfilename(
            title="Referenzdatei auswählen",
            filetypes=[
                ("Bilddateien", " ".join(IMAGE_EXTENSIONS)),
                ("Alle Dateien", "*.*")
            ]
        )
        if not path:
            return
        self._ref_file_path = path
        self._ref_file_var.set(path)
        self._copy_btn.config(state=tk.NORMAL)

        # Read and preview metadata of reference
        try:
            data = self.exiftool.read_metadata_extended(path)
            date = data.get("DateTimeOriginal", "")
            lat  = data.get("GPSLatitude", "")
            lon  = data.get("GPSLongitude", "")
            parts = []
            if date: parts.append(f"Datum: {date}")
            if lat:  parts.append(f"Lat: {lat}")
            if lon:  parts.append(f"Lon: {lon}")
            self._ref_info_var.set("  ℹ " + "   │   ".join(parts) if parts else "  ⚠ Keine Datum/GPS-Daten gefunden")
            self._ref_meta = data
        except Exception as e:
            self._ref_info_var.set(f"  ⚠ Fehler beim Lesen: {e}")
            self._ref_meta = {}

    def _copy_from_reference(self):
        """Transfer date and/or GPS from reference file into the input fields."""
        meta = getattr(self, "_ref_meta", {})
        if not meta:
            messagebox.showwarning("Keine Daten", "Keine Metadaten der Referenzdatei gefunden.")
            return

        copied = []
        if self._copy_date_var.get():
            date = meta.get("DateTimeOriginal") or meta.get("CreateDate")
            if date:
                self._date_var.set(str(date))
                copied.append("Datum")

        if self._copy_gps_var.get():
            lat = meta.get("GPSLatitude")
            lon = meta.get("GPSLongitude")
            if lat and lon:
                # ExifTool returns e.g. '48.4010 N' — extract numeric part
                self._lat_var.set(str(lat).split()[0])
                self._lon_var.set(str(lon).split()[0])
                copied.append("GPS")

        if copied:
            messagebox.showinfo("Metadaten übernommen",
                                f"{', '.join(copied)} aus Referenzdatei in Felder eingetragen.\n"
                                f"Jetzt 'Anwenden' drücken um zu schreiben.")
        else:
            messagebox.showwarning("Keine Daten",
                                   "Die gewählten Felder (Datum/GPS) sind in der Referenzdatei nicht vorhanden.")

    # ------------------------------------------------------------------ #
    # Date / Map pickers                                                   #
    # ------------------------------------------------------------------ #

    def _open_date_picker(self):
        try:
            from .date_picker import DateTimePickerDialog
            DateTimePickerDialog(self, on_confirm=lambda v: self._date_var.set(v),
                                 initial=self._date_var.get())
        except ImportError:
            pass

    def _open_map_picker(self):
        initial_lat = initial_lon = None
        try:
            if self._lat_var.get(): initial_lat = float(self._lat_var.get())
            if self._lon_var.get(): initial_lon = float(self._lon_var.get())
        except ValueError:
            pass
        MapPickerDialog(self, on_confirm=lambda la, lo: (
            self._lat_var.set(f"{la:.6f}"), self._lon_var.set(f"{lo:.6f}")
        ), initial_lat=initial_lat, initial_lon=initial_lon)

    def _on_coords_selected(self, lat, lon):
        self._lat_var.set(f"{lat:.6f}")
        self._lon_var.set(f"{lon:.6f}")

    # ------------------------------------------------------------------ #
    # Apply                                                                #
    # ------------------------------------------------------------------ #

    def _get_selected_files(self):
        return [self.file_listbox.get(i) for i in self.file_listbox.curselection()]

    def _get_all_files(self):
        return list(self.file_listbox.get(0, tk.END))

    def _apply(self, files):
        if not files:
            messagebox.showwarning("Keine Dateien", "Bitte Dateien auswählen.")
            return
        date = self._date_var.get().strip() or None
        lat  = self._lat_var.get().strip() or None
        lon  = self._lon_var.get().strip() or None
        if not any([date, lat, lon]):
            messagebox.showwarning("Keine Änderungen", "Bitte Datum oder GPS eingeben.")
            return
        try:
            self.exiftool.write_metadata(files, date=date, lat=lat, lon=lon)
            messagebox.showinfo("Erfolg", f"{len(files)} Datei(en) erfolgreich aktualisiert.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def _apply_selected(self): self._apply(self._get_selected_files())
    def _apply_all(self):      self._apply(self._get_all_files())
