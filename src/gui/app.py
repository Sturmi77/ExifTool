"""Main application window."""
import tkinter as tk
from tkinter import ttk, messagebox
from .folder_panel import FolderPanel
from .edit_panel import EditPanel
from core.exiftool import ExifToolWrapper


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ExifTool GUI")
        self.geometry("800x600")
        self.resizable(True, True)

        self.exiftool = ExifToolWrapper()
        self._check_exiftool()
        self._build_ui()

    def _check_exiftool(self):
        """Verify that exiftool binary is available."""
        if not self.exiftool.is_available():
            messagebox.showerror(
                "ExifTool not found",
                "ExifTool is not installed or not in PATH.\n"
                "Please install it from https://exiftool.org/"
            )
            self.destroy()

    def _build_ui(self):
        """Build main layout."""
        # Top: Folder selection
        self.folder_panel = FolderPanel(self)
        self.folder_panel.pack(fill=tk.X, padx=10, pady=(10, 0))

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=8)

        # Middle: File list
        frame_list = ttk.LabelFrame(self, text="Dateien im Ordner")
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10)

        self.file_listbox = tk.Listbox(frame_list, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind folder panel to populate list
        self.folder_panel.on_folder_selected = self._on_folder_selected

        # Bottom: Edit panel
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=8)
        self.edit_panel = EditPanel(self, self.exiftool, self.file_listbox)
        self.edit_panel.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _on_folder_selected(self, files):
        """Populate file list when folder is chosen."""
        self.file_listbox.delete(0, tk.END)
        for f in files:
            self.file_listbox.insert(tk.END, f)
