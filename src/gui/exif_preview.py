"""EXIF preview panel — shows metadata of the currently selected image file."""
import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


DISPLAY_TAGS = [
    ("FileName",          "Dateiname"),
    ("DateTimeOriginal",  "Aufnahmedatum"),
    ("CreateDate",        "Erstelldatum"),
    ("ModifyDate",        "Änderungsdatum"),
    ("GPSLatitude",       "Breitengrad"),
    ("GPSLongitude",      "Längengrad"),
    ("GPSAltitude",       "Höhe ü. NN"),
    ("Make",              "Kamerahersteller"),
    ("Model",             "Kameramodell"),
    ("LensModel",         "Objektiv"),
    ("FocalLength",       "Brennweite"),
    ("Aperture",          "Blende"),
    ("ExposureTime",      "Belichtungszeit"),
    ("ISO",               "ISO"),
    ("ImageSize",         "Bildgröße"),
    ("FileSize",          "Dateigröße"),
    ("MIMEType",          "Dateityp"),
]

THUMBNAIL_SIZE = (180, 180)


class ExifPreviewPanel(ttk.LabelFrame):
    def __init__(self, parent, exiftool):
        super().__init__(parent, text="EXIF-Vorschau")
        self.exiftool = exiftool
        self._current_file: Optional[str] = None
        self._thumb_ref = None
        self._build()

    def _build(self):
        self._thumb_label = ttk.Label(self, text="Kein Bild ausgewählt",
                                      anchor=tk.CENTER, foreground="gray")
        self._thumb_label.pack(fill=tk.X, padx=8, pady=(8, 4))

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=8, pady=2)

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._tag_frame = ttk.Frame(self._canvas)

        self._tag_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.create_window((0, 0), window=self._tag_frame, anchor=tk.NW)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Cross-platform scroll: Windows/macOS use <MouseWheel> with delta,
        # Linux/X11 (incl. noVNC) uses Button-4 / Button-5
        if sys.platform == "win32":
            self._canvas.bind_all(
                "<MouseWheel>",
                lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units")
            )
        else:
            self._canvas.bind_all(
                "<Button-4>",
                lambda e: self._canvas.yview_scroll(-1, "units")
            )
            self._canvas.bind_all(
                "<Button-5>",
                lambda e: self._canvas.yview_scroll(1, "units")
            )

        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var, foreground="gray",
                  font=("Segoe UI", 8)).pack(fill=tk.X, padx=8, pady=(0, 4))

    def load_file(self, filepath: str):
        if filepath == self._current_file:
            return
        self._current_file = filepath
        self._status_var.set("Lade EXIF-Daten...")
        self.update_idletasks()
        self._update_thumbnail(filepath)
        self._update_tags(filepath)
        self._status_var.set(os.path.basename(filepath))

    def clear(self):
        self._current_file = None
        self._thumb_label.config(image="", text="Kein Bild ausgewählt")
        self._thumb_ref = None
        for widget in self._tag_frame.winfo_children():
            widget.destroy()
        self._status_var.set("")

    def _update_thumbnail(self, filepath: str):
        if not PIL_AVAILABLE:
            self._thumb_label.config(
                image="", text="(pip install Pillow für Thumbnail-Vorschau)",
                foreground="gray"
            )
            return
        try:
            img = Image.open(filepath)
            img.thumbnail(THUMBNAIL_SIZE)
            self._thumb_ref = ImageTk.PhotoImage(img)
            self._thumb_label.config(image=self._thumb_ref, text="")
        except Exception:
            self._thumb_label.config(image="", text="⚠ Vorschau nicht verfügbar",
                                     foreground="orange")
            self._thumb_ref = None

    def _update_tags(self, filepath: str):
        for widget in self._tag_frame.winfo_children():
            widget.destroy()
        try:
            data = self.exiftool.read_metadata_extended(filepath)
        except Exception as e:
            ttk.Label(self._tag_frame, text=f"Fehler: {e}",
                      foreground="red", wraplength=200).pack(anchor=tk.W, padx=4)
            return

        row = 0
        for tag_key, label in DISPLAY_TAGS:
            value = data.get(tag_key)
            if not value:
                continue
            ttk.Label(self._tag_frame, text=f"{label}:",
                      font=("Segoe UI", 8, "bold"), anchor=tk.W
                      ).grid(row=row, column=0, sticky=tk.W, padx=(4, 2), pady=1)
            val_entry = tk.Entry(
                self._tag_frame,
                font=("Segoe UI", 8),
                relief=tk.FLAT,
                readonlybackground=self._tag_frame.cget("background"),
                state="readonly",
                width=24
            )
            val_entry.insert(0, str(value))
            val_entry.config(state="readonly")
            val_entry.grid(row=row, column=1, sticky=tk.W, padx=(0, 4), pady=1)
            row += 1

        if row == 0:
            ttk.Label(self._tag_frame, text="Keine EXIF-Daten gefunden.",
                      foreground="gray").grid(row=0, column=0, columnspan=2, padx=4, pady=4)
