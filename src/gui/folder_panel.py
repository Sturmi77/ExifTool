"""Folder/file selection panel."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".raw",
                    ".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2"}
DEFAULT_PHOTOS_DIR = "/photos"


class FolderPanel(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Dateien laden")
        self.on_files_changed: Optional[Callable[[list[str]], None]] = None
        self._recursive_var = tk.BooleanVar(value=False)
        self._build()

    def _build(self):
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, padx=5, pady=(6, 2))

        ttk.Label(row1, text="Ordner:").pack(side=tk.LEFT)
        self._folder_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._folder_var, state="readonly", width=45).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(row1, text="📂 Fotos-Ordner",
                   command=self._load_default_dir).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(row1, text="📁 Ordner wählen",
                   command=self._browse_folder).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Checkbutton(row1, text="Unterordner",
                        variable=self._recursive_var).pack(side=tk.LEFT, padx=(4, 0))

        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, padx=5, pady=(2, 6))

        ttk.Label(row2, text="Einzeldateien:").pack(side=tk.LEFT)
        self._files_label_var = tk.StringVar(value="— keine Dateien ausgewählt —")
        ttk.Label(row2, textvariable=self._files_label_var,
                  foreground="gray", anchor=tk.W).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(row2, text="🖼 Dateien wählen",
                   command=self._browse_files).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(row2, text="✖ Liste leeren",
                   command=self._clear).pack(side=tk.LEFT)

    def _load_default_dir(self):
        folder = DEFAULT_PHOTOS_DIR
        if not os.path.isdir(folder):
            messagebox.showwarning(
                "Ordner nicht gefunden",
                f"'{folder}' existiert nicht.\nBitte PHOTOS_DIR im Config Set prüfen."
            )
            return
        self._load_folder(folder)

    def _browse_folder(self):
        start = DEFAULT_PHOTOS_DIR if os.path.isdir(DEFAULT_PHOTOS_DIR) else "/"
        folder = filedialog.askdirectory(
            title="Ordner mit Fotos auswählen",
            initialdir=start
        )
        if folder:
            self._load_folder(folder)

    def _load_folder(self, folder: str):
        """Scannt Ordner und zeigt Ergebnis inkl. Fehlermeldung bei leerem Scan."""
        self._folder_var.set(folder)
        files, skipped = self._scan_folder(folder, recursive=self._recursive_var.get())

        if not files:
            msg = f"Keine Bilddateien in '{folder}' gefunden."
            if skipped:
                msg += f"\n\n{skipped} Ordner konnten nicht gelesen werden (Berechtigungen)."
            msg += "\n\nUnterstützte Formate: " + ", ".join(sorted(IMAGE_EXTENSIONS))
            messagebox.showinfo("Keine Dateien", msg)
        else:
            info = f"{len(files)} Bild(er) geladen"
            if skipped:
                info += f" ({skipped} Ordner übersprungen)"
            self._files_label_var.set(info)

        self._notify(files)

    def _browse_files(self):
        start = DEFAULT_PHOTOS_DIR if os.path.isdir(DEFAULT_PHOTOS_DIR) else "/"
        paths = filedialog.askopenfilenames(
            title="Einzelne Fotos auswählen",
            initialdir=start,
            filetypes=[
                ("Bilddateien", " ".join(f"*{ext}" for ext in IMAGE_EXTENSIONS)),
                ("Alle Dateien", "*.*"),
            ]
        )
        if not paths:
            return
        files = sorted(paths)
        self._folder_var.set("— Einzeldateien —")
        self._files_label_var.set(f"{len(files)} Datei(en) ausgewählt")
        self._notify(files)

    def _clear(self):
        self._folder_var.set("")
        self._files_label_var.set("— keine Dateien ausgewählt —")
        self._notify([])

    def _scan_folder(self, folder: str, recursive: bool = False) -> tuple[list[str], int]:
        """Scannt Ordner nach Bilddateien. Gibt (dateien, uebersprungene_ordner) zurueck."""
        result = []
        skipped = 0
        if recursive:
            for root, dirs, filenames in os.walk(folder, onerror=lambda e: None):
                # Synology-Systemordner überspringen
                dirs[:] = [d for d in dirs if not d.startswith('@') and d != '.@__thumb']
                for name in sorted(filenames):
                    if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
                        full = os.path.join(root, name)
                        try:
                            if os.access(full, os.R_OK):
                                result.append(full)
                        except OSError:
                            pass
        else:
            try:
                entries = sorted(os.scandir(folder), key=lambda e: e.name)
            except PermissionError:
                return [], 1
            for entry in entries:
                try:
                    if entry.is_file(follow_symlinks=False):
                        if os.path.splitext(entry.name)[1].lower() in IMAGE_EXTENSIONS:
                            if os.access(entry.path, os.R_OK):
                                result.append(entry.path)
                    elif entry.is_dir(follow_symlinks=False):
                        if entry.name.startswith('@') or entry.name == '.@__thumb':
                            skipped += 1
                except OSError:
                    skipped += 1
        return result, skipped

    def _notify(self, files: list[str]):
        if self.on_files_changed:
            self.on_files_changed(files)
