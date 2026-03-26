"""Modal date & time picker combining tkcalendar (calendar view) + time spinboxes.

Fallback: if tkcalendar is not installed, a plain Entry-based dialog is shown.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Callable, Optional

try:
    from tkcalendar import Calendar
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False


class DateTimePickerDialog(tk.Toplevel):
    """
    Modal dialog for selecting a date via calendar widget and
    entering a time via spinboxes (HH / MM / SS).
    The result is returned as EXIF-formatted string 'YYYY:MM:DD HH:MM:SS'
    via the on_confirm callback.
    """

    EXIF_FORMAT = "%Y:%m:%d %H:%M:%S"

    def __init__(self, parent, on_confirm: Callable[[str], None],
                 initial: Optional[str] = None):
        super().__init__(parent)
        self.title("Datum & Uhrzeit auswählen")
        self.resizable(False, False)
        self.grab_set()  # Modal

        self.on_confirm = on_confirm

        # Parse initial value or use now
        try:
            self._dt = datetime.strptime(initial, self.EXIF_FORMAT) if initial else datetime.now()
        except (ValueError, TypeError):
            self._dt = datetime.now()

        self._build_ui()
        self.update_idletasks()
        self._center(parent)

    def _center(self, parent):
        """Center dialog over parent window."""
        pw = parent.winfo_rootx() + parent.winfo_width() // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        if CALENDAR_AVAILABLE:
            self._build_calendar(**pad)
        else:
            self._build_fallback_date(**pad)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=2)
        self._build_time_row(**pad)
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=2)
        self._build_preview(**pad)
        self._build_buttons(**pad)

    # ------------------------------------------------------------------ #
    #  Calendar section                                                    #
    # ------------------------------------------------------------------ #

    def _build_calendar(self, **pad):
        """Full calendar widget (requires tkcalendar)."""
        frame = ttk.LabelFrame(self, text="Datum")
        frame.pack(fill=tk.X, **pad)

        self._calendar = Calendar(
            frame,
            selectmode="day",
            year=self._dt.year,
            month=self._dt.month,
            day=self._dt.day,
            date_pattern="yyyy/mm/dd",
            locale="de_AT",
            firstweekday="monday",
            showweeknumbers=False,
            font=("Segoe UI", 9),
        )
        self._calendar.pack(padx=6, pady=6)
        self._calendar.bind("<<CalendarSelected>>", self._on_date_selected)

    def _on_date_selected(self, _event=None):
        """Update preview when calendar date changes."""
        self._update_preview()

    def _build_fallback_date(self, **pad):
        """Simple date entry fallback when tkcalendar is not installed."""
        frame = ttk.LabelFrame(self, text="Datum (YYYY:MM:DD)")
        frame.pack(fill=tk.X, **pad)

        self._date_entry_var = tk.StringVar(value=self._dt.strftime("%Y:%m:%d"))
        entry = ttk.Entry(frame, textvariable=self._date_entry_var, width=14, justify="center",
                          font=("Courier", 11))
        entry.pack(padx=6, pady=8)
        entry.bind("<KeyRelease>", lambda e: self._update_preview())

        ttk.Label(frame, text="(pip install tkcalendar für Kalenderansicht)",
                  foreground="gray").pack(pady=(0, 4))

    # ------------------------------------------------------------------ #
    #  Time section                                                        #
    # ------------------------------------------------------------------ #

    def _build_time_row(self, **pad):
        """HH:MM:SS spinboxes for time selection."""
        frame = ttk.LabelFrame(self, text="Uhrzeit")
        frame.pack(fill=tk.X, **pad)

        inner = ttk.Frame(frame)
        inner.pack(pady=8)

        self._hour_var = tk.StringVar(value=f"{self._dt.hour:02d}")
        self._min_var = tk.StringVar(value=f"{self._dt.minute:02d}")
        self._sec_var = tk.StringVar(value=f"{self._dt.second:02d}")

        spin_opts = dict(width=4, justify="center", font=("Courier", 13), wrap=True)

        ttk.Label(inner, text="Stunde", font=("Segoe UI", 8)).grid(row=0, column=0, padx=6)
        ttk.Label(inner, text="Minute", font=("Segoe UI", 8)).grid(row=0, column=2, padx=6)
        ttk.Label(inner, text="Sekunde", font=("Segoe UI", 8)).grid(row=0, column=4, padx=6)

        tk.Spinbox(inner, from_=0, to=23, textvariable=self._hour_var,
                   command=self._update_preview, **spin_opts).grid(row=1, column=0, padx=6)
        ttk.Label(inner, text=":", font=("Courier", 16)).grid(row=1, column=1)
        tk.Spinbox(inner, from_=0, to=59, textvariable=self._min_var,
                   command=self._update_preview, **spin_opts).grid(row=1, column=2, padx=6)
        ttk.Label(inner, text=":", font=("Courier", 16)).grid(row=1, column=3)
        tk.Spinbox(inner, from_=0, to=59, textvariable=self._sec_var,
                   command=self._update_preview, **spin_opts).grid(row=1, column=4, padx=6)

        # Bind manual typing in spinboxes too
        for var in (self._hour_var, self._min_var, self._sec_var):
            var.trace_add("write", lambda *_: self._update_preview())

        # Quick-set buttons
        btn_row = ttk.Frame(frame)
        btn_row.pack(pady=(0, 6))
        ttk.Button(btn_row, text="Jetzt", width=8,
                   command=self._set_now).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Mitternacht", width=12,
                   command=self._set_midnight).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Mittag", width=8,
                   command=self._set_noon).pack(side=tk.LEFT, padx=4)

    def _set_now(self):
        now = datetime.now()
        self._hour_var.set(f"{now.hour:02d}")
        self._min_var.set(f"{now.minute:02d}")
        self._sec_var.set(f"{now.second:02d}")

    def _set_midnight(self):
        self._hour_var.set("00")
        self._min_var.set("00")
        self._sec_var.set("00")

    def _set_noon(self):
        self._hour_var.set("12")
        self._min_var.set("00")
        self._sec_var.set("00")

    # ------------------------------------------------------------------ #
    #  Preview & confirm                                                   #
    # ------------------------------------------------------------------ #

    def _build_preview(self, **pad):
        """Live preview of the resulting EXIF date string."""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, **pad)
        ttk.Label(frame, text="EXIF-Wert:").pack(side=tk.LEFT)
        self._preview_var = tk.StringVar(value=self._build_exif_string())
        ttk.Label(frame, textvariable=self._preview_var,
                  font=("Courier", 11), foreground="#0055aa").pack(side=tk.LEFT, padx=6)

    def _build_buttons(self, **pad):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, **pad)
        ttk.Button(frame, text="✔ Übernehmen", command=self._confirm).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(frame, text="Abbrechen", command=self.destroy).pack(side=tk.LEFT)

    def _get_selected_date_str(self) -> str:
        """Return selected date as 'YYYY:MM:DD' from calendar or fallback entry."""
        if CALENDAR_AVAILABLE:
            # tkcalendar returns e.g. '2026/03/26' with date_pattern yyyy/mm/dd
            raw = self._calendar.get_date()
            return raw.replace("/", ":")
        else:
            return self._date_entry_var.get().strip()

    def _build_exif_string(self) -> str:
        """Assemble the full EXIF datetime string from current inputs."""
        try:
            date_part = self._get_selected_date_str()  # YYYY:MM:DD
            h = int(self._hour_var.get())
            m = int(self._min_var.get())
            s = int(self._sec_var.get())
            return f"{date_part} {h:02d}:{m:02d}:{s:02d}"
        except (ValueError, AttributeError):
            return ""

    def _update_preview(self, *_):
        self._preview_var.set(self._build_exif_string())

    def _confirm(self):
        value = self._build_exif_string()
        if not value:
            return
        self.on_confirm(value)
        self.destroy()
