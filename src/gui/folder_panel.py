"""Folder selection panel."""
import os
import tkinter as tk
from tkinter import ttk, filedialog

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".raw", ".cr2", ".nef", ".arw"}


class FolderPanel(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Ordner auswählen")
        self.on_folder_selected = None  # callback
        self._selected_folder = tk.StringVar()
        self._build()

    def _build(self):
        self._entry = ttk.Entry(self, textvariable=self._selected_folder, state="readonly", width=70)
        self._entry.pack(side=tk.LEFT, padx=(5, 5), pady=8, fill=tk.X, expand=True)

        btn = ttk.Button(self, text="Durchsuchen...", command=self._browse)
        btn.pack(side=tk.LEFT, padx=(0, 5), pady=8)

    def _browse(self):
        folder = filedialog.askdirectory(title="Ordner auswählen")
        if not folder:
            return
        self._selected_folder.set(folder)
        files = self._scan_folder(folder)
        if self.on_folder_selected:
            self.on_folder_selected(files)

    def _scan_folder(self, folder: str) -> list[str]:
        """Return list of image file paths in folder."""
        result = []
        for entry in sorted(os.scandir(folder), key=lambda e: e.name):
            if entry.is_file() and os.path.splitext(entry.name)[1].lower() in IMAGE_EXTENSIONS:
                result.append(entry.path)
        return result
