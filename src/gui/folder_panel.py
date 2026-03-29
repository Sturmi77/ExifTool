"""Folder/file selection panel — supports folder picker AND individual file picker."""
import os
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".raw", ".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2"}

# Standard-Startverzeichnis im Container (gemounteter Host-Ordner)
DEFAULT_PHOTOS_DIR = "/photos"


class FolderPanel(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Dateien laden")
        self.on_files_changed: Optional[Callable[[list[str]], None]] = None
        self._recursive_var = tk.BooleanVar(value=False)
        self._build()

    def _build(self):
        # Row 1: folder selection
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, padx=5, pady=(6, 2))

        ttk.Label(row1, text="Ordner:").pack(side=tk.LEFT)
        self._folder_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._folder_var, state="readonly", width=45).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Schnell-Laden: direkt /photos öffnen ohne Dialog
        ttk.Button(row1, text="📂 Fotos-Ordner",
                   command=self._load_default_dir).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(row1, text="📁 Ordner wählen",
                   command=self._browse_folder).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Checkbutton(row1, text="Unterordner",
                        variable=self._recursive_var).pack(side=tk.LEFT, padx=(4, 0))

        # Row 2: single/multiple file selection
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

    # ------------------------------------------------------------------ #

    def _load_default_dir(self):
        """Direkt /photos laden ohne Dialog — schnellster Weg im Container."""
        folder = DEFAULT_PHOTOS_DIR
        if not os.path.isdir(folder):
            tk.messagebox.showwarning(
                "Ordner nicht gefunden",
                f"'{folder}' existiert nicht.\nBitte PHOTOS_DIR im Config Set prüfen."
            )
            return
        self._folder_var.set(folder)
        files = self._scan_folder(folder, recursive=self._recursive_var.get())
        self._files_label_var.set(f"{len(files)} Bild(er) aus Fotos-Ordner geladen")
        self._notify(files)

    def _browse_folder(self):
        """Ordner-Dialog — startet immer bei /photos."""
        start = DEFAULT_PHOTOS_DIR if os.path.isdir(DEFAULT_PHOTOS_DIR) else "/"
        folder = filedialog.askdirectory(
            title="Ordner mit Fotos auswählen",
            initialdir=start
        )
        if not folder:
            return
        self._folder_var.set(folder)
        files = self._scan_folder(folder, recursive=self._recursive_var.get())
        self._files_label_var.set(f"{len(files)} Bild(er) aus Ordner geladen")
        self._notify(files)

    def _browse_files(self):
        """Datei-Dialog — startet immer bei /photos."""
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

    def _scan_folder(self, folder: str, recursive: bool = False) -> list[str]:
        result = []
        if recursive:
            for root, _, filenames in os.walk(folder):
                for name in sorted(filenames):
                    if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
                        result.append(os.path.join(root, name))
        else:
            for entry in sorted(os.scandir(folder), key=lambda e: e.name):
                if entry.is_file() and os.path.splitext(entry.name)[1].lower() in IMAGE_EXTENSIONS:
                    result.append(entry.path)
        return result

    def _notify(self, files: list[str]):
        if self.on_files_changed:
            self.on_files_changed(files)
