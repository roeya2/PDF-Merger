import tkinter as tk
from tkinter import ttk
import os
import logging
from typing import Dict, Any, Optional

# Core dependencies
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import tkinterdnd2 as tkdnd

from app.constants import LOGGER_NAME, DEFAULT_OUTPUT_FILENAME, DEFAULT_COMPRESSION, DEFAULT_PRESERVE_BOOKMARKS, DEFAULT_PASSWORD_PROTECT, DEFAULT_COLOR_MODE, DEFAULT_DPI, PDF_FILETYPE, ALL_FILES_FILETYPE
from app.config_manager import ConfigManager # Assuming ConfigManager is in its own file
from app.tooltip import Tooltip # Assuming Tooltip is also in its own file

class OutputPanel(ttk.LabelFrame):
    """Represents the Output Options section of the UI."""
    def __init__(self, parent, config_manager: ConfigManager, output_path_var: tk.StringVar, compression_level_var: tk.StringVar, preserve_bookmarks_var: tk.BooleanVar, password_protect_var: tk.BooleanVar, password_var: tk.StringVar, color_mode_var: tk.StringVar, dpi_var: tk.StringVar, **kwargs):
        super().__init__(parent, text="Output Options", padding=10, **kwargs)
        self.logger = logging.getLogger(LOGGER_NAME)

        self.config_manager = config_manager
        self.output_path = output_path_var
        self.compression_level = compression_level_var
        self.preserve_bookmarks = preserve_bookmarks_var
        self.output_password_protect = password_protect_var
        self.output_password = password_var
        self.output_color_mode = color_mode_var
        self.output_dpi = dpi_var

        self._create_widgets()
        self._bind_events()
        self.toggle_password_entry_state() # Set initial state of password entry

        self.logger.debug("OutputPanel initialized.")

    def _create_widgets(self):
        """Creates the widgets within the output options panel."""
        Tooltip(self, "Settings for the final merged PDF file.")

        # Layout in two columns
        col1_frame = ttk.Frame(self)
        col1_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))

        # Output File Path
        path_frame = ttk.Frame(col1_frame)
        path_frame.pack(fill=tk.X, pady=2, anchor="w")
        ttk.Label(path_frame, text="Output File:").pack(side=tk.LEFT, padx=(0, 5))
        self.output_entry = ttk.Entry(path_frame, textvariable=self.output_path)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        Tooltip(self.output_entry, "Path and filename for the merged PDF file.")

        self.choose_output_btn = ttk.Button(path_frame, text="Choose...", command=self._choose_output_file)
        self.choose_output_btn.pack(side=tk.LEFT)
        Tooltip(self.choose_output_btn, "Browse to select an output file location and name.")

        # Compression and Bookmarks
        comp_frame = ttk.Frame(col1_frame)
        comp_frame.pack(fill=tk.X, pady=2, anchor="w")
        ttk.Label(comp_frame, text="Compression:").pack(side=tk.LEFT, padx=(0, 5))
        comp_dropdown_values = ["none", "fast", "normal", "maximum"]
        self.comp_dropdown = ttk.Combobox(comp_frame, textvariable=self.compression_level, values=comp_dropdown_values, width=10, state="readonly")
        self.comp_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        self.comp_dropdown.set(self.config_manager.config.get("compression_level", DEFAULT_COMPRESSION))
        Tooltip(self.comp_dropdown, "Set compression level for the output PDF. 'None' is fastest; 'Maximum' yields smaller files but is slower.")

        self.bookmark_check = ttk.Checkbutton(comp_frame, text="Preserve Bookmarks", variable=self.preserve_bookmarks)
        self.bookmark_check.pack(side=tk.LEFT)
        Tooltip(self.bookmark_check, "If checked, bookmarks (outlines) from the source PDFs will be included in the merged file.")


        col2_frame = ttk.Frame(self)
        col2_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))

        # Password Protection
        pass_protect_frame = ttk.Frame(col2_frame)
        pass_protect_frame.pack(fill=tk.X, pady=2, anchor="w")
        self.pass_protect_cb = ttk.Checkbutton(pass_protect_frame, text="Protect with password:", variable=self.output_password_protect)
        self.pass_protect_cb.pack(side=tk.LEFT)
        Tooltip(self.pass_protect_cb, "Check to encrypt the output PDF with a password.")

        self.password_entry = ttk.Entry(pass_protect_frame, textvariable=self.output_password, show="*", width=15)
        self.password_entry.pack(side=tk.LEFT, padx=5)
        Tooltip(self.password_entry, "Enter the password to be used for encrypting the output PDF if 'Protect' is checked.")

        # Color Mode (Experimental)
        color_mode_frame = ttk.Frame(col2_frame)
        color_mode_frame.pack(fill=tk.X, pady=2, anchor="w")
        ttk.Label(color_mode_frame, text="Color Mode:").pack(side=tk.LEFT, padx=(0,5))
        color_modes = ["Colorful (Original)", "Grayscale (Experimental)", "B&W (Experimental)"]
        self.color_mode_combo = ttk.Combobox(color_mode_frame, textvariable=self.output_color_mode, values=color_modes, width=20, state="readonly")
        self.color_mode_combo.pack(side=tk.LEFT)
        self.color_mode_combo.set(self.config_manager.config.get("output_color_mode", DEFAULT_COLOR_MODE))
        Tooltip(self.color_mode_combo, "Select output color mode (Note: This feature requires advanced PDF processing and is not yet functional).")
        ttk.Label(color_mode_frame, text="(Experimental, not yet functional)", foreground="gray").pack(side=tk.LEFT, padx=5)


        # DPI (Experimental)
        dpi_frame = ttk.Frame(col2_frame)
        dpi_frame.pack(fill=tk.X, pady=2, anchor="w")
        ttk.Label(dpi_frame, text="DPI:").pack(side=tk.LEFT, padx=(0,5))
        dpi_options = ["Original", "72", "96", "150", "300", "600"]
        self.dpi_combo = ttk.Combobox(dpi_frame, textvariable=self.output_dpi, values=dpi_options, width=10, state="readonly")
        self.dpi_combo.pack(side=tk.LEFT)
        self.dpi_combo.set(self.config_manager.config.get("output_dpi", DEFAULT_DPI))
        Tooltip(self.dpi_combo, "Select output DPI (dots per inch) (Note: This feature requires advanced PDF processing and is not yet functional).")
        ttk.Label(dpi_frame, text="(Experimental, not yet functional)", foreground="gray").pack(side=tk.LEFT, padx=5)


    def _bind_events(self):
        """Binds events for UI elements in this panel."""
        self.output_password_protect.trace_add("write", lambda *_: self.toggle_password_entry_state())

    def toggle_password_entry_state(self):
        """Enables/disables the password entry based on the checkbox state."""
        if self.output_password_protect.get():
            self.password_entry.config(state=tk.NORMAL)
        else:
            self.password_entry.config(state=tk.DISABLED)
            self.output_password.set("") # Clear password when protection is disabled

    def _choose_output_file(self):
        """Opens a save file dialog for the output PDF."""
        self.logger.debug("Choose output file dialog initiated.")
        current_output_path = self.output_path.get()
        initial_dir = os.path.dirname(current_output_path) or self.config_manager.config.get("default_output_dir", str(Path.home()))
        initial_file = os.path.basename(current_output_path) or DEFAULT_OUTPUT_FILENAME

        path = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".pdf",
            filetypes=[PDF_FILETYPE, ALL_FILES_FILETYPE],
            parent=self # Parent should be the main window or top-level, but self works for basic dialogs
        )
        if path:
            self.output_path.set(path)
            try:
                 # Save the directory as the default output directory
                 self.config_manager.config["default_output_dir"] = os.path.dirname(path)
                 # config_manager.save_config() # Config save happens on app close now
            except Exception as e:
                 self.logger.warning(f"Failed to set default output directory {os.path.dirname(path)}: {e}")

            self.logger.info(f"Output file set to: {path}")
            # Update status bar - This should be done by the main app class or a shared status object
            # self.status_text.set(f"Output file set to: {os.path.basename(path)}") # Removed direct status update


    def get_output_settings(self) -> Dict[str, Any]:
        """Retrieves the current output settings from the UI."""
        settings = {
            "output_path": self.output_path.get().strip(),
            "compression_level": self.compression_level.get(),
            "preserve_bookmarks": self.preserve_bookmarks.get(),
            "password_protect": self.output_password_protect.get(),
            "password": self.output_password.get(), # Get password only when needed
            "color_mode": self.output_color_mode.get(),
            "dpi": self.output_dpi.get()
        }
        self.logger.debug(f"Retrieved output settings: {settings}")
        return settings

    def apply_settings_from_profile(self, profile_data: Dict[str, Any]):
        """Applies relevant settings from a loaded profile."""
        self.compression_level.set(profile_data.get("compression_level", DEFAULT_COMPRESSION))
        self.preserve_bookmarks.set(profile_data.get("preserve_bookmarks", DEFAULT_PRESERVE_BOOKMARKS))
        self.output_password_protect.set(profile_data.get("output_password_protect", DEFAULT_PASSWORD_PROTECT))
        self.output_color_mode.set(profile_data.get("output_color_mode", DEFAULT_COLOR_MODE))
        self.output_dpi.set(profile_data.get("output_dpi", DEFAULT_DPI))
        # Do NOT set password from profile data
        self.toggle_password_entry_state() # Ensure password entry state is correct

        self.logger.debug(f"Applied settings from profile.")