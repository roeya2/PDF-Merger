import os
import sys
import logging
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from pathlib import Path
from typing import Optional

from constants import (
    LOGGER_NAME, DEFAULT_FONT_FAMILY, HEADER_FONT_SIZE, TITLE_FONT_SIZE,
    ACTION_BUTTON_FONT_SIZE, FALLBACK_FONT_SIZE, TOOLTIP_BACKGROUND,
    TOOLTIP_FOREGROUND, TOOLTIP_LABEL_PADDING, DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
)
from app.exceptions import PDFMergerError


class AppInitializer:
    """Handles application initialization including window state, styles, and icons."""
    
    def __init__(self, app):
        """Initialize with reference to main app instance."""
        self.app = app
        self.logger = logging.getLogger(LOGGER_NAME)
        self._app_icon_png: Optional[tk.PhotoImage] = None

    def setup_styles(self):
        """Sets up ttk styles and fonts."""
        style = ttk.Style()
        preferred_themes = ["azure", "clam", "alt", "vista", "xpnative", "winnative", "default"]
        if sys.platform == "darwin":
            preferred_themes.insert(0, "aqua")

        theme_set = False
        current_theme = style.theme_use()
        for theme_name in preferred_themes:
            try:
                if theme_name in style.theme_names():
                    style.theme_use(theme_name)
                    self.logger.info(f"Using theme: {theme_name}")
                    theme_set = True
                    break
            except tk.TclError:
                self.logger.warning(f"Failed to apply theme: {theme_name}")

        if not theme_set:
            self.logger.info(f"Using default theme: {style.theme_use()}")

        # Define custom styles with constants
        try:
            header_font = tkfont.Font(family=DEFAULT_FONT_FAMILY, size=HEADER_FONT_SIZE, weight="bold")
            title_font = tkfont.Font(family=DEFAULT_FONT_FAMILY, size=TITLE_FONT_SIZE, weight="bold")
            action_button_font = tkfont.Font(family=DEFAULT_FONT_FAMILY, size=ACTION_BUTTON_FONT_SIZE, weight="bold")
        except tk.TclError as e:
            self.logger.warning(f"Could not create '{DEFAULT_FONT_FAMILY}' font. Falling back to system defaults.")
            raise PDFMergerError(f"Could not create font: {e}")

        style.configure("Header.TLabel", font=header_font)
        style.configure("Title.TLabel", font=title_font)
        style.configure("Preview.TFrame", relief="sunken", borderwidth=1)
        style.configure("Action.TButton", font=action_button_font)
        style.configure("Tooltip.TLabel", background=TOOLTIP_BACKGROUND, foreground=TOOLTIP_FOREGROUND, padding=TOOLTIP_LABEL_PADDING)
        style.configure("Tooltip.TFrame", background=TOOLTIP_BACKGROUND, relief="solid", borderwidth=1)

        self.logger.debug("Styles configured.")

    def apply_window_state(self):
        """Applies loaded window geometry and minimum size."""
        saved_geometry = self.app._saved_geometry
        
        if saved_geometry:
            try:
                self.app.root.geometry(saved_geometry)
                self.logger.debug(f"Applied saved window geometry: {saved_geometry}")
            except tk.TclError as e:
                raise PDFMergerError(f"Invalid saved window geometry: '{saved_geometry}'. Using default.")
        else:
            self.app.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")

        self.app.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    def apply_saved_sash_positions(self):
        """Applies sash positions loaded from configuration to the paned window."""
        if hasattr(self.app, 'upper_panedwindow') and self.app.upper_panedwindow.winfo_exists():
            sash_positions = self.app._saved_sash_positions.get('upper_panedwindow')
            if sash_positions and isinstance(sash_positions, (list, tuple)) and len(sash_positions) > 0:
                try:
                    self.app.upper_panedwindow.sashpos(0, sash_positions[0])
                    self.logger.debug(f"Applied saved sash position: {sash_positions[0]}")
                except tk.TclError as e:
                    self.logger.warning(f"Failed to apply saved sash positions {sash_positions}: {e}")
                except IndexError:
                    self.logger.warning(f"Saved sash positions {sash_positions} has unexpected format.")
            elif sash_positions:
                self.logger.warning(f"Saved sash positions {sash_positions} has unexpected format. Expected list/tuple.")

        # Clear the stored positions after attempting to apply
        self.app._saved_sash_positions = {}

    def load_application_icon(self):
        """Loads and sets the application window icon."""
        try:
            icon_set_by_photo = False
            icon_set_by_bitmap = False

            # Attempt to load .png with iconphoto
            png_path = Path("pdf-merger-pro-logo.png")
            if png_path.exists():
                try:
                    self._app_icon_png = tk.PhotoImage(file=png_path)
                    self.app.root.iconphoto(True, self._app_icon_png)
                    self.logger.info(f"Successfully set application icon using iconphoto with {png_path}")
                    icon_set_by_photo = True
                except tk.TclError as photo_err:
                    raise PDFMergerError(f"Error loading PNG icon '{png_path}' with iconphoto: {photo_err}")

            # Also attempt to load .ico with iconbitmap (especially for Windows taskbar)
            ico_path = Path("assets/pdf-merger-pro-logo.ico")
            if ico_path.exists():
                try:
                    self.app.root.iconbitmap(str(ico_path))
                    self.logger.info(f"Successfully set application icon using iconbitmap with {ico_path}")
                    icon_set_by_bitmap = True
                except tk.TclError as ico_err:
                    raise PDFMergerError(f"Error loading ICO icon '{ico_path}' with iconbitmap: {ico_err}")

            if not icon_set_by_photo and not icon_set_by_bitmap:
                self.logger.warning("No application icon could be set from pdf-merger-pro-logo.png or pdf-merger-pro-logo.ico.")

        except Exception as e:
            self.logger.warning(f"General error during application icon setup: {e}", exc_info=True)