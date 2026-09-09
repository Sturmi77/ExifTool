"""Main application window."""
import tkinter as tk
from tkinter import ttk, messagebox
from .folder_panel import FolderPanel
from .edit_panel import EditPanel
from .exif_preview import ExifPreviewPanel
from core.exiftool import ExifToolWrapper


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ExifTool GUI")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.resizable(True, True)

        # Grid-basiertes Layout: mittlerer Bereich wächst, unterer Edit-Block bleibt sichtbar
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)  # middle frame dehnt sich, nicht der Edit-Block

        self.exiftool = ExifToolWrapper()
        self._check_exiftool()
        self._build_ui()

    def _check_exiftool(self):
        if not self.exiftool.is_available():
            messagebox.showerror(
                "ExifTool nicht gefunden",
                "ExifTool ist nicht installiert oder nicht im PATH.\n"
                "Bitte installieren: https://exiftool.org/"
            )
            self.destroy()

    def _build_ui(self):
        # ── Top: folder/file selection ──────────────────────────────────
        self.folder_panel = FolderPanel(self)
        self.folder_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.folder_panel.on_files_changed = self._on_files_changed

        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=10, pady=6
        )

        # ── Middle: horizontal split (file list | EXIF preview) ─────────
        middle = ttk.Frame(self)
        middle.grid(row=2, column=0, sticky="nsew", padx=10)

        # Links: Dateiliste
        list_frame = ttk.LabelFrame(middle, text="Dateien")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.file_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            activestyle="dotbox",
            font=("Segoe UI", 9)
        )
        sb_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        sb_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.file_listbox.xview)
        self.file_listbox.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)

        # Auswahl-Info
        self._sel_info_var = tk.StringVar(value="")
        ttk.Label(
            list_frame,
            textvariable=self._sel_info_var,
            foreground="gray",
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, padx=4, pady=2)

        # Bind selection change → update EXIF preview
        self.file_listbox.bind("<<ListboxSelect>>", self._on_file_select)

        # Rechts: EXIF-Vorschau (feste Breite)
        self.exif_preview = ExifPreviewPanel(middle, self.exiftool)
        self.exif_preview.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        self.exif_preview.config(width=240)

        # ── Bottom: edit panel ──────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").grid(
            row=3, column=0, sticky="ew", padx=10, pady=6
        )
        self.edit_panel = EditPanel(self, self.exiftool, self.file_listbox)
        self.edit_panel.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))

    # ------------------------------------------------------------------ #

    def _on_files_changed(self, files: list[str]):
        """Repopulate file list when folder or files selection changes."""
        self.file_listbox.delete(0, tk.END)
        for f in files:
            self.file_listbox.insert(tk.END, f)
        self.exif_preview.clear()
        self._sel_info_var.set(f"{len(files)} Datei(en) geladen")

    def _on_file_select(self, _event=None):
        """Load EXIF preview for the first selected file."""
        indices = self.file_listbox.curselection()
        if not indices:
            self.exif_preview.clear()
            self._sel_info_var.set("")
            return

        count = len(indices)
        self._sel_info_var.set(
            f"{count} von {self.file_listbox.size()} Datei(en) ausgewählt"
        )
        # Preview only first selected file
        filepath = self.file_listbox.get(indices[0])
        self.exif_preview.load_file(filepath)
