import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional

# Core dependencies
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import tkinterdnd2 as tkdnd

from ..utils.constants import LOGGER_NAME, STATUS_READY
from .tooltip import Tooltip # Assuming Tooltip is also in its own file

class StatusBar(ttk.Frame):
    """Represents the application's status bar."""
    def __init__(self, parent, status_text: tk.StringVar, progress_value: tk.DoubleVar, **kwargs):
        super().__init__(parent, relief=tk.SUNKEN, borderwidth=1, **kwargs)
        self.logger = logging.getLogger(LOGGER_NAME)

        self.status_text = status_text
        self.progress_value = progress_value

        self._create_widgets()
        self.logger.debug("StatusBar initialized.")

    def _create_widgets(self):
        """Creates the widgets within the status bar frame."""
        self.status_label = ttk.Label(self, textvariable=self.status_text)
        self.status_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        Tooltip(self.status_label, "Displays current status, file counts, and informational messages.")

        self.progress_bar = ttk.Progressbar(self, variable=self.progress_value, mode="determinate", length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
        Tooltip(self.progress_bar, "Shows the progress of operations like merging or validation.")

    def set_status(self, message: str):
        """Sets the text in the status bar."""
        self.status_text.set(message)

    def set_progress(self, value: float, mode: str = "determinate", maximum: float = 100.0):
        """Sets the progress bar value, mode, and maximum."""
        self.progress_bar.config(mode=mode, maximum=maximum)
        self.progress_value.set(value)
        if mode == "indeterminate":
            self.progress_bar.start()
        else:
            self.progress_bar.stop()

    def clear_progress(self):
        """Resets the progress bar."""
        self.set_progress(0, mode="determinate")
        self.progress_bar.stop() # Ensure animation is stopped
        self.progress_value.set(0) # Explicitly set value to 0
