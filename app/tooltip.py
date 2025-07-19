import tkinter as tk
from tkinter import ttk
import sys
import logging
from typing import Optional

# Core dependencies
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import tkinterdnd2 as tkdnd

from app.constants import LOGGER_NAME

class Tooltip:
    """Provides tooltips for Tkinter widgets."""
    def __init__(self, widget, text, delay=500, wraplength=250):
        self.widget = widget
        self.text = text
        self.logger = logging.getLogger(LOGGER_NAME)

        if not self.text:
            self.logger.debug(f"Tooltip created for widget {widget} but no text provided.")
            return

        self.delay = delay
        self.wraplength = wraplength
        self.tooltip_window: Optional[tk.Toplevel] = None
        self._schedule_id: Optional[str] = None
        self._visible = False

        self.widget.bind("<Enter>", self._schedule_tooltip, add="+")
        self.widget.bind("<Leave>", self._hide_tooltip_now, add="+")
        self.widget.bind("<ButtonPress>", self._hide_tooltip_now, add="+")
        self.widget.bind("<Unmap>", self._hide_tooltip_now, add="+")
        self.widget.bind("<Destroy>", self._destroy_tooltip, add="+")
        self.logger.debug(f"Tooltip initialized for widget {widget} with text: '{text[:50]}...'")


    def _schedule_tooltip(self, event=None):
        """Schedules the tooltip to appear after a delay."""
        self._unschedule_tooltip()
        self._schedule_id = self.widget.after(self.delay, self._check_and_show_tooltip)

    def _check_and_show_tooltip(self):
        """Checks mouse position and shows the tooltip if still over the widget."""
        try:
            if not self.widget.winfo_exists() or not self.widget.winfo_ismapped():
                 self._hide_tooltip_now()
                 return

            pointer_x, pointer_y = self.widget.winfo_pointerx(), self.widget.winfo_pointery()
            widget_under_pointer = self.widget.winfo_containing(pointer_x, pointer_y)

            if widget_under_pointer == self.widget:
                self._show_tooltip(pointer_x, pointer_y)
            else:
                self._hide_tooltip_now()

        except tk.TclError:
            self._hide_tooltip_now()
        except Exception as e:
            self.logger.error(f"Error in tooltip _check_and_show_tooltip: {e}", exc_info=True)
            self._hide_tooltip_now()


    def _unschedule_tooltip(self):
        """Cancels any pending scheduled tooltip."""
        if self._schedule_id:
            try:
                self.widget.after_cancel(self._schedule_id)
            except tk.TclError:
                pass
            self._schedule_id = None

    def _show_tooltip(self, x_root, y_root):
        """Creates and displays the tooltip window."""
        if self._visible or not self.text:
            return

        self._visible = True
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)

        try:
            if sys.platform == "darwin":
                tw.wm_attributes("-toolwindow", True)
            elif sys.platform.startswith("linux") or sys.platform.startswith("freebsd"):
                tw.wm_attributes("-type", "tooltip")
            else:
                 tw.wm_attributes("-topmost", True)
        except tk.TclError:
            self.logger.warning(f"Tooltip: Failed to set platform-specific attribute for {sys.platform}. Falling back to -topmost.")
            try: tw.wm_attributes("-topmost", True)
            except tk.TclError: self.logger.error("Tooltip: Failed to set -topmost attribute.")

        frame = ttk.Frame(tw, padding=(5, 3), style="Tooltip.TFrame")
        frame.pack(fill="both", expand=True)

        label = ttk.Label(frame, text=self.text, justify='left',
                          wraplength=self.wraplength, style="Tooltip.TLabel")
        label.pack(fill="both", expand=True)

        self._position_tooltip(x_root, y_root)
        tw.update_idletasks()

    def _position_tooltip(self, x_root, y_root):
        """Positions the tooltip window near the mouse pointer, adjusting for screen boundaries."""
        if not self.tooltip_window or not self._visible:
            return

        tw = self.tooltip_window
        tw.update_idletasks()

        x, y = x_root + 15, y_root + 10

        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        tip_width = tw.winfo_width()
        tip_height = tw.winfo_height()

        if x + tip_width > screen_width:
            x = x_root - tip_width - 5
        if y + tip_height > screen_height:
            y = y_root - tip_height - 5

        if x < 0: x = 0
        if y < 0: y = 0

        tw.wm_geometry(f"+{int(x)}+{int(y)}")

    def _hide_tooltip_now(self, event=None):
        """Hides the tooltip immediately and cancels any scheduled show."""
        self._unschedule_tooltip()
        if self.tooltip_window and self._visible:
            try:
                self.tooltip_window.destroy()
            except tk.TclError:
                pass
            self.tooltip_window = None
        self._visible = False

    def _destroy_tooltip(self, event=None):
        """Cleans up when the parent widget is destroyed."""
        self._hide_tooltip_now()